"""Live business documentation lookups.

Nothing here is persisted - every call reads Postgres native
`COMMENT ON TABLE` / `COMMENT ON COLUMN` metadata directly via the MCP
`list_tables` / `get_table_comments` tools. Table matching combines simple
keyword overlap with live semantic similarity (via the active LLM config's
embedding model, when supported) - embeddings are computed fresh on every
call and discarded immediately after scoring, never stored anywhere. Used by
the documentation agent's `search_business_docs` tool.
"""
from __future__ import annotations

import math

from db.models import DatabaseConnection
from services import mcp_client_service
from services.embedding_factory import get_embeddings_from_credentials


async def list_table_names(connection: DatabaseConnection, schema: str = "public") -> list[str]:
    tables = await mcp_client_service.call_tool(connection, "list_tables", {"schema": schema})
    return [t["table_name"] for t in tables if t.get("table_name")]


async def get_table_comments(connection: DatabaseConnection, table_name: str, schema: str = "public") -> dict:
    return await mcp_client_service.call_tool(
        connection, "get_table_comments", {"table_name": table_name, "schema": schema}
    )


def _match_tables(query: str, table_names: list[str]) -> list[str]:
    """Find table names referenced by a free-text question, preferring exact
    substring mentions and falling back to loose word overlap."""
    q = query.lower()
    exact = [name for name in table_names if name.lower() in q]
    if exact:
        return exact

    words = [w.strip(".,?!'\"") for w in q.split() if len(w) > 2]
    scored: list[tuple[int, str]] = []
    for name in table_names:
        name_l = name.lower()
        score = sum(1 for w in words if w in name_l or name_l in w)
        if score > 0:
            scored.append((score, name))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [name for _, name in scored[:3]]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _semantic_match_tables(
    query: str, table_names: list[str], llm_credentials: dict | None, top_k: int = 3
) -> list[str]:
    """Embed the query and every table name live (nothing persisted) and
    return the best matches by cosine similarity. Returns [] if the provider
    has no embeddings support, embedding fails, or nothing scores well enough."""
    if not llm_credentials or not table_names:
        return []
    embeddings = get_embeddings_from_credentials(llm_credentials)
    if embeddings is None:
        return []
    try:
        query_vec = await embeddings.aembed_query(query)
        name_vecs = await embeddings.aembed_documents([name.replace("_", " ") for name in table_names])
    except Exception:  # noqa: BLE001
        return []

    scored = [(_cosine(query_vec, vec), name) for name, vec in zip(table_names, name_vecs)]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [name for score, name in scored[:top_k] if score > 0.3]


async def search_documentation(
    connection: DatabaseConnection, query: str, llm_credentials: dict | None = None, schema: str = "public"
) -> list[dict]:
    """Find Postgres-native comments relevant to a free-text question about a
    table/column's business meaning. Combines keyword matching with live
    semantic matching (when an embedding-capable LLM is configured) to also
    catch paraphrased questions that don't share literal words with the table
    name. Returns [] if no table could be matched - this does NOT mean no
    comment exists, only that no table matched this query."""
    table_names = await list_table_names(connection, schema)
    matched = list(dict.fromkeys(_match_tables(query, table_names)))  # de-duped, order-preserving
    semantic = await _semantic_match_tables(query, table_names, llm_credentials)
    for name in semantic:
        if name not in matched:
            matched.append(name)
    return [await get_table_comments(connection, name, schema) for name in matched]
