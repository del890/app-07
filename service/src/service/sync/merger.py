"""Validate and merge fetched draws into the current dataset.

Takes raw draw dicts from the fetcher (data.json format: id, date, numbers)
and validates each against the same rules used by the ingestion loader:
- date is DD-MM-YYYY
- exactly 15 numbers
- each number in 1–25
- no duplicates within a draw

Returns the merged list in reverse-chronological order (newest first), ready
to be written back to data.json.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

log = logging.getLogger("service.sync.merger")

_DATE_FMT = "%d-%m-%Y"


class MergeError(ValueError):
    """Raised when validation of a fetched draw fails."""


def _validate_draw(draw: dict[str, Any]) -> None:
    """Raise MergeError if draw does not meet data.json schema requirements."""
    draw_id = draw.get("id", "?")
    date_val = draw.get("date", "")
    numbers = draw.get("numbers", [])

    # Validate date format.
    if not isinstance(date_val, str):
        raise MergeError(f"draw id={draw_id}: date must be a string, got {type(date_val)}")
    try:
        datetime.strptime(date_val, _DATE_FMT)
    except ValueError:
        raise MergeError(
            f"draw id={draw_id}: date '{date_val}' does not match DD-MM-YYYY"
        )

    # Validate numbers.
    if not isinstance(numbers, list):
        raise MergeError(f"draw id={draw_id}: numbers must be a list")
    if len(numbers) != 15:
        raise MergeError(
            f"draw id={draw_id}: expected 15 numbers, got {len(numbers)}"
        )
    for n in numbers:
        if not isinstance(n, int) or n < 1 or n > 25:
            raise MergeError(
                f"draw id={draw_id}: number {n} outside valid range 1–25"
            )
    if len(set(numbers)) != len(numbers):
        raise MergeError(f"draw id={draw_id}: duplicate numbers in draw")


def merge_new_draws(
    existing_dataset: list[dict[str, Any]],
    fetched_draws: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    """Validate and append new draws to the existing dataset.

    Args:
        existing_dataset: The current ``dataset`` list from data.json (any order).
        fetched_draws: Raw draw dicts returned by the fetcher (ascending order).

    Returns:
        A tuple of (merged_dataset, draws_added_count).
        ``merged_dataset`` is ordered in reverse-chronological order (newest
        first) to match the data.json serialization convention.

    Invalid fetched draws are logged and skipped; they do not abort the merge.
    """
    existing_ids = {d["id"] for d in existing_dataset}
    accepted: list[dict[str, Any]] = []

    for draw in fetched_draws:
        draw_id = draw.get("id")
        if draw_id in existing_ids:
            # Already present — skip silently.
            continue
        try:
            _validate_draw(draw)
        except MergeError as exc:
            log.warning("sync.merger.invalid_draw", extra={"error": str(exc)})
            continue
        accepted.append(draw)
        existing_ids.add(draw_id)

    if not accepted:
        return existing_dataset, 0

    merged = existing_dataset + accepted
    # Sort descending by id (newest first) to match data.json convention.
    merged.sort(key=lambda d: d["id"], reverse=True)
    return merged, len(accepted)
