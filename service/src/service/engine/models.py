"""Pydantic models for the prediction engine.

A next-draw distribution is a vector of 25 per-number marginal probabilities —
the probability that each number appears in the next draw. Because each draw
contains exactly 15 numbers, the expected mass is 15 (not 1). Downstream
consumers rely on that invariant.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Expected mass for any valid next-draw distribution.
EXPECTED_MASS = 15
NUMBER_COUNT = 25


class ModelVersion(BaseModel):
    """Identifies a specific model artifact used to produce a distribution.

    Keep model versions short and human-readable; bump on any change to
    training code, feature spec, or hyperparameters.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    details: dict[str, str] = Field(default_factory=dict)

    def label(self) -> str:
        return f"{self.name}:{self.version}"


class NumberProbability(BaseModel):
    model_config = ConfigDict(frozen=True)

    number: int = Field(ge=1, le=25)
    probability: float = Field(ge=0.0, le=1.0)


class NextDrawDistribution(BaseModel):
    """Ensemble next-draw distribution.

    ``probabilities`` is length 25, one per number, and ``sum(probabilities)``
    is `EXPECTED_MASS` (15) up to floating-point tolerance.
    """

    model_config = ConfigDict(frozen=True)

    dataset_hash: str
    computed_at: datetime
    ensemble_weights: dict[str, float] = Field(
        description="Weight applied to each component model when combining."
    )
    model_versions: tuple[ModelVersion, ...]
    probabilities: tuple[NumberProbability, ...]


class ComponentDistribution(BaseModel):
    """A single component of the ensemble (e.g. baseline or learned).

    Exposed so the agent tool layer can surface each component to explain the
    ensemble's output, not just the final weighted vector.
    """

    model_config = ConfigDict(frozen=True)

    model_version: ModelVersion
    probabilities: tuple[NumberProbability, ...]
