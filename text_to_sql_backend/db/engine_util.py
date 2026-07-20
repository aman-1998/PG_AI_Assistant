"""Shared helpers for building SQLAlchemy engines that work against either
SQLite (the default, for the on-premise/desktop build) or Postgres (optional,
for a shared-server deployment). Keeping engine construction in one place lets
the control-plane store (db/database.py) and the RAG store
(services/rag/rag_db.py) stay dialect-agnostic.
"""
from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url

log = logging.getLogger(__name__)


def is_sqlite_url(url: str) -> bool:
    """True if the SQLAlchemy URL targets SQLite (any driver)."""
    return make_url(url).get_backend_name() == "sqlite"


def _ensure_sqlite_parent_dir(url: str) -> None:
    """Create the parent directory of a file-based SQLite database if missing so
    the very first startup doesn't fail on a fresh checkout."""
    database = make_url(url).database
    if database and database != ":memory:":
        Path(database).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def build_engine(url: str, *, load_sqlite_vec: bool = False) -> Engine:
    """Create an engine tuned for the URL's dialect.

    SQLite: a single local file, thread-safe session usage across FastAPI's
    threadpool, WAL journaling + foreign-key enforcement, and (optionally) the
    sqlite-vec extension loaded on every connection for vector search.

    Other dialects (Postgres): a pooled engine with pre-ping/recycle.
    """
    if is_sqlite_url(url):
        _ensure_sqlite_parent_dir(url)
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        _register_sqlite_pragmas(engine, load_sqlite_vec=load_sqlite_vec)
        return engine
    return create_engine(url, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800)


def _register_sqlite_pragmas(engine: Engine, *, load_sqlite_vec: bool) -> None:
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_conn, _record):  # noqa: ANN001
        cursor = dbapi_conn.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
        finally:
            cursor.close()
        if load_sqlite_vec:
            _load_vec_extension(dbapi_conn)


def _load_vec_extension(dbapi_conn) -> None:  # noqa: ANN001
    """Load the sqlite-vec loadable extension onto a raw sqlite3 connection.
    Raises on failure so the caller (RAG init_schema) can disable the optional
    vector feature gracefully instead of crashing the app."""
    import sqlite_vec

    dbapi_conn.enable_load_extension(True)
    try:
        sqlite_vec.load(dbapi_conn)
    finally:
        dbapi_conn.enable_load_extension(False)
