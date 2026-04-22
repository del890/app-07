"""Gap statistics + deterministic hot/cold classification.

Thresholds (documented, deterministic):

    hot       if current_gap <  0.5 × mean_gap  (appearing more often than baseline)
    cold      if current_gap >  2.0 × mean_gap  (overdue)
    neutral   otherwise

These factors are the `HotColdThreshold` returned alongside every result — the
rule is explicit, reproducible, and callable from an agent tool without hidden
state.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory
from service.statistics.base import NUMBER_RANGE, StatMeta, make_meta

HotColdLabel = str  # Literal["hot", "neutral", "cold"] — kept as str for Pydantic friendliness


class HotColdThreshold(BaseModel):
    """Published thresholds used to derive `hot`/`cold` classifications."""

    model_config = ConfigDict(frozen=True)

    hot_factor: float = Field(
        default=0.5,
        description=("A number is 'hot' when its current gap is below this factor × mean gap."),
    )
    cold_factor: float = Field(
        default=2.0,
        description=("A number is 'cold' when its current gap is above this factor × mean gap."),
    )


class NumberGap(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int = Field(ge=1, le=25)
    current_gap: int = Field(ge=0, description="Draws since the number last appeared.")
    mean_gap: float = Field(ge=0.0, description="Arithmetic mean of inter-appearance gaps.")
    max_gap: int = Field(ge=0, description="Longest observed inter-appearance gap.")
    appearances: int = Field(ge=0)
    classification: HotColdLabel = Field(
        description="'hot' | 'neutral' | 'cold' per HotColdThreshold."
    )


class GapResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: StatMeta
    threshold: HotColdThreshold
    gaps: tuple[NumberGap, ...]


def _classify(*, current_gap: int, mean_gap: float, threshold: HotColdThreshold) -> HotColdLabel:
    if mean_gap == 0:
        return "neutral"
    if current_gap < threshold.hot_factor * mean_gap:
        return "hot"
    if current_gap > threshold.cold_factor * mean_gap:
        return "cold"
    return "neutral"


def compute_gaps(
    history: DrawHistory,
    *,
    threshold: HotColdThreshold | None = None,
) -> GapResult:
    """Return per-number gap statistics over the full history.

    Gap statistics are inherently global (they need the complete appearance
    history), so there is no rolling-window variant — callers who want a
    window-scoped view should compute frequencies instead.
    """
    threshold = threshold or HotColdThreshold()
    records = history.records
    total = len(records)

    last_seen: dict[int, int] = {}
    gaps_by_number: dict[int, list[int]] = {n: [] for n in NUMBER_RANGE}
    appearances: dict[int, int] = dict.fromkeys(NUMBER_RANGE, 0)

    for idx, record in enumerate(records):
        for n in record.numbers_sorted:
            appearances[n] += 1
            if n in last_seen:
                gaps_by_number[n].append(idx - last_seen[n])
            last_seen[n] = idx

    rows: list[NumberGap] = []
    for n in NUMBER_RANGE:
        seen = last_seen.get(n)
        # current_gap: draws since last appearance.
        # If never seen, treat as `total` (the whole history is a gap).
        current_gap = (total - 1 - seen) if seen is not None else total
        observed_gaps = gaps_by_number[n]
        mean_gap = sum(observed_gaps) / len(observed_gaps) if observed_gaps else 0.0
        max_gap = max(observed_gaps) if observed_gaps else 0
        classification = _classify(current_gap=current_gap, mean_gap=mean_gap, threshold=threshold)
        rows.append(
            NumberGap(
                number=n,
                current_gap=current_gap,
                mean_gap=mean_gap,
                max_gap=max_gap,
                appearances=appearances[n],
                classification=classification,
            )
        )

    meta = make_meta(history, descriptor="full", window_size=total)
    return GapResult(meta=meta, threshold=threshold, gaps=tuple(rows))
