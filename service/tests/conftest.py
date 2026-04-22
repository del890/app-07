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
