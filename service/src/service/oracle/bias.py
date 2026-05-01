"""Bias vector builder for the dream-oracle capability.

Converts a list of ``ExtractedSymbol`` objects into a 25-length probability
vector that sums to 15.0 (the Lotofácil expected draw mass).
"""

from __future__ import annotations

import logging

from service.oracle.catalog import lookup
from service.oracle.models import ExtractedSymbol

logger = logging.getLogger(__name__)


def build_bias_vector(
    symbols: list[ExtractedSymbol],
    *,
    max_symbols: int = 8,
) -> list[float]:
    """Build a 25-length probability bias vector summing to 15.0.

    Parameters
    ----------
    symbols:
        Symbolic signals extracted from the dream description.
    max_symbols:
        Maximum number of symbols to apply (top by intensity). Symbols beyond
        this cap are ignored to keep the bias vector bounded.

    Returns
    -------
    list[float]
        25-length vector of probabilities; ``sum(vector) == 15.0``.
    """
    # Sort by intensity descending, truncate to max_symbols.
    sorted_syms = sorted(symbols, key=lambda s: s.intensity, reverse=True)[:max_symbols]

    # Uniform baseline — every number starts with weight 1.0.
    vector = [1.0] * 25

    for sym in sorted_syms:
        rule = lookup(sym.category, sym.label)
        if rule is None:
            logger.warning(
                "Dream-oracle: unknown symbol (%s, %s) — skipping",
                sym.category,
                sym.label,
            )
            continue
        for n in rule.numbers:
            # n is 1-based; vector is 0-indexed.
            vector[n - 1] += rule.multiplier * sym.intensity

    # Normalize so that sum(vector) == 15.0.
    total = sum(vector)
    if total <= 0:
        # Degenerate fallback: uniform distribution.
        return [15.0 / 25] * 25
    factor = 15.0 / total
    return [v * factor for v in vector]
