"""RAG Database Layer — Postgres + pgvector store for uploaded-file RAG.

Completely separate from db/postgres.py (control-plane store) and from
customer Postgres connections opened via MCP.
Scoped by connection_id (the customer DatabaseConnection this file was
uploaded against) + user_id.

Uses settings.RAG_DATABASE_URL if set, otherwise falls back to reusing the
same Postgres server as the control-plane store (settings.DATABASE_URL) with
its own rag_files/rag_chunks tables. If that Postgres instance is unreachable
or doesn't have the pgvector extension available, this module's functions are
no-ops / return empty results so the rest of the app keeps working without
this optional feature.

Tables (auto-created if missing via init_schema()):
    rag_files   — tracks uploaded files, dedup via file_hash
    rag_chunks  — text chunks with vector embeddings
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.rag_config import rag_config
from config.settings import settings

log = logging.getLogger(__name__)

_engine: Engine | None = None
_engine_initialized = False


def _get_engine() -> Engine | None:
    """Lazily create the pgvector engine, reusing DATABASE_URL unless
    RAG_DATABASE_URL overrides it with a dedicated Postgres instance. Sessions
    default their search_path to settings.DB_SCHEMA so unqualified table names
    (rag_files/rag_chunks) resolve there instead of the "public" schema."""
    global _engine
    if _engine is None:
        url = settings.RAG_DATABASE_URL or settings.DATABASE_URL
        _engine = create_engine(
            url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            connect_args={"options": f"-c search_path={settings.DB_SCHEMA}"},
        )
    return _engine


def is_enabled() -> bool:
    return _engine_initialized and _get_engine() is not None


def init_schema() -> None:
    """Create the pgvector extension + tables if missing. Safe to call on every
    startup. Logs a warning and disables the feature (rather than crashing the
    app) if the RAG store is unreachable or misconfigured."""
    global _engine_initialized
    engine = _get_engine()
    if engine is None:
        log.info("RAG store engine unavailable — uploaded-file RAG feature disabled")
        return
    try:
        with engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.DB_SCHEMA}"'))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS rag_files (
                        id UUID PRIMARY KEY,
                        file_hash TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        size_kb INTEGER NOT NULL,
                        connection_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'processing',
                        chunk_count INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
            )
            conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS rag_chunks (
                        id UUID PRIMARY KEY,
                        file_id UUID NOT NULL REFERENCES rag_files(id) ON DELETE CASCADE,
                        connection_id BIGINT NOT NULL,
                        user_id BIGINT NOT NULL,
                        chunk_index INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        embedding VECTOR({rag_config.EMBEDDING_DIM}) NOT NULL,
                        source TEXT
                    )
                    """
                )
            )
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_rag_chunks_scope ON rag_chunks (connection_id, user_id)")
            )
            conn.commit()
        _engine_initialized = True
        log.info("RAG store schema ready")
    except Exception:  # noqa: BLE001
        log.warning("RAG store unreachable/misconfigured — uploaded-file RAG feature disabled", exc_info=True)
        _engine_initialized = False


def compute_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def get_existing_file(file_hash: str, connection_id: int, user_id: int) -> Optional[dict]:
    engine = _get_engine()
    if engine is None:
        return None
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, filename, file_type, size_kb, status, chunk_count
                FROM rag_files
                WHERE file_hash = :file_hash AND connection_id = :connection_id AND user_id = :user_id
                """
            ),
            {"file_hash": file_hash, "connection_id": connection_id, "user_id": user_id},
        ).mappings().first()
    if row is None:
        return None
    result = dict(row)
    result["id"] = str(result["id"])
    return result


def create_file_record(file_hash: str, filename: str, file_type: str, size_kb: int, connection_id: int, user_id: int) -> str:
    engine = _get_engine()
    file_id = str(uuid.uuid4())
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                INSERT INTO rag_files (id, file_hash, filename, file_type, size_kb, connection_id, user_id, status)
                VALUES (:id, :file_hash, :filename, :file_type, :size_kb, :connection_id, :user_id, 'processing')
                """
            ),
            {
                "id": file_id,
                "file_hash": file_hash,
                "filename": filename,
                "file_type": file_type,
                "size_kb": size_kb,
                "connection_id": connection_id,
                "user_id": user_id,
            },
        )
        conn.commit()
    return file_id


