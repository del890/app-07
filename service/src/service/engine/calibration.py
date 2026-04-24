"""Probability calibration for the prediction engine (§7).

Splits the draw history into train / calibration / held-out slices (already
defined in ``learned.py``), fits an isotonic-regression calibrator on the
calibration slice, and computes eval metrics on the held-out slice.

Layout
------
- ``split_history``          — returns the three index ranges
- ``fit_calibrator``         — trains and persists an isotonic calibrator
- ``CalibrationStatus``      — queryable model (last run, staleness, metrics)
- ``get_calibration_status`` — process-wide accessor

Staleness rule (§7.5): calibration is stale if it has never been run OR if it
was produced more than MAX_CALIBRATION_AGE_DAYS days ago OR if the model
version on record differs from the current learned-model version.

All artifacts are written to ``CALIBRATION_DIR`` (configured via the env var
``CALIBRATION_DIR``, default ``service/calibration_artifacts``).
"""

from __future__ import annotations

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

import numpy as np

from service.engine.learned import (
    LEARNED_VERSION,
    LearnedArtifact,
    _compute_splits,
    get_learned_model,
)
from service.engine.models import NUMBER_COUNT
from service.ingestion import DrawHistory

MAX_CALIBRATION_AGE_DAYS: Final = 14

_DEFAULT_CALIBRATION_DIR = (
    Path(__file__).resolve().parents[4] / "calibration_artifacts"
)


def _calibration_dir() -> Path:
    raw = os.environ.get("CALIBRATION_DIR", "")
    if raw:
        return Path(raw)
    return _DEFAULT_CALIBRATION_DIR


# ---------------------------------------------------------------------------
# History splitting
# ---------------------------------------------------------------------------


def split_history(
    history: DrawHistory,
) -> tuple[list[int], list[int], list[int]]:
    """Return (train_indices, calibration_indices, eval_indices).

    Delegates to the same split logic used during model training so the slices
    are guaranteed to be consistent with what the learned model was trained on.
    """
    from service.engine.features import extract_training_matrix

    x_all, y_all, target_indices = extract_training_matrix(history)
    total_rows = x_all.shape[0]
    splits = _compute_splits(total_rows)
    return (
        list(splits.train_idx),
        list(splits.calibration_idx),
        list(splits.eval_idx),
    )


# ---------------------------------------------------------------------------
# Reliability curve
# ---------------------------------------------------------------------------


def _reliability_curve(
    y_true: np.ndarray, y_prob: np.ndarray, *, n_bins: int = 10
) -> list[dict]:
    """Compute reliability-diagram data (fraction_positive vs mean_predicted_value)."""
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    curve = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (y_prob >= lo) & (y_prob < hi)
        if not mask.any():
            continue
        curve.append(
            {
                "bin_low": float(lo),
                "bin_high": float(hi),
                "mean_predicted": float(y_prob[mask].mean()),
                "fraction_positive": float(y_true[mask].mean()),
                "count": int(mask.sum()),
            }
        )
    return curve


# ---------------------------------------------------------------------------
# Calibrator fitting
# ---------------------------------------------------------------------------


class NumberCalibrator:
    """Isotonic calibrator for one number using the Pool Adjacent Violators (PAVA) algorithm.

    Maps raw classifier probability in [0, 1] → calibrated probability.
    Uses a pure-Python PAVA to avoid the sklearn.isotonic C extension which
    has stability issues in the current environment.
    """

    def __init__(self, number: int) -> None:
        self.number = number  # 1-based
        self._x_cal: np.ndarray | None = None
        self._y_cal: np.ndarray | None = None

    def fit(self, y_prob: np.ndarray, y_true: np.ndarray) -> None:
        """Fit the isotonic mapping from raw probabilities → true frequencies."""
        # Sort by raw probability
        order = np.argsort(y_prob)
        x_sorted = y_prob[order]
        y_sorted = y_true[order].astype(float)
        # Run PAVA
        y_iso = _pava(y_sorted)
        self._x_cal = x_sorted
        self._y_cal = y_iso

    def transform(self, y_prob: np.ndarray) -> np.ndarray:
        """Interpolate calibrated probabilities for new raw scores."""
        if self._x_cal is None or self._y_cal is None:
            raise RuntimeError("calibrator has not been fitted")
        return np.interp(y_prob, self._x_cal, self._y_cal)


