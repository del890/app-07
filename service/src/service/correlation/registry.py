"""Process-wide signal registry.

Signal files live under `service/signals/` (CSV or JSON). On startup the
registry scans that directory, validates each file, and keeps a name → series
map in memory. The registry is read-mostly; mutations happen only at startup
or from tests via `reset()`.
"""

from __future__ import annotations

import threading
from pathlib import Path

from service.correlation.loader import SignalLoadError, load_csv, load_json
from service.correlation.models import SignalCadence, SignalSeries

DEFAULT_SIGNALS_DIR = Path(__file__).resolve().parents[3] / "signals"

_lock = threading.Lock()
_registered: dict[str, SignalSeries] = {}


def register(series: SignalSeries) -> None:
    with _lock:
        _registered[series.name] = series


def get(name: str) -> SignalSeries | None:
    return _registered.get(name)


def names() -> list[str]:
    return sorted(_registered)


def reset() -> None:
    with _lock:
        _registered.clear()


def load_directory(
    directory: Path = DEFAULT_SIGNALS_DIR,
    *,
    csv_defaults: dict[str, tuple[str, SignalCadence, str, str]] | None = None,
) -> list[str]:
    """Load every signal file under *directory* into the registry.

    JSON files must use the envelope form (their metadata is read from the file).
    CSV files require caller-supplied metadata via ``csv_defaults`` keyed by
    filename stem: ``{"ibov_close": (name, cadence, unit, source), ...}``. CSVs
    without a matching entry are skipped with a warning-style `SignalLoadError`
    that the caller can surface.
    """
    if not directory.is_dir():
        return []
    loaded: list[str] = []
    csv_defaults = csv_defaults or {}
    for path in sorted(directory.iterdir()):
        if path.is_dir():
            continue
        if path.suffix.lower() == ".json":
            series = load_json(path)
            register(series)
            loaded.append(series.name)
        elif path.suffix.lower() == ".csv":
            defaults = csv_defaults.get(path.stem)
            if defaults is None:
                # Skip rather than guess — silently defaulting would produce
                # mis-labeled signals.
                raise SignalLoadError(
                    f"{path}: CSV signal needs metadata defaults; "
                    f"add an entry for '{path.stem}' to csv_defaults"
                )
            name, cadence, unit, source = defaults
            series = load_csv(path, name=name, cadence=cadence, unit=unit, source=source)
            register(series)
            loaded.append(series.name)
    return loaded
