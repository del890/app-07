"""Shared pytest fixtures."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from service import ingestion
from service.config import Settings


@pytest.fixture(autouse=True)
def _reset_ingestion_cache() -> Iterator[None]:
    """Ensure each test starts with a clean ingestion cache."""
    ingestion.reset_cache()
    yield
    ingestion.reset_cache()


@pytest.fixture(autouse=True)
def _reset_stat_caches() -> Iterator[None]:
    """Drop memoized statistics counters so tests stay hermetic."""
    from service.statistics import clear_cooccurrence_cache

    clear_cooccurrence_cache()
    yield
    clear_cooccurrence_cache()


@pytest.fixture(autouse=True)
def _reset_engine_cache() -> Iterator[None]:
    """Drop the learned-model cache so tests stay hermetic."""
    from service.engine import reset_learned_cache

    reset_learned_cache()
    yield
    reset_learned_cache()


def _write_data_json(path: Path, draws: list[dict[str, object]]) -> None:
    payload = {
        "allowed_numbers": list(range(1, 26)),
        "dataset": draws,
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def tmp_data_json(tmp_path: Path):
    """Factory that writes a temp data.json and returns (path, content_hash)."""

    def _factory(draws: list[dict[str, object]]) -> tuple[Path, str]:
        path = tmp_path / "data.json"
        _write_data_json(path, draws)
        content_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, content_hash

    return _factory


# --- Shared tiny history for statistics tests ------------------------------

# Three hand-crafted draws — chosen so that golden values are easy to verify:
#   id=1 → [1..15]        sum=120, evens=7
#   id=2 → [2..16]        sum=135, evens=8
#   id=3 → unsorted mix   sum=175, evens=2, sorted=[1,2,3,4,5,7,9,11,13,15,17,19,21,23,25]
TINY_DATASET: tuple[dict[str, object], ...] = (
    {
        "id": 3,
        "date": "03-01-2020",
        "numbers": [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 2, 4],
    },
    {
        "id": 2,
        "date": "02-01-2020",
        "numbers": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
    },
    {"id": 1, "date": "01-01-2020", "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]},
)


@pytest.fixture
def tiny_history(tmp_path: Path):
    """A DrawHistory over TINY_DATASET."""
    from service.ingestion import load

    path = tmp_path / "tiny.json"
    _write_data_json(path, list(TINY_DATASET))
    return load(path)


@pytest.fixture
def make_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Factory that returns a Settings instance pointed at a given data.json path."""

    def _factory(data_path: Path, *, with_api_key: bool = True) -> Settings:
        env = {
            "ANTHROPIC_API_KEY": "test-key" if with_api_key else "",
            "DATA_JSON_PATH": str(data_path),
            "ENV": "dev",
            "LOG_LEVEL": "WARNING",
        }
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        return Settings()

    return _factory
