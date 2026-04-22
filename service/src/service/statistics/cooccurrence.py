"""Co-occurrence counts for number combinations (arities 2, 3, 4).

Counts are cached per (dataset hash, arity) — computing quadruplets across
3,656 draws is ~C(15,4) × 3656 ≈ 5M increments, cheap but worth memoizing so
repeat queries from the agent don't re-scan.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from itertools import combinations

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory
from service.statistics.base import StatMeta, make_meta

ARITY_MIN = 2
ARITY_MAX = 4
TOP_K_MAX = 500


class Combination(BaseModel):
    model_config = ConfigDict(frozen=True)

    numbers: tuple[int, ...]
    count: int = Field(ge=1)
    share: float = Field(
        ge=0.0,
        le=1.0,
        description="Fraction of draws in which the combination co-occurred.",
    )


class CooccurrenceResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    meta: StatMeta
    arity: int = Field(ge=ARITY_MIN, le=ARITY_MAX)
    top_k: int = Field(ge=1, le=TOP_K_MAX)
    combinations: tuple[Combination, ...]


CounterKey = tuple[int, ...]
RecordsKey = tuple[tuple[int, ...], ...]


# Raw Counter cache keyed by (dataset hash, arity). Pydantic result objects
# embed a `computed_at` timestamp, so caching the Counter (not the result) keeps
# timestamps fresh per call.
@lru_cache(maxsize=128)
def _count_combinations(
    dataset_hash: str, arity: int, records_key: RecordsKey
) -> Counter[CounterKey]:
    counter: Counter[CounterKey] = Counter()
    for sorted_numbers in records_key:
        for combo in combinations(sorted_numbers, arity):
            counter[combo] += 1
    return counter


def _records_key(history: DrawHistory) -> RecordsKey:
    """Hashable snapshot of each draw's sorted numbers."""
    return tuple(r.numbers_sorted for r in history.records)


def compute_cooccurrence(
    history: DrawHistory,
    *,
    arity: int,
    top_k: int,
) -> CooccurrenceResult:
    """Return the top-K most common combinations at the given arity."""
    if arity < ARITY_MIN or arity > ARITY_MAX:
        raise ValueError(f"arity must be in [{ARITY_MIN}, {ARITY_MAX}], got {arity}")
    if top_k < 1 or top_k > TOP_K_MAX:
        raise ValueError(f"top_k must be in [1, {TOP_K_MAX}], got {top_k}")

    records = history.records
    total = len(records)
    counter = _count_combinations(history.provenance.content_hash, arity, _records_key(history))

    # sorted: highest count first, ties broken by lexicographic combination
    most_common = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]

    combinations_tuple = tuple(
        Combination(
            numbers=combo,
            count=count,
            share=count / total if total else 0.0,
        )
        for combo, count in most_common
    )
    meta = make_meta(history, descriptor="full", window_size=total)
    return CooccurrenceResult(
        meta=meta,
        arity=arity,
        top_k=top_k,
        combinations=combinations_tuple,
    )


def clear_cooccurrence_cache() -> None:
    """Drop the memoized co-occurrence counters. Only used in tests."""
    _count_combinations.cache_clear()
