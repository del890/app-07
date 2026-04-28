"""Draw-data ingestion capability.

Public surface:
- `DrawRecord`, `Provenance` — typed models returned to downstream capabilities.
- `DrawHistory` — immutable, chronologically ordered draw collection.
- `load(path)` — validate + normalize a `data.json` file.
- `ingest_from_settings(settings)` — idempotent process-wide ingestion entrypoint.
- `get_cached_history()` — return the cached history, or None if not yet loaded.
- `reload_from_settings(settings)` — clear the cache and re-ingest from disk.
- `reset_cache()` — clear the cache; only intended for tests.
"""

from __future__ import annotations

import threading

from service.config import Settings, get_settings
from service.ingestion.loader import DataIngestionError, DrawHistory, load
from service.ingestion.models import DrawRecord, Provenance

__all__ = [
    "DataIngestionError",
    "DrawHistory",
    "DrawRecord",
    "Provenance",
    "get_cached_history",
    "ingest_from_settings",
    "load",
    "reload_from_settings",
    "reset_cache",
]

_cached: DrawHistory | None = None
_lock = threading.Lock()


def ingest_from_settings(settings: Settings | None = None) -> DrawHistory:
    """Load `data.json` once per process; subsequent calls return the cached history.

    Thread-safe. The cached result is invalidated only by `reset_cache()` or
    `reload_from_settings()`.
    """
    global _cached
    if _cached is not None:
        return _cached
    with _lock:
        if _cached is None:
            s = settings or get_settings()
            _cached = load(s.data_json_path)
    return _cached


def reload_from_settings(settings: Settings | None = None) -> DrawHistory:
    """Clear the in-memory cache and re-ingest from `data.json` on disk.

    Thread-safe. Intended for use after the dataset file has been updated by
    the sync task. Subsequent calls to `get_cached_history()` will return the
    freshly loaded history.
    """
    global _cached
    with _lock:
        _cached = None
        s = settings or get_settings()
        _cached = load(s.data_json_path)
    return _cached


def get_cached_history() -> DrawHistory | None:
    return _cached


def reset_cache() -> None:
    """Clear the cached history. Only for test teardown."""
    global _cached
    with _lock:
        _cached = None
