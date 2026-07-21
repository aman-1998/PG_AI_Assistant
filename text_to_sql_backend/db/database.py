"""SQLAlchemy engine/session setup for the control-plane store.

The app is SQLite-only: the database lives at DATA_DIR/app.db (see
config.settings). SQLite has no schema concept, so table namespacing is unused.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.schema import MetaData

from config.settings import CHAT_HISTORY_RETENTION_DEFAULT_DAYS, MAX_CHAT_SESSIONS_DEFAULT, settings
from db.engine_util import build_engine, is_sqlite_url

logger = logging.getLogger(__name__)

IS_SQLITE = is_sqlite_url(settings.DATABASE_URL)
# SQLite has no schemas, so the tables are never namespaced.
DB_SCHEMA = None

engine = build_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    metadata = MetaData(schema=DB_SCHEMA)


def _run_lightweight_migrations() -> None:
    """`Base.metadata.create_all()` only creates missing tables, it never alters
    existing ones. This repo has no Alembic setup, so new columns on existing
    tables are added here via idempotent ALTER TABLE statements (ignoring the
    "already exists" error on repeat runs).
    """
    prefix = ""
    ts_type = "TIMESTAMP" if IS_SQLITE else "TIMESTAMPTZ"
    int_type = "INTEGER" if IS_SQLITE else "INT"
    bool_true = "1" if IS_SQLITE else "TRUE"
    statements = [
        f"ALTER TABLE {prefix}users ADD COLUMN chat_history_retention_days "
        f"{int_type} NOT NULL DEFAULT {CHAT_HISTORY_RETENTION_DEFAULT_DAYS}",
        f"ALTER TABLE {prefix}users ADD COLUMN reset_token_hash VARCHAR(255)",
        f"ALTER TABLE {prefix}users ADD COLUMN reset_token_expires_at {ts_type}",
        f"ALTER TABLE {prefix}users ADD COLUMN max_chat_sessions "
        f"{int_type} NOT NULL DEFAULT {MAX_CHAT_SESSIONS_DEFAULT}",
        f"ALTER TABLE {prefix}chat_sessions ADD COLUMN title VARCHAR(255)",
        f"ALTER TABLE {prefix}llm_configs ADD COLUMN supports_temperature "
        f"BOOLEAN NOT NULL DEFAULT {bool_true}",
    ]
    for statement in statements:
        try:
            with engine.begin() as conn:
                conn.execute(text(statement))
        except (OperationalError, ProgrammingError) as exc:
            if "already exists" in str(exc).lower() or "duplicate column" in str(exc).lower():
                continue
            logger.warning("Skipping migration statement due to error: %s (%s)", statement, exc)


def init_db() -> None:
    """Create all tables (if missing)."""
    from db import models  # noqa: F401  (ensure models are registered on Base.metadata)

    Base.metadata.create_all(bind=engine)
    _run_lightweight_migrations()


def get_db() -> Generator:
    """FastAPI dependency yielding a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator:
    """Context manager for use outside of FastAPI request scope."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
