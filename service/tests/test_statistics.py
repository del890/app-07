"""Hand-verified golden tests for the statistical-analysis capability.

Every computation is checked against the tiny three-draw `tiny_history`
fixture. Values are derived by hand in the comments above each assertion so a
reviewer can reproduce them without executing the code.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from service.statistics import (
    HotColdThreshold,
    WindowSelection,
    compute_cooccurrence,
    compute_frequency,
    compute_gaps,
    compute_order,
    compute_pi_alignment,
    compute_structural,
)

# ---------------------------------------------------------------------------
# Provenance contract
# ---------------------------------------------------------------------------


def _assert_meta(result, *, dataset_hash: str, window: str, window_size: int) -> None:
    meta = result.meta
    assert meta.dataset_hash == dataset_hash
    assert meta.window == window
    assert meta.window_size == window_size
    assert isinstance(meta.computed_at, datetime)


# ---------------------------------------------------------------------------
# Frequency
# ---------------------------------------------------------------------------


def test_frequency_full_window_golden(tiny_history) -> None:
    result = compute_frequency(tiny_history)
    _assert_meta(
        result,
        dataset_hash=tiny_history.provenance.content_hash,
        window="full",
        window_size=3,
    )
    # Expected counts derived by hand from TINY_DATASET:
    # numbers 2,3,4,5,7,9,11,13,15 appear in all 3 draws → count=3
    # 1,6,8,10,12,14 appear in 2 draws → count=2
    # 16,17,19,21,23,25 appear in 1 draw
    # 18,20,22,24 never appear
    expected_counts = {
        1: 2,
        2: 3,
        3: 3,
        4: 3,
        5: 3,
        6: 2,
        7: 3,
        8: 2,
        9: 3,
        10: 2,
        11: 3,
        12: 2,
        13: 3,
        14: 2,
        15: 3,
        16: 1,
        17: 1,
        18: 0,
        19: 1,
        20: 0,
        21: 1,
        22: 0,
        23: 1,
        24: 0,
        25: 1,
    }
    by_number = {row.number: row for row in result.frequencies}
    for number, expected in expected_counts.items():
        assert by_number[number].count == expected, f"number {number}"
        assert by_number[number].share == pytest.approx(expected / 3)


def test_frequency_rolling_window(tiny_history) -> None:
    # Window of size 1 → only the most recent draw (id=3).
    result = compute_frequency(tiny_history, window=WindowSelection(kind="last_n", n=1))
    assert result.meta.window == "last-1"
    assert result.meta.window_size == 1
    by_number = {row.number: row for row in result.frequencies}
    # Draw id=3 sorted: [1,2,3,4,5,7,9,11,13,15,17,19,21,23,25]
    present = {1, 2, 3, 4, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25}
    for n in range(1, 26):
        expected_share = 1.0 if n in present else 0.0
        assert by_number[n].share == pytest.approx(expected_share)


def test_frequency_window_larger_than_history(tiny_history) -> None:
    """Requesting last-100 on a 3-draw history uses all draws but reports 'last-100'."""
    result = compute_frequency(tiny_history, window=WindowSelection(kind="last_n", n=100))
    assert result.meta.window == "last-100"
    assert result.meta.window_size == 3


# ---------------------------------------------------------------------------
# Gaps + hot/cold
# ---------------------------------------------------------------------------


def test_gaps_golden(tiny_history) -> None:
    result = compute_gaps(tiny_history)
    _assert_meta(
        result,
        dataset_hash=tiny_history.provenance.content_hash,
        window="full",
        window_size=3,
    )
    assert result.threshold == HotColdThreshold()  # defaults

    by_n = {g.number: g for g in result.gaps}

    # Number 1: appears at index 0 and 2 → observed_gaps=[2]; mean=2, max=2.
    # Last-seen index = 2; current_gap = (total-1 - last_seen) = 0.
    # 0 < 0.5*2 → classification 'hot'.
    assert by_n[1].current_gap == 0
    assert by_n[1].mean_gap == pytest.approx(2.0)
    assert by_n[1].max_gap == 2
    assert by_n[1].appearances == 2
    assert by_n[1].classification == "hot"

    # Number 16: appears only at index 1; observed_gaps=[]; mean_gap=0.
    # mean_gap==0 ⇒ classification 'neutral' (rule short-circuit).
    # Last-seen=1; current_gap = 3-1-1 = 1.
    assert by_n[16].current_gap == 1
    assert by_n[16].mean_gap == 0.0
    assert by_n[16].appearances == 1
    assert by_n[16].classification == "neutral"

    # Number 18: never appears. current_gap = total = 3, mean_gap = 0.
    assert by_n[18].appearances == 0
    assert by_n[18].current_gap == 3
    assert by_n[18].mean_gap == 0.0
    assert by_n[18].classification == "neutral"


def test_gaps_custom_threshold_is_reported(tiny_history) -> None:
    t = HotColdThreshold(hot_factor=0.9, cold_factor=1.1)
    result = compute_gaps(tiny_history, threshold=t)
    assert result.threshold.hot_factor == 0.9
    assert result.threshold.cold_factor == 1.1


# ---------------------------------------------------------------------------
# Co-occurrence
# ---------------------------------------------------------------------------


def test_cooccurrence_pairs_top_k(tiny_history) -> None:
    result = compute_cooccurrence(tiny_history, arity=2, top_k=5)
    _assert_meta(
        result,
        dataset_hash=tiny_history.provenance.content_hash,
        window="full",
        window_size=3,
    )
    assert result.arity == 2
    assert result.top_k == 5
    assert len(result.combinations) == 5
    # The 9 numbers common to all 3 draws are {2,3,4,5,7,9,11,13,15}.
    # Any pair drawn from that set co-occurs in all 3 draws ⇒ count=3, share=1.
    # Lexicographic-first 5 such pairs:
    assert result.combinations[0].numbers == (2, 3)
    assert result.combinations[0].count == 3
    assert result.combinations[0].share == pytest.approx(1.0)
    for combo in result.combinations:
        assert combo.count == 3
        assert combo.share == pytest.approx(1.0)


@pytest.mark.parametrize("arity", [2, 3, 4])
def test_cooccurrence_arity_range(tiny_history, arity: int) -> None:
    result = compute_cooccurrence(tiny_history, arity=arity, top_k=1)
    assert result.combinations[0].count >= 1


def test_cooccurrence_rejects_bad_arity(tiny_history) -> None:
    with pytest.raises(ValueError, match=r"arity must be in \[2, 4\]"):
        compute_cooccurrence(tiny_history, arity=5, top_k=1)
    with pytest.raises(ValueError, match=r"arity must be in \[2, 4\]"):
        compute_cooccurrence(tiny_history, arity=1, top_k=1)


def test_cooccurrence_rejects_bad_top_k(tiny_history) -> None:
    with pytest.raises(ValueError, match=r"top_k must be in \[1,"):
        compute_cooccurrence(tiny_history, arity=2, top_k=0)


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------


def test_structural_golden(tiny_history) -> None:
    result = compute_structural(tiny_history)
    _assert_meta(
        result,
        dataset_hash=tiny_history.provenance.content_hash,
        window="full",
        window_size=3,
    )
    # sums: 120, 135, 175 → each count=1
    sums = {b.value: b.count for b in result.sum_histogram}
    assert sums == {120: 1, 135: 1, 175: 1}

    # even counts: draw1=7, draw2=8, draw3=2 → counts {7:1, 8:1, 2:1}
    evens = {b.value: b.count for b in result.even_count_histogram}
    assert evens == {2: 1, 7: 1, 8: 1}

    # min histogram: min(draw1)=1, min(draw2)=2, min(draw3 sorted)=1 → {1:2, 2:1}
    mins = {b.value: b.count for b in result.min_number_histogram}
    assert mins == {1: 2, 2: 1}

    # max histogram: max(draw1)=15, max(draw2)=16, max(draw3 sorted)=25 → {15:1, 16:1, 25:1}
    maxs = {b.value: b.count for b in result.max_number_histogram}
    assert maxs == {15: 1, 16: 1, 25: 1}


# ---------------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------------


def test_order_labels_source(tiny_history) -> None:
    result = compute_order(tiny_history)
    _assert_meta(
        result,
        dataset_hash=tiny_history.provenance.content_hash,
        window="full",
        window_size=3,
    )
    # Draw id=3 is unsorted in the source, so ingestion sets order_source='original'.
    assert result.order_source == "original"
    assert "originally drawn" in result.disclaimer.lower()
    # 15 position stats
    assert len(result.position_stats) == 15
    assert len(result.mean_adjacent_delta) == 14


# ---------------------------------------------------------------------------
# PI alignment
# ---------------------------------------------------------------------------


def test_pi_alignment_digit_sum_mod10_golden(tiny_history) -> None:
    # draw id=1 sum=120, draw_mod=0; PI[0:15] sum=77, pi_mod=7 → score=0.0
    result = compute_pi_alignment(tiny_history, rule="digit_sum_mod10", target_original_id=1)
    assert result.rule == "digit_sum_mod10"
    assert result.score == 0.0
    assert result.pi_digits_used == "141592653589793"  # first 15 PI digits
    assert result.target == "draw:original_id=1"


def test_pi_alignment_position_digit_match_golden(tiny_history) -> None:
    # Draw id=1 sorted [1..15]. Only pos 0 matches (1 == PI[0]=1). score=1/15.
    result = compute_pi_alignment(tiny_history, rule="position_digit_match", target_original_id=1)
    assert result.score == pytest.approx(1 / 15)
    assert result.rule_description  # non-empty


def test_pi_alignment_unknown_rule_rejected(tiny_history) -> None:
    with pytest.raises(ValueError, match="unknown PI rule"):
        compute_pi_alignment(tiny_history, rule="not_a_rule", target_original_id=1)


def test_pi_alignment_unknown_draw_rejected(tiny_history) -> None:
    with pytest.raises(ValueError, match="not found"):
        compute_pi_alignment(tiny_history, rule="digit_sum_mod10", target_original_id=999)


def test_pi_alignment_reproducible(tiny_history) -> None:
    a = compute_pi_alignment(tiny_history, rule="digit_sum_mod10", target_original_id=1)
    b = compute_pi_alignment(tiny_history, rule="digit_sum_mod10", target_original_id=1)
    assert a.score == b.score
    assert a.rule == b.rule
    assert a.pi_digits_used == b.pi_digits_used
    # meta.computed_at will differ but the semantic result is identical
