"""Admin endpoints for dataset sync operations.

Routes:
  POST /admin/sync        — trigger an immediate sync, return result.
  GET  /admin/sync/status — report last sync state and dataset row count.

Note: These routes are intended for operator use only. They are not
authenticated in the current implementation and should not be exposed publicly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter

from service.config import get_settings
from service.ingestion import get_cached_history
from service.sync.task import SyncResult, run_sync, sync_state

router = APIRouter(prefix="/admin")


@router.post("/sync")
async def trigger_sync() -> dict[str, Any]:
    """Trigger an immediate dataset sync and return the outcome."""
    settings = get_settings()
    draws_added = await run_sync(
        api_url=settings.lotofacil_api_url,
        data_path=settings.data_json_path,
        state=sync_state,
    )
    history = get_cached_history()
    return {
        "result": sync_state.last_sync_result,
        "draws_added": draws_added,
        "total_draws": len(history) if history is not None else 0,
        "synced_at": sync_state.last_sync_at,
        "error": sync_state.last_error,
    }


@router.get("/sync/status")
async def sync_status() -> dict[str, Any]:
    """Return the last sync state and current dataset row count."""
    history = get_cached_history()
    return {
        "last_sync_at": sync_state.last_sync_at,
        "last_sync_result": sync_state.last_sync_result,
        "draws_added": sync_state.last_draws_added,
        "total_draws": len(history) if history is not None else 0,
        "error": sync_state.last_error,
    }
