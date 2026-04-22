"""API package.

Exposes a single `api_router` mounted at `/v1` by the FastAPI app, plus the
exception-handler installer. Route modules live alongside this file and are
composed here so the app entrypoint stays small.
"""

from __future__ import annotations

from fastapi import APIRouter

from service.api.correlations import router as correlations_router
from service.api.dataset import router as dataset_router
from service.api.errors import ApiError, install_error_handlers
from service.api.health import router as health_router
from service.api.statistics import router as statistics_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router, tags=["health"])
api_router.include_router(dataset_router, tags=["dataset"])
api_router.include_router(statistics_router, tags=["statistics"])
api_router.include_router(correlations_router, tags=["correlations"])

__all__ = ["ApiError", "api_router", "install_error_handlers"]
