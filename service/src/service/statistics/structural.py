"""Per-draw structural statistics and their histograms across the history.

Quintile bins over the 1–25 space:

    q1: 1–5      q2: 6–10     q3: 11–15    q4: 16–20    q5: 21–25
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory
from service.statistics.base import StatMeta, make_meta

QUINTILE_EDGES = (5, 10, 15, 20, 25)  # upper bounds, inclusive
NUMBERS_PER_DRAW = 15
# A draw's sum ranges over [sum(1..15), sum(11..25)] = [120, 270].
SUM_MIN = sum(range(1, 16))
SUM_MAX = sum(range(11, 26))


class HistogramBin(BaseModel):
    model_config = ConfigDict(frozen=True)
    value: int
    count: int = Field(ge=0)


class StructuralResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: StatMeta
    sum_min: int
    sum_max: int
    sum_histogram: tuple[HistogramBin, ...]
    even_count_histogram: tuple[HistogramBin, ...]  # 0..15 even numbers per draw
    quintile_histogram: tuple[HistogramBin, ...]  # aggregated: avg count per quintile-bucket
    quintile_per_draw_mean: tuple[float, ...]  # length 5, per-quintile avg count per draw
    min_number_histogram: tuple[HistogramBin, ...]  # min across the 15 numbers per draw
    max_number_histogram: tuple[HistogramBin, ...]  # max across the 15 numbers per draw


def _quintile_index(n: int) -> int:
    for i, edge in enumerate(QUINTILE_EDGES):
        if n <= edge:
            return i
    raise ValueError(f"number {n} out of range")


def compute_structural(history: DrawHistory) -> StructuralResult:
    """Return per-draw structural histograms across the full history."""
    records = history.records
    total = len(records)

    sum_counts: dict[int, int] = {}
    even_counts: dict[int, int] = {}
    min_counts: dict[int, int] = {}
    max_counts: dict[int, int] = {}
    quintile_totals = [0] * 5  # aggregate count across draws per quintile

    for record in records:
        numbers = record.numbers_sorted
        s = sum(numbers)
        sum_counts[s] = sum_counts.get(s, 0) + 1
        e = sum(1 for n in numbers if n % 2 == 0)
        even_counts[e] = even_counts.get(e, 0) + 1
        min_counts[numbers[0]] = min_counts.get(numbers[0], 0) + 1
        max_counts[numbers[-1]] = max_counts.get(numbers[-1], 0) + 1
        for n in numbers:
            quintile_totals[_quintile_index(n)] += 1

    def _bins_dict(d: dict[int, int]) -> tuple[HistogramBin, ...]:
        return tuple(HistogramBin(value=v, count=c) for v, c in sorted(d.items()))

    quintile_per_draw_mean = tuple((qt / total) if total else 0.0 for qt in quintile_totals)
    quintile_histogram = tuple(
        HistogramBin(value=i + 1, count=quintile_totals[i]) for i in range(5)
    )

    meta = make_meta(history, descriptor="full", window_size=total)
    return StructuralResult(
        meta=meta,
        sum_min=SUM_MIN,
        sum_max=SUM_MAX,
        sum_histogram=_bins_dict(sum_counts),
        even_count_histogram=_bins_dict(even_counts),
        quintile_histogram=quintile_histogram,
        quintile_per_draw_mean=quintile_per_draw_mean,
        min_number_histogram=_bins_dict(min_counts),
        max_number_histogram=_bins_dict(max_counts),
    )
