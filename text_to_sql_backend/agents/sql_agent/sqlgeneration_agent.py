"""Thin wrapper that builds a ReAct agent scoped to SQL-generation tools."""
from __future__ import annotations

from agents.sql_agent.sqlgeneration_prompt import SQL_GENERATION_PROMPT
from agents.utils.agent_utils import sql_agent_tools
from core.agent import get_or_create
from db.models import DatabaseConnection


async def build_agent(*, user_id: int, connection: DatabaseConnection, llm_config_id: int, llm_credentials: dict):
    return await get_or_create(
        user_id=user_id,
        connection=connection,
        llm_config_id=llm_config_id,
        llm_credentials=llm_credentials,
        intent="sql_generation",
        tool_filter_fn=sql_agent_tools,
        system_prompt=SQL_GENERATION_PROMPT,
    )
