"""Thin wrapper that builds a ReAct agent scoped to the explain_plan tool."""
from __future__ import annotations

from agents.explainplan_agent.explainplan_prompt import EXPLAIN_PLAN_PROMPT
from agents.utils.agent_utils import explainplan_agent_tools
from core.agent import get_or_create
from db.models import DatabaseConnection


async def build_agent(*, user_id: int, connection: DatabaseConnection, llm_config_id: int, llm_credentials: dict):
    return await get_or_create(
        user_id=user_id,
        connection=connection,
        llm_config_id=llm_config_id,
        llm_credentials=llm_credentials,
        intent="explain_plan",
        tool_filter_fn=explainplan_agent_tools,
        system_prompt=EXPLAIN_PLAN_PROMPT,
    )