def delete_file_record(file_id: str) -> None:
    engine = _get_engine()
    if engine is None:
        return
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM rag_files WHERE id = :file_id"), {"file_id": file_id})
        conn.commit()


def update_file_status(file_id: str, status: str, chunk_count: int = 0) -> None:
    engine = _get_engine()
    if engine is None:
        return
    with engine.connect() as conn:
        conn.execute(
            text(
                """
                UPDATE rag_files SET status = :status, chunk_count = :chunk_count, updated_at = NOW()
                WHERE id = :file_id
                """
            ),
            {"file_id": file_id, "status": status, "chunk_count": chunk_count},
        )
        conn.commit()


def list_files(connection_id: int, user_id: int) -> list[dict]:
    engine = _get_engine()
    if engine is None:
        return []
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, filename, file_type, size_kb, status, chunk_count, created_at
                FROM rag_files
                WHERE connection_id = :connection_id AND user_id = :user_id AND status = 'ready'
                ORDER BY created_at DESC
                """
            ),
            {"connection_id": connection_id, "user_id": user_id},
        ).mappings().all()
    return [{**dict(r), "id": str(r["id"])} for r in rows]


def delete_file(file_id: str, connection_id: int, user_id: int) -> bool:
    """Delete a file (and its chunks, via ON DELETE CASCADE) if it belongs to this
    connection/user. Returns True if a row was deleted."""
    engine = _get_engine()
    if engine is None:
        return False
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM rag_files WHERE id = :file_id AND connection_id = :connection_id AND user_id = :user_id"),
            {"file_id": file_id, "connection_id": connection_id, "user_id": user_id},
        )
        conn.commit()
    return result.rowcount > 0


_STORE_BATCH_SIZE = rag_config.STORE_BATCH_SIZE


def store_chunks(file_id: str, connection_id: int, user_id: int, chunks: list[dict]) -> None:
    """Each chunk must have: text, embedding (list[float]), chunk_index, source (optional)."""
    engine = _get_engine()
    if engine is None or not chunks:
        return

    rows = []
    for chunk in chunks:
        embedding_str = "[" + ",".join(str(v) for v in chunk["embedding"]) + "]"
        rows.append(
            {
                "id": str(uuid.uuid4()),
                "file_id": file_id,
                "connection_id": connection_id,
                "user_id": user_id,
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "embedding": embedding_str,
                "source": chunk.get("source"),
            }
        )

    insert_sql = text(
        """
        INSERT INTO rag_chunks (id, file_id, connection_id, user_id, chunk_index, text, embedding, source)
        VALUES (CAST(:id AS UUID), CAST(:file_id AS UUID), :connection_id, :user_id, :chunk_index, :text, CAST(:embedding AS vector), :source)
        """
    )

    with engine.connect() as conn:
        for i in range(0, len(rows), _STORE_BATCH_SIZE):
            conn.execute(insert_sql, rows[i : i + _STORE_BATCH_SIZE])
        conn.commit()


def similarity_search(
    query_embedding: list[float], connection_id: int, user_id: int, top_k: int = 5, min_score: float = 0.35
) -> list[dict]:
    """Returns list of {text, source, file_id, score}, best score first."""
    engine = _get_engine()
    if engine is None:
        return []

    embedding_str = "[" + ",".join(str(v) for v in query_embedding) + "]"
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT c.text, c.source, c.file_id, 1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
                FROM rag_chunks c
                WHERE c.connection_id = :connection_id AND c.user_id = :user_id
                ORDER BY c.embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            ),
            {"embedding": embedding_str, "connection_id": connection_id, "user_id": user_id, "top_k": top_k},
        ).mappings().all()

    return [dict(r) for r in rows if float(r["score"]) >= min_score]
