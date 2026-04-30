"""Sync task orchestration.

Provides the top-level ``run_sync`` coroutine that:
  1. Reads the current dataset state.
  2. Fetches new draws from the Caixa API.
  3. Merges and validates the new draws.
  4. Writes the updated dataset atomically.
  5. Hot-reloads the in-memory DrawHistory.
  6. Updates the shared SyncState for operational visibility.

Also exposes the ``SyncState`` singleton used by the admin status endpoint.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from service.engine import run_calibration
from service.ingestion import get_cached_history, reload_from_settings
from service.sync.fetcher import FetchError, fetch_new_draws
from service.sync.merger import merge_new_draws
from service.sync.writer import WriteError, write_dataset

log = logging.getLogger("service.sync.task")

SyncResult = Literal["success", "no_op", "error"]


@dataclass
class SyncState:
    """Mutable state updated after each sync run.  Accessed by the admin endpoint."""

    last_sync_at: datetime | None = None
    last_sync_result: SyncResult | None = None
    last_draws_added: int = 0
    last_error: str | None = None


# Process-wide singleton.
sync_state = SyncState()


async def run_sync(
    api_url: str,
    data_path: Path,
    *,
    state: SyncState | None = None,
) -> int:
    """Fetch new draws, persist, and reload the in-memory dataset.

    Returns the number of draws added (0 = no-op).
    Updates ``state`` (defaults to the module-level ``sync_state`` singleton).
    Never raises — errors are logged and recorded in ``state``.
    """
    _state = state if state is not None else sync_state

    try:
        # --- 1. Read the current dataset ----------------------------------
        raw = json.loads(data_path.read_bytes())
        existing_dataset: list[dict] = raw.get("dataset", [])
        allowed_numbers: list[int] = raw.get("allowed_numbers", list(range(1, 26)))
        current_max_id = max((d["id"] for d in existing_dataset), default=0)

        # --- 2. Fetch new draws -------------------------------------------
        fetched = await fetch_new_draws(api_url, current_max_id)
        if not fetched:
            _state.last_sync_at = datetime.now(timezone.utc)
            _state.last_sync_result = "no_op"
            _state.last_draws_added = 0
            _state.last_error = None
            log.info("sync.task.no_op", extra={"max_id": current_max_id})
            return 0

        # --- 3. Validate and merge ----------------------------------------
        merged_dataset, draws_added = merge_new_draws(existing_dataset, fetched)
        if draws_added == 0:
            _state.last_sync_at = datetime.now(timezone.utc)
            _state.last_sync_result = "no_op"
            _state.last_draws_added = 0
            _state.last_error = None
            return 0

        # --- 4. Atomic write ----------------------------------------------
        write_dataset(data_path, allowed_numbers, merged_dataset)

        # --- 5. Hot-reload ------------------------------------------------
        reload_from_settings()

        # --- 6. Re-calibrate so Play mode reflects the new draws ----------
        _history = get_cached_history()
        if _history is not None:
            log.info("sync.task.calibration.begin", extra={"draws_added": draws_added})
            try:
                run_calibration(_history)
                log.info("sync.task.calibration.done")
            except Exception as cal_exc:  # noqa: BLE001
                log.error("sync.task.calibration.error", extra={"error": str(cal_exc)})

        # --- 7. Update state ----------------------------------------------
        _state.last_sync_at = datetime.now(timezone.utc)
        _state.last_sync_result = "success"
        _state.last_draws_added = draws_added
        _state.last_error = None

        log.info(
            "sync.task.success",
            extra={"draws_added": draws_added, "total": len(merged_dataset)},
        )
        return draws_added

    except (FetchError, WriteError, OSError, ValueError, KeyError) as exc:
        error_msg = str(exc)
        _state.last_sync_at = datetime.now(timezone.utc)
        _state.last_sync_result = "error"
        _state.last_draws_added = 0
        _state.last_error = error_msg
        log.error("sync.task.error", extra={"error": error_msg})
        return 0
