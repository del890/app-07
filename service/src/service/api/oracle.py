"""Dream-oracle endpoint under ``/v1/oracle``."""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator

from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from service.oracle import interpret_dream
from service.oracle.guard import DreamGuardError, check_dream_description

router = APIRouter(prefix="/oracle")

_SSE_CONTENT_TYPE = "text/event-stream"


class DreamRequest(BaseModel):
    """Request body for the dream-oracle endpoint."""

    description: str = Field(
        min_length=1,
        max_length=2000,
        description="A dream, nightmare, or scenario description (max 2000 characters).",
    )


def _sse_event(data: Any) -> str:
    return f"data: {json.dumps(data)}\n\n"


async def _sse_stream_from_sync(gen: Any) -> AsyncIterator[str]:
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
        yield _sse_event(value)


@router.post("/dream")
async def dream_oracle(
    body: DreamRequest,
    accept: str = Header(default="application/json"),
) -> Any:
    """Interpret a dream description and return 15 Lotofácil number suggestions.

    Supports both ``application/json`` (default) and ``text/event-stream``.
    Results are labelled ``artifact_type: entertainment`` — no statistical basis.
    The dream description is never stored or logged.
    """
    # Validate input before any LLM call. Returns 422 on guard failure.
    try:
        check_dream_description(body.description)
    except DreamGuardError as exc:
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "invalid_description", "message": exc.reason, "details": {}}},
        )

    if _SSE_CONTENT_TYPE in accept:
        gen = interpret_dream(body.description, streaming=True)

        async def _stream() -> AsyncIterator[bytes]:
            async for chunk in _sse_stream_from_sync(gen):
                yield chunk.encode()

        return StreamingResponse(
            _stream(),
            media_type=_SSE_CONTENT_TYPE,
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: interpret_dream(body.description, streaming=False),
    )
    return JSONResponse(content=result)
