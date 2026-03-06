"""
Raw-layer loader: writes records to PostgreSQL using upsert semantics.

The raw layer is append-only by convention, but we use upsert on the
source primary key to avoid duplicates on re-runs.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class PostgresLoader:
    """Loads raw source records into the PostgreSQL raw layer."""

    def __init__(self, database_url: str) -> None:
        """Initialise the loader.

        Args:
            database_url: SQLAlchemy-compatible PostgreSQL connection string.
        """
        self._engine: Engine = create_engine(database_url, pool_pre_ping=True)

    def load(
        self,
        records: list[dict[str, Any]],
        schema: str,
        table: str,
        primary_key: str,
        flatten: bool = True,
    ) -> int:
        """Load records into a raw table, creating the table if needed.

        Adds an ``_ingested_at`` timestamp column to every row.
        Uses INSERT ... ON CONFLICT DO NOTHING on the primary key
        to prevent duplicates on re-runs.

        Args:
            records: List of dicts from the source API.
            schema: Target PostgreSQL schema (e.g. 'raw_printful').
            table: Target table name (e.g. 'orders').
            primary_key: Column name used for conflict detection.
            flatten: If True, nested dicts are JSON-serialised to strings.

        Returns:
            Number of rows successfully inserted.
        """
        if not records:
            logger.info("No records to load into %s.%s", schema, table)
            return 0

        ingested_at = datetime.now(tz=timezone.utc).isoformat()

        rows = []
        for rec in records:
            row = _flatten(rec) if flatten else dict(rec)
            row["_ingested_at"] = ingested_at
            rows.append(row)

        df = pd.DataFrame(rows)

        with self._engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

        df.to_sql(
            name=table,
            con=self._engine,
            schema=schema,
            if_exists="append",
            index=False,
            method=_upsert_on_conflict(primary_key),
        )

        logger.info("Loaded %d rows into %s.%s", len(rows), schema, table)
        return len(rows)


def _flatten(obj: Any, prefix: str = "") -> dict[str, Any]:
    """Recursively flatten a nested dict, joining keys with underscores."""
    items: dict[str, Any] = {}
    for k, v in obj.items():
        key = f"{prefix}_{k}" if prefix else k
        if isinstance(v, dict):
            items.update(_flatten(v, prefix=key))
        else:
            items[key] = v
    return items


def _upsert_on_conflict(primary_key: str):  # type: ignore[return]
    """Return a pandas to_sql method that does INSERT ... ON CONFLICT DO NOTHING."""
    from sqlalchemy.dialects.postgresql import insert

    def method(table, conn, keys, data_iter):  # type: ignore[return]
        stmt = insert(table.table).values(list(data_iter))
        stmt = stmt.on_conflict_do_nothing(index_elements=[primary_key])
        conn.execute(stmt)

    return method
