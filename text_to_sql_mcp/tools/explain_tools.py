"""EXPLAIN plan tool."""
from db_utils import fetch_all
from mcp_instance import mcp
from security import classify_statement


@mcp.tool()
def explain_plan(sql: str, analyze: bool = True) -> dict:
    """Return the Postgres query plan for a SQL statement.

    Uses EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) by default (analyze=True), which
    actually executes the query to gather real timing/row-count data. Pass
    analyze=False to get an estimate-only plan without executing the statement
    (safer for DDL/DML-adjacent or expensive queries).
    """
    statement_kind = classify_statement(sql)
    if statement_kind not in ("DQL", "OTHER"):
        return {"error": f"explain_plan only supports read statements; detected '{statement_kind}'."}

    options = "ANALYZE, BUFFERS, FORMAT JSON" if analyze else "FORMAT JSON"
    plan_sql = f"EXPLAIN ({options}) {sql}"
    rows = fetch_all(plan_sql)
    plan = rows[0]["QUERY PLAN"] if rows else None
    return {"analyze": analyze, "plan": plan}