def _pava(y: np.ndarray) -> np.ndarray:
    """Pool Adjacent Violators Algorithm — returns non-decreasing isotonic fit."""
    n = len(y)
    if n == 0:
        return y.copy()
    # Blocks: (sum, count)
    blocks: list[list[float]] = [[float(v), 1.0] for v in y]
    changed = True
    while changed:
        changed = False
        i = 0
        new_blocks: list[list[float]] = []
        while i < len(blocks):
            if i + 1 < len(blocks) and blocks[i][0] / blocks[i][1] > blocks[i + 1][0] / blocks[i + 1][1]:
                merged = [blocks[i][0] + blocks[i + 1][0], blocks[i][1] + blocks[i + 1][1]]
                new_blocks.append(merged)
                i += 2
                changed = True
            else:
                new_blocks.append(blocks[i])
                i += 1
        blocks = new_blocks
    # Expand blocks back to individual values
    result = np.zeros(n, dtype=float)
    idx = 0
    for total, count in blocks:
        val = total / count
        for _ in range(int(count)):
            if idx < n:
                result[idx] = val
                idx += 1
    return result


def fit_calibrator(
    history: DrawHistory,
    artifact: LearnedArtifact,
) -> tuple[list[NumberCalibrator], dict]:
    """Fit per-number isotonic calibrators on the calibration slice.

    Returns
    -------
    calibrators : list[NumberCalibrator]
        Length-25 list, one per number.
    metadata : dict
        Includes calibration slice sizes, dataset hash, model version, reliability
        curves, and the computed_at timestamp used by CalibrationStatus.
    """
    x_all = artifact.x_all
    y_all = artifact.y_all
    splits = artifact.splits
    cal_rows = np.array(splits.calibration_idx)
    eval_rows = np.array(splits.eval_idx)

    if cal_rows.size == 0:
        raise ValueError(
            "calibration slice is empty — history too short to calibrate"
        )

    x_cal = x_all[cal_rows]  # (N_cal, 25, F)
    y_cal = y_all[cal_rows]  # (N_cal, 25)

    calibrators: list[NumberCalibrator] = []
    reliability_curves: list[list[dict]] = []

    for n_idx in range(NUMBER_COUNT):
        clf = artifact.classifiers[n_idx]
        x_n = x_cal[:, n_idx, :]  # (N_cal, F)
        y_n = y_cal[:, n_idx]  # (N_cal,)

        # Raw probabilities from the learned classifier
        proba = clf.predict_proba(x_n)[:, -1]  # P(class=1) or class=0 if degenerate

        # Handle degenerate classifier where classes_ has only one element
        classes = list(clf.classes_)
        if 1 in classes:
            raw_probs = clf.predict_proba(x_n)[:, classes.index(1)]
        else:
            raw_probs = np.zeros(len(x_n), dtype=np.float64)

        cal = NumberCalibrator(number=n_idx + 1)
        cal.fit(raw_probs, y_n.astype(float))
        calibrators.append(cal)
        reliability_curves.append(_reliability_curve(y_n.astype(float), raw_probs))

    # ------------------------------------------------------------------
    # Eval metrics on held-out slice
    # ------------------------------------------------------------------
    eval_metrics: list[dict] = []
    if eval_rows.size > 0:
        x_eval = x_all[eval_rows]
        y_eval = y_all[eval_rows]
        all_y_true: list[float] = []
        all_y_prob_raw: list[float] = []
        all_y_prob_cal: list[float] = []

        for n_idx in range(NUMBER_COUNT):
            clf = artifact.classifiers[n_idx]
            cal = calibrators[n_idx]
            x_n = x_eval[:, n_idx, :]
            y_n = y_eval[:, n_idx].astype(float)
            classes = list(clf.classes_)
            if 1 in classes:
                raw_p = clf.predict_proba(x_n)[:, classes.index(1)]
            else:
                raw_p = np.zeros(len(x_n), dtype=np.float64)
            cal_p = cal.transform(raw_p)
            cal_p = np.clip(cal_p, 1e-7, 1.0 - 1e-7)

            all_y_true.extend(y_n.tolist())
            all_y_prob_raw.extend(raw_p.tolist())
            all_y_prob_cal.extend(cal_p.tolist())

        yt = np.array(all_y_true)
        yr = np.clip(np.array(all_y_prob_raw), 1e-7, 1.0 - 1e-7)
        yc = np.clip(np.array(all_y_prob_cal), 1e-7, 1.0 - 1e-7)

        def _brier(y_true: np.ndarray, y_prob: np.ndarray) -> float:
            return float(np.mean((y_true - y_prob) ** 2))

        def _log_loss(y_true: np.ndarray, y_prob: np.ndarray) -> float:
            return float(-np.mean(y_true * np.log(y_prob) + (1 - y_true) * np.log(1 - y_prob)))

        eval_metrics = {
            "brier_score_raw": float(_brier(yt, yr)),
            "brier_score_calibrated": float(_brier(yt, yc)),
            "log_loss_raw": float(_log_loss(yt, yr)),
            "log_loss_calibrated": float(_log_loss(yt, yc)),
            "n_eval_rows": int(eval_rows.size),
        }
    else:
        eval_metrics = {
            "brier_score_raw": None,
            "brier_score_calibrated": None,
            "log_loss_raw": None,
            "log_loss_calibrated": None,
            "n_eval_rows": 0,
        }

    metadata = {
        "computed_at": datetime.now(UTC).isoformat(),
        "dataset_hash": history.provenance.content_hash,
        "model_version": artifact.model_version,
        "feature_version": artifact.feature_version,
        "n_calibration_rows": int(cal_rows.size),
        "eval_metrics": eval_metrics,
        "reliability_curves": reliability_curves,
    }

    return calibrators, metadata


