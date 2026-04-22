"""Shared primitives for the statistical-analysis capability.

Every statistical result carries `StatMeta`: dataset hash, window descriptor,
and computation timestamp. Downstream consumers (tools, agent, API) depend on
this contract — per the spec, a result without provenance is a bug.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from service.ingestion import DrawHistory, DrawRecord

WindowDescriptor = str  # "full" or "last-N"
NUMBER_RANGE = tuple(range(1, 26))


class StatMeta(BaseModel):
    """Provenance attached to every statistical result."""

    model_config = ConfigDict(frozen=True)

    dataset_hash: str
    window: WindowDescriptor = "full"
    window_size: int = Field(
        ge=0,
        description="Number of draws actually used for the computation.",
    )
    computed_at: datetime


class WindowSelection(BaseModel):
    """Normalized window inputs.

    `kind == 'full'` uses the entire history. `kind == 'last_n'` uses the last
    `n` draws, capped at `len(history)`; if `n > len(history)`, we use all
    draws and still report the requested `n` in the descriptor for traceability.
    """

    model_config = ConfigDict(frozen=True)

    kind: Literal["full", "last_n"] = "full"
    n: int | None = None

    def descriptor(self) -> WindowDescriptor:
        if self.kind == "full":
            return "full"
        return f"last-{self.n}"


def resolve_window(
    history: DrawHistory, selection: WindowSelection | None
) -> tuple[tuple[DrawRecord, ...], WindowDescriptor, int]:
    """Return (records slice, descriptor, actual sample count)."""
    records = history.records
    if selection is None or selection.kind == "full":
        return records, "full", len(records)
    n = selection.n or 0
    if n <= 0:
        raise ValueError(f"window size must be positive, got {n}")
    if n >= len(records):
        return records, f"last-{n}", len(records)
    return records[-n:], f"last-{n}", n


def make_meta(
    history: DrawHistory,
    *,
    descriptor: WindowDescriptor = "full",
    window_size: int,
) -> StatMeta:
    return StatMeta(
        dataset_hash=history.provenance.content_hash,
        window=descriptor,
        window_size=window_size,
        computed_at=datetime.now(UTC),
    )
