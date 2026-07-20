"""RAG Database Layer — vector store for uploaded-file RAG.

Works against either SQLite + sqlite-vec (default, on-premise/desktop build)
or Postgres + pgvector (optional, shared-server deployment), chosen from the
same URL as the control-plane store unless RAG_DATABASE_URL overrides it.

Completely separate from db/database.py (control-plane store) and from
customer database connections opened via MCP. Scoped by connection_id (the
customer DatabaseConnection this file was uploaded against) + user_id.

If the vector store is unreachable or its extension (sqlite-vec / pgvector) is
unavailable, this module's functions are no-ops / return empty results so the
rest of the app keeps working without this optional feature.

Tables (auto-created if missing via init_schema()):
    rag_files        — tracks uploaded files, dedup via file_hash
    rag_chunks       — text chunks + metadata
    rag_chunks_vec   — (SQLite only) sqlite-vec virtual table holding the
                       embeddings, keyed by rag_chunks.id; on Postgres the
                       embedding lives in a pgvector column on rag_chunks
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from config.rag_config import rag_config
from config.settings import settings
from db.engine_util import build_engine, is_sqlite_url

log = logging.getLogger(__name__)

_engine: Engine | None = None
_engine_initialized = False


# Schema used ONLY by the optional Postgres/pgvector RAG store (when
# RAG_DATABASE_URL points at Postgres). The default SQLite store ignores it.
_PG_SCHEMA = "nltosql"


def _rag_url() -> str:
    return settings.RAG_DATABASE_URL or settings.DATABASE_URL


def _is_sqlite() -> bool:
    return is_sqlite_url(_rag_url())


def _get_engine() -> Engine | None:
    """Lazily create the vector-store engine, reusing DATABASE_URL unless
    RAG_DATABASE_URL overrides it. On Postgres, sessions default their
    search_path to _PG_SCHEMA so unqualified table names resolve there
    instead of "public"."""
    global _engine
    if _engine is None:
        url = _rag_url()
        if is_sqlite_url(url):
            _engine = build_engine(url, load_sqlite_vec=True)
        else:
            from sqlalchemy import create_engine

            _engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                connect_args={"options": f"-c search_path={_PG_SCHEMA}"},
            )
    return _engine


def is_enabled() -> bool:
    return _engine_initialized and _get_engine() is not None


def init_schema() -> None:
    """Create the vector extension + tables if missing. Safe to call on every
    startup. Logs a warning and disables the feature (rather than crashing the
    app) if the vector store is unreachable or misconfigured (e.g. the
    sqlite-vec / pgvector extension can't be loaded)."""
    global _engine_initialized
    engine = _get_engine()
    if engine is None:
        log.info("RAG store engine unavailable — uploaded-file RAG feature disabled")
        return
    try:
        if _is_sqlite():
            _init_schema_sqlite(engine)
        else:
            _init_schema_postgres(engine)
        _engine_initialized = True
        log.info("RAG store schema ready (%s)", "sqlite-vec" if _is_sqlite() else "pgvector")
    except Exception:  # noqa: BLE001
        log.warning("RAG store unreachable/misconfigured — uploaded-file RAG feature disabled", exc_info=True)
        _engine_initialized = False


def _init_schema_sqlite(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS rag_files (
                    id TEXT PRIMARY KEY,
                    file_hash TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    size_kb INTEGER NOT NULL,
                    connection_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'processing',
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS rag_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT NOT NULL REFERENCES rag_files(id) ON DELETE CASCADE,
                    connection_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    source TEXT
                )
                """
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS idx_rag_chunks_scope ON rag_chunks (connection_id, user_id)")
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_rag_chunks_file ON rag_chunks (file_id)"))
        # sqlite-vec virtual table holding the embeddings, keyed by rag_chunks.id.
        conn.execute(
            text(
                f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_vec USING vec0(
                    embedding float[{rag_config.EMBEDDING_DIM}] distance_metric=cosine
                )
                """
            )
        )


