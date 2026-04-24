"""Prediction-engine capability: baseline + learned + ensemble.

Public surface; the agent tool layer (§8) wires these into typed handlers.

- `compute_baseline` — deterministic frequency-recency baseline
- `train_learned` / `get_learned_model` — per-number GBM classifiers
- `compute_next_draw_distribution` — weighted ensemble of the two
- `NextDrawDistribution`, `ComponentDistribution`, `ModelVersion`,
  `NumberProbability` — response models
"""

from __future__ import annotations

from service.engine.baseline import (
    BASELINE_NAME,
    BASELINE_VERSION,
    DEFAULT_DECAY,
    DEFAULT_WINDOW,
    compute_baseline,
)
from service.engine.ensemble import (
    DEFAULT_BASELINE_WEIGHT,
    DEFAULT_LEARNED_WEIGHT,
    compute_next_draw_distribution,
)
from service.engine.features import (
    FEATURE_COUNT,
    FEATURE_NAMES,
    FEATURE_VERSION,
    MIN_PRIOR_DRAWS,
)
from service.engine.learned import (
    LEARNED_NAME,
    LEARNED_VERSION,
    LearnedArtifact,
    TrainingSplits,
    get_learned_model,
    history_supports_learned,
    reset_learned_cache,
    train_learned,
)
from service.engine.calibration import (
    MAX_CALIBRATION_AGE_DAYS,
    CalibrationStatus,
    NumberCalibrator,
    fit_calibrator,
    get_calibration_status,
    reset_calibration,
    run_calibration,
    split_history,
)
from service.engine.models import (
    EXPECTED_MASS,
    NUMBER_COUNT,
    ComponentDistribution,
    ModelVersion,
    NextDrawDistribution,
    NumberProbability,
)

__all__ = [
    "BASELINE_NAME",
    "BASELINE_VERSION",
    "DEFAULT_BASELINE_WEIGHT",
    "DEFAULT_DECAY",
    "DEFAULT_LEARNED_WEIGHT",
    "DEFAULT_WINDOW",
    "EXPECTED_MASS",
    "FEATURE_COUNT",
    "FEATURE_NAMES",
    "FEATURE_VERSION",
    "LEARNED_NAME",
    "LEARNED_VERSION",
    "MAX_CALIBRATION_AGE_DAYS",
    "MIN_PRIOR_DRAWS",
    "NUMBER_COUNT",
    "CalibrationStatus",
    "ComponentDistribution",
    "LearnedArtifact",
    "ModelVersion",
    "NextDrawDistribution",
    "NumberCalibrator",
    "NumberProbability",
    "TrainingSplits",
    "compute_baseline",
    "compute_next_draw_distribution",
    "fit_calibrator",
    "get_calibration_status",
    "get_learned_model",
    "history_supports_learned",
    "reset_calibration",
    "reset_learned_cache",
    "run_calibration",
    "split_history",
    "train_learned",
]
