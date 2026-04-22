"""Per-number frequency over the full history or a rolling window."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory
from service.statistics.base import (
    NUMBER_RANGE,
    StatMeta,
    WindowSelection,
    make_meta,
    resolve_window,
)


class NumberFrequency(BaseModel):
    """Count and share for a single number over the selected window."""

    model_config = ConfigDict(frozen=True)

    number: int = Field(ge=1, le=25)
    count: int = Field(ge=0)
    share: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of draws in the window that contained this number.",
    )


class FrequencyResult(BaseModel):
    """Frequency report for all 25 numbers."""

    model_config = ConfigDict(frozen=True)

    meta: StatMeta
    frequencies: tuple[NumberFrequency, ...]


def compute_frequency(
    history: DrawHistory,
    *,
    window: WindowSelection | None = None,
) -> FrequencyResult:
    """Return per-number counts and shares over the selected window.

    Shares are `count / window_size` — i.e. the fraction of draws in which
    a number appeared, not a probability mass function. Shares therefore sum
    to 15 (expected numbers per draw), not 1.
    """
    records, descriptor, sample_count = resolve_window(history, window)

    counts: dict[int, int] = dict.fromkeys(NUMBER_RANGE, 0)
    for record in records:
        for n in record.numbers_sorted:
            counts[n] += 1

    frequencies = tuple(
        NumberFrequency(
            number=n,
            count=counts[n],
            share=(counts[n] / sample_count) if sample_count else 0.0,
        )
        for n in NUMBER_RANGE
    )
    meta = make_meta(history, descriptor=descriptor, window_size=sample_count)
    return FrequencyResult(meta=meta, frequencies=frequencies)
