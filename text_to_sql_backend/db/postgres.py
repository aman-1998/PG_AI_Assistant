"""SQLAlchemy engine/session setup for the Postgres control-plane store."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.schema import MetaData

from config.settings import CHAT_HISTORY_RETENTION_DEFAULT_DAYS, MAX_CHAT_SESSIONS_DEFAULT, settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    metadata = MetaData(schema=settings.DB_SCHEMA)


def _run_lightweight_migrations() -> None:
    """`Base.metadata.create_all()` only creates missing tables, it never alters
    existing ones. This repo has no Alembic setup, so new columns on existing
    tables are added here via idempotent ALTER TABLE statements (ignoring the
    "already exists" error on repeat runs).
    """
    statements = [
        f"ALTER TABLE {settings.DB_SCHEMA}.users ADD COLUMN chat_history_retention_days "
        f"INT NOT NULL DEFAULT {CHAT_HISTORY_RETENTION_DEFAULT_DAYS}",
        f"ALTER TABLE {settings.DB_SCHEMA}.users ADD COLUMN reset_token_hash VARCHAR(255)",
        f"ALTER TABLE {settings.DB_SCHEMA}.users ADD COLUMN reset_token_expires_at TIMESTAMPTZ",
        f"ALTER TABLE {settings.DB_SCHEMA}.users ADD COLUMN max_chat_sessions "
        f"INT NOT NULL DEFAULT {MAX_CHAT_SESSIONS_DEFAULT}",
        f"ALTER TABLE {settings.DB_SCHEMA}.chat_sessions ADD COLUMN title VARCHAR(255)",
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
    """Create the DB_SCHEMA schema (if missing) and all tables (if missing)."""
    from db import models  # noqa: F401  (ensure models are registered on Base.metadata)

    with engine.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.DB_SCHEMA}"'))

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
