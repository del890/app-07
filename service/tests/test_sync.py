"""Unit tests for the sync module.

Covers:
- fetch_new_draws: success (new draws), no-op (already up to date), HTTP 4xx/5xx,
  network timeout.
- merge_new_draws: adds valid records, skips invalid records, skips known IDs.
- write_dataset: atomic write creates .bak and new file; write failure leaves
  original intact.
- run_sync: success, no-op, error paths; SyncState updated correctly.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from service.sync.fetcher import FetchError, fetch_new_draws
from service.sync.merger import MergeError, merge_new_draws
from service.sync.task import SyncState, run_sync
from service.sync.writer import WriteError, write_dataset


# ── helpers ────────────────────────────────────────────────────────────────


def _draw(id_: int, date: str = "01-01-2020") -> dict[str, Any]:
    return {"id": id_, "date": date, "numbers": list(range(1, 16))}


def _caixa_response(contest_id: int, date_str: str = "01/01/2020") -> dict[str, Any]:
    """Simulate a Caixa API response dict."""
    return {
        "numeroConcurso": contest_id,
        "dataApuracao": date_str,
        "dezenas": [f"{n:02d}" for n in range(1, 16)],
    }


# ── fetcher tests ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_new_draws_returns_new_records() -> None:
    """When remote has draws newer than current_max_id, they are returned."""
    latest = _caixa_response(5, "05/01/2020")

    async def _mock_get(url: str, **kwargs):  # noqa: ARG001
        response = MagicMock()
        response.status_code = 200
        # For latest (no suffix) return id=5; for others, adjust.
        if url.endswith("/5") or not any(url.endswith(f"/{i}") for i in range(1, 10)):
            response.json.return_value = latest
        else:
            # Extract id from URL
            contest_id = int(url.rsplit("/", 1)[-1])
            response.json.return_value = _caixa_response(contest_id, f"0{contest_id}/01/2020")
        return response

    with patch("service.sync.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=_mock_get)
        mock_client_cls.return_value = mock_client

        result = await fetch_new_draws("http://fake/lotofacil", current_max_id=3)

    # Should have fetched ids 4 and 5.
    assert len(result) == 2
    assert {d["id"] for d in result} == {4, 5}


@pytest.mark.asyncio
async def test_fetch_new_draws_no_op_when_up_to_date() -> None:
    """When remote max equals local max, returns empty list."""
    latest = _caixa_response(3, "03/01/2020")

    async def _mock_get(url: str, **kwargs):  # noqa: ARG001
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = latest
        return response

    with patch("service.sync.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=_mock_get)
        mock_client_cls.return_value = mock_client

        result = await fetch_new_draws("http://fake/lotofacil", current_max_id=3)

    assert result == []


@pytest.mark.asyncio
async def test_fetch_new_draws_raises_on_http_4xx() -> None:
    async def _mock_get(url: str, **kwargs):  # noqa: ARG001
        response = MagicMock()
        response.status_code = 403
        return response

    with patch("service.sync.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=_mock_get)
        mock_client_cls.return_value = mock_client

        with pytest.raises(FetchError, match="HTTP 403"):
            await fetch_new_draws("http://fake/lotofacil", current_max_id=0)


@pytest.mark.asyncio
async def test_fetch_new_draws_raises_on_http_5xx() -> None:
    async def _mock_get(url: str, **kwargs):  # noqa: ARG001
        response = MagicMock()
        response.status_code = 503
        return response

    with patch("service.sync.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=_mock_get)
        mock_client_cls.return_value = mock_client

        with pytest.raises(FetchError, match="HTTP 503"):
            await fetch_new_draws("http://fake/lotofacil", current_max_id=0)


@pytest.mark.asyncio
async def test_fetch_new_draws_raises_on_timeout() -> None:
    async def _mock_get(url: str, **kwargs):  # noqa: ARG001
        raise httpx.TimeoutException("timed out")

    with patch("service.sync.fetcher.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=_mock_get)
        mock_client_cls.return_value = mock_client

        with pytest.raises(FetchError, match="Timeout"):
            await fetch_new_draws("http://fake/lotofacil", current_max_id=0)


# ── merger tests ───────────────────────────────────────────────────────────


def test_merge_adds_valid_new_draws() -> None:
    existing = [_draw(1), _draw(2)]
    new = [_draw(3, "03-01-2020"), _draw(4, "04-01-2020")]
    merged, added = merge_new_draws(existing, new)
    assert added == 2
    ids = {d["id"] for d in merged}
    assert ids == {1, 2, 3, 4}


def test_merge_skips_known_ids() -> None:
    existing = [_draw(1), _draw(2)]
    fetched = [_draw(2), _draw(3)]  # id=2 already known
    merged, added = merge_new_draws(existing, fetched)
    assert added == 1
    assert {d["id"] for d in merged} == {1, 2, 3}


def test_merge_skips_invalid_draws() -> None:
    existing = [_draw(1)]
    bad = {"id": 2, "date": "bad-date", "numbers": list(range(1, 16))}
    good = _draw(3, "03-01-2020")
    merged, added = merge_new_draws(existing, [bad, good])
    assert added == 1
    assert {d["id"] for d in merged} == {1, 3}


def test_merge_returns_reverse_chronological_order() -> None:
    existing = [_draw(2), _draw(1)]  # already descending
    new = [_draw(3)]
    merged, _ = merge_new_draws(existing, new)
    ids = [d["id"] for d in merged]
    assert ids == sorted(ids, reverse=True)


def test_merge_empty_fetched_returns_unchanged() -> None:
    existing = [_draw(1)]
    merged, added = merge_new_draws(existing, [])
    assert added == 0
    assert merged is existing  # unchanged reference


# ── writer tests ───────────────────────────────────────────────────────────


def test_write_dataset_creates_file_and_bak(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    original = {"allowed_numbers": list(range(1, 26)), "dataset": [_draw(1)]}
    data_path.write_text(json.dumps(original), encoding="utf-8")

    new_dataset = [_draw(2), _draw(1)]
    write_dataset(data_path, list(range(1, 26)), new_dataset)

    bak_path = tmp_path / "data.json.bak"
    assert bak_path.exists(), ".bak should be created"

    written = json.loads(data_path.read_text(encoding="utf-8"))
    assert len(written["dataset"]) == 2
    assert written["dataset"][0]["id"] == 2


def test_write_dataset_leaves_original_on_write_failure(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    original_content = {"allowed_numbers": list(range(1, 26)), "dataset": [_draw(1)]}
    data_path.write_text(json.dumps(original_content), encoding="utf-8")

    with patch("service.sync.writer.os.replace", side_effect=OSError("disk error")):
        with pytest.raises(WriteError):
            write_dataset(data_path, list(range(1, 26)), [_draw(2)])

    # Original must be intact.
    remaining = json.loads(data_path.read_text(encoding="utf-8"))
    assert len(remaining["dataset"]) == 1


# ── run_sync tests ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_sync_success_path(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    payload = {"allowed_numbers": list(range(1, 26)), "dataset": [_draw(1)]}
    data_path.write_text(json.dumps(payload), encoding="utf-8")

    state = SyncState()

    with (
        patch(
            "service.sync.task.fetch_new_draws",
            new=AsyncMock(return_value=[_draw(2, "02-01-2020")]),
        ),
        patch("service.sync.task.reload_from_settings"),
    ):
        added = await run_sync("http://fake", data_path, state=state)

    assert added == 1
    assert state.last_sync_result == "success"
    assert state.last_draws_added == 1
    assert state.last_error is None


@pytest.mark.asyncio
async def test_run_sync_no_op_when_nothing_new(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    payload = {"allowed_numbers": list(range(1, 26)), "dataset": [_draw(1)]}
    data_path.write_text(json.dumps(payload), encoding="utf-8")

    state = SyncState()

    with patch("service.sync.task.fetch_new_draws", new=AsyncMock(return_value=[])):
        added = await run_sync("http://fake", data_path, state=state)

    assert added == 0
    assert state.last_sync_result == "no_op"


@pytest.mark.asyncio
async def test_run_sync_error_path_does_not_raise(tmp_path: Path) -> None:
    data_path = tmp_path / "data.json"
    payload = {"allowed_numbers": list(range(1, 26)), "dataset": [_draw(1)]}
    data_path.write_text(json.dumps(payload), encoding="utf-8")

    state = SyncState()

    with patch(
        "service.sync.task.fetch_new_draws",
        new=AsyncMock(side_effect=FetchError("network down")),
    ):
        added = await run_sync("http://fake", data_path, state=state)

    assert added == 0
    assert state.last_sync_result == "error"
    assert state.last_error is not None
    assert "network down" in state.last_error
