"""Per-number learned model (HistGradientBoostingClassifier).

Trains one binary classifier per number — will this number appear in the next
draw? Uses the oldest 80% of the training matrix built in `features.py`. The
remaining 20% (calibration + held-out eval) is reserved for §7 and returned
here as index ranges so the caller can slice later.

Determinism: classifiers use a fixed ``random_state`` and sklearn's GBM is
deterministic under that seed + fixed feature ordering.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Final

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier

from service.engine.features import (
    FEATURE_VERSION,
    MIN_PRIOR_DRAWS,
    extract_features_at,
    extract_training_matrix,
)
from service.engine.models import (
    EXPECTED_MASS,
    NUMBER_COUNT,
    ComponentDistribution,
    ModelVersion,
    NumberProbability,
)
from service.ingestion import DrawHistory

LEARNED_NAME: Final = "learned"
LEARNED_VERSION: Final = "v1"
RANDOM_STATE: Final = 42

# 80% train / 15% calibration / 5% held-out — calibration + eval are §7's job
# but the split is defined here so all downstream slicing stays consistent.
TRAIN_FRACTION: Final = 0.80
CALIBRATION_FRACTION: Final = 0.15


@dataclass(frozen=True)
class TrainingSplits:
    train_idx: tuple[int, ...]
    calibration_idx: tuple[int, ...]
    eval_idx: tuple[int, ...]


@dataclass(frozen=True)
class LearnedArtifact:
    """Trained per-number models plus metadata. Immutable once built."""

    classifiers: tuple[HistGradientBoostingClassifier, ...]  # length 25
    feature_version: str
    model_version: str
    train_split_size: int
    splits: TrainingSplits
    dataset_hash: str

    def predict_probabilities(self, history: DrawHistory) -> ComponentDistribution:
        """Produce a 25-length distribution for the draw immediately after the history."""
        target_index = len(history)
        features = extract_features_at(history, predict_for_index=target_index)

        probs = np.zeros(NUMBER_COUNT, dtype=np.float64)
        for n_idx in range(NUMBER_COUNT):
            clf = self.classifiers[n_idx]
            x = features[n_idx].reshape(1, -1)
            # predict_proba returns shape (1, 2) with columns [P(class=0), P(class=1)]
            # — take P(class=1), i.e. P(this number appears).
            proba = clf.predict_proba(x)[0]
            # Some classes may have been missing in training — classes_ is 1-length.
            classes = list(clf.classes_)
            if 1 in classes:
                probs[n_idx] = float(proba[classes.index(1)])
            else:
                probs[n_idx] = 0.0

        # Renormalise to EXPECTED_MASS. Learned classifiers are trained
        # independently per number, so raw probabilities do not naturally sum
        # to 15; the normalisation here produces the per-number marginal mass
        # that the ensemble contract requires.
        mass = probs.sum()
        if mass > 0:
            probs *= EXPECTED_MASS / mass
        probs = np.clip(probs, 0.0, 1.0)
        # Re-scale after clipping, because clipping can shrink total mass below 15.
        post_mass = probs.sum()
        if post_mass > 0:
            probs *= EXPECTED_MASS / post_mass
        probs = np.clip(probs, 0.0, 1.0)

        probabilities = tuple(
            NumberProbability(number=i + 1, probability=float(probs[i]))
            for i in range(NUMBER_COUNT)
        )
        return ComponentDistribution(
            model_version=ModelVersion(
                name=LEARNED_NAME,
                version=self.model_version,
                details={
                    "feature_version": self.feature_version,
                    "train_rows": str(self.train_split_size),
                },
            ),
            probabilities=probabilities,
        )


def _compute_splits(total_rows: int) -> TrainingSplits:
    train_end = int(total_rows * TRAIN_FRACTION)
    cal_end = int(total_rows * (TRAIN_FRACTION + CALIBRATION_FRACTION))
    # Guarantee at least one row per split when total is small — tests rely on this.
    train_end = max(1, train_end)
    cal_end = max(train_end + 1, cal_end) if total_rows > train_end else train_end
    train = tuple(range(0, train_end))
    cal = tuple(range(train_end, cal_end))
    ev = tuple(range(cal_end, total_rows))
    return TrainingSplits(train_idx=train, calibration_idx=cal, eval_idx=ev)


def train_learned(history: DrawHistory) -> LearnedArtifact:
    """Train 25 per-number GBMs on the training slice of *history*.

    Raises ``ValueError`` when history is too short to produce features.
    """
    x_all, y_all, _target_indices = extract_training_matrix(history)
    total_rows = x_all.shape[0]
    splits = _compute_splits(total_rows)

    train_rows = np.array(splits.train_idx)
    if train_rows.size < 10:
        raise ValueError(
            f"training slice has {train_rows.size} rows after MIN_PRIOR_DRAWS; "
            "need at least 10 — history too short for the learned model"
        )

    x_train = x_all[train_rows]  # shape (N_train, 25, FEATURE_COUNT)
    y_train = y_all[train_rows]  # shape (N_train, 25)

    classifiers: list[HistGradientBoostingClassifier] = []
    for n_idx in range(NUMBER_COUNT):
        x_n = x_train[:, n_idx, :]  # shape (N_train, FEATURE_COUNT)
        y_n = y_train[:, n_idx]  # shape (N_train,)
        clf = HistGradientBoostingClassifier(
            max_iter=80,
            max_depth=4,
            learning_rate=0.05,
            random_state=RANDOM_STATE,
            l2_regularization=0.1,
        )
        # If a number never (or always) appeared in the training slice, fit a
        # degenerate classifier that still responds to predict_proba.
        if len(np.unique(y_n)) < 2:
            classifiers.append(_DegenerateClassifier(label=int(y_n[0])))
        else:
            clf.fit(x_n, y_n)
            classifiers.append(clf)

    return LearnedArtifact(
        classifiers=tuple(classifiers),
        feature_version=FEATURE_VERSION,
        model_version=LEARNED_VERSION,
        train_split_size=int(train_rows.size),
        splits=splits,
        dataset_hash=history.provenance.content_hash,
    )


class _DegenerateClassifier:
    """Stand-in for a fitted classifier when one class never appeared.

    Exposes the ``classes_`` / ``predict_proba`` surface that the rest of the
    engine uses. Returns a fixed probability — 1.0 if the label was 1 in
    training, 0.0 otherwise.
    """

    def __init__(self, *, label: int) -> None:
        self.classes_ = np.array([label])
        self._label = label

    def predict_proba(self, x: np.ndarray) -> np.ndarray:
        n = x.shape[0]
        prob = 1.0 if self._label == 1 else 0.0
        return np.full((n, 1), prob, dtype=np.float64)


# --- Process-wide cache ----------------------------------------------------

_lock = threading.Lock()
_cached: LearnedArtifact | None = None


def get_learned_model(history: DrawHistory) -> LearnedArtifact:
    """Return a learned model for *history*, training on first use.

    Cached per process. If the dataset hash changes, the cache is discarded
    and the model is retrained.
    """
    global _cached
    if _cached is not None and _cached.dataset_hash == history.provenance.content_hash:
        return _cached
    with _lock:
        if _cached is None or _cached.dataset_hash != history.provenance.content_hash:
            _cached = train_learned(history)
    return _cached


def reset_learned_cache() -> None:
    """Drop the cached learned model. Only for tests."""
    global _cached
    with _lock:
        _cached = None


def history_supports_learned(history: DrawHistory) -> bool:
    """Return whether the history has enough rows to produce a learned model."""
    return len(history) >= MIN_PRIOR_DRAWS + 11  # +1 target + ≥10 training rows
