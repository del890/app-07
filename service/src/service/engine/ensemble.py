"""Ensemble the baseline and learned distributions into a single next-draw vector.

Final shape: 25 per-number marginal probabilities summing to ``EXPECTED_MASS``.
Every result carries the model versions and weights used so the agent tool
layer can cite exact provenance.

Default weights (per design.md §5): 0.4 baseline / 0.6 learned. When the
history is too short to support the learned model, the ensemble falls back to
the baseline alone and reports that fact in the weights.
"""

from __future__ import annotations

from datetime import UTC, datetime

from service.engine.baseline import compute_baseline
from service.engine.learned import get_learned_model, history_supports_learned
from service.engine.models import (
    EXPECTED_MASS,
    NUMBER_COUNT,
    ComponentDistribution,
    NextDrawDistribution,
    NumberProbability,
)
from service.ingestion import DrawHistory

DEFAULT_BASELINE_WEIGHT = 0.4
DEFAULT_LEARNED_WEIGHT = 0.6


def compute_next_draw_distribution(
    history: DrawHistory,
    *,
    baseline_weight: float = DEFAULT_BASELINE_WEIGHT,
    learned_weight: float = DEFAULT_LEARNED_WEIGHT,
) -> NextDrawDistribution:
    """Combine baseline + learned into a single distribution.

    Weights must be non-negative and sum to > 0. They are normalised internally
    so the relative ratio is what matters; the reported weights in the result
    reflect what was actually applied.
    """
    if baseline_weight < 0 or learned_weight < 0:
        raise ValueError("ensemble weights must be non-negative")
    if baseline_weight == 0 and learned_weight == 0:
        raise ValueError("at least one ensemble weight must be positive")

    baseline = compute_baseline(history)
    components: list[ComponentDistribution] = [baseline]

    if history_supports_learned(history) and learned_weight > 0:
        learned = get_learned_model(history).predict_probabilities(history)
        components.append(learned)
        weight_map = {
            baseline.model_version.label(): baseline_weight,
            learned.model_version.label(): learned_weight,
        }
    else:
        # Learned model unavailable (history too short or user-disabled).
        weight_map = {baseline.model_version.label(): 1.0}

    # Normalise weights to sum to 1.0
    weight_total = sum(weight_map.values())
    normalised = {k: v / weight_total for k, v in weight_map.items()}

    combined = [0.0] * NUMBER_COUNT
    for component in components:
        label = component.model_version.label()
        w = normalised.get(label, 0.0)
        if w == 0.0:
            continue
        for p in component.probabilities:
            combined[p.number - 1] += w * p.probability

    # Renormalise final vector to EXPECTED_MASS and clip to [0, 1].
    mass = sum(combined)
    if mass > 0:
        combined = [v * EXPECTED_MASS / mass for v in combined]
    combined = [min(1.0, max(0.0, v)) for v in combined]
    # A second normalisation after clipping keeps the invariant to FP tolerance.
    post_mass = sum(combined)
    if post_mass > 0 and post_mass != EXPECTED_MASS:
        combined = [v * EXPECTED_MASS / post_mass for v in combined]
        combined = [min(1.0, max(0.0, v)) for v in combined]

    probabilities = tuple(
        NumberProbability(number=i + 1, probability=combined[i]) for i in range(NUMBER_COUNT)
    )
    model_versions = tuple(c.model_version for c in components)
    return NextDrawDistribution(
        dataset_hash=history.provenance.content_hash,
        computed_at=datetime.now(UTC),
        ensemble_weights=normalised,
        model_versions=model_versions,
        probabilities=probabilities,
    )
