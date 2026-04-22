"""Readiness registry: one entry per capability that gates `/v1/ready`.

Each capability's startup hook registers itself. The `/v1/ready` handler
queries the registry; if any required condition is missing or stale,
readiness returns 503 with a body enumerating the missing preconditions.

Currently registered:
- ``ingestion`` — required; OK once `data.json` has been loaded.
- ``calibration`` — required; NOT YET IMPLEMENTED (always missing until §7 lands).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from service.ingestion import get_cached_history

ReadinessCheck = Callable[[], "ReadinessStatus"]


@dataclass(frozen=True)
class ReadinessStatus:
    name: str
    ok: bool
    required: bool
    detail: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Registry:
    checks: dict[str, ReadinessCheck] = field(default_factory=dict)


_registry = _Registry()


def register(name: str, check: ReadinessCheck) -> None:
    """Register or replace a readiness check."""
    _registry.checks[name] = check


def clear() -> None:
    """Drop all registered checks. Tests use this; production never calls it."""
    _registry.checks.clear()


def snapshot() -> list[ReadinessStatus]:
    return [check() for _, check in sorted(_registry.checks.items())]


# --- Default checks --------------------------------------------------------


def _ingestion_check() -> ReadinessStatus:
    history = get_cached_history()
    if history is None:
        return ReadinessStatus(
            name="ingestion",
            ok=False,
            required=True,
            detail="data.json has not been ingested yet",
        )
    return ReadinessStatus(
        name="ingestion",
        ok=True,
        required=True,
        detail="data.json ingested successfully",
        extra={
            "total_draws": history.provenance.total_draws,
            "dataset_hash": history.provenance.content_hash,
        },
    )


def _calibration_check() -> ReadinessStatus:
    # Placeholder until §7 lands. Calibration is required by spec; while the
    # engine doesn't exist yet, /ready reports it as missing rather than
    # silently pretending it's OK.
    return ReadinessStatus(
        name="calibration",
        ok=False,
        required=True,
        detail=(
            "prediction-engine calibration not implemented yet; play-surface "
            "predictions are unavailable until calibration runs"
        ),
        extra={"status": "not_implemented"},
    )


def install_default_checks() -> None:
    register("ingestion", _ingestion_check)
    register("calibration", _calibration_check)
