"""Per-agent tool-name allow-lists, mirroring ai-service/agents/utils/agent_utils.py.

Tool names must exactly match the @mcp.tool() function names registered in
text_to_sql_mcp/tools/*.py.
"""
from __future__ import annotations

# Shared response-formatting guidance appended to every agent's system prompt, so
# replies look like a polished chat UI (bold section headers, bullet lists) instead
# of dense paragraphs.
FORMATTING_GUIDELINES = """

## Formatting
- Structure your reply with bold markdown section headers (e.g. **Summary**,
  **Suggestions**, **Next steps**) instead of one long paragraph.
- Prefer bullet points over dense prose whenever listing multiple items (tables,
  findings, suggestions, steps).
- Keep each section short and scannable; still use fenced code blocks for SQL/plans
  as instructed above.
"""

_SQL_AGENT_TOOLS = frozenset(
    {
        "list_schemas",
        "list_tables",
        "describe_table",
        "execute_query",
        "execute_ddl_dml",
        "get_query_execution_time",
        "list_indexes",
        "export_query_to_csv",
        "export_query_to_json",
        "generate_er_diagram",
        "get_object_ddl",
    }
)

_OPTIMIZATION_AGENT_TOOLS = frozenset(
    {
        "optimize_query",
        "list_indexes",
        "get_query_execution_time",
        "explain_plan",
    }
)

_EXPLAINPLAN_AGENT_TOOLS = frozenset({"explain_plan"})

_DOCUMENTATION_AGENT_TOOLS: frozenset[str] = frozenset({"list_tables", "get_table_comments"})


def _filter(tools: list, allowed: frozenset[str]) -> list:
    return [t for t in tools if getattr(t, "name", None) in allowed]


def sql_agent_tools(tools: list) -> list:
    return _filter(tools, _SQL_AGENT_TOOLS)


def optimization_agent_tools(tools: list) -> list:
    return _filter(tools, _OPTIMIZATION_AGENT_TOOLS)


def explainplan_agent_tools(tools: list) -> list:
    return _filter(tools, _EXPLAINPLAN_AGENT_TOOLS)


def documentation_agent_tools(tools: list) -> list:
    return _filter(tools, _DOCUMENTATION_AGENT_TOOLS)


def fallback_agent_tools(tools: list) -> list:
    return tools
