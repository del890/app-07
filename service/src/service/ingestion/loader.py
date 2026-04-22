"""Load, validate, and normalize the Lotofácil historical dataset.

`data.json` shape (observed, treated as the contract)::

    {
      "allowed_numbers": [1..25],
      "dataset": [
        {"id": int, "date": "DD-MM-YYYY", "numbers": [15 ints from 1..25]},
        ...
      ]
    }

The source file is in reverse-chronological order (highest id first). The loader
reverses it once so downstream code always sees oldest→newest.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from service.ingestion.models import (
    NUMBER_MAX,
    NUMBER_MIN,
    NUMBERS_PER_DRAW,
    DrawRecord,
    Provenance,
)


class DataIngestionError(ValueError):
    """Raised when `data.json` is missing, malformed, or fails validation."""


class DrawHistory:
    """In-memory, sorted-ascending history of validated draw records.

    Immutable after construction. Exposes O(1) lookups by chronological index
    and by the original upstream id, plus dataset-wide provenance.
    """

    __slots__ = ("_by_id", "_provenance", "_records")

    def __init__(self, records: tuple[DrawRecord, ...], provenance: Provenance) -> None:
        self._records = records
        self._by_id = {r.original_id: r for r in records}
        self._provenance = provenance

    @property
    def records(self) -> tuple[DrawRecord, ...]:
        return self._records

    @property
    def provenance(self) -> Provenance:
        return self._provenance

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._records)

    def at(self, index: int) -> DrawRecord:
        return self._records[index]

    def by_original_id(self, original_id: int) -> DrawRecord:
        return self._by_id[original_id]


def _parse_date(value: object, *, original_id: int) -> date:
    if not isinstance(value, str):
        raise DataIngestionError(
            f"record id={original_id}: expected date string, got {type(value).__name__}"
        )
    try:
        return datetime.strptime(value, "%d-%m-%Y").date()
    except ValueError as exc:
        raise DataIngestionError(
            f"record id={original_id}: date '{value}' is not DD-MM-YYYY"
        ) from exc


def _validate_numbers(raw: object, *, original_id: int) -> tuple[int, ...]:
    if not isinstance(raw, list):
        raise DataIngestionError(
            f"record id={original_id}: expected list of numbers, got {type(raw).__name__}"
        )
    if len(raw) != NUMBERS_PER_DRAW:
        raise DataIngestionError(
            f"record id={original_id}: expected {NUMBERS_PER_DRAW} numbers, got {len(raw)}"
        )
    numbers: list[int] = []
    for n in raw:
        if not isinstance(n, int) or isinstance(n, bool):
            raise DataIngestionError(f"record id={original_id}: non-integer number {n!r}")
        if n < NUMBER_MIN or n > NUMBER_MAX:
            raise DataIngestionError(
                f"record id={original_id}: number {n} outside [{NUMBER_MIN},{NUMBER_MAX}]"
            )
        numbers.append(n)
    if len(set(numbers)) != NUMBERS_PER_DRAW:
        raise DataIngestionError(
            f"record id={original_id}: duplicate numbers in draw: {sorted(numbers)}"
        )
    return tuple(numbers)


def load(path: Path) -> DrawHistory:
    """Load, validate, and normalize the dataset at *path*.

    Raises DataIngestionError on any validation failure; the error message
    identifies the offending record by its upstream id.
    """
    if not path.is_file():
        raise DataIngestionError(f"data.json not found at {path}")

    raw_bytes = path.read_bytes()
    content_hash = hashlib.sha256(raw_bytes).hexdigest()

    try:
        payload: Any = json.loads(raw_bytes)
    except json.JSONDecodeError as exc:
        raise DataIngestionError(f"data.json at {path} is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict) or "dataset" not in payload:
        raise DataIngestionError(f"data.json at {path} must be an object with a 'dataset' array")
    dataset = payload["dataset"]
    if not isinstance(dataset, list) or not dataset:
        raise DataIngestionError(f"data.json at {path} has no draws in 'dataset'")

    raw_records: list[tuple[int, date, tuple[int, ...]]] = []
    for raw in dataset:
        if not isinstance(raw, dict):
            raise DataIngestionError(f"draw entry is not an object: {raw!r}")
        if "id" not in raw or "date" not in raw or "numbers" not in raw:
            raise DataIngestionError(f"draw entry missing required fields id/date/numbers: {raw!r}")
        original_id_raw = raw["id"]
        if not isinstance(original_id_raw, int) or isinstance(original_id_raw, bool):
            raise DataIngestionError(f"draw entry 'id' is not an integer: {raw!r}")
        iso_date = _parse_date(raw["date"], original_id=original_id_raw)
        numbers_drawn = _validate_numbers(raw["numbers"], original_id=original_id_raw)
        raw_records.append((original_id_raw, iso_date, numbers_drawn))

    # Sort ascending by date, breaking ties by original id.
    raw_records.sort(key=lambda t: (t[1], t[0]))

    records: list[DrawRecord] = []
    for index, (original_id, iso_date, numbers_drawn) in enumerate(raw_records):
        numbers_sorted = tuple(sorted(numbers_drawn))
        records.append(
            DrawRecord(
                index=index,
                iso_date=iso_date,
                numbers_sorted=numbers_sorted,
                numbers_drawn=numbers_drawn,
                original_id=original_id,
            )
        )

    # Original draw order is preserved when at least one draw's drawn order
    # differs from its sorted order — i.e. the source didn't pre-sort.
    order_source = (
        "original" if any(r.numbers_drawn != r.numbers_sorted for r in records) else "canonical"
    )

    provenance = Provenance(
        source_path=str(path),
        content_hash=content_hash,
        total_draws=len(records),
        first_date=records[0].iso_date,
        last_date=records[-1].iso_date,
        order_source=order_source,
    )
    return DrawHistory(tuple(records), provenance)
