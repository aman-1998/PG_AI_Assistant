"""Intent classification + agent routing, mirroring ai-service/core/orchestrator.py."""
from __future__ import annotations

from agents.default_fallback_agent import fallback_agent
from agents.documentation_agent import documentation_agent
from agents.explainplan_agent import explainplan_agent
from agents.optimization_agent import optimization_agent
from agents.sql_agent import sqlgeneration_agent
from db.models import DatabaseConnection
from services.llm_factory import get_llm_from_credentials

VALID_INTENTS = {"sql_generation", "explain_plan", "optimization", "documentation", "general"}

_AGENT_BUILDERS = {
    "sql_generation": sqlgeneration_agent.build_agent,
    "explain_plan": explainplan_agent.build_agent,
    "optimization": optimization_agent.build_agent,
    "documentation": documentation_agent.build_agent,
    "general": fallback_agent.build_agent,
}

_CLASSIFIER_PROMPT = """Classify the user's latest message into exactly one of these intents:
- sql_generation: browsing schema, generating/running SELECT/INSERT/UPDATE/DELETE/CREATE/ALTER/DROP SQL;
  ALSO any request for a visual/ER (Entity-Relationship) diagram or schema diagram of tables
  (e.g. "give me an ER diagram for the public schema", "show me a diagram of tables t1, t2, t3",
  "visualize the schema") - these must be classified as sql_generation, NOT documentation;
  ALSO any request for the DDL/definition/"create query"/"create statement" of a table, view,
  function, procedure, trigger, sequence, or index (e.g. "give me the DDL for table customers",
  "show me the definition of procedure add_two_nums") - these must be classified as
  sql_generation, NOT documentation
- explain_plan: asking to explain/show a query's execution plan
- optimization: asking to optimize/speed up a query, or asking about indexes for performance
- documentation: general PostgreSQL concept/how-to questions; questions about the business
  meaning/purpose of the user's own tables or columns (e.g. "what is the products table for",
  "what does the items column mean", "tell me about the configuration schema") - but NOT
  requests for a visual/ER diagram or an object's DDL/definition, which are sql_generation; greetings/
  small talk/casual conversation (e.g. "hi", "I'm bored", "how are you"); or any other
  question unrelated to databases/SQL/this application (e.g. "how is the weather", "tell me
  a joke", general trivia)
- general: anything else / unclear

Respond with ONLY the intent keyword, nothing else.

Conversation history (most recent last):
{history}

User message: {message}
"""


async def classify_intent(message: str, history: list[dict], llm_credentials: dict) -> str:
    llm = get_llm_from_credentials(llm_credentials)
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    prompt = _CLASSIFIER_PROMPT.format(history=history_text, message=message)
    response = await llm.ainvoke(prompt)
    raw = (response.content or "").strip().lower()
    for intent in VALID_INTENTS:
        if intent in raw:
            return intent
    return "general"


async def resolve_intent(
    *, explicit_intent: str | None, message: str, history: list[dict], llm_credentials: dict
) -> str:
    if explicit_intent and explicit_intent in VALID_INTENTS:
        return explicit_intent
    return await classify_intent(message, history, llm_credentials)


async def get_agent_for_intent(
    *,
    intent: str,
    user_id: int,
    connection: DatabaseConnection,
    llm_config_id: int,
    llm_credentials: dict,
):
    builder = _AGENT_BUILDERS.get(intent, fallback_agent.build_agent)
    return await builder(
        user_id=user_id, connection=connection, llm_config_id=llm_config_id, llm_credentials=llm_credentials
    )
