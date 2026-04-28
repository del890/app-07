"""Statistical-analysis endpoints under `/v1/statistics/*`."""

from __future__ import annotations

from itertools import combinations
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, field_validator

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


# ── Draw profile ──────────────────────────────────────────────────────────


class DrawProfileRequest(BaseModel):
    """15 unique integers in 1–25 representing the user's chosen draw."""

    numbers: list[int] = Field(
        min_length=15,
        max_length=15,
        description="Exactly 15 unique integers in 1–25.",
    )

    @field_validator("numbers")
    @classmethod
    def _validate_numbers(cls, v: list[int]) -> list[int]:
        for n in v:
            if n < 1 or n > 25:
                raise ValueError(f"Number {n} is outside the valid range 1–25.")
        if len(set(v)) != len(v):
            raise ValueError("Duplicate numbers are not allowed.")
        return v


class NumberProfile(BaseModel):
    """Frequency profile for a single number in the selection."""

    number: int
    historical_count: int
    frequency_rank: int  # 1 = most frequent across all 25 numbers


class PairCooccurrence(BaseModel):
    """Co-occurrence count for a pair of numbers in the selection."""

    numbers: tuple[int, int]
    count: int


class StructuralProfile(BaseModel):
    """Structural metrics for the 15-number selection."""

    total_sum: int
    even_count: int
    odd_count: int
    min_number: int
    max_number: int
    range_span: int  # max - min
    quintile_counts: list[int]  # 5 quintiles: [1-5], [6-10], [11-15], [16-20], [21-25]


class DatasetMatch(BaseModel):
    """A historical draw that exactly matches the user's selection."""

    original_id: int
    date: str  # ISO-8601


class DrawProfileResponse(BaseModel):
    """Full statistical profile for the user's draw combination."""

    numbers: list[int]  # sorted
    number_profiles: list[NumberProfile]
    pair_cooccurrences: list[PairCooccurrence]
    structural: StructuralProfile
    dataset_match: DatasetMatch | None


@router.post("/draw-profile")
async def draw_profile(body: DrawProfileRequest) -> DrawProfileResponse:
    """Return a statistical profile for a user-supplied 15-number draw combination."""
    history = _require_history()
    records = list(history)
    selected = sorted(set(body.numbers))

    # --- Per-number frequency count and rank ---
    all_counts: dict[int, int] = {n: 0 for n in range(1, 26)}
    for r in records:
        for n in r.numbers_sorted:
            all_counts[n] += 1

    # Rank 1 = highest count.
    sorted_by_freq = sorted(all_counts.items(), key=lambda x: -x[1])
    freq_rank: dict[int, int] = {n: i + 1 for i, (n, _) in enumerate(sorted_by_freq)}

    number_profiles = [
        NumberProfile(
            number=n,
            historical_count=all_counts[n],
            frequency_rank=freq_rank[n],
        )
        for n in selected
    ]

    # --- Pairwise co-occurrence ---
    pair_counts: dict[tuple[int, int], int] = {}
    for r in records:
        nums = set(r.numbers_sorted)
        for a, b in combinations(selected, 2):
            if a in nums and b in nums:
                key = (min(a, b), max(a, b))
                pair_counts[key] = pair_counts.get(key, 0) + 1

    pair_cooccurrences = [
        PairCooccurrence(numbers=(a, b), count=pair_counts.get((a, b), 0))
        for a, b in combinations(selected, 2)
    ]
    # Sort descending by count for easy consumption.
    pair_cooccurrences.sort(key=lambda p: -p.count)

    # --- Structural metrics ---
    quintile_counts = [0, 0, 0, 0, 0]
    for n in selected:
        quintile_counts[(n - 1) // 5] += 1

    structural = StructuralProfile(
        total_sum=sum(selected),
        even_count=sum(1 for n in selected if n % 2 == 0),
        odd_count=sum(1 for n in selected if n % 2 != 0),
        min_number=selected[0],
        max_number=selected[-1],
        range_span=selected[-1] - selected[0],
        quintile_counts=quintile_counts,
    )

    # --- Dataset match check ---
    selected_tuple = tuple(selected)
    dataset_match: DatasetMatch | None = None
    for r in records:
        if r.numbers_sorted == selected_tuple:
            dataset_match = DatasetMatch(
                original_id=r.original_id,
                date=r.iso_date.isoformat(),
            )
            break

    return DrawProfileResponse(
        numbers=selected,
        number_profiles=number_profiles,
        pair_cooccurrences=pair_cooccurrences,
        structural=structural,
        dataset_match=dataset_match,
    )
