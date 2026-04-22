"""File-based signal loader.

Reads CSV or JSON signal files and produces validated `SignalSeries`. Expected
layouts:

**CSV** — first row is a header, accepts either ``date,value`` or
``Date,Value``; date cells are ISO-8601 (``YYYY-MM-DD``) or ``DD-MM-YYYY``::

    date,value
    2020-01-01,123.4
    2020-01-02,125.1

**JSON** — either a list of ``{date, value}`` objects or a full envelope with
metadata::

    {
      "name": "ibovespa_close",
      "cadence": "daily",
      "unit": "BRL",
      "source": "B3 daily close",
      "description": "IBOVESPA daily closing value",
      "points": [
        {"date": "2020-01-02", "value": 118573.1},
        ...
      ]
    }

When a CSV is loaded, the caller supplies the metadata (name, cadence, unit,
source) because CSV headers cannot carry it. When a JSON file has the envelope
form, its metadata wins; callers can still override fields on load.
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from service.correlation.models import SignalCadence, SignalPoint, SignalSeries


class SignalLoadError(ValueError):
    """Raised when a signal file cannot be parsed or fails validation."""


def _parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise SignalLoadError(
        f"could not parse date '{value}'; accepted formats: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY"
    )


def _parse_value(raw: str, *, context: str) -> float:
    try:
        return float(raw)
    except ValueError as exc:
        raise SignalLoadError(f"{context}: value '{raw}' is not a number") from exc


def _points_from_rows(rows: list[dict[str, str]]) -> tuple[SignalPoint, ...]:
    if not rows:
        raise SignalLoadError("signal file has no data rows")
    cols = {k.lower() for k in rows[0]}
    if "date" not in cols or "value" not in cols:
        raise SignalLoadError("signal CSV must have columns 'date' and 'value' (case-insensitive)")
    normalized: list[SignalPoint] = []
    for i, row in enumerate(rows, start=2):  # start=2 because header is row 1
        row_lc = {k.lower(): v for k, v in row.items()}
        if "date" not in row_lc or "value" not in row_lc:
            raise SignalLoadError(f"row {i}: missing 'date' or 'value' column")
        date_str = (row_lc["date"] or "").strip()
        value_str = (row_lc["value"] or "").strip()
        if not date_str or not value_str:
            raise SignalLoadError(f"row {i}: empty date or value")
        normalized.append(
            SignalPoint(
                date=_parse_date(date_str),
                value=_parse_value(value_str, context=f"row {i}"),
            )
        )
    return tuple(normalized)


def load_csv(
    path: Path,
    *,
    name: str,
    cadence: SignalCadence,
    unit: str,
    source: str,
    description: str = "",
) -> SignalSeries:
    """Load a two-column CSV (date, value) into a `SignalSeries`.

    The CSV has no metadata header, so name/cadence/unit/source are caller-supplied.
    """
    if not path.is_file():
        raise SignalLoadError(f"signal file not found at {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    points = _points_from_rows(rows)
    return SignalSeries(
        name=name,
        cadence=cadence,
        unit=unit,
        source=source,
        description=description,
        points=points,
    )


def _points_from_json_list(raw: Any, *, context: str) -> tuple[SignalPoint, ...]:
    if not isinstance(raw, list):
        raise SignalLoadError(f"{context}: expected list of points, got {type(raw).__name__}")
    if not raw:
        raise SignalLoadError(f"{context}: empty points list")
    points: list[SignalPoint] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict) or "date" not in item or "value" not in item:
            raise SignalLoadError(f"{context}: point {i} must be an object with 'date' and 'value'")
        points.append(
            SignalPoint(
                date=_parse_date(str(item["date"])),
                value=float(item["value"]),
            )
        )
    return tuple(points)


def load_json(
    path: Path,
    *,
    name: str | None = None,
    cadence: SignalCadence | None = None,
    unit: str | None = None,
    source: str | None = None,
    description: str | None = None,
) -> SignalSeries:
    """Load a JSON signal file. Accepts either a bare list of points or a full envelope.

    Caller-supplied metadata overrides envelope metadata when both are present,
    allowing one file to be registered under multiple names during experiments.
    """
    if not path.is_file():
        raise SignalLoadError(f"signal file not found at {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SignalLoadError(f"{path} is not valid JSON: {exc}") from exc

    if isinstance(payload, list):
        points = _points_from_json_list(payload, context=str(path))
        metadata: dict[str, Any] = {}
    elif isinstance(payload, dict):
        if "points" not in payload:
            raise SignalLoadError(f"{path}: JSON object must contain a 'points' list")
        points = _points_from_json_list(payload["points"], context=str(path))
        metadata = {
            k: payload[k]
            for k in ("name", "cadence", "unit", "source", "description")
            if k in payload
        }
    else:
        raise SignalLoadError(f"{path}: unsupported JSON shape {type(payload).__name__}")

    resolved_name = name or metadata.get("name")
    resolved_cadence = cadence or metadata.get("cadence")
    resolved_unit = unit or metadata.get("unit")
    resolved_source = source or metadata.get("source")
    resolved_description = (
        description if description is not None else metadata.get("description", "")
    )

    missing = [
        field
        for field, value in (
            ("name", resolved_name),
            ("cadence", resolved_cadence),
            ("unit", resolved_unit),
            ("source", resolved_source),
        )
        if not value
    ]
    if missing:
        raise SignalLoadError(
            f"{path}: missing required signal metadata: {missing}. "
            "Provide them in the JSON envelope or as load_json() arguments."
        )

    return SignalSeries(
        name=str(resolved_name),
        cadence=resolved_cadence,  # type: ignore[arg-type]
        unit=str(resolved_unit),
        source=str(resolved_source),
        description=str(resolved_description),
        points=points,
    )
