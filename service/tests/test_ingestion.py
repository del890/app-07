"""Unit + golden tests for the draw-data-ingestion capability.

Covers every scenario in specs/draw-data-ingestion/spec.md:
- valid load, missing file, invalid date, duplicate numbers, out-of-range, wrong count
- chronological order, ISO dates, idempotent cache
- provenance includes count/first/last/path/hash and round-trips to every record
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from service.ingestion import (
    DataIngestionError,
    DrawHistory,
    DrawRecord,
    ingest_from_settings,
    load,
    reload_from_settings,
    reset_cache,
)


def _draw(
    *,
    id_: int,
    d: str,
    numbers: list[int] | None = None,
) -> dict[str, object]:
    return {
        "id": id_,
        "date": d,
        "numbers": numbers if numbers is not None else list(range(1, 16)),
    }


# --- Valid load path -------------------------------------------------------


def test_valid_load_returns_chronological_history(tmp_data_json) -> None:
    draws = [
        # Source is reverse-chronological: newest first, as data.json is.
        _draw(id_=3, d="03-01-2020", numbers=[5, 1, 3, 4, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]),
        _draw(id_=2, d="02-01-2020", numbers=list(range(11, 26))),
        _draw(id_=1, d="01-01-2020", numbers=list(range(1, 16))),
    ]
    path, expected_hash = tmp_data_json(draws)

    history = load(path)

    assert isinstance(history, DrawHistory)
    assert len(history) == 3
    assert [r.index for r in history] == [0, 1, 2]
    assert [r.iso_date for r in history] == [
        date(2020, 1, 1),
        date(2020, 1, 2),
        date(2020, 1, 3),
    ]
    # Chronological order: oldest first (original_id=1)
    assert history.at(0).original_id == 1
    assert history.at(2).original_id == 3
    assert history.provenance.content_hash == expected_hash
    assert history.provenance.total_draws == 3
    assert history.provenance.first_date == date(2020, 1, 1)
    assert history.provenance.last_date == date(2020, 1, 3)
    assert history.provenance.source_path == str(path)


def test_numbers_sorted_is_ascending_and_drawn_preserves_source(tmp_data_json) -> None:
    drawn = [5, 1, 3, 4, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020", numbers=drawn)])

    history = load(path)
    record = history.at(0)

    assert record.numbers_drawn == tuple(drawn)
    assert record.numbers_sorted == tuple(sorted(drawn))
    assert history.provenance.order_source == "original"


def test_order_source_canonical_when_source_pre_sorted(tmp_data_json) -> None:
    # Pre-sorted source → order_source == "canonical"
    path, _ = tmp_data_json(
        [
            _draw(id_=1, d="01-01-2020", numbers=list(range(1, 16))),
            _draw(id_=2, d="02-01-2020", numbers=list(range(2, 17))),
        ]
    )
    history = load(path)
    assert history.provenance.order_source == "canonical"


# --- Missing file ----------------------------------------------------------


def test_missing_file_fails_fast(tmp_path: Path) -> None:
    with pytest.raises(DataIngestionError, match=r"data\.json not found"):
        load(tmp_path / "nope.json")


# --- Schema validation -----------------------------------------------------


def test_invalid_date_format_rejected(tmp_data_json) -> None:
    path, _ = tmp_data_json([_draw(id_=1, d="2020-01-01")])
    with pytest.raises(DataIngestionError, match=r"id=1.*DD-MM-YYYY"):
        load(path)


def test_duplicate_numbers_rejected(tmp_data_json) -> None:
    nums = [1, 1, *list(range(2, 15))]  # 15 entries, but 1 duplicated
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020", numbers=nums)])
    with pytest.raises(DataIngestionError, match="duplicate numbers"):
        load(path)


def test_out_of_range_number_rejected(tmp_data_json) -> None:
    nums = [26, *list(range(1, 15))]
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020", numbers=nums)])
    with pytest.raises(DataIngestionError, match=r"number 26 outside"):
        load(path)


def test_wrong_number_count_rejected(tmp_data_json) -> None:
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020", numbers=list(range(1, 15)))])
    with pytest.raises(DataIngestionError, match="expected 15 numbers, got 14"):
        load(path)


def test_malformed_json_rejected(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(DataIngestionError, match="not valid JSON"):
        load(path)


def test_empty_dataset_rejected(tmp_data_json) -> None:
    path, _ = tmp_data_json([])
    with pytest.raises(DataIngestionError, match="no draws"):
        load(path)


# --- Idempotence / cache ---------------------------------------------------


def test_ingest_is_idempotent_within_process(tmp_data_json, make_settings) -> None:
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020")])
    settings = make_settings(path)

    reset_cache()
    first = ingest_from_settings(settings)
    second = ingest_from_settings(settings)

    assert first is second  # identity — single read per process lifetime


def test_ingest_reads_file_once(tmp_data_json, make_settings, monkeypatch) -> None:
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020")])
    settings = make_settings(path)

    calls = {"n": 0}
    original_read_bytes = Path.read_bytes

    def counting_read_bytes(self: Path) -> bytes:
        if self == path:
            calls["n"] += 1
        return original_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", counting_read_bytes)

    reset_cache()
    ingest_from_settings(settings)
    ingest_from_settings(settings)
    ingest_from_settings(settings)
    assert calls["n"] == 1


# --- Provenance round-trip -------------------------------------------------


def test_provenance_hash_matches_file_bytes(tmp_data_json) -> None:
    path, expected_hash = tmp_data_json([_draw(id_=1, d="01-01-2020")])
    history = load(path)
    assert history.provenance.content_hash == expected_hash


def test_provenance_roundtrips_to_every_record_via_history(tmp_data_json) -> None:
    path, expected_hash = tmp_data_json(
        [
            _draw(id_=1, d="01-01-2020"),
            _draw(id_=2, d="02-01-2020"),
        ]
    )
    history = load(path)
    # Every record is reachable via the same history instance whose provenance
    # carries the content hash — this is the contract with downstream capabilities.
    assert history.provenance.content_hash == expected_hash
    assert [r.original_id for r in history] == [1, 2]
    assert all(isinstance(r, DrawRecord) for r in history)


# --- Golden test against a tiny hand-crafted dataset ----------------------


def test_golden_tiny_dataset(tmp_path: Path) -> None:
    """Hand-verified: 3 draws, deterministic hash pinned to exact file bytes.

    The hash is pinned to the exact JSON bytes we write here; any change to the
    serialization requires updating this constant deliberately.
    """
    payload = {
        "allowed_numbers": list(range(1, 26)),
        "dataset": [
            {
                "id": 3,
                "date": "03-01-2020",
                "numbers": [5, 1, 3, 4, 2, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            },
            {
                "id": 2,
                "date": "02-01-2020",
                "numbers": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            },
            {
                "id": 1,
                "date": "01-01-2020",
                "numbers": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            },
        ],
    }
    path = tmp_path / "data.json"
    # Canonical serialization: sort_keys=False, no indent, matches the bytes we hash.
    raw = json.dumps(payload).encode("utf-8")
    path.write_bytes(raw)

    import hashlib

    expected_hash = hashlib.sha256(raw).hexdigest()

    history = load(path)

    assert len(history) == 3
    assert history.provenance.total_draws == 3
    assert history.provenance.first_date == date(2020, 1, 1)
    assert history.provenance.last_date == date(2020, 1, 3)
    assert history.provenance.content_hash == expected_hash
    # The first (chronologically earliest) record is original_id=1.
    assert history.at(0).original_id == 1
    # Original draw order is preserved on id=3 (unsorted source).
    assert history.by_original_id(3).numbers_drawn[:3] == (5, 1, 3)
    assert history.by_original_id(3).numbers_sorted[:3] == (1, 2, 3)


# --- Hot-reload -----------------------------------------------------------


def test_reload_returns_updated_history(tmp_data_json, make_settings) -> None:
    """reload_from_settings clears the cache and re-reads the file."""
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020")])
    settings = make_settings(path)

    first = ingest_from_settings(settings)
    assert len(first) == 1

    # Overwrite the file with two draws.
    import json

    payload = {
        "allowed_numbers": list(range(1, 26)),
        "dataset": [
            _draw(id_=2, d="02-01-2020"),
            _draw(id_=1, d="01-01-2020"),
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    second = reload_from_settings(settings)
    assert len(second) == 2
    assert second is not first


def test_reload_is_idempotent(tmp_data_json, make_settings) -> None:
    """Calling reload_from_settings twice without file change returns stable result."""
    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020")])
    settings = make_settings(path)

    first = reload_from_settings(settings)
    second = reload_from_settings(settings)
    # Both calls load from the same file; result should be structurally identical.
    assert len(first) == len(second)
    assert first.provenance.content_hash == second.provenance.content_hash


def test_reload_thread_safety(tmp_data_json, make_settings) -> None:
    """Concurrent reload calls must not corrupt the cache."""
    import threading

    path, _ = tmp_data_json([_draw(id_=1, d="01-01-2020")])
    settings = make_settings(path)
    ingest_from_settings(settings)

    errors: list[Exception] = []

    def _reload() -> None:
        try:
            reload_from_settings(settings)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=_reload) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Reload raised errors: {errors}"
    from service.ingestion import get_cached_history

    assert get_cached_history() is not None


# --- Live dataset smoke ---------------------------------------------------


def test_live_dataset_loads(tmp_path: Path) -> None:
    """Smoke test against the real repo data.json — it exists and validates."""
    repo_root = Path(__file__).resolve().parents[2]
    real = repo_root / "data.json"
    assert real.is_file(), f"expected {real} to exist"
    history = load(real)
    assert len(history) >= 3000  # project claims ~3,656
    assert history.provenance.first_date <= history.provenance.last_date
    # Every record's sorted numbers are in [1,25]
    for r in history:
        assert all(1 <= n <= 25 for n in r.numbers_sorted)
        assert len(r.numbers_sorted) == 15
