"""Integration tests for the admin sync endpoints.

Covers:
- POST /v1/admin/sync: success (new draws added), no-op, error path.
- GET /v1/admin/sync/status: reflects last sync state and total_draws.
"""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from service import config as config_module
from service import ingestion
from service.api import readiness as readiness_registry
from service.correlation import registry as signal_registry
from service.sync import task as sync_task_module

SENTINEL_KEY = "sk-ant-TEST-SENTINEL-abc123XYZ"


@pytest.fixture
def app_client_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[TestClient, Path]]:
    """Build a fresh FastAPI app against a throwaway data.json for sync tests."""
    data_path = tmp_path / "data.json"
    payload = {
        "allowed_numbers": list(range(1, 26)),
        "dataset": [
            {"id": 1, "date": "01-01-2020", "numbers": list(range(1, 16))},
        ],
    }
    data_path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setenv("ANTHROPIC_API_KEY", SENTINEL_KEY)
    monkeypatch.setenv("DATA_JSON_PATH", str(data_path))
    monkeypatch.setenv("ENV", "dev")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    # Disable the scheduler so it doesn't fire during tests.
    monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "0")

    config_module.reset_settings_cache()
    ingestion.reset_cache()
    readiness_registry.clear()
    signal_registry.reset()
    # Reset sync state between tests.
    sync_task_module.sync_state.last_sync_at = None
    sync_task_module.sync_state.last_sync_result = None
    sync_task_module.sync_state.last_draws_added = 0
    sync_task_module.sync_state.last_error = None

    from service.main import app

    try:
        with TestClient(app) as client:
            yield client, data_path
    finally:
        config_module.reset_settings_cache()
        ingestion.reset_cache()
        readiness_registry.clear()
        signal_registry.reset()


# ── POST /v1/admin/sync ────────────────────────────────────────────────────


def test_admin_sync_success_adds_draws(app_client_sync, tmp_path: Path) -> None:
    client, data_path = app_client_sync
    new_draw = {"id": 2, "date": "02-01-2020", "numbers": list(range(1, 16))}

    with patch(
        "service.sync.task.fetch_new_draws",
        new=AsyncMock(return_value=[new_draw]),
    ):
        resp = client.post("/v1/admin/sync")

    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == "success"
    assert body["draws_added"] == 1
    assert body["total_draws"] == 2


def test_admin_sync_no_op_when_nothing_new(app_client_sync) -> None:
    client, _ = app_client_sync

    with patch(
        "service.sync.task.fetch_new_draws",
        new=AsyncMock(return_value=[]),
    ):
        resp = client.post("/v1/admin/sync")

    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == "no_op"
    assert body["draws_added"] == 0


def test_admin_sync_error_path_returns_error_result(app_client_sync) -> None:
    client, _ = app_client_sync
    from service.sync.fetcher import FetchError

    with patch(
        "service.sync.task.fetch_new_draws",
        new=AsyncMock(side_effect=FetchError("remote unavailable")),
    ):
        resp = client.post("/v1/admin/sync")

    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == "error"
    assert body["draws_added"] == 0
    assert body["error"] is not None
    assert "remote unavailable" in body["error"]


# ── GET /v1/admin/sync/status ─────────────────────────────────────────────


def test_admin_sync_status_initial_state(app_client_sync) -> None:
    client, _ = app_client_sync
    resp = client.get("/v1/admin/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_sync_at"] is None
    assert body["last_sync_result"] is None
    assert body["draws_added"] == 0
    assert body["total_draws"] == 1


def test_admin_sync_status_reflects_last_run(app_client_sync) -> None:
    client, _ = app_client_sync

    with patch(
        "service.sync.task.fetch_new_draws",
        new=AsyncMock(return_value=[]),
    ):
        client.post("/v1/admin/sync")

    resp = client.get("/v1/admin/sync/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_sync_result"] == "no_op"
    assert body["last_sync_at"] is not None