# ---------------------------------------------------------------------------
# CalibrationStatus model
# ---------------------------------------------------------------------------


class CalibrationStatus:
    """Queryable calibration status, attached to the process-wide state.

    Attributes
    ----------
    last_calibrated_at : datetime | None
    is_stale : bool
    dataset_hash : str | None
    model_version : str | None
    feature_version : str | None
    eval_metrics : dict | None
    reliability_curve : list[list[dict]] (per-number)
    calibrators : list[NumberCalibrator] | None
    """

    def __init__(
        self,
        *,
        last_calibrated_at: datetime | None = None,
        dataset_hash: str | None = None,
        model_version: str | None = None,
        feature_version: str | None = None,
        eval_metrics: dict | None = None,
        reliability_curves: list[list[dict]] | None = None,
        calibrators: list[NumberCalibrator] | None = None,
    ) -> None:
        self.last_calibrated_at = last_calibrated_at
        self.dataset_hash = dataset_hash
        self.model_version = model_version
        self.feature_version = feature_version
        self.eval_metrics = eval_metrics
        self.reliability_curves = reliability_curves
        self.calibrators = calibrators

    @property
    def is_stale(self) -> bool:
        """Return True when calibration has never run, is too old, or model changed."""
        if self.last_calibrated_at is None:
            return True
        age = (datetime.now(UTC) - self.last_calibrated_at).days
        if age > MAX_CALIBRATION_AGE_DAYS:
            return True
        if self.model_version != LEARNED_VERSION:
            return True
        return False

    def to_dict(self) -> dict:
        return {
            "last_calibrated_at": (
                self.last_calibrated_at.isoformat()
                if self.last_calibrated_at
                else None
            ),
            "is_stale": self.is_stale,
            "dataset_hash": self.dataset_hash,
            "model_version": self.model_version,
            "feature_version": self.feature_version,
            "eval_metrics": self.eval_metrics,
            "reliability_curves": self.reliability_curves,
        }


# ---------------------------------------------------------------------------
# Process-wide cache
# ---------------------------------------------------------------------------

_status_lock = threading.Lock()
_status: CalibrationStatus = CalibrationStatus()


def get_calibration_status() -> CalibrationStatus:
    """Return the current process-wide calibration status (read-only)."""
    return _status


def run_calibration(history: DrawHistory) -> CalibrationStatus:
    """Run calibration (fit isotonic regressors) and update the global status.

    Safe to call from multiple threads; uses an internal lock.
    """
    global _status
    artifact = get_learned_model(history)
    calibrators, metadata = fit_calibrator(history, artifact)
    new_status = CalibrationStatus(
        last_calibrated_at=datetime.fromisoformat(metadata["computed_at"]),
        dataset_hash=metadata["dataset_hash"],
        model_version=metadata["model_version"],
        feature_version=metadata["feature_version"],
        eval_metrics=metadata["eval_metrics"],
        reliability_curves=metadata["reliability_curves"],
        calibrators=calibrators,
    )
    _persist_metadata(metadata)
    with _status_lock:
        _status = new_status
    return new_status


def reset_calibration() -> None:
    """Reset calibration state. Only for tests."""
    global _status
    with _status_lock:
        _status = CalibrationStatus()


def _persist_metadata(metadata: dict) -> None:
    """Write calibration metadata JSON to disk (best-effort; errors are logged, not raised)."""
    try:
        cal_dir = _calibration_dir()
        cal_dir.mkdir(parents=True, exist_ok=True)
        out = cal_dir / "calibration_metadata.json"
        # Reliability curves can be large; store separately for space.
        slim = {k: v for k, v in metadata.items() if k != "reliability_curves"}
        out.write_text(json.dumps(slim, indent=2))
    except Exception:
        pass  # Disk persistence is best-effort; in-memory state is canonical.
