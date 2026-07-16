"""Central configuration for the uploaded-file RAG pipeline (embedding model,
chunking, retrieval). Mirrors ai-service/config/rag_config.py's shape, scoped
down to what this feature needs. All values can be overridden via RAG_-prefixed
environment variables.
"""
from __future__ import annotations

import os

from pydantic import BaseModel


def _env_or(name: str, default):
    raw = os.getenv(f"RAG_{name}")
    if raw is None:
        return default
    if isinstance(default, bool):
        return raw.lower() in ("1", "true", "yes")
    if isinstance(default, int):
        return int(raw)
    if isinstance(default, float):
        return float(raw)
    return raw


class RAGConfig(BaseModel):
    # Embedding model — local, offline, provider-independent (does not rely on
    # a customer's chosen LLM/embeddings provider or API key).
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # Chunking (character-based; good enough for .sql text and image descriptions)
    CHUNK_SIZE: int = 1200
    CHUNK_OVERLAP: int = 150
    MIN_CHUNK_SIZE: int = 50

    # Retrieval
    RETRIEVAL_TOP_K: int = 5
    RETRIEVAL_MIN_SCORE: float = 0.35

    # Storage
    STORE_BATCH_SIZE: int = 200

    # Upload limits
    MAX_UPLOAD_MB: int = 50


def _build_config() -> RAGConfig:
    return RAGConfig(
        EMBEDDING_MODEL_NAME=_env_or("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
        EMBEDDING_DIM=_env_or("EMBEDDING_DIM", 384),
        CHUNK_SIZE=_env_or("CHUNK_SIZE", 1200),
        CHUNK_OVERLAP=_env_or("CHUNK_OVERLAP", 150),
        MIN_CHUNK_SIZE=_env_or("MIN_CHUNK_SIZE", 50),
        RETRIEVAL_TOP_K=_env_or("RETRIEVAL_TOP_K", 5),
        RETRIEVAL_MIN_SCORE=_env_or("RETRIEVAL_MIN_SCORE", 0.35),
        STORE_BATCH_SIZE=_env_or("STORE_BATCH_SIZE", 200),
        MAX_UPLOAD_MB=_env_or("MAX_UPLOAD_MB", 20),
    )


rag_config = _build_config()
