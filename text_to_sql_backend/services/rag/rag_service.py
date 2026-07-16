"""RAG Service — ingestion orchestrator: parse -> chunk -> embed -> store.

Nothing here talks to customer Postgres connections directly (that's MCP's
job elsewhere) — this only manages the separate pgvector store for uploaded
file content. Dedup via file_hash so re-uploading the same file for the same
connection is a no-op.
"""
from __future__ import annotations

import logging

from services.rag import rag_db
from services.rag.rag_chunker import chunk_text
from services.rag.rag_embedder import embed_texts
from services.rag.rag_parser import parse_upload

log = logging.getLogger(__name__)


class RagDisabledError(Exception):
    """Raised when the uploaded-file RAG Postgres store is not configured/reachable."""


def ingest_file(filename: str, content: bytes, connection_id: int, user_id: int, llm_credentials: dict) -> dict:
    """Parses, chunks, embeds, and stores an uploaded file. Returns the file
    record dict. Reuses an existing 'ready' record if this exact file
    (by hash) was already uploaded for this connection+user."""
    if not rag_db.is_enabled():
        raise RagDisabledError("Uploaded-file RAG is not configured or its Postgres store is unreachable.")

    file_hash = rag_db.compute_file_hash(content)
    existing = rag_db.get_existing_file(file_hash, connection_id, user_id)
    if existing and existing["status"] == "ready":
        log.info("File already ingested, reusing | filename=%s file_id=%s", filename, existing["id"])
        return existing
    if existing:
        rag_db.delete_file_record(existing["id"])

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
    file_id = rag_db.create_file_record(
        file_hash=file_hash,
        filename=filename,
        file_type=ext,
        size_kb=len(content) // 1024,
        connection_id=connection_id,
        user_id=user_id,
    )

    try:
        text = parse_upload(filename, content, llm_credentials)
        chunks = chunk_text(text, source=filename)
        if not chunks:
            rag_db.update_file_status(file_id, "failed")
            raise ValueError("No usable content extracted from this file.")

        vectors = embed_texts([c["text"] for c in chunks])
        for chunk, vector in zip(chunks, vectors):
            chunk["embedding"] = vector

        rag_db.store_chunks(file_id, connection_id, user_id, chunks)
        rag_db.update_file_status(file_id, "ready", chunk_count=len(chunks))
        log.info("File ingested | filename=%s file_id=%s chunks=%d", filename, file_id, len(chunks))
        return {"id": file_id, "filename": filename, "status": "ready", "chunk_count": len(chunks)}
    except Exception:
        rag_db.update_file_status(file_id, "failed")
        raise


def list_uploaded_files(connection_id: int, user_id: int) -> list[dict]:
    return rag_db.list_files(connection_id, user_id)


def delete_uploaded_file(file_id: str, connection_id: int, user_id: int) -> bool:
    return rag_db.delete_file(file_id, connection_id, user_id)
