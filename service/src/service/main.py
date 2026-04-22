"""FastAPI entrypoint.

Wires structured logging, fail-fast startup (ANTHROPIC_API_KEY, data.json),
ingestion, request-log middleware, and the ``/v1/health`` route. The rest of the
router surface (statistics, correlations, predictions) is added by downstream
capabilities and imported here as they land.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from service import __version__
from service.config import ConfigError, get_settings, require_runtime_ready
from service.ingestion import get_cached_history, ingest_from_settings
from service.logging_config import configure_logging

log = logging.getLogger("service.request")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    require_runtime_ready(settings)
    # Trigger ingestion once at startup so /ready can reflect actual state.
    ingest_from_settings(settings)
    logging.getLogger("service.startup").info(
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


@app.exception_handler(ConfigError)
async def _config_error_handler(_request: Request, exc: ConfigError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "configuration_error",
                "message": str(exc),
                "details": {},
            }
        },
    )


@app.middleware("http")
async def _request_log_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    start = time.perf_counter()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        status = 500
        log.exception(
            "request.error",
            extra={
                "request_id": request_id,
                "route": request.url.path,
                "method": request.method,
                "status": status,
                "duration_ms": round((time.perf_counter() - start) * 1000, 2),
            },
        )
        raise
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    history = get_cached_history()
    log.info(
        "request",
        extra={
            "request_id": request_id,
            "route": request.url.path,
            "method": request.method,
            "status": status,
            "duration_ms": duration_ms,
            "dataset_hash": history.provenance.content_hash if history else None,
        },
    )
    response.headers["x-request-id"] = request_id
    return response


@app.get("/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
