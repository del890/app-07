"""Unit tests for the dream-oracle bias vector builder."""

from __future__ import annotations

import math

from service.oracle.bias import build_bias_vector
from service.oracle.models import ExtractedSymbol


def _sym(category: str, label: str, intensity: float = 1.0) -> ExtractedSymbol:
    return ExtractedSymbol(category=category, label=label, intensity=intensity)


def test_vector_length_is_always_25() -> None:
    symbols = [_sym("element", "water")]
    vector = build_bias_vector(symbols)
    assert len(vector) == 25


def test_vector_sum_is_15() -> None:
    for symbols in [
        [_sym("element", "water")],
        [_sym("emotion", "joy"), _sym("color", "blue")],
        [_sym("archetype", "falling"), _sym("count", "13"), _sym("emotion", "rage")],
    ]:
        vector = build_bias_vector(symbols)
        assert math.isclose(sum(vector), 15.0, abs_tol=1e-9), (
            f"Sum is {sum(vector)}, not 15.0"
        )


def test_vector_sum_is_15_with_empty_after_truncation() -> None:
    # Even with 10 symbols (truncated to 8), sum must be 15.
    symbols = [
        _sym("element", "water", 0.9),
        _sym("element", "fire", 0.8),
        _sym("color", "red", 0.7),
        _sym("color", "blue", 0.6),
        _sym("emotion", "joy", 0.5),
        _sym("emotion", "fear", 0.4),
        _sym("archetype", "falling", 0.3),
        _sym("archetype", "flying", 0.2),
        _sym("archetype", "hiding", 0.1),   # 9th — truncated
        _sym("archetype", "chasing", 0.05), # 10th — truncated
    ]
    vector = build_bias_vector(symbols, max_symbols=8)
    assert len(vector) == 25
    assert math.isclose(sum(vector), 15.0, abs_tol=1e-9)


def test_top_8_truncation_by_intensity() -> None:
    """Top-8 symbols by intensity are applied; the rest are ignored."""
    # Create 10 symbols, first 8 high-intensity affecting number 1, last 2 low-intensity
    # affecting number 25 only. After truncation, number 25 should not be extra-boosted.
    high = [_sym("count", "1", intensity=1.0) for _ in range(8)]
    low = [_sym("count", "25", intensity=0.01), _sym("count", "25", intensity=0.01)]
    symbols = high + low

    v_with_truncation = build_bias_vector(symbols, max_symbols=8)
    v_without_low = build_bias_vector(high, max_symbols=8)

    # The vectors should be identical since the low-intensity symbols are cut.
    for a, b in zip(v_with_truncation, v_without_low):
        assert math.isclose(a, b, abs_tol=1e-9), (
            "Low-intensity symbols beyond max_symbols should not affect the vector"
        )


def test_unknown_symbol_is_skipped() -> None:
    known = [_sym("element", "water", 1.0)]
    unknown = [_sym("totally_unknown", "nonsense", 1.0)]

    vec_known = build_bias_vector(known)
    vec_both = build_bias_vector(known + unknown)

    # Adding an unknown symbol should not change the normalized vector.
    for a, b in zip(vec_known, vec_both):
        assert math.isclose(a, b, abs_tol=1e-9), (
            "Unknown symbol should be silently skipped, not alter the vector"
        )


def test_all_values_positive() -> None:
    symbols = [_sym("element", "void")]  # only 3 numbers get boosted
    vector = build_bias_vector(symbols)
    # Baseline of 1.0 ensures every number has positive weight.
    assert all(v > 0 for v in vector), "All bias values must be strictly positive"
