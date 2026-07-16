"""Wrapper around langchain-mcp-adapters MultiServerMCPClient for the single
text_to_sql_mcp server. Mirrors ai-service/services/mcp_manager.py's caching
pattern, adapted to a single fixed MCP server URL with a per-connection
encrypted header (X-DB-Conn-Token) instead of per-cluster YAML config.
"""
from __future__ import annotations

import ast
import json
import time
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from config.settings import settings
from db.models import DatabaseConnection
from services.db_connection_service import build_connection_token

_CACHE_TTL_SECONDS = 3600
_client_cache: dict[int, dict[str, Any]] = {}  # connection_id -> {"client":..., "tools":..., "ts":...}


def _try_parse(value: Any) -> Any:
    """MCP tools that return dicts/lists often come back through `ainvoke` as
    serialized text rather than a parsed object - and depending on the server's
    serialization, that text may be valid JSON or a Python literal (single
    quotes, None/True/False) e.g. when a tool returns rows straight from a
    DB driver. Try both before giving up and returning the raw string."""
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        pass
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def _build_client(conn: DatabaseConnection) -> MultiServerMCPClient:
    token = build_connection_token(conn)
    config = {
        "postgres": {
            "url": settings.MCP_SERVER_URL,
            "transport": "streamable_http",
            "headers": {"X-DB-Conn-Token": token},
        }
    }
    return MultiServerMCPClient(config)


async def get_tools(conn: DatabaseConnection, force_refresh: bool = False) -> list:
    """Return the cached list of LangChain tool objects for a database connection."""
    cached = _client_cache.get(conn.id)
    now = time.time()
    if not force_refresh and cached and (now - cached["ts"]) < _CACHE_TTL_SECONDS:
        return cached["tools"]

    client = _build_client(conn)
    tools = await client.get_tools()
    _client_cache[conn.id] = {"client": client, "tools": tools, "ts": now}
    return tools


async def call_tool(conn: DatabaseConnection, tool_name: str, tool_args: dict) -> Any:
    """Invoke a single MCP tool directly (outside of the agent loop), e.g. for
    dashboard metrics refresh."""
    tools = await get_tools(conn)
    for tool in tools:
        if getattr(tool, "name", None) == tool_name:
            result = await tool.ainvoke(tool_args)
            parsed = _try_parse(result)
            if isinstance(parsed, list):
                return [_try_parse(item) for item in parsed]
            return parsed
    raise ValueError(f"MCP tool '{tool_name}' not found for connection {conn.id}")


def evict(connection_id: int) -> None:
    _client_cache.pop(connection_id, None)


def clear_all() -> None:
    _client_cache.clear()
