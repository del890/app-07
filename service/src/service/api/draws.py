"""GET /v1/dataset/draws — paginated historical draw records."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Query

from service.api.errors import ApiError
from service.ingestion import get_cached_history

router = APIRouter(prefix="/dataset")


@router.get("/draws")
async def get_draws(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> dict[str, Any]:
    """Return a paginated list of historical Lotofácil draws, newest first."""
    history = get_cached_history()
    if history is None:
        raise ApiError(
            status_code=503,
            code="ingestion_not_ready",
            message="data.json has not been ingested yet",
        )

    records = history.records  # oldest → newest
    total = len(records)
    # Reverse for newest-first presentation
    reversed_records = list(reversed(records))
    start = (page - 1) * page_size
    end = start + page_size
    page_records = reversed_records[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "draws": [
            {
                "index": r.index,
                "original_id": r.original_id,
                "date": r.iso_date.isoformat(),
                "numbers": list(r.numbers_sorted),
            }
            for r in page_records
        ],
    }
