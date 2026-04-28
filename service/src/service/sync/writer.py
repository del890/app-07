"""Atomic write of data.json with backup preservation.

Writes the updated dataset to a temporary file alongside data.json, then
renames it over the original atomically. A .bak copy of the previous file
is preserved immediately before the rename.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("service.sync.writer")


class WriteError(OSError):
    """Raised when the atomic write or rename fails."""


def write_dataset(
    data_path: Path,
    allowed_numbers: list[int],
    dataset: list[dict[str, Any]],
) -> None:
    """Atomically replace ``data_path`` with the updated dataset.

    Steps:
    1. Serialise the full payload to a sibling temp file.
    2. Copy the existing file to ``data_path.with_suffix('.json.bak')``.
    3. Rename the temp file over ``data_path``.

    The original file is intact until step 3 completes.  If step 1 fails,
    nothing changes.

    Args:
        data_path: Absolute path to data.json.
        allowed_numbers: The ``allowed_numbers`` list to preserve in the file.
        dataset: The updated ``dataset`` list (reverse-chronological order).

    Raises:
        WriteError: If the write or rename fails.
    """
    payload = {
        "allowed_numbers": allowed_numbers,
        "dataset": dataset,
    }
    serialised = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

    # Write to a temp file first.
    tmp_path = data_path.with_name(data_path.name + ".tmp")
    try:
        tmp_path.write_bytes(serialised)
    except OSError as exc:
        raise WriteError(f"Failed to write temporary dataset file {tmp_path}: {exc}") from exc

    # Preserve the previous version as .bak
    bak_path = data_path.with_name(data_path.name + ".bak")
    if data_path.exists():
        try:
            import shutil
            shutil.copy2(data_path, bak_path)
        except OSError as exc:
            # Non-fatal: log and continue; the rename below is what matters.
            log.warning(
                "sync.writer.bak_failed",
                extra={"bak": str(bak_path), "error": str(exc)},
            )

    # Atomic rename over the target.
    try:
        os.replace(tmp_path, data_path)
    except OSError as exc:
        # Clean up the temp file if rename failed.
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise WriteError(
            f"Failed to rename {tmp_path} → {data_path}: {exc}"
        ) from exc

    log.info(
        "sync.writer.wrote",
        extra={"path": str(data_path), "records": len(dataset)},
    )
