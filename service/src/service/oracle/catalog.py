"""Versioned symbolic catalog for the dream-oracle capability.

Maps (category, label) pairs to a BiasRule that specifies which Lotofácil
numbers (1–25) receive a probability multiplier when that symbol appears in a
dream.

Catalog v1 categories:
  element   — water, fire, earth, air, void
  color     — red, orange, yellow, green, blue
  emotion   — joy, fear, calm, rage
  archetype — falling, flying, chasing, hiding
  count     — integers 1–25 (label = str(n))
"""

from __future__ import annotations

from pydantic import BaseModel

CATALOG_VERSION = "1.0"

# ---------------------------------------------------------------------------
# BiasRule
# ---------------------------------------------------------------------------


class BiasRule(BaseModel):
    """A mapping from a symbol to a set of boosted numbers."""

    numbers: list[int]
    multiplier: float
    rationale: str


# ---------------------------------------------------------------------------
# Number sets used by multiple rules
# ---------------------------------------------------------------------------

_EVENS = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
_ODDS = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
_MULT3 = [3, 6, 9, 12, 15, 18, 21, 24]
_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23]

# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

CATALOG: dict[tuple[str, str], BiasRule] = {
    # ── Elements ──────────────────────────────────────────────────────────
    ("element", "water"): BiasRule(
        numbers=list(range(1, 8)),
        multiplier=3.0,
        rationale="Water flows low and clean — numbers 1 to 7",
    ),
    ("element", "fire"): BiasRule(
        numbers=list(range(19, 26)),
        multiplier=3.0,
        rationale="Fire burns high — numbers 19 to 25",
    ),
    ("element", "earth"): BiasRule(
        numbers=list(range(8, 15)),
        multiplier=3.0,
        rationale="Earth is grounded in the middle range — numbers 8 to 14",
    ),
    ("element", "air"): BiasRule(
        numbers=list(range(15, 22)),
        multiplier=3.0,
        rationale="Air is light and rises — numbers 15 to 21",
    ),
    ("element", "void"): BiasRule(
        numbers=[1, 13, 25],
        multiplier=4.0,
        rationale="Void occupies the liminal numbers — 1, 13, and 25",
    ),
    # ── Colors ────────────────────────────────────────────────────────────
    ("color", "red"): BiasRule(
        numbers=list(range(1, 6)),
        multiplier=3.0,
        rationale="Red is the first intensity — numbers 1 to 5",
    ),
    ("color", "orange"): BiasRule(
        numbers=list(range(6, 11)),
        multiplier=3.0,
        rationale="Orange glows warm — numbers 6 to 10",
    ),
    ("color", "yellow"): BiasRule(
        numbers=list(range(11, 16)),
        multiplier=3.0,
        rationale="Yellow is central brightness — numbers 11 to 15",
    ),
    ("color", "green"): BiasRule(
        numbers=list(range(16, 21)),
        multiplier=3.0,
        rationale="Green grows outward — numbers 16 to 20",
    ),
    ("color", "blue"): BiasRule(
        numbers=list(range(21, 26)),
        multiplier=3.0,
        rationale="Blue reaches the sky — numbers 21 to 25",
    ),
    # ── Emotions ──────────────────────────────────────────────────────────
    ("emotion", "joy"): BiasRule(
        numbers=_EVENS,
        multiplier=2.5,
        rationale="Joy is even, balanced, and harmonious",
    ),
    ("emotion", "fear"): BiasRule(
        numbers=_ODDS,
        multiplier=2.5,
        rationale="Fear is sharp and odd",
    ),
    ("emotion", "calm"): BiasRule(
        numbers=_MULT3,
        multiplier=2.5,
        rationale="Calm flows in multiples of three — the rhythm of breath",
    ),
    ("emotion", "rage"): BiasRule(
        numbers=_PRIMES,
        multiplier=3.0,
        rationale="Rage is prime — indivisible and fierce",
    ),
    # ── Archetypes ────────────────────────────────────────────────────────
    ("archetype", "falling"): BiasRule(
        numbers=list(range(21, 26)),
        multiplier=3.0,
        rationale="Falling dreams pull toward the high numbers",
    ),
    ("archetype", "flying"): BiasRule(
        numbers=list(range(1, 6)),
        multiplier=3.0,
        rationale="Flying rises from the lowest numbers",
    ),
    ("archetype", "chasing"): BiasRule(
        numbers=list(range(16, 26)),
        multiplier=2.5,
        rationale="Chasing reaches for the far end of the range",
    ),
    ("archetype", "hiding"): BiasRule(
        numbers=list(range(1, 11)),
        multiplier=2.5,
        rationale="Hiding stays small and low",
    ),
}

# ── Count: explicit integers 1–25 ─────────────────────────────────────────
for _n in range(1, 26):
    CATALOG[("count", str(_n))] = BiasRule(
        numbers=[_n],
        multiplier=5.0,
        rationale=f"The number {_n} appears directly in the dream",
    )


# ---------------------------------------------------------------------------
# Lookup helper
# ---------------------------------------------------------------------------


def lookup(category: str, label: str) -> BiasRule | None:
    """Return the BiasRule for ``(category, label)`` or ``None`` if unknown."""
    return CATALOG.get((category.lower(), label.lower()))
