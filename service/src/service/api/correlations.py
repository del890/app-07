"""Correlation endpoints under `/v1/correlations`."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from service.api.errors import ApiError
from service.api.statistics import _require_history  # reuse guard
from service.correlation import (
    AlignmentPolicyName,
    BatchCorrelationResult,
    CorrelationResult,
    MetricSpec,
    SignalSeries,
    correlate,
    correlate_batch,
)
from service.correlation import registry as signal_registry

router = APIRouter(prefix="/correlations")


class CorrelationRequest(BaseModel):
    """Single correlation request body."""

    signal: str = Field(min_length=1, description="Registered signal name.")
    metric: MetricSpec
    alignment: AlignmentPolicyName = "forward_fill"
    lag_draws: int = Field(default=0, ge=-100, le=100)
    min_sample_size: int = Field(default=30, ge=1, le=10000)


class BatchCorrelationRequest(BaseModel):
    """Batch correlation request body."""

    signals: list[str] = Field(min_length=1, description="Registered signal names.")
    metrics: list[MetricSpec] = Field(min_length=1)
    alignment: AlignmentPolicyName = "forward_fill"
    lag_draws: int = Field(default=0, ge=-100, le=100)
    min_sample_size: int = Field(default=30, ge=1, le=10000)


def _resolve_signal(name: str) -> SignalSeries:
    """Return the series or raise a 404 ApiError."""
    series = signal_registry.get(name)
    if series is None:
        raise ApiError(
            status_code=404,
            code="signal_not_found",
            message=f"signal '{name}' is not registered",
            details={"available": signal_registry.names()},
        )
    return series


@router.get("/signals")
async def list_signals() -> dict[str, object]:
    """List signals currently registered in the process.

    Empty when `service/signals/` is empty. Clients can introspect this to
    know which names to pass to `POST /correlations`.
    """
    out = []
    for name in signal_registry.names():
        series = signal_registry.get(name)
        assert series is not None
        out.append(
            {
                "name": series.name,
                "cadence": series.cadence,
                "unit": series.unit,
                "source": series.source,
                "description": series.description,
                "point_count": len(series.points),
                "first_date": series.points[0].date.isoformat(),
                "last_date": series.points[-1].date.isoformat(),
            }
        )
    return {"signals": out}


@router.post("")
async def correlate_single(body: CorrelationRequest) -> CorrelationResult:
    signal = _resolve_signal(body.signal)
    return correlate(
        _require_history(),
        signal=signal,
        metric=body.metric,
        alignment=body.alignment,
        lag_draws=body.lag_draws,
        min_sample_size=body.min_sample_size,
    )


@router.post("/batch")
async def correlate_batch_endpoint(
    body: BatchCorrelationRequest,
) -> BatchCorrelationResult:
    signals = [_resolve_signal(name) for name in body.signals]
    return correlate_batch(
        _require_history(),
        signals=signals,
        metrics=body.metrics,
        alignment=body.alignment,
        lag_draws=body.lag_draws,
        min_sample_size=body.min_sample_size,
    )
