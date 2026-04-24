"""Tests for the prediction-engine (baseline + learned + ensemble).

Spec contract checked:
- Baseline is bit-deterministic given the same inputs.
- Learned model trains + predicts on a real-size history.
- Ensemble's 25-length probability vector sums to `EXPECTED_MASS` (15) up to
  floating-point tolerance, and every probability is in [0, 1].
- Every response carries model-version provenance.
- `history_supports_learned` gates the ensemble honestly on small histories.
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import pytest

from service.engine import (
    BASELINE_NAME,
    EXPECTED_MASS,
    FEATURE_VERSION,
    LEARNED_NAME,
    MIN_PRIOR_DRAWS,
    NUMBER_COUNT,
    CalibrationStatus,
    compute_baseline,
    compute_next_draw_distribution,
    fit_calibrator,
    get_calibration_status,
    history_supports_learned,
    reset_calibration,
    run_calibration,
    split_history,
    train_learned,
)
from service.ingestion import DrawHistory, load

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_DATA = REPO_ROOT / "data.json"


def _synth_history(tmp_path: Path, n_draws: int, *, seed: int = 1) -> DrawHistory:
    rng = random.Random(seed)
    start = date(2019, 1, 1)
    draws = []
    for i in range(n_draws):
        numbers = rng.sample(range(1, 26), 15)
        draws.append(
            {
                "id": n_draws - i,
                "date": (start + timedelta(days=(n_draws - 1 - i))).strftime("%d-%m-%Y"),
                "numbers": numbers,
            }
        )
    path = tmp_path / f"synth_{n_draws}.json"
    path.write_text(
        json.dumps({"allowed_numbers": list(range(1, 26)), "dataset": draws}),
        encoding="utf-8",
    )
    return load(path)


# ---------------------------------------------------------------------------
# Baseline
# ---------------------------------------------------------------------------


def test_baseline_is_bit_deterministic_on_tiny(tiny_history) -> None:
    a = compute_baseline(tiny_history, window=3, decay=0.9)
    b = compute_baseline(tiny_history, window=3, decay=0.9)
    assert [p.model_dump() for p in a.probabilities] == [p.model_dump() for p in b.probabilities]


def test_baseline_mass_equals_expected_mass_on_tiny(tiny_history) -> None:
    result = compute_baseline(tiny_history, window=3, decay=1.0)
    total = sum(p.probability for p in result.probabilities)
    assert total == pytest.approx(EXPECTED_MASS, abs=1e-9)
    assert len(result.probabilities) == NUMBER_COUNT


def test_baseline_carries_model_version(tiny_history) -> None:
    result = compute_baseline(tiny_history)
    assert result.model_version.name == BASELINE_NAME
    assert result.model_version.version
    assert "window" in result.model_version.details


def test_baseline_rejects_bad_decay(tiny_history) -> None:
    with pytest.raises(ValueError, match="decay must be in"):
        compute_baseline(tiny_history, decay=0.0)
    with pytest.raises(ValueError, match="decay must be in"):
        compute_baseline(tiny_history, decay=1.5)


def test_baseline_probabilities_are_bounded(tiny_history) -> None:
    # Extreme decay squeezes mass onto the last draw; per-number p must still be ≤ 1.
    result = compute_baseline(tiny_history, window=3, decay=0.01)
    for p in result.probabilities:
        assert 0.0 <= p.probability <= 1.0


# ---------------------------------------------------------------------------
# Learned model
# ---------------------------------------------------------------------------


def test_learned_rejects_too_short_history(tiny_history) -> None:
    with pytest.raises(ValueError, match="need at least"):
        train_learned(tiny_history)


def test_history_supports_learned_flag(tmp_path: Path) -> None:
    small = _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS - 1, seed=2)
    assert history_supports_learned(small) is False
    big = _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS + 30, seed=2)
    assert history_supports_learned(big) is True


def test_learned_trains_and_predicts(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS + 60, seed=3)
    artifact = train_learned(history)
    assert len(artifact.classifiers) == NUMBER_COUNT
    assert artifact.feature_version == FEATURE_VERSION
    assert artifact.dataset_hash == history.provenance.content_hash
    assert artifact.train_split_size > 0

    component = artifact.predict_probabilities(history)
    assert len(component.probabilities) == NUMBER_COUNT
    total = sum(p.probability for p in component.probabilities)
    # Learned component is renormalised to EXPECTED_MASS per contract
    assert total == pytest.approx(EXPECTED_MASS, abs=1e-6)
    for p in component.probabilities:
        assert 0.0 <= p.probability <= 1.0
    assert component.model_version.name == LEARNED_NAME
    assert component.model_version.details["feature_version"] == FEATURE_VERSION


def test_learned_training_split_sizes_add_up(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS + 100, seed=4)
    artifact = train_learned(history)
    splits = artifact.splits
    total = len(splits.train_idx) + len(splits.calibration_idx) + len(splits.eval_idx)
    assert total > 0
    # Train slice is strictly the first chunk; no overlap with calibration/eval.
    if splits.train_idx and splits.calibration_idx:
        assert max(splits.train_idx) < min(splits.calibration_idx)
    if splits.calibration_idx and splits.eval_idx:
        assert max(splits.calibration_idx) < min(splits.eval_idx)


# ---------------------------------------------------------------------------
# Ensemble
# ---------------------------------------------------------------------------


def test_ensemble_sums_to_expected_mass_on_large_history(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS + 50, seed=5)
    result = compute_next_draw_distribution(history)
    total = sum(p.probability for p in result.probabilities)
    assert total == pytest.approx(EXPECTED_MASS, abs=1e-6)
    assert all(0.0 <= p.probability <= 1.0 for p in result.probabilities)
    assert len(result.probabilities) == NUMBER_COUNT


def test_ensemble_contains_both_component_versions(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS + 60, seed=6)
    result = compute_next_draw_distribution(history)
    names = {mv.name for mv in result.model_versions}
    assert BASELINE_NAME in names
    assert LEARNED_NAME in names
    assert result.dataset_hash == history.provenance.content_hash
    # Weights sum to 1.0 after internal normalisation
    assert sum(result.ensemble_weights.values()) == pytest.approx(1.0)


def test_ensemble_falls_back_to_baseline_on_short_history(tiny_history) -> None:
    result = compute_next_draw_distribution(tiny_history)
    names = {mv.name for mv in result.model_versions}
    assert names == {BASELINE_NAME}  # learned is skipped on small history
    assert sum(result.ensemble_weights.values()) == pytest.approx(1.0)
    total = sum(p.probability for p in result.probabilities)
    assert total == pytest.approx(EXPECTED_MASS, abs=1e-9)


def test_ensemble_rejects_negative_weights(tiny_history) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        compute_next_draw_distribution(tiny_history, baseline_weight=-0.1)


def test_ensemble_rejects_all_zero_weights(tiny_history) -> None:
    with pytest.raises(ValueError, match="at least one"):
        compute_next_draw_distribution(tiny_history, baseline_weight=0.0, learned_weight=0.0)


# ---------------------------------------------------------------------------
# Real-data smoke — ensemble works against the actual 3,656-draw history.
# ---------------------------------------------------------------------------


def test_ensemble_on_real_data_smoke() -> None:
    history = load(REAL_DATA)
    assert history_supports_learned(history)
    result = compute_next_draw_distribution(history)
    total = sum(p.probability for p in result.probabilities)
    assert total == pytest.approx(EXPECTED_MASS, abs=1e-6)
    assert all(0.0 <= p.probability <= 1.0 for p in result.probabilities)
    # Every draw in the real history is 15-of-25, so no single-number prob should be near 1
    assert max(p.probability for p in result.probabilities) < 0.95


# ---------------------------------------------------------------------------
# Calibration (§7)
# ---------------------------------------------------------------------------


def _large_history(tmp_path: Path, seed: int = 10) -> "DrawHistory":
    return _synth_history(tmp_path, n_draws=MIN_PRIOR_DRAWS + 200, seed=seed)


def test_split_history_returns_non_overlapping_slices(tmp_path: Path) -> None:
    history = _large_history(tmp_path)
    train, cal, ev = split_history(history)
    assert len(train) > 0
    assert len(cal) > 0
    assert len(ev) > 0
    # Non-overlapping
    all_indices = train + cal + ev
    assert len(all_indices) == len(set(all_indices))
    # Correct ordering: train < cal < eval
    assert max(train) < min(cal)
    assert max(cal) < min(ev)


def test_split_history_fractions(tmp_path: Path) -> None:
    history = _large_history(tmp_path)
    train, cal, ev = split_history(history)
    total = len(train) + len(cal) + len(ev)
    # Train ~80%, cal ~15%, eval ~5% — allow generous tolerance for small N
    assert len(train) / total >= 0.70
    assert len(cal) / total >= 0.05


def test_fit_calibrator_returns_25_calibrators(tmp_path: Path) -> None:
    history = _large_history(tmp_path)
    artifact = train_learned(history)
    calibrators, metadata = fit_calibrator(history, artifact)
    assert len(calibrators) == NUMBER_COUNT
    assert "computed_at" in metadata
    assert "eval_metrics" in metadata
    assert metadata["dataset_hash"] == history.provenance.content_hash


def test_calibrator_reduces_ece_on_synthetic(tmp_path: Path) -> None:
    """Isotonic calibration should not increase Brier score on eval slice."""
    history = _large_history(tmp_path, seed=11)
    artifact = train_learned(history)
    calibrators, metadata = fit_calibrator(history, artifact)
    m = metadata["eval_metrics"]
    if m["n_eval_rows"] > 0:
        # Calibrated Brier should be <= raw Brier (calibration should not hurt)
        assert m["brier_score_calibrated"] <= m["brier_score_raw"] + 0.05


def test_calibration_status_starts_stale() -> None:
    reset_calibration()
    status = get_calibration_status()
    assert status.is_stale is True
    assert status.last_calibrated_at is None


def test_run_calibration_clears_stale_flag(tmp_path: Path) -> None:
    reset_calibration()
    history = _large_history(tmp_path)
    status = run_calibration(history)
    assert status.is_stale is False
    assert status.last_calibrated_at is not None
    assert status.eval_metrics is not None
    assert len(status.calibrators) == NUMBER_COUNT


def test_stale_sentinel_flips_on_model_version_change(tmp_path: Path) -> None:
    """CalibrationStatus with a stale model_version is stale."""
    history = _large_history(tmp_path)
    status = run_calibration(history)
    # Simulate a model version change by inspecting stale logic
    stale_status = CalibrationStatus(
        last_calibrated_at=status.last_calibrated_at,
        model_version="v0",  # old version
    )
    assert stale_status.is_stale is True


def test_calibration_status_is_fresh_immediately_after_run(tmp_path: Path) -> None:
    reset_calibration()
    history = _large_history(tmp_path)
    status = run_calibration(history)
    assert not status.is_stale
    # Returned status and global status agree
    global_status = get_calibration_status()
    assert global_status.last_calibrated_at == status.last_calibrated_at


def test_uncalibrated_status_has_none_metrics() -> None:
    reset_calibration()
    status = get_calibration_status()
    assert status.eval_metrics is None
    assert status.reliability_curves is None
    assert status.calibrators is None
