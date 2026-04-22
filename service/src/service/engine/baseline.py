"""Frequency-recency baseline predictor.

For each number 1-25, compute a recency-weighted count over the full history
(or a trailing window). Recent draws weigh more than old ones via an
exponential decay factor. The resulting vector is normalized so its sum equals
`EXPECTED_MASS` (15), matching the expected number of draws per round.

Deterministic: given the same ``(dataset_hash, window, decay)`` tuple, the
output is bit-identical. Carries a model version string.
"""

from __future__ import annotations

from service.engine.models import (
    EXPECTED_MASS,
    NUMBER_COUNT,
    ComponentDistribution,
    ModelVersion,
    NumberProbability,
)
from service.ingestion import DrawHistory

BASELINE_NAME = "baseline"
BASELINE_VERSION = "v1"

DEFAULT_WINDOW = 200
DEFAULT_DECAY = 0.98


def compute_baseline(
    history: DrawHistory,
    *,
    window: int = DEFAULT_WINDOW,
    decay: float = DEFAULT_DECAY,
) -> ComponentDistribution:
    """Return a 25-length recency-weighted distribution, summing to 15.

    - ``window``: trailing number of draws to include; clamped to history length.
    - ``decay``: recency decay factor; 1.0 means flat, <1.0 emphasises recent draws.
      Required range: ``0 < decay <= 1``.
    """
    if not 0.0 < decay <= 1.0:
        raise ValueError(f"decay must be in (0, 1], got {decay}")
    if window < 1:
        raise ValueError(f"window must be >= 1, got {window}")

    records = history.records
    effective_window = min(window, len(records))
    if effective_window == 0:
        raise ValueError("cannot compute baseline over an empty history")

    sliced = records[-effective_window:]

    # weight[i] applied to the i-th draw in `sliced`, where i=0 is the oldest
    # in-window draw and i=effective_window-1 is the most recent.
    # decay < 1 → more recent draws have higher weight.
    weights: list[float] = []
    for i in range(effective_window):
        age = effective_window - 1 - i
        weights.append(decay**age)
    total_weight = sum(weights)

    counts = [0.0] * NUMBER_COUNT
    for draw, w in zip(sliced, weights, strict=True):
        for n in draw.numbers_sorted:
            counts[n - 1] += w

    # Normalise to EXPECTED_MASS: each draw contributes 15 numbers worth of mass,
    # so total raw sum equals 15 * total_weight. Dividing by total_weight gives
    # per-draw expected counts; that already sums to 15.
    scale = 1.0 / total_weight
    probabilities = tuple(
        NumberProbability(
            number=i + 1,
            probability=min(1.0, max(0.0, counts[i] * scale)),
        )
        for i in range(NUMBER_COUNT)
    )

    # Sanity: after the per-number clamp, mass may have drifted very slightly —
    # renormalise so the downstream EXPECTED_MASS invariant holds exactly.
    mass = sum(p.probability for p in probabilities)
    if mass > 0:
        adjust = EXPECTED_MASS / mass
        probabilities = tuple(
            NumberProbability(
                number=p.number,
                probability=min(1.0, p.probability * adjust),
            )
            for p in probabilities
        )

    version = ModelVersion(
        name=BASELINE_NAME,
        version=BASELINE_VERSION,
        details={
            "window": str(effective_window),
            "decay": f"{decay:.4f}",
        },
    )
    return ComponentDistribution(model_version=version, probabilities=probabilities)
