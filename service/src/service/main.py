"""FastAPI entrypoint.

Startup sequence:
1. Configure structured JSON logging.
2. Validate runtime config (fails fast if ANTHROPIC_API_KEY missing).
3. Ingest `data.json` once.
4. Install default readiness checks (ingestion, calibration).
5. Scan `service/signals/` into the signal registry (best-effort).

The `/v1` surface is composed in `service.api` and mounted here.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request

from service import __version__
from service.api import api_router, install_error_handlers
from service.api import readiness as readiness_registry
from service.config import get_settings, require_runtime_ready
from service.correlation import registry as signal_registry
from service.correlation.loader import SignalLoadError
from service.ingestion import get_cached_history, ingest_from_settings
from service.logging_config import configure_logging

log = logging.getLogger("service.request")
startup_log = logging.getLogger("service.startup")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    require_runtime_ready(settings)

    ingest_from_settings(settings)

    readiness_registry.install_default_checks()

    try:
        loaded = signal_registry.load_directory()
        startup_log.info("signals.loaded", extra={"signals": loaded})
    except SignalLoadError as exc:
        # Missing metadata for a CSV is a config bug, not a runtime crash.
        # Log loudly and continue with whatever loaded successfully.
        startup_log.error("signals.load_error", extra={"error": str(exc)})

    startup_log.info(
        "service.ready",
        extra={
            "version": __version__,
            "env": settings.env,
            "dataset_path": str(settings.data_json_path),
        },
    )
    yield


app = FastAPI(
    title="Lotofácil Prediction Service",
    version=__version__,
    lifespan=lifespan,
)

install_error_handlers(app)
app.include_router(api_router)


@app.middleware("http")
async def _request_log_middleware(request: Request, call_next: Any) -> Any:
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    # Populate state for handlers to stash additional context (e.g. model_versions,
    # tool_call_count, token_usage) once predictions exist.
    request.state.log_extra = {}
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log.exception(
            "request.error",
            extra={
                "request_id": request_id,
                "route": request.url.path,
                "method": request.method,
                "status": 500,
                "duration_ms": duration_ms,
            },
        )
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    history = get_cached_history()
    extra = {
        "request_id": request_id,
        "route": request.url.path,
        "method": request.method,
        "status": status_code,
        "duration_ms": duration_ms,
        "dataset_hash": history.provenance.content_hash if history else None,
    }
    extra.update(getattr(request.state, "log_extra", {}) or {})
    log.info("request", extra=extra)
    response.headers["x-request-id"] = request_id
    return response
