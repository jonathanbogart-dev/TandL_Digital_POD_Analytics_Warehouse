"""Dataset file store.

Each dataset is persisted as a JSON file under DATASET_STORE_PATH.
A _registry.json index tracks metadata for all stored datasets.

The store path is controlled by the DATASET_STORE_PATH environment variable
(default: ``./datasets`` relative to the process working directory).
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Resolved once at import time; can be overridden in tests via env var.
STORE_PATH = Path(os.environ.get("DATASET_STORE_PATH", "datasets")).resolve()

_REGISTRY_FILE = "_registry.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ensure_store() -> None:
    STORE_PATH.mkdir(parents=True, exist_ok=True)


def _registry_path() -> Path:
    return STORE_PATH / _REGISTRY_FILE


def _data_path(name: str) -> Path:
    return STORE_PATH / f"{name}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_registry() -> dict[str, dict[str, Any]]:
    """Return the full registry dict keyed by dataset name."""
    _ensure_store()
    p = _registry_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read registry, returning empty: %s", exc)
        return {}


def _save_registry(registry: dict[str, dict[str, Any]]) -> None:
    _registry_path().write_text(
        json.dumps(registry, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_dataset(
    name: str,
    new_records: list[dict[str, Any]],
    source_filename: str,
    mode: str,
) -> dict[str, Any]:
    """Write records to storage and update the registry.

    Args:
        name: Dataset identifier (slug).
        new_records: Records parsed from the uploaded file.
        source_filename: Original filename of the upload.
        mode: ``"replace"`` discards existing data; ``"append"`` concatenates.

    Returns:
        Updated registry entry for this dataset.
    """
    _ensure_store()
    registry = load_registry()
    now = _now_iso()

    if mode == "append":
        p = _data_path(name)
        if p.exists():
            try:
                existing = json.loads(p.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []
            records = existing + new_records
        else:
            records = new_records
    else:
        records = new_records

    _data_path(name).write_text(
        json.dumps(records, ensure_ascii=False),
        encoding="utf-8",
    )

    entry: dict[str, Any] = {
        "name": name,
        "source_filename": source_filename,
        "row_count": len(records),
        "rows_in_upload": len(new_records),
        "updated_at": now,
        "created_at": registry.get(name, {}).get("created_at", now),
    }
    registry[name] = entry
    _save_registry(registry)
    logger.info(
        "Saved dataset '%s' (%s mode): %d total rows", name, mode, len(records)
    )
    return entry


def load_dataset(name: str) -> list[dict[str, Any]]:
    """Return all records for *name*, or raise FileNotFoundError."""
    _ensure_store()
    p = _data_path(name)
    if not p.exists():
        raise FileNotFoundError(f"Dataset '{name}' not found in store.")
    return json.loads(p.read_text(encoding="utf-8"))


def delete_dataset(name: str) -> None:
    """Remove a dataset and its registry entry.

    Raises:
        FileNotFoundError: If the dataset does not exist.
    """
    _ensure_store()
    registry = load_registry()
    if name not in registry:
        raise FileNotFoundError(f"Dataset '{name}' not found in store.")
    p = _data_path(name)
    if p.exists():
        p.unlink()
    registry.pop(name)
    _save_registry(registry)
    logger.info("Deleted dataset '%s'", name)
