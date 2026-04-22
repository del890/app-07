"""Tests for the external-signal-correlation capability.

Covers (mapping to spec scenarios):
- SignalSeries metadata is mandatory and date-sorted.
- File-based CSV and JSON signal loaders.
- Forward-fill alignment with lag.
- Event-keyed alignment rejects non-exact-date matches.
- Spearman returns significant on a known-correlated synthetic series.
- Mann-Whitney handles a binary metric (number_present).
- Under-powered aligned sample flags `under_powered=True`, does NOT suppress.
- Single correlation does not fabricate a q-value.
- Batch correlation applies BH correction matching a hand calculation.
- Research-artifact label and disclaimer are present on every result.
"""

from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import pytest

from service.correlation import (
    DEFAULT_MIN_SAMPLE_SIZE,
    RESEARCH_DISCLAIMER,
    MetricSpec,
    SignalLoadError,
    SignalPoint,
    SignalSeries,
    benjamini_hochberg,
    correlate,
    correlate_batch,
    load_csv,
    load_json,
)
from service.ingestion import DrawHistory, load


def _write_dataset(path: Path, draws: list[dict[str, object]]) -> None:
    payload = {"allowed_numbers": list(range(1, 26)), "dataset": draws}
    path.write_text(json.dumps(payload), encoding="utf-8")


def _synth_history(tmp_path: Path, n_draws: int, *, seed: int = 1) -> DrawHistory:
    """Build a pseudo-random draw history of *n_draws* draws."""
    rng = random.Random(seed)
    start = date(2019, 1, 1)
    draws = []
    for i in range(n_draws):
        numbers = rng.sample(range(1, 26), 15)
        # Reverse-chronological in source, as data.json is:
        draws.append(
            {
                "id": n_draws - i,
                "date": (start + timedelta(days=(n_draws - 1 - i))).strftime("%d-%m-%Y"),
                "numbers": numbers,
            }
        )
    path = tmp_path / f"synth_{n_draws}.json"
    _write_dataset(path, draws)
    return load(path)


# ---------------------------------------------------------------------------
# SignalSeries model
# ---------------------------------------------------------------------------


def test_signal_series_sorts_and_rejects_duplicates() -> None:
    # Unordered input is sorted by date automatically.
    series = SignalSeries(
        name="foo",
        cadence="daily",
        unit="unit",
        source="test",
        points=(
            SignalPoint(date=date(2020, 1, 3), value=3.0),
            SignalPoint(date=date(2020, 1, 1), value=1.0),
            SignalPoint(date=date(2020, 1, 2), value=2.0),
        ),
    )
    assert [p.date for p in series.points] == [
        date(2020, 1, 1),
        date(2020, 1, 2),
        date(2020, 1, 3),
    ]

    # Duplicate dates are ambiguous under forward-fill and rejected.
    with pytest.raises(ValueError, match="duplicate date"):
        SignalSeries(
            name="dup",
            cadence="daily",
            unit="u",
            source="s",
            points=(
                SignalPoint(date=date(2020, 1, 1), value=1.0),
                SignalPoint(date=date(2020, 1, 1), value=2.0),
            ),
        )


def test_signal_series_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one point"):
        SignalSeries(name="x", cadence="daily", unit="u", source="s", points=())


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def test_load_csv_parses_both_date_formats(tmp_path: Path) -> None:
    path = tmp_path / "s.csv"
    path.write_text(
        "date,value\n2020-01-01,100\n02-01-2020,101\n2020-01-03,102\n",
        encoding="utf-8",
    )
    series = load_csv(path, name="s", cadence="daily", unit="u", source="test")
    assert len(series.points) == 3
    assert series.points[0].date == date(2020, 1, 1)
    assert series.points[1].date == date(2020, 1, 2)


def test_load_csv_rejects_missing_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("foo,bar\n1,2\n", encoding="utf-8")
    with pytest.raises(SignalLoadError, match="columns 'date' and 'value'"):
        load_csv(path, name="s", cadence="daily", unit="u", source="test")


def test_load_json_bare_list_requires_caller_metadata(tmp_path: Path) -> None:
    path = tmp_path / "s.json"
    path.write_text(
        json.dumps([{"date": "2020-01-01", "value": 1.0}, {"date": "2020-01-02", "value": 2.0}]),
        encoding="utf-8",
    )
    series = load_json(path, name="s", cadence="daily", unit="u", source="test")
    assert series.name == "s"
    assert len(series.points) == 2

    with pytest.raises(SignalLoadError, match="missing required signal metadata"):
        load_json(path)  # no name/cadence/unit/source


