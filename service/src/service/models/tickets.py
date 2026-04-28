"""Pydantic response models for the tickets capability."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ScannedTicket(BaseModel):
    """Structured result of a ticket OCR scan.

    ``games`` is a list of up to 3 game sets.  Each inner list contains the
    marked numbers (1–25) in ascending order for one game grid.
    """

    games: list[list[int]] = Field(
        ...,
        description="Up to 3 game sets; each is a sorted list of marked numbers (1–25).",
    )

    @field_validator("games")
    @classmethod
    def _validate_games(cls, v: list[list[int]]) -> list[list[int]]:
        for idx, game in enumerate(v):
            for n in game:
                if not 1 <= n <= 25:
                    raise ValueError(
                        f"games[{idx}] contains invalid number {n!r}; must be 1–25"
                    )
        return v
