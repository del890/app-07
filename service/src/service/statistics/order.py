"""Intra-draw order analysis.

When the source data preserves the original draw sequence (`order_source ==
"original"` on ingestion), this module reports statistics over that order.
Otherwise it falls back to the sorted-canonical order and labels the result
accordingly so callers can't mistake canonical-order artifacts for "what was
actually drawn first".
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory
from service.statistics.base import StatMeta, make_meta

NUMBERS_PER_DRAW = 15


class PositionStat(BaseModel):
    model_config = ConfigDict(frozen=True)
    position: int = Field(ge=0, le=NUMBERS_PER_DRAW - 1)
    mean: float
    stdev: float = Field(ge=0.0)


class OrderResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: StatMeta
    order_source: str = Field(
        description="'original' (as drawn) or 'canonical' (sorted ascending fallback)."
    )
    disclaimer: str = Field(
        description=(
            "Human-readable label describing how the order was derived; clients must "
            "surface this when rendering order-based results."
        ),
    )
    position_stats: tuple[PositionStat, ...]
    mean_adjacent_delta: tuple[float, ...] = Field(
        description="Length 14 — mean (numbers[i+1] - numbers[i]) across the history."
    )


def compute_order(history: DrawHistory) -> OrderResult:
    records = history.records
    total = len(records)
    order_source = history.provenance.order_source

    if order_source == "original":
        sequences = [r.numbers_drawn for r in records]
        disclaimer = (
            "Order-based statistics reflect the numbers as originally drawn, "
            "per the upstream source."
        )
    else:
        sequences = [r.numbers_sorted for r in records]
        disclaimer = (
            "Original draw order was not available in the source; statistics "
            "reflect sorted-ascending canonical order, not the sequence numbers "
            "were actually drawn."
        )

    # Per-position mean + stdev
    position_stats: list[PositionStat] = []
    for p in range(NUMBERS_PER_DRAW):
        values = [seq[p] for seq in sequences]
        n = len(values)
        if n == 0:
            position_stats.append(PositionStat(position=p, mean=0.0, stdev=0.0))
            continue
        mean = sum(values) / n
        variance = sum((v - mean) ** 2 for v in values) / n
        position_stats.append(PositionStat(position=p, mean=mean, stdev=math.sqrt(variance)))

    # Adjacent deltas
    adjacent_sums = [0.0] * (NUMBERS_PER_DRAW - 1)
    for seq in sequences:
        for i in range(NUMBERS_PER_DRAW - 1):
            adjacent_sums[i] += seq[i + 1] - seq[i]
    mean_adjacent_delta = tuple((s / total) if total else 0.0 for s in adjacent_sums)

    meta = make_meta(history, descriptor="full", window_size=total)
    return OrderResult(
        meta=meta,
        order_source=order_source,
        disclaimer=disclaimer,
        position_stats=tuple(position_stats),
        mean_adjacent_delta=mean_adjacent_delta,
    )
