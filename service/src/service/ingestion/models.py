"""Pydantic models for the draw-data-ingestion capability."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

NUMBER_MIN = 1
NUMBER_MAX = 25
NUMBERS_PER_DRAW = 15


class DrawRecord(BaseModel):
    """A single Lotofácil draw, post-validation and normalization.

    - ``index`` is the zero-based *chronological* position (oldest = 0).
    - ``iso_date`` is the draw date in ISO-8601 (converted from DD-MM-YYYY once at ingestion).
    - ``numbers_sorted`` is the sorted-ascending canonical 15-number set.
    - ``numbers_drawn`` preserves the original order as it appears in the source file
      (when available); callers who need canonical order use ``numbers_sorted``.
    - ``original_id`` is the upstream record id from ``data.json`` (the Lotofácil draw number).
    """

    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=0)
    iso_date: date
    numbers_sorted: tuple[int, ...]
    numbers_drawn: tuple[int, ...]
    original_id: int

    @field_validator("numbers_sorted", "numbers_drawn")
    @classmethod
    def _validate_numbers(cls, v: tuple[int, ...]) -> tuple[int, ...]:
        if len(v) != NUMBERS_PER_DRAW:
            raise ValueError(f"expected {NUMBERS_PER_DRAW} numbers, got {len(v)}")
        if any(n < NUMBER_MIN or n > NUMBER_MAX for n in v):
            raise ValueError(f"numbers must be in [{NUMBER_MIN}, {NUMBER_MAX}], got {sorted(v)}")
        if len(set(v)) != NUMBERS_PER_DRAW:
            raise ValueError(f"duplicate numbers in draw: {sorted(v)}")
        return v


class Provenance(BaseModel):
    """Dataset provenance surfaced on every downstream result."""

    model_config = ConfigDict(frozen=True)

    source_path: str
    content_hash: str
    total_draws: int
    first_date: date
    last_date: date
    order_source: str = Field(
        description=(
            "'original' when the source preserves original draw order, 'canonical' "
            "when we fell back to sorted-ascending."
        ),
    )
