"""Calibration endpoint — `POST /v1/calibrate`."""

from __future__ import annotations

from fastapi import APIRouter

from service.api.errors import ApiError
from service.engine import CalibrationStatus, get_calibration_status, run_calibration
from service.ingestion import get_cached_history

router = APIRouter(prefix="/calibrate")


@router.post("", summary="Run or re-run prediction-engine calibration")
async def trigger_calibration() -> dict[str, object]:
    """Run the calibration pipeline against the loaded draw history.

    This is idempotent — calling it repeatedly is safe. The calibration result
    is stored in the process-global engine state and reflected immediately in
    ``GET /v1/ready``.
    """
    history = get_cached_history()
    if history is None:
        raise ApiError(
            status_code=503,
            code="ingestion_not_ready",
            message="Dataset not yet loaded; retry after /v1/ready returns 200.",
        )
    status: CalibrationStatus = run_calibration(history)
    return {
        "ok": not status.is_stale,
        "last_calibrated_at": (
            status.last_calibrated_at.isoformat()
            if status.last_calibrated_at is not None
            else None
        ),
        "eval_metrics": status.eval_metrics,
    }


@router.get("/status", summary="Get current calibration status")
async def calibration_status() -> dict[str, object]:
    """Return the current calibration status without triggering a run."""
    status = get_calibration_status()
    return {
        "ok": not status.is_stale,
        "last_calibrated_at": (
            status.last_calibrated_at.isoformat()
            if status.last_calibrated_at is not None
            else None
        ),
        "eval_metrics": status.eval_metrics,
    }
