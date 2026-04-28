"""Fetch draw results from the official Caixa Econômica Federal Lotofácil API.

The endpoint returns paginated results ordered by contest number. We fetch from
the latest contest down to the first one not present in our dataset.

Caixa API response shape (relevant fields)::

    {
        "numeroConcurso": 3656,
        "dataApuracao": "08/04/2026",
        "dezenas": ["03", "04", "06", "07", "08", ...],
        ...
    }

We convert ``dataApuracao`` (``DD/MM/YYYY``) to ``DD-MM-YYYY`` to match
``data.json`` conventions, and ``dezenas`` strings to integers.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger("service.sync.fetcher")

# Timeout for HTTP requests to the Caixa API.
_TIMEOUT_SECONDS = 30.0


class FetchError(RuntimeError):
    """Raised when the Caixa API is unreachable or returns an unexpected response."""


def _parse_draw(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a Caixa API draw dict to the data.json record format.

    Returns a dict with keys ``id``, ``date``, ``numbers``.
    """
    contest_id = int(raw["numeroConcurso"])
    # dataApuracao: "DD/MM/YYYY" → "DD-MM-YYYY"
    date_str: str = raw["dataApuracao"].replace("/", "-")
    numbers = [int(d) for d in raw["dezenas"]]
    return {"id": contest_id, "date": date_str, "numbers": numbers}


async def fetch_latest_draw(url: str) -> dict[str, Any]:
    """Fetch the single latest draw (no contest number = latest by default).

    Returns a raw draw dict in data.json format: {id, date, numbers}.
    Raises FetchError on network or HTTP errors.
    """
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(url)
    except httpx.TimeoutException as exc:
        raise FetchError(f"Timeout contacting Caixa API at {url}") from exc
    except httpx.RequestError as exc:
        raise FetchError(f"Network error contacting Caixa API: {exc}") from exc

    if response.status_code != 200:
        raise FetchError(
            f"Caixa API returned HTTP {response.status_code} at {url}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise FetchError(f"Caixa API response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or "numeroConcurso" not in data:
        raise FetchError(
            f"Unexpected Caixa API response shape; keys: {list(data.keys()) if isinstance(data, dict) else type(data)}"
        )

    return _parse_draw(data)


async def fetch_draw_by_id(url: str, contest_id: int) -> dict[str, Any]:
    """Fetch a specific draw by contest number.

    Returns a raw draw dict in data.json format: {id, date, numbers}.
    Raises FetchError on network, HTTP, or parse errors.
    """
    contest_url = f"{url}/{contest_id}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.get(contest_url)
    except httpx.TimeoutException as exc:
        raise FetchError(f"Timeout fetching contest {contest_id}") from exc
    except httpx.RequestError as exc:
        raise FetchError(f"Network error fetching contest {contest_id}: {exc}") from exc

    if response.status_code == 404:
        raise FetchError(f"Contest {contest_id} not found at {contest_url}")
    if response.status_code != 200:
        raise FetchError(
            f"Caixa API returned HTTP {response.status_code} for contest {contest_id}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise FetchError(f"Contest {contest_id} response is not valid JSON: {exc}") from exc

    if not isinstance(data, dict) or "numeroConcurso" not in data:
        raise FetchError(f"Unexpected shape for contest {contest_id}")

    return _parse_draw(data)


async def fetch_new_draws(url: str, current_max_id: int) -> list[dict[str, Any]]:
    """Fetch all draws with contest ID > ``current_max_id``.

    Starts by fetching the latest draw. If it is already known, returns an
    empty list (no-op). Otherwise fetches all draws between ``current_max_id + 1``
    and the latest, inclusive.

    Returns draws in ascending order (oldest first) matching data.json convention.
    Raises FetchError on any network / HTTP error.
    """
    latest = await fetch_latest_draw(url)
    latest_id = latest["id"]

    if latest_id <= current_max_id:
        log.info(
            "sync.fetch.no_new_draws",
            extra={"latest_remote": latest_id, "local_max": current_max_id},
        )
        return []

    new_draws: list[dict[str, Any]] = []
    for contest_id in range(current_max_id + 1, latest_id + 1):
        if contest_id == latest_id:
            new_draws.append(latest)
        else:
            draw = await fetch_draw_by_id(url, contest_id)
            new_draws.append(draw)

    log.info(
        "sync.fetch.fetched",
        extra={"count": len(new_draws), "from": current_max_id + 1, "to": latest_id},
    )
    return new_draws  # already ascending by construction