def test_load_json_envelope_metadata_wins_when_unspecified(tmp_path: Path) -> None:
    path = tmp_path / "e.json"
    path.write_text(
        json.dumps(
            {
                "name": "ibov",
                "cadence": "daily",
                "unit": "BRL",
                "source": "B3 close",
                "description": "IBOVESPA daily close",
                "points": [{"date": "2020-01-02", "value": 118573.1}],
            }
        ),
        encoding="utf-8",
    )
    series = load_json(path)
    assert series.name == "ibov"
    assert series.cadence == "daily"
    assert series.unit == "BRL"


# ---------------------------------------------------------------------------
# Correlation — Spearman on known-correlated signal
# ---------------------------------------------------------------------------


def test_correlate_significant_on_known_correlated(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=60, seed=42)
    # Signal that equals draw_sum with no noise → Spearman rho == 1.0
    metric_values = [float(sum(r.numbers_sorted)) for r in history.records]
    points = tuple(
        SignalPoint(date=r.iso_date, value=v)
        for r, v in zip(history.records, metric_values, strict=True)
    )
    signal = SignalSeries(
        name="sum_mirror",
        cadence="daily",
        unit="sum",
        source="test",
        points=points,
    )

    result = correlate(
        history,
        signal=signal,
        metric=MetricSpec(name="sum", kind="continuous"),
    )
    assert result.test == "spearman"
    assert result.effect_size == pytest.approx(1.0)
    assert result.p_value < 0.01
    assert result.under_powered is False
    assert result.sample_size == len(history)
    assert result.q_value is None  # single-correlation call does not invent a q
    assert result.artifact_type == "research"
    assert result.disclaimer == RESEARCH_DISCLAIMER
    assert result.alignment.policy == "forward_fill"
    assert result.alignment.lag_draws == 0


# ---------------------------------------------------------------------------
# Correlation — Mann-Whitney on binary metric
# ---------------------------------------------------------------------------


def test_correlate_mann_whitney_on_binary_metric(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=60, seed=7)
    # Signal: explicit split — high when number 1 is present, low when absent.
    points = []
    for r in history.records:
        v = 100.0 if 1 in r.numbers_sorted else 10.0
        points.append(SignalPoint(date=r.iso_date, value=v))
    signal = SignalSeries(
        name="cheat",
        cadence="daily",
        unit="u",
        source="test",
        points=tuple(points),
    )

    result = correlate(
        history,
        signal=signal,
        metric=MetricSpec(name="number_present", kind="binary", params={"number": 1}),
    )
    assert result.test == "mann_whitney_u"
    assert result.p_value < 0.01  # clearly distinguishable groups
    # Rank-biserial effect size is in [-1, 1]; positive means group_one (present=1) tends higher.
    assert result.effect_size > 0.9


# ---------------------------------------------------------------------------
# Under-powered gate
# ---------------------------------------------------------------------------


def test_under_powered_is_flagged_not_suppressed(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=10, seed=3)  # < default min of 30
    metric_values = [float(sum(r.numbers_sorted)) for r in history.records]
    signal = SignalSeries(
        name="s",
        cadence="daily",
        unit="u",
        source="test",
        points=tuple(
            SignalPoint(date=r.iso_date, value=v)
            for r, v in zip(history.records, metric_values, strict=True)
        ),
    )
    result = correlate(history, signal=signal, metric=MetricSpec(name="sum", kind="continuous"))
    assert result.sample_size == 10
    assert result.under_powered is True
    assert result.min_sample_size == DEFAULT_MIN_SAMPLE_SIZE


# ---------------------------------------------------------------------------
# Alignment — event_keyed drops misses, lag is reported
# ---------------------------------------------------------------------------


def test_event_keyed_only_aligns_on_exact_dates(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=40, seed=11)
    # Signal only exists on every 3rd draw date.
    signal_points = tuple(
        SignalPoint(date=history.records[i].iso_date, value=float(i)) for i in range(0, 40, 3)
    )
    signal = SignalSeries(
        name="events",
        cadence="event_keyed",
        unit="u",
        source="test",
        points=signal_points,
    )
    result = correlate(
        history,
        signal=signal,
        metric=MetricSpec(name="sum", kind="continuous"),
        alignment="event_keyed",
    )
    # Expect ~14 pairs (every third of 40).
    assert 10 <= result.sample_size <= 16
    assert result.alignment.policy == "event_keyed"


