"""Append-only JSON Lines prediction store.

Each line is a JSON object with:
  {
    "id": "<uuid>",
    "kind": "next_draw" | "scenario_path",
    "stored_at": "<ISO datetime>",
    "prediction": { ... }
  }

The in-memory list mirrors the file so reads never touch disk.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

_lock = threading.Lock()
_entries: list[dict[str, Any]] = []
_loaded = False

PredictionKind = Literal["next_draw", "scenario_path"]


def _store_path() -> Path:
    raw = os.environ.get("PREDICTIONS_STORE_PATH", "")
    if raw:
        return Path(raw)
    # Default: repo-root/store/predictions.jsonl
    return Path(__file__).resolve().parents[4] / "store" / "predictions.jsonl"


def _ensure_loaded() -> None:
    """Load persisted entries from disk once per process."""
    global _loaded
    if _loaded:
        return
    path = _store_path()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    _entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # Skip corrupt lines
    _loaded = True


def _append_to_disk(entry: dict[str, Any]) -> None:
    """Append a single JSON entry to the store file (best-effort)."""
    try:
        path = _store_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Disk write is best-effort; in-memory state is canonical


def _save(kind: PredictionKind, prediction: dict[str, Any]) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "kind": kind,
        "stored_at": datetime.now(UTC).isoformat(),
        "prediction": prediction,
    }
    with _lock:
        _ensure_loaded()
        _entries.append(entry)
        _append_to_disk(entry)
    return entry


def save_next_draw(prediction: dict[str, Any]) -> dict[str, Any]:
    """Persist a next-draw prediction and return the stored entry."""
    return _save("next_draw", prediction)


def save_scenario_path(prediction: dict[str, Any]) -> dict[str, Any]:
    """Persist a scenario-path prediction and return the stored entry."""
    return _save("scenario_path", prediction)


def list_predictions(
    kind: PredictionKind | None = None,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Return a paginated list of stored predictions, newest first.

    Parameters
    ----------
    kind:
        Filter by ``"next_draw"`` or ``"scenario_path"``. ``None`` returns both.
    page:
        1-based page number.
    page_size:
        Maximum entries per page (capped at 100).
    """
    page_size = min(page_size, 100)
    with _lock:
        _ensure_loaded()
        items = [e for e in reversed(_entries) if kind is None or e["kind"] == kind]

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items[start:end],
    }


def reset_store() -> None:
    """Clear in-memory state. Only for test teardown."""
    global _loaded
    with _lock:
        _entries.clear()
        _loaded = False