def _init_schema_postgres(engine: Engine) -> None:
    with engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{_PG_SCHEMA}"'))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(
            text(
                """
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
    with engine.begin() as conn:
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
    return file_id


def _sqlite_purge_chunks(conn, file_id: str) -> None:  # noqa: ANN001
    """Delete a file's chunk rows and their matching sqlite-vec entries (a
    virtual table isn't covered by ON DELETE CASCADE)."""
    rowids = [
        r[0]
        for r in conn.execute(text("SELECT id FROM rag_chunks WHERE file_id = :fid"), {"fid": file_id}).all()
    ]
    for rowid in rowids:
        conn.execute(text("DELETE FROM rag_chunks_vec WHERE rowid = :rowid"), {"rowid": rowid})
    conn.execute(text("DELETE FROM rag_chunks WHERE file_id = :fid"), {"fid": file_id})


def delete_file_record(file_id: str) -> None:
    engine = _get_engine()
    if engine is None:
        return
    with engine.begin() as conn:
        if _is_sqlite():
            _sqlite_purge_chunks(conn, file_id)
        conn.execute(text("DELETE FROM rag_files WHERE id = :file_id"), {"file_id": file_id})


def update_file_status(file_id: str, status: str, chunk_count: int = 0) -> None:
    engine = _get_engine()
    if engine is None:
        return
    now_expr = "CURRENT_TIMESTAMP" if _is_sqlite() else "NOW()"
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                UPDATE rag_files SET status = :status, chunk_count = :chunk_count, updated_at = {now_expr}
                WHERE id = :file_id
                """
            ),
            {"file_id": file_id, "status": status, "chunk_count": chunk_count},
        )


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
    """Delete a file (and its chunks) if it belongs to this connection/user.
    Returns True if a row was deleted. On Postgres the chunks go via
    ON DELETE CASCADE; on SQLite the sqlite-vec rows are purged explicitly."""
    engine = _get_engine()
    if engine is None:
        return False
    with engine.begin() as conn:
        if _is_sqlite():
            _sqlite_purge_chunks(conn, file_id)
        result = conn.execute(
            text("DELETE FROM rag_files WHERE id = :file_id AND connection_id = :connection_id AND user_id = :user_id"),
            {"file_id": file_id, "connection_id": connection_id, "user_id": user_id},
        )
    return result.rowcount > 0


_STORE_BATCH_SIZE = rag_config.STORE_BATCH_SIZE


def store_chunks(file_id: str, connection_id: int, user_id: int, chunks: list[dict]) -> None:
    """Each chunk must have: text, embedding (list[float]), chunk_index, source (optional)."""
    engine = _get_engine()
    if engine is None or not chunks:
        return
    if _is_sqlite():
        _store_chunks_sqlite(engine, file_id, connection_id, user_id, chunks)
    else:
        _store_chunks_postgres(engine, file_id, connection_id, user_id, chunks)


def _store_chunks_sqlite(engine: Engine, file_id: str, connection_id: int, user_id: int, chunks: list[dict]) -> None:
    import sqlite_vec

    with engine.begin() as conn:
        for chunk in chunks:
            result = conn.execute(
                text(
                    """
                    INSERT INTO rag_chunks (file_id, connection_id, user_id, chunk_index, text, source)
                    VALUES (:file_id, :connection_id, :user_id, :chunk_index, :text, :source)
                    """
                ),
                {
                    "file_id": file_id,
                    "connection_id": connection_id,
                    "user_id": user_id,
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "source": chunk.get("source"),
                },
            )
            conn.execute(
                text("INSERT INTO rag_chunks_vec (rowid, embedding) VALUES (:rowid, :embedding)"),
                {"rowid": result.lastrowid, "embedding": sqlite_vec.serialize_float32(chunk["embedding"])},
            )


def _store_chunks_postgres(engine: Engine, file_id: str, connection_id: int, user_id: int, chunks: list[dict]) -> None:
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

    with engine.begin() as conn:
        for i in range(0, len(rows), _STORE_BATCH_SIZE):
            conn.execute(insert_sql, rows[i : i + _STORE_BATCH_SIZE])


def similarity_search(
    query_embedding: list[float], connection_id: int, user_id: int, top_k: int = 5, min_score: float = 0.35
) -> list[dict]:
    """Returns list of {text, source, file_id, score}, best score first."""
    engine = _get_engine()
    if engine is None:
        return []
    if _is_sqlite():
        return _similarity_search_sqlite(engine, query_embedding, connection_id, user_id, top_k, min_score)
    return _similarity_search_postgres(engine, query_embedding, connection_id, user_id, top_k, min_score)


def _similarity_search_sqlite(
    engine: Engine, query_embedding: list[float], connection_id: int, user_id: int, top_k: int, min_score: float
) -> list[dict]:
    import sqlite_vec

    serialized = sqlite_vec.serialize_float32(query_embedding)
    # sqlite-vec KNN can't filter on the joined metadata table, so over-fetch
    # globally then filter by connection/user and re-rank in Python.
    fetch_k = max(top_k * 10, 50)
    with engine.connect() as conn:
        knn = conn.execute(
            text(
                """
                SELECT rowid, distance
                FROM rag_chunks_vec
                WHERE embedding MATCH :embedding AND k = :k
                ORDER BY distance
                """
            ),
            {"embedding": serialized, "k": fetch_k},
        ).mappings().all()
        if not knn:
            return []

        distance_by_id = {row["rowid"]: float(row["distance"]) for row in knn}
        rowids = list(distance_by_id.keys())
        placeholders = ",".join(f":id{i}" for i in range(len(rowids)))
        params = {f"id{i}": rid for i, rid in enumerate(rowids)}
        params.update({"cid": connection_id, "uid": user_id})
        chunk_rows = conn.execute(
            text(
                f"""
                SELECT id, text, source, file_id
                FROM rag_chunks
                WHERE id IN ({placeholders}) AND connection_id = :cid AND user_id = :uid
                """
            ),
            params,
        ).mappings().all()

    chunk_by_id = {row["id"]: row for row in chunk_rows}
    results: list[dict] = []
    for rowid in sorted(rowids, key=lambda r: distance_by_id[r]):
        chunk = chunk_by_id.get(rowid)
        if chunk is None:
            continue
        score = 1.0 - distance_by_id[rowid]
        if score < min_score:
            continue
        results.append({"text": chunk["text"], "source": chunk["source"], "file_id": str(chunk["file_id"]), "score": score})
        if len(results) >= top_k:
            break
    return results


def _similarity_search_postgres(
    engine: Engine, query_embedding: list[float], connection_id: int, user_id: int, top_k: int, min_score: float
) -> list[dict]:
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
