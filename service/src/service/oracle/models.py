"""Pydantic models for the dream-oracle capability."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExtractedSymbol(BaseModel):
    """A single symbolic signal identified in a dream description."""

    category: str = Field(
        description=(
            "Symbol category: 'element', 'color', 'emotion', 'archetype', or 'count'."
        )
    )
    label: str = Field(
        description=(
            "Symbol label within the category (e.g. 'water', 'red', 'joy', 'falling', '7')."
        )
    )
    intensity: float = Field(
        ge=0.0,
        le=1.0,
        description="How prominently this symbol featured in the dream (0.0–1.0).",
    )


class DreamOracleResult(BaseModel):
    """A dream-oracle number suggestion — labelled entertainment, never prediction."""

    numbers: list[int] = Field(description="15 suggested Lotofácil numbers.")
    explanation: str = Field(
        description="Human-readable explanation mapping symbols to the suggested numbers."
    )
    symbols: list[ExtractedSymbol] = Field(
        description="Symbolic signals extracted from the dream description."
    )
    catalog_version: str = Field(description="Version of the symbolic catalog used.")
    artifact_type: Literal["entertainment"] = "entertainment"
    disclaimer: str = Field(description="Entertainment-only disclaimer.")
