"""Statistical-analysis endpoints under `/v1/statistics/*`."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from service.api.errors import ApiError
from service.ingestion import DrawHistory, get_cached_history
from service.statistics import (
    CooccurrenceResult,
    FrequencyResult,
    GapResult,
    HotColdThreshold,
    OrderResult,
    PiAlignmentResult,
    StructuralResult,
    WindowSelection,
    compute_cooccurrence,
    compute_frequency,
    compute_gaps,
    compute_order,
    compute_pi_alignment,
    compute_structural,
)

router = APIRouter(prefix="/statistics")


def _require_history() -> DrawHistory:
    history = get_cached_history()
    if history is None:
        raise ApiError(
            status_code=503,
            code="ingestion_not_ready",
            message="data.json has not been ingested yet",
        )
    return history


@router.get("/frequency")
async def frequency(
    window: Annotated[
        int | None,
        Query(
            ge=1,
            le=10000,
            description=("Rolling window size in draws. Omit for full-history frequency."),
        ),
    ] = None,
) -> FrequencyResult:
    selection = WindowSelection(kind="last_n", n=window) if window else None
    return compute_frequency(_require_history(), window=selection)


@router.get("/gaps")
async def gaps(
    hot_factor: Annotated[float, Query(gt=0.0, le=1.0)] = 0.5,
    cold_factor: Annotated[float, Query(gt=1.0, le=10.0)] = 2.0,
) -> GapResult:
    threshold = HotColdThreshold(hot_factor=hot_factor, cold_factor=cold_factor)
    return compute_gaps(_require_history(), threshold=threshold)


@router.get("/cooccurrence")
async def cooccurrence(
    arity: Annotated[int, Query(ge=2, le=4)] = 2,
    top_k: Annotated[int, Query(ge=1, le=500)] = 20,
) -> CooccurrenceResult:
    return compute_cooccurrence(_require_history(), arity=arity, top_k=top_k)


@router.get("/structural")
async def structural() -> StructuralResult:
    return compute_structural(_require_history())


@router.get("/order")
async def order() -> OrderResult:
    return compute_order(_require_history())


@router.get("/pi-alignment")
async def pi_alignment(
    rule: Annotated[str, Query(description="Rule name from the PI rule catalog.")],
    target_original_id: Annotated[
        int,
        Query(
            ge=1,
            description="Upstream draw id from data.json to evaluate the rule against.",
        ),
    ],
) -> PiAlignmentResult:
    history = _require_history()
    try:
        return compute_pi_alignment(history, rule=rule, target_original_id=target_original_id)
    except ValueError as exc:
        # Missing draw id → 404, unknown rule → 400. Distinguish by message.
        message = str(exc)
        if "not found" in message:
            raise ApiError(status_code=404, code="draw_not_found", message=message) from exc
        raise  # Let the global ValueError handler turn this into 400.
