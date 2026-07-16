"""Thin wrapper that builds a ReAct agent scoped to query-optimization tools."""
from __future__ import annotations

from agents.optimization_agent.optimization_prompt import OPTIMIZATION_PROMPT
from agents.utils.agent_utils import optimization_agent_tools
from core.agent import get_or_create
from db.models import DatabaseConnection


async def build_agent(*, user_id: int, connection: DatabaseConnection, llm_config_id: int, llm_credentials: dict):
    return await get_or_create(
        user_id=user_id,
        connection=connection,
        llm_config_id=llm_config_id,
        llm_credentials=llm_credentials,
        intent="optimization",
        tool_filter_fn=optimization_agent_tools,
        system_prompt=OPTIMIZATION_PROMPT,
    )
