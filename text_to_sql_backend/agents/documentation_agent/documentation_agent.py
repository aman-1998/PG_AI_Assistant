"""Builds a ReAct agent for general chat, PostgreSQL Q&A, and business
documentation lookups. The `search_business_docs` tool reads Postgres native
COMMENT ON TABLE/COLUMN metadata live via MCP, matched against the question via
keyword overlap plus live semantic similarity - nothing is persisted. The
`search_uploaded_docs` tool retrieves relevant chunks from user-uploaded .sql
files/images for this connection (embedded once at upload time and persisted
in a dedicated pgvector store - unrelated to the live Postgres reads above)."""
from __future__ import annotations

from langchain_core.tools import tool

from agents.documentation_agent.documentation_prompt import DOCUMENTATION_PROMPT
from agents.utils.agent_utils import documentation_agent_tools
from core.agent import get_or_create
from db.models import DatabaseConnection
from services import business_docs_service
from services.rag import rag_retriever


def _build_search_tool(connection: DatabaseConnection, llm_credentials: dict):
    @tool
    async def search_business_docs(query: str) -> str:
        """Look up Postgres-native business documentation (COMMENT ON TABLE / COMMENT ON
        COLUMN text) for tables/columns relevant to this question. Always call this
        before answering questions about what a table or column means/is used for."""
        results = await business_docs_service.search_documentation(connection, query, llm_credentials)
        if not results:
            return "No matching table found for this question, and/or no COMMENT ON TABLE/COLUMN documentation exists for it."
        lines = []
        for info in results:
            table_name = info.get("table_name")
            table_comment = info.get("table_comment")
            lines.append(f"Table: {table_name} - {table_comment if table_comment else '(no table-level comment set)'}")
            for col in info.get("columns", []) or []:
                comment = col.get("comment")
                if comment:
                    lines.append(f"  - column {col.get('column_name')}: {comment}")
        return "\n".join(lines)

    return search_business_docs


def _build_uploaded_docs_tool(connection: DatabaseConnection, user_id: int):
    @tool
    def search_uploaded_docs(query: str) -> str:
        """Search documentation the user has uploaded for this database connection
        (.sql files and images like ER diagrams/schema screenshots). Call this when
        the live Postgres comments don't answer the question, or when the user refers
        to something they uploaded."""
        results = rag_retriever.retrieve_context(query, connection.id, user_id)
        if not results:
            return "No relevant uploaded documentation found for this question."
        return "\n\n".join(f"(from {r.get('source')}, relevance {r['score']:.2f}):\n{r['text']}" for r in results)

    return search_uploaded_docs


async def build_agent(*, user_id: int, connection: DatabaseConnection, llm_config_id: int, llm_credentials: dict):
    search_tool = _build_search_tool(connection, llm_credentials)
    uploaded_docs_tool = _build_uploaded_docs_tool(connection, user_id)
    return await get_or_create(
        user_id=user_id,
        connection=connection,
        llm_config_id=llm_config_id,
        llm_credentials=llm_credentials,
        intent="documentation",
        tool_filter_fn=documentation_agent_tools,
        system_prompt=DOCUMENTATION_PROMPT,
        extra_tools=[search_tool, uploaded_docs_tool],
    )

