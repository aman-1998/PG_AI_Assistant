"""RAG Embedder — local, offline embedding model (fastembed / ONNX Runtime).

Deliberately independent of any customer's configured LLM provider/API key:
uploaded-file content must be embeddable regardless of which LLM a connection
happens to use (and works even for providers with no embeddings API, e.g.
anthropic/azure_openai). Loaded lazily on first use, not at import time, so
app startup never depends on this feature being available.
"""
from __future__ import annotations

import logging
import threading

from config.rag_config import rag_config

log = logging.getLogger(__name__)

_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                from fastembed import TextEmbedding

                log.info("Loading RAG embedding model | model=%s", rag_config.EMBEDDING_MODEL_NAME)
                _model = TextEmbedding(model_name=rag_config.EMBEDDING_MODEL_NAME)
                log.info("RAG embedding model ready | model=%s", rag_config.EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = _get_model()
    return [vector.tolist() for vector in model.embed(texts, batch_size=256)]


def embed_query(query: str) -> list[float]:
    model = _get_model()
    return next(iter(model.embed([query], batch_size=1))).tolist()
