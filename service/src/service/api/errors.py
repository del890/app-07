"""Canonical error envelope and FastAPI exception handlers.

Every non-success response uses:

    { "error": { "code": "<machine>", "message": "<human>", "details": {...} } }

Handlers are registered by `install_error_handlers(app)` in `main.py`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from service.config import ConfigError
from service.correlation.loader import SignalLoadError
from service.ingestion import DataIngestionError

log = logging.getLogger("service.error")


class ApiError(Exception):
    """Explicit error intended to surface via the canonical envelope."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


def _envelope(*, code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details or {}}}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error_handler(_req: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(code=exc.code, message=exc.message, details=exc.details),
        )

    @app.exception_handler(ConfigError)
    async def _config_error_handler(_req: Request, exc: ConfigError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_envelope(code="configuration_error", message=str(exc)),
        )

    @app.exception_handler(DataIngestionError)
    async def _ingestion_error_handler(_req: Request, exc: DataIngestionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=_envelope(code="ingestion_error", message=str(exc)),
        )

    @app.exception_handler(SignalLoadError)
    async def _signal_load_error_handler(_req: Request, exc: SignalLoadError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_envelope(code="signal_load_error", message=str(exc)),
        )

    @app.exception_handler(ValueError)
    async def _value_error_handler(_req: Request, exc: ValueError) -> JSONResponse:
        # Business-rule violations from capabilities (bad arity, unknown metric, etc.)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_envelope(code="bad_request", message=str(exc)),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_req: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=_envelope(
                code="validation_error",
                message="request body failed validation",
                details={"errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_exception_handler(_req: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
            status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(
                code=code_map.get(exc.status_code, "http_error"),
                message=str(exc.detail),
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(_req: Request, exc: Exception) -> JSONResponse:
        # Never leak exception text with our secret in it; message is generic.
        log.exception("unhandled_exception", extra={"exc_type": type(exc).__name__})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(
                code="internal_error",
                message="an unexpected error occurred",
            ),
        )
