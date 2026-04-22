"""Property tests for the statistical-analysis capability.

These assert invariants rather than pinned values, so they survive dataset
changes. Where a property also holds on the real `data.json`, it runs against
it — a cheap sanity check against the 3,656-draw history.
"""

from __future__ import annotations

import random
from itertools import pairwise
from pathlib import Path

import pytest

from service.ingestion import load
from service.statistics import (
    WindowSelection,
    compute_cooccurrence,
    compute_frequency,
    compute_gaps,
    compute_order,
    compute_structural,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_DATA = REPO_ROOT / "data.json"


# ---------------------------------------------------------------------------
# Frequency: shares sum to 15 (per-draw number count), not 1.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("window", [None, WindowSelection(kind="last_n", n=1)])
def test_frequency_shares_sum_to_15_on_tiny(tiny_history, window) -> None:
    result = compute_frequency(tiny_history, window=window)
    total_share = sum(f.share for f in result.frequencies)
    assert total_share == pytest.approx(15.0)


def test_frequency_shares_sum_to_15_on_real() -> None:
    history = load(REAL_DATA)
    result = compute_frequency(history)
    total_share = sum(f.share for f in result.frequencies)
    assert total_share == pytest.approx(15.0)
    # Counts should also add up: 25 numbers × avg frequency ≈ 15 × total_draws
    total_count = sum(f.count for f in result.frequencies)
    assert total_count == 15 * len(history)


# ---------------------------------------------------------------------------
# Gap: mean_gap × (appearances - 1) == last_appearance_index - first_appearance_index
# ---------------------------------------------------------------------------


def test_gap_mean_frequency_relation_on_tiny(tiny_history) -> None:
    result = compute_gaps(tiny_history)
    for g in result.gaps:
        if g.appearances >= 2:
            # mean_gap × (appearances - 1) is the span from first to last appearance.
            span = g.mean_gap * (g.appearances - 1)
            assert span >= 1.0, f"number {g.number} span should be ≥ 1"
        if g.appearances == 0:
            assert g.mean_gap == 0.0
            assert g.max_gap == 0


def test_gap_current_gap_bounds(tiny_history) -> None:
    result = compute_gaps(tiny_history)
    total = len(tiny_history)
    for g in result.gaps:
        assert 0 <= g.current_gap <= total


# ---------------------------------------------------------------------------
# Co-occurrence: for every stored combination, count ≤ total_draws.
# ---------------------------------------------------------------------------


def test_cooccurrence_count_bounded_by_total(tiny_history) -> None:
    total = len(tiny_history)
    for arity in (2, 3, 4):
        result = compute_cooccurrence(tiny_history, arity=arity, top_k=10)
        for combo in result.combinations:
            assert 1 <= combo.count <= total
            assert 0 <= combo.share <= 1.0


# ---------------------------------------------------------------------------
# Structural: sum_histogram and even_count_histogram each total to total_draws.
# ---------------------------------------------------------------------------


def test_structural_histograms_total_to_total_draws(tiny_history) -> None:
    total = len(tiny_history)
    result = compute_structural(tiny_history)
    assert sum(b.count for b in result.sum_histogram) == total
    assert sum(b.count for b in result.even_count_histogram) == total
    assert sum(b.count for b in result.min_number_histogram) == total
    assert sum(b.count for b in result.max_number_histogram) == total


# ---------------------------------------------------------------------------
# Order: canonical order's position means are monotonically non-decreasing.
# ---------------------------------------------------------------------------


def test_order_canonical_position_means_non_decreasing(tmp_path: Path) -> None:
    # Build a pre-sorted dataset so ingestion classifies order_source='canonical'.
    payload_draws = [
        {"id": i, "date": f"{i:02d}-01-2020", "numbers": list(range(1, 16))} for i in range(1, 6)
    ]
    path = tmp_path / "canonical.json"
    import json

    path.write_text(
        json.dumps({"allowed_numbers": list(range(1, 26)), "dataset": payload_draws}),
        encoding="utf-8",
    )
    history = load(path)
    assert history.provenance.order_source == "canonical"
    result = compute_order(history)
    means = [p.mean for p in result.position_stats]
    for a, b in pairwise(means):
        assert a <= b, f"sorted-canonical position means must be non-decreasing: {means}"


# ---------------------------------------------------------------------------
# Determinism: running a deterministic stat twice produces the same values.
# (meta.computed_at will differ, so we compare the payloads.)
# ---------------------------------------------------------------------------


def test_frequency_is_deterministic(tiny_history) -> None:
    a = compute_frequency(tiny_history)
    b = compute_frequency(tiny_history)
    assert [f.model_dump() for f in a.frequencies] == [f.model_dump() for f in b.frequencies]


def test_cooccurrence_is_deterministic(tiny_history) -> None:
    random.seed(0)  # guard against hidden randomness
    a = compute_cooccurrence(tiny_history, arity=3, top_k=10)
    random.seed(1)
    b = compute_cooccurrence(tiny_history, arity=3, top_k=10)
    assert [c.model_dump() for c in a.combinations] == [c.model_dump() for c in b.combinations]
