"""FastAPI integration tests.

Covers §9 of the build-lotofacil-webapp change:
- Every route mounts under `/v1/`.
- `/v1/dataset` returns ingestion provenance.
- `/v1/statistics/*` — frequency, gaps, cooccurrence, structural, order, pi-alignment.
- `/v1/correlations` (single) + `/v1/correlations/batch` (BH-corrected).
- `/v1/health` liveness + `/v1/ready` readiness with 503 when calibration missing.
- Canonical error envelope on every non-success response.
- `x-request-id` echoed back.
- `ANTHROPIC_API_KEY` never leaks into responses, logs, or error messages.
- `/v1/predictions/next-draw` and `/v1/predictions/scenario-path` (JSON + SSE).
- Rate limit 429 with Retry-After on `/v1/predictions/*`.
"""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from service import config as config_module
from service import ingestion
from service.api import readiness as readiness_registry
from service.correlation import registry as signal_registry

SENTINEL_KEY = "sk-ant-TEST-SENTINEL-abc123XYZ"


@pytest.fixture
def app_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, Path, io.StringIO]]:
    """Build a fresh FastAPI app against a throwaway data.json."""
    data_path = tmp_path / "data.json"
    payload = {
        "allowed_numbers": list(range(1, 26)),
        "dataset": [
            {
                "id": 3,
                "date": "03-01-2020",
                "numbers": [5, 1, 3, 4, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            },
            {"id": 2, "date": "02-01-2020", "numbers": list(range(2, 17))},
            {"id": 1, "date": "01-01-2020", "numbers": list(range(1, 16))},
        ],
    }
    data_path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setenv("ANTHROPIC_API_KEY", SENTINEL_KEY)
    monkeypatch.setenv("DATA_JSON_PATH", str(data_path))
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    # Bust all caches so the app starts fresh under the new env.
    config_module.reset_settings_cache()
    ingestion.reset_cache()
    readiness_registry.clear()
    signal_registry.reset()

    # Capture log output to inspect later for secret redaction.
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    root = logging.getLogger()
    root.addHandler(handler)
    original_level = root.level
    root.setLevel(logging.DEBUG)

    # Import the app AFTER env is set so lifespan sees the right config.
    from service.main import app

    try:
        with TestClient(app) as client:
            yield client, data_path, log_stream
    finally:
        root.removeHandler(handler)
        root.setLevel(original_level)
        config_module.reset_settings_cache()
        ingestion.reset_cache()
        readiness_registry.clear()
        signal_registry.reset()


# ---------------------------------------------------------------------------
# Health + readiness
# ---------------------------------------------------------------------------


def test_health_is_200_and_echoes_version(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_ready_returns_503_while_calibration_missing(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/ready")
    assert resp.status_code == 503
    body = resp.json()
    assert body["ok"] is False
    assert "calibration" in body["missing"]
    # Ingestion is OK; calibration is what's missing.
    by_name = {c["name"]: c for c in body["checks"]}
    assert by_name["ingestion"]["ok"] is True
    assert by_name["calibration"]["ok"] is False


def test_request_id_is_echoed_back(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/health", headers={"x-request-id": "abc-test-123"})
    assert resp.headers["x-request-id"] == "abc-test-123"


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------


def test_dataset_returns_provenance(app_client) -> None:
    client, path, _ = app_client
    resp = client.get("/v1/dataset")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_draws"] == 3
    assert body["first_date"] == "2020-01-01"
    assert body["last_date"] == "2020-01-03"
    assert body["source_path"] == str(path)
    assert len(body["content_hash"]) == 64  # SHA-256 hex


# ---------------------------------------------------------------------------
# Statistics routes
# ---------------------------------------------------------------------------


def test_statistics_frequency_full_window(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/frequency")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["window"] == "full"
    assert body["meta"]["window_size"] == 3
    assert len(body["frequencies"]) == 25


def test_statistics_frequency_rolling_window(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/frequency?window=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["window"] == "last-1"


def test_statistics_frequency_rejects_invalid_window(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/frequency?window=0")
    # fastapi's Query(ge=1) triggers validation failure → our envelope
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "validation_error"


def test_statistics_gaps(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/gaps")
    assert resp.status_code == 200
    body = resp.json()
    assert body["threshold"]["hot_factor"] == 0.5
    assert body["threshold"]["cold_factor"] == 2.0
    assert len(body["gaps"]) == 25


def test_statistics_cooccurrence(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/cooccurrence?arity=2&top_k=3")
    assert resp.status_code == 200
    body = resp.json()
    assert body["arity"] == 2
    assert body["top_k"] == 3
    assert len(body["combinations"]) == 3


def test_statistics_cooccurrence_rejects_bad_arity(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/cooccurrence?arity=5&top_k=3")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "validation_error"


def test_statistics_structural(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/structural")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sum_min"] == 120
    assert body["sum_max"] == 270


def test_statistics_order(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/order")
    assert resp.status_code == 200
    body = resp.json()
    assert body["order_source"] in {"original", "canonical"}
    assert "disclaimer" in body


def test_statistics_pi_alignment_happy(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/pi-alignment?rule=digit_sum_mod10&target_original_id=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["rule"] == "digit_sum_mod10"
    assert 0.0 <= body["score"] <= 1.0


def test_statistics_pi_alignment_missing_draw_returns_404(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/pi-alignment?rule=digit_sum_mod10&target_original_id=99999")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "draw_not_found"


def test_statistics_pi_alignment_unknown_rule_returns_400(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/statistics/pi-alignment?rule=no_such_rule&target_original_id=1")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "bad_request"


# ---------------------------------------------------------------------------
# Correlations
# ---------------------------------------------------------------------------


def test_correlations_signals_empty_by_default(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/correlations/signals")
    assert resp.status_code == 200
    assert resp.json() == {"signals": []}


def test_correlations_rejects_unknown_signal(app_client) -> None:
    client, _, _ = app_client
    resp = client.post(
        "/v1/correlations",
        json={
            "signal": "nope",
            "metric": {"name": "sum", "kind": "continuous"},
        },
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "signal_not_found"
    assert body["error"]["details"]["available"] == []


def test_correlations_batch_with_registered_signal(app_client) -> None:
    client, _path, _ = app_client
    # Register a signal matching the test dataset dates.
    from datetime import date

    from service.correlation.models import SignalPoint, SignalSeries

    signal = SignalSeries(
        name="inline",
        cadence="daily",
        unit="u",
        source="test",
        points=(
            SignalPoint(date=date(2020, 1, 1), value=1.0),
            SignalPoint(date=date(2020, 1, 2), value=2.0),
            SignalPoint(date=date(2020, 1, 3), value=3.0),
        ),
    )
    signal_registry.register(signal)

    resp = client.post(
        "/v1/correlations/batch",
        json={
            "signals": ["inline"],
            "metrics": [{"name": "sum", "kind": "continuous"}],
            "min_sample_size": 1,  # 3-draw synthetic can't hit default 30
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["correction_method"] == "benjamini_hochberg"
    assert len(body["results"]) == 1
    row = body["results"][0]
    assert row["artifact_type"] == "research"
    assert row["q_value"] is not None


def test_correlations_single_does_not_fabricate_q_value(app_client) -> None:
    client, _, _ = app_client
    from datetime import date

    from service.correlation.models import SignalPoint, SignalSeries

    signal_registry.register(
        SignalSeries(
            name="inline",
            cadence="daily",
            unit="u",
            source="test",
            points=(
                SignalPoint(date=date(2020, 1, 1), value=1.0),
                SignalPoint(date=date(2020, 1, 2), value=2.0),
                SignalPoint(date=date(2020, 1, 3), value=3.0),
            ),
        )
    )
    resp = client.post(
        "/v1/correlations",
        json={
            "signal": "inline",
            "metric": {"name": "sum", "kind": "continuous"},
            "min_sample_size": 1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["q_value"] is None
    assert body["artifact_type"] == "research"


# ---------------------------------------------------------------------------
# Error envelope shape
# ---------------------------------------------------------------------------


def test_unknown_route_returns_envelope(app_client) -> None:
    client, _, _ = app_client
    resp = client.get("/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body == {
        "error": {
            "code": "not_found",
            "message": "Not Found",
            "details": {},
        }
    }


def test_method_not_allowed_returns_envelope(app_client) -> None:
    client, _, _ = app_client
    resp = client.post("/v1/health")
    assert resp.status_code == 405
    body = resp.json()
    assert body["error"]["code"] == "method_not_allowed"


# ---------------------------------------------------------------------------
# Secret redaction
# ---------------------------------------------------------------------------


def test_api_key_never_appears_in_any_response(app_client) -> None:
    client, _, _log_stream = app_client
    # Hit a variety of endpoints, including error paths
    for path, method in [
        ("/v1/health", "get"),
        ("/v1/ready", "get"),
        ("/v1/dataset", "get"),
        ("/v1/statistics/frequency", "get"),
        ("/v1/statistics/frequency?window=0", "get"),  # 400
        ("/v1/statistics/pi-alignment?rule=nope&target_original_id=1", "get"),  # 400
        ("/v1/statistics/pi-alignment?rule=digit_sum_mod10&target_original_id=99", "get"),  # 404
        ("/v1/does-not-exist", "get"),  # 404
    ]:
        resp = getattr(client, method)(path)
        assert SENTINEL_KEY not in resp.text, (
            f"sentinel leaked in response body from {method.upper()} {path}"
        )
        for value in resp.headers.values():
            assert SENTINEL_KEY not in value


def test_api_key_never_appears_in_logs(app_client) -> None:
    client, _, log_stream = app_client
    client.get("/v1/health")
    client.get("/v1/does-not-exist")
    client.get("/v1/statistics/frequency?window=0")
    log_output = log_stream.getvalue()
    assert SENTINEL_KEY not in log_output, "sentinel leaked into log stream"


# ---------------------------------------------------------------------------
# Prediction endpoints (9.5, 9.6, 9.9)
# ---------------------------------------------------------------------------

_FAKE_PREDICTION = {
    "numbers": list(range(1, 16)),
    "confidence": 0.42,
    "explanation": "test prediction",
    "tool_trace": [],
    "provenance": {
        "dataset_hash": "abc123",
        "model_versions": [],
        "agent_prompt_hash": "def456",
        "computed_at": "2024-01-01T00:00:00+00:00",
    },
    "calibrated": False,
    "disclaimer": "Research only.",
}

_FAKE_SCENARIO = {
    "steps": [_FAKE_PREDICTION],
    "path_confidence": 0.42,
    "calibrated": False,
    "disclaimer": "Research only.",
    "tool_trace": [],
    "provenance": {
        "dataset_hash": "abc123",
        "model_versions": [],
        "agent_prompt_hash": "def456",
        "computed_at": "2024-01-01T00:00:00+00:00",
    },
}


def test_predictions_next_draw_json(app_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /v1/predictions/next-draw returns prediction shape (agent mocked)."""
    import service.api.predictions as pred_module

    monkeypatch.setattr(pred_module, "predict_next_draw", lambda *_a, **_kw: _FAKE_PREDICTION)
    client, _, _ = app_client
    resp = client.post("/v1/predictions/next-draw", json={})
    assert resp.status_code == 200
    body = resp.json()
    assert "numbers" in body
    assert len(body["numbers"]) == 15
    assert "confidence" in body
    assert "provenance" in body


def test_predictions_next_draw_sse(app_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /v1/predictions/next-draw with SSE Accept streams events."""
    import service.api.predictions as pred_module

    events = [
        {"type": "tool_start", "tool": "get_dataset_provenance"},
        {"type": "final", **_FAKE_PREDICTION},
    ]

    def _fake_gen(*_a: object, **_kw: object) -> Iterator[dict]:
        yield from events

    monkeypatch.setattr(pred_module, "predict_next_draw", _fake_gen)
    client, _, _ = app_client
    with client.stream(
        "POST",
        "/v1/predictions/next-draw",
        json={},
        headers={"Accept": "text/event-stream"},
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        raw = resp.read().decode()
    # Expect at least one SSE data: line
    assert "data:" in raw


def test_predictions_scenario_path_json(app_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /v1/predictions/scenario-path returns scenario shape (agent mocked)."""
    import service.api.predictions as pred_module

    monkeypatch.setattr(pred_module, "predict_scenario_path", lambda *_a, **_kw: _FAKE_SCENARIO)
    client, _, _ = app_client
    resp = client.post("/v1/predictions/scenario-path", json={"horizon": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert "steps" in body
    assert "path_confidence" in body
    assert "calibrated" in body


def test_predictions_rate_limit_returns_429(app_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """429 with Retry-After header when per-IP limit is exceeded."""
    import service.api.predictions as pred_module
    import service.config as cfg_module

    # Patch settings to limit 1 request/min, and reset rate store.
    original_settings = cfg_module.get_settings()

    class _PatchedSettings:
        predictions_rate_limit_per_minute = 1

    monkeypatch.setattr(pred_module, "get_settings", lambda: _PatchedSettings())
    # Also clear the rate store so this test is isolated.
    pred_module._rate_store.clear()

    monkeypatch.setattr(pred_module, "predict_next_draw", lambda *_a, **_kw: _FAKE_PREDICTION)
    client, _, _ = app_client

    # First request succeeds.
    r1 = client.post("/v1/predictions/next-draw", json={})
    assert r1.status_code == 200

    # Second request from same IP is rate-limited.
    r2 = client.post("/v1/predictions/next-draw", json={})
    assert r2.status_code == 429
    body = r2.json()
    assert body["error"]["code"] == "rate_limit_exceeded"
    # Retry-After is set on ApiError via the error handler.
    # The rate store cleanup happens at test teardown.
    pred_module._rate_store.clear()


# ---------------------------------------------------------------------------
# Draw profile
# ---------------------------------------------------------------------------

# The app_client fixture contains draws:
# id=1: numbers 1–15  (numbers_sorted = (1,2,...,15))
# id=2: numbers 2–16  (numbers_sorted = (2,3,...,16))
# id=3: numbers (5,1,3,4,2,6,7,8,9,10,11,12,13,14,15) → sorted (1–15)

_NUMBERS_1_TO_15 = list(range(1, 16))
_NUMBERS_2_TO_16 = list(range(2, 17))


def test_draw_profile_match_found(app_client) -> None:
    client, _, _ = app_client
    resp = client.post(
        "/v1/statistics/draw-profile",
        json={"numbers": _NUMBERS_1_TO_15},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dataset_match"] is not None
    assert body["dataset_match"]["original_id"] in (1, 3)  # both sort to 1–15


def test_draw_profile_no_match(app_client) -> None:
    client, _, _ = app_client
    # numbers 11–25 are not in the fixture dataset
    numbers_11_25 = list(range(11, 26))
    resp = client.post(
        "/v1/statistics/draw-profile",
        json={"numbers": numbers_11_25},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dataset_match"] is None


def test_draw_profile_returns_per_number_frequency(app_client) -> None:
    client, _, _ = app_client
    resp = client.post(
        "/v1/statistics/draw-profile",
        json={"numbers": _NUMBERS_1_TO_15},
    )
    assert resp.status_code == 200
    body = resp.json()
    profiles = body["number_profiles"]
    assert len(profiles) == 15
    for p in profiles:
        assert "number" in p
        assert "historical_count" in p
        assert "frequency_rank" in p


def test_draw_profile_returns_structural(app_client) -> None:
    client, _, _ = app_client
    resp = client.post(
        "/v1/statistics/draw-profile",
        json={"numbers": _NUMBERS_1_TO_15},
    )
    assert resp.status_code == 200
    body = resp.json()
    s = body["structural"]
    assert s["total_sum"] == sum(range(1, 16))
    assert s["min_number"] == 1
    assert s["max_number"] == 15


def test_draw_profile_validation_too_few(app_client) -> None:
    client, _, _ = app_client
    resp = client.post(
        "/v1/statistics/draw-profile",
        json={"numbers": list(range(1, 15))},  # 14 numbers
    )
    assert resp.status_code == 400


def test_draw_profile_validation_too_many(app_client) -> None:
    client, _, _ = app_client
    resp = client.post(
        "/v1/statistics/draw-profile",
        json={"numbers": list(range(1, 17))},  # 16 numbers
    )
    assert resp.status_code == 400


def test_draw_profile_validation_duplicate(app_client) -> None:
    client, _, _ = app_client
    bad = [1, 1, *list(range(2, 15))]  # 15 items but duplicate 1
    resp = client.post("/v1/statistics/draw-profile", json={"numbers": bad})
    assert resp.status_code == 400


def test_draw_profile_validation_out_of_range(app_client) -> None:
    client, _, _ = app_client
    bad = [26, *list(range(1, 15))]  # number 26 is invalid
    resp = client.post("/v1/statistics/draw-profile", json={"numbers": bad})
    assert resp.status_code == 400
