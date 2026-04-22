"""Liveness (`/v1/health`) and readiness (`/v1/ready`) endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Response, status

from service import __version__
from service.api import readiness as readiness_registry

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: always returns 200 while the process is up."""
    return {"status": "ok", "version": __version__}


@router.get("/ready")
async def ready(response: Response) -> dict[str, Any]:
    """Readiness: 200 only when every required check reports ok."""
    statuses = readiness_registry.snapshot()
    required_missing = [s for s in statuses if s.required and not s.ok]
    payload = {
        "ok": not required_missing,
        "version": __version__,
        "checks": [
            {
                "name": s.name,
                "ok": s.ok,
                "required": s.required,
                "detail": s.detail,
                "extra": s.extra,
            }
            for s in statuses
        ],
    }
    if required_missing:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        payload["missing"] = [s.name for s in required_missing]
    return payload
