"""Thin wrapper that builds a ReAct agent with access to all MCP tools (fallback)."""
from __future__ import annotations

from agents.default_fallback_agent.fallbackagent_prompt import FALLBACK_PROMPT
from agents.utils.agent_utils import fallback_agent_tools
from core.agent import get_or_create
from db.models import DatabaseConnection


async def build_agent(*, user_id: int, connection: DatabaseConnection, llm_config_id: int, llm_credentials: dict):
    return await get_or_create(
        user_id=user_id,
        connection=connection,
        llm_config_id=llm_config_id,
        llm_credentials=llm_credentials,
        intent="general",
        tool_filter_fn=fallback_agent_tools,
        system_prompt=FALLBACK_PROMPT,
    )
