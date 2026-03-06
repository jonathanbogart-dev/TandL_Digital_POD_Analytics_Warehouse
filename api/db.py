"""
Database connection pool shared across routes.

Uses SQLAlchemy's async-compatible connection pool with psycopg2.
The DATABASE_URL env var must be set (e.g. postgresql://user:pass@host/db).
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return (and lazily create) the shared SQLAlchemy engine."""
    global _engine
    if _engine is None:
        database_url = os.environ["DATABASE_URL"]
        _engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def query(sql: str, params: dict | None = None) -> list[dict]:
    """Execute a SQL query and return results as a list of dicts."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in result.fetchall()]
