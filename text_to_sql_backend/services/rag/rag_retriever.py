"""RAG Retriever — embeds a query and retrieves relevant uploaded-file chunks
from the pgvector store, scoped to one connection + user."""
from __future__ import annotations

from config.rag_config import rag_config
from services.rag import rag_db
from services.rag.rag_embedder import embed_query


def retrieve_context(query: str, connection_id: int, user_id: int) -> list[dict]:
    """Returns [] if the RAG store is disabled or nothing scores well enough.
    Otherwise returns [{text, source, file_id, score}, ...] best-first."""
    if not rag_db.is_enabled():
        return []
    query_vector = embed_query(query)
    return rag_db.similarity_search(
        query_vector,
        connection_id,
        user_id,
        top_k=rag_config.RETRIEVAL_TOP_K,
        min_score=rag_config.RETRIEVAL_MIN_SCORE,
    )
