"""Prediction endpoints under `/v1/predictions/*`.

Supports both JSON and Server-Sent Events (SSE) via the `Accept` header:
  - `application/json`: awaits the full response, returns a single JSON body.
  - `text/event-stream`: streams agent events (tool_start, tool_result, final)
    as they arrive using FastAPI `StreamingResponse`.

Rate limiting: in-process sliding-window counter per client IP, configurable
via `predictions_rate_limit_per_minute` in Settings.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from threading import Lock
from typing import Any, AsyncIterator

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from service.agents import predict_next_draw, predict_scenario_path
from service.api.errors import ApiError
from service.api.statistics import _require_history
from service.config import get_settings
from service.store import list_predictions, save_next_draw, save_scenario_path

router = APIRouter(prefix="/predictions")

# ---------------------------------------------------------------------------
# Per-client rate limiter — sliding window, keyed by IP address
# ---------------------------------------------------------------------------

_RateLimitEntry = deque  # type: ignore[type-arg]
_rate_store: dict[str, deque[float]] = {}
_rate_lock = Lock()


def _check_rate_limit(client_ip: str) -> float | None:
    """Return None if the request is allowed. Return retry_after_seconds if not."""
    settings = get_settings()
    limit = settings.predictions_rate_limit_per_minute
    window = 60.0
    now = time.monotonic()
    with _rate_lock:
        if client_ip not in _rate_store:
            _rate_store[client_ip] = deque()
        timestamps = _rate_store[client_ip]
        # Evict entries outside the window
        while timestamps and timestamps[0] < now - window:
            timestamps.popleft()
        if len(timestamps) >= limit:
            oldest = timestamps[0]
            retry_after = (oldest + window) - now
            return max(retry_after, 1.0)
        timestamps.append(now)
        return None


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit_error(retry_after: float) -> ApiError:
    return ApiError(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        code="rate_limit_exceeded",
        message="Too many prediction requests. Please retry after the indicated delay.",
        details={"retry_after_seconds": round(retry_after, 1)},
    )


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class NextDrawRequest(BaseModel):
    baseline_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    learned_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    model: str | None = Field(default=None, description="Override LLM model name.")


class ScenarioPathRequest(BaseModel):
    horizon: int = Field(default=3, ge=1, le=10, description="Number of future draws to predict.")
    model: str | None = Field(default=None, description="Override LLM model name.")


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

_SSE_CONTENT_TYPE = "text/event-stream"


def _sse_event(data: Any) -> str:
    """Format a single SSE data event."""
    return f"data: {json.dumps(data)}\n\n"


async def _sse_stream_from_sync(
    gen: Any,
    on_final: Any = None,
) -> AsyncIterator[str]:
    """Wrap a synchronous generator in an async generator for StreamingResponse.

    If ``on_final`` is provided it is called with the prediction dict whenever
    an event with ``type == "final"`` is emitted, so the result can be
    persisted even when using SSE streaming.
    """
    loop = asyncio.get_event_loop()
    sentinel = object()

    def _next(it: Any) -> Any:
        try:
            return next(it)
        except StopIteration:
            return sentinel

    while True:
        value = await loop.run_in_executor(None, _next, gen)
        if value is sentinel:
            break
        if on_final is not None and isinstance(value, dict) and value.get("type") == "final":
            try:
                on_final(value.get("result", {}))
            except Exception:
                pass  # Never let a storage failure break the stream
        yield _sse_event(value)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/next-draw")
async def next_draw(
    body: NextDrawRequest,
    request: Request,
    accept: str = Header(default="application/json"),
) -> Any:
    """Predict the next Lotofácil draw.

    Supports JSON (default) and SSE (`Accept: text/event-stream`).
    """
    retry_after = _check_rate_limit(_client_ip(request))
    if retry_after is not None:
        err = _rate_limit_error(retry_after)
        if _SSE_CONTENT_TYPE in accept:
            # Even for SSE clients, rate-limit errors are returned as JSON.
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": {"code": err.code, "message": err.message, "details": err.details}},
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        raise err

    history = _require_history()

    if _SSE_CONTENT_TYPE in accept:
        gen = predict_next_draw(
            history,
            **({"model": body.model} if body.model else {}),
            streaming=True,
        )

        async def _stream() -> AsyncIterator[bytes]:
            async for chunk in _sse_stream_from_sync(gen, on_final=save_next_draw):
                yield chunk.encode()

        return StreamingResponse(
            _stream(),
            media_type=_SSE_CONTENT_TYPE,
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # JSON response — run synchronously in executor to avoid blocking
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: predict_next_draw(history, **({"model": body.model} if body.model else {}), streaming=False),
    )
    save_next_draw(result)
    return JSONResponse(content=result)


@router.post("/scenario-path")
async def scenario_path(
    body: ScenarioPathRequest,
    request: Request,
    accept: str = Header(default="application/json"),
) -> Any:
    """Predict a multi-draw scenario path.

    Supports JSON (default) and SSE (`Accept: text/event-stream`).
    Path-level confidence is monotonically non-increasing with horizon.
    """
    retry_after = _check_rate_limit(_client_ip(request))
    if retry_after is not None:
        err = _rate_limit_error(retry_after)
        if _SSE_CONTENT_TYPE in accept:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": {"code": err.code, "message": err.message, "details": err.details}},
                headers={"Retry-After": str(int(retry_after) + 1)},
            )
        raise err

    history = _require_history()

    if _SSE_CONTENT_TYPE in accept:
        gen = predict_scenario_path(
            history,
            horizon=body.horizon,
            **({"model": body.model} if body.model else {}),
            streaming=True,
        )

        async def _stream() -> AsyncIterator[bytes]:
            async for chunk in _sse_stream_from_sync(gen, on_final=save_scenario_path):
                yield chunk.encode()

        return StreamingResponse(
            _stream(),
            media_type=_SSE_CONTENT_TYPE,
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: predict_scenario_path(history, horizon=body.horizon, **({"model": body.model} if body.model else {}), streaming=False),
    )
    save_scenario_path(result)
    return JSONResponse(content=result)


@router.get("/history")
async def prediction_history(
    kind: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> Any:
    """Return paginated stored predictions (newest first).

    ``kind`` may be ``"next_draw"`` or ``"scenario_path"``. Omit to return both.
    """
    if kind not in (None, "next_draw", "scenario_path"):
        raise ApiError(
            status_code=400,
            code="invalid_kind",
            message='kind must be "next_draw", "scenario_path", or omitted.',
        )
    return list_predictions(kind=kind, page=page, page_size=page_size)  # type: ignore[arg-type]
