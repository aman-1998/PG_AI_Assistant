"""Build (and cache) a LangGraph ReAct agent per (user, database connection,
LLM config, intent). Mirrors ai-service/core/agent.py's get_or_create() pattern.
"""
from __future__ import annotations

import time
from typing import Any, Callable

from langgraph.prebuilt import create_react_agent

from db.models import DatabaseConnection
from services import mcp_client_service
from services.llm_factory import get_llm_from_credentials

_AGENT_CACHE_TTL_SECONDS = 3600
_agent_cache: dict[str, dict[str, Any]] = {}


def _cache_key(user_id: int, connection_id: int, llm_config_id: int, intent: str) -> str:
    return f"{intent}|{user_id}|{connection_id}|{llm_config_id}"


async def get_or_create(
    *,
    user_id: int,
    connection: DatabaseConnection,
    llm_config_id: int,
    llm_credentials: dict,
    intent: str,
    tool_filter_fn: Callable[[list], list],
    system_prompt: str,
    extra_tools: list | None = None,
):
    """Return a cached ReAct agent, creating one if absent/expired."""
    key = _cache_key(user_id, connection.id, llm_config_id, intent)
    now = time.time()
    cached = _agent_cache.get(key)
    if cached and (now - cached["ts"]) < _AGENT_CACHE_TTL_SECONDS:
        return cached["agent"]

    all_tools = await mcp_client_service.get_tools(connection)
    tools = tool_filter_fn(all_tools) + list(extra_tools or [])
    llm = get_llm_from_credentials(llm_credentials)

    agent = create_react_agent(model=llm, tools=tools, prompt=system_prompt)
    _agent_cache[key] = {"agent": agent, "ts": now}
    return agent


def clear_cache() -> None:
    _agent_cache.clear()
