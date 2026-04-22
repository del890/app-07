"""`GET /v1/dataset` — ingestion provenance."""

from __future__ import annotations

from fastapi import APIRouter

from service.api.errors import ApiError
from service.ingestion import Provenance, get_cached_history

router = APIRouter(prefix="/dataset")


@router.get("")
async def get_dataset() -> Provenance:
    history = get_cached_history()
    if history is None:
        raise ApiError(
            status_code=503,
            code="ingestion_not_ready",
            message="data.json has not been ingested yet",
        )
    return history.provenance