def test_lag_is_reported_in_alignment(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=40, seed=5)
    signal = SignalSeries(
        name="s",
        cadence="daily",
        unit="u",
        source="test",
        points=tuple(
            SignalPoint(date=r.iso_date, value=float(i)) for i, r in enumerate(history.records)
        ),
    )
    result = correlate(
        history,
        signal=signal,
        metric=MetricSpec(name="sum", kind="continuous"),
        lag_draws=3,
    )
    assert result.alignment.lag_draws == 3
    # With lag=3, the last 3 draws cannot be paired (metric index out of bounds).
    assert result.sample_size == len(history) - 3


# ---------------------------------------------------------------------------
# Batch correlation — BH correction matches hand calc
# ---------------------------------------------------------------------------


def test_benjamini_hochberg_hand_calc() -> None:
    # Hand-verified:
    # p=[0.01, 0.04, 0.03, 0.20], m=4
    # sort asc → [(orig_idx, p)] = [(0,0.01),(2,0.03),(1,0.04),(3,0.20)]
    # raw q by rank: 0.04, 0.06, 0.0533..., 0.20
    # enforce monotonicity top-down: 0.04, 0.0533..., 0.0533..., 0.20
    # map back (original order): [0]=0.04, [1]=0.0533..., [2]=0.0533..., [3]=0.20
    q = benjamini_hochberg([0.01, 0.04, 0.03, 0.20])
    assert q[0] == pytest.approx(0.04)
    assert q[1] == pytest.approx(0.04 * 4 / 3)  # 0.0533...
    assert q[2] == pytest.approx(0.04 * 4 / 3)
    assert q[3] == pytest.approx(0.20)


def test_benjamini_hochberg_empty_and_single() -> None:
    assert benjamini_hochberg([]) == []
    assert benjamini_hochberg([0.01]) == pytest.approx([0.01])


def test_correlate_batch_applies_bh_and_labels(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=60, seed=17)
    metric_values = [float(sum(r.numbers_sorted)) for r in history.records]
    high_corr = SignalSeries(
        name="mirror",
        cadence="daily",
        unit="u",
        source="test",
        points=tuple(
            SignalPoint(date=r.iso_date, value=v)
            for r, v in zip(history.records, metric_values, strict=True)
        ),
    )
    # A second, noisy signal that should be weakly correlated
    rng = random.Random(0)
    noisy = SignalSeries(
        name="noisy",
        cadence="daily",
        unit="u",
        source="test",
        points=tuple(SignalPoint(date=r.iso_date, value=rng.gauss(0, 1)) for r in history.records),
    )

    batch = correlate_batch(
        history,
        signals=[high_corr, noisy],
        metrics=[MetricSpec(name="sum", kind="continuous")],
    )
    assert batch.artifact_type == "research"
    assert batch.correction_method == "benjamini_hochberg"
    assert len(batch.results) == 2
    assert all(r.q_value is not None for r in batch.results)
    # q_value is >= the row's raw p_value (BH never reduces p below its own value by
    # much more than m/rank scaling; for m=2, the smallest rank's q == p_min * 2 / 1).
    for r in batch.results:
        assert r.q_value is not None
        assert r.q_value >= r.p_value - 1e-9
        assert r.artifact_type == "research"
        assert r.disclaimer == RESEARCH_DISCLAIMER


# ---------------------------------------------------------------------------
# Uncorrelated signal returns non-significant
# ---------------------------------------------------------------------------


def test_uncorrelated_signal_is_not_significant(tmp_path: Path) -> None:
    history = _synth_history(tmp_path, n_draws=120, seed=13)
    rng = random.Random(42)
    signal = SignalSeries(
        name="noise",
        cadence="daily",
        unit="u",
        source="test",
        points=tuple(SignalPoint(date=r.iso_date, value=rng.gauss(0, 1)) for r in history.records),
    )
    result = correlate(history, signal=signal, metric=MetricSpec(name="sum", kind="continuous"))
    # Not a strict test (noise can occasionally produce a low p), but for this seed
    # we expect a very weak effect.
    assert abs(result.effect_size) < 0.3
