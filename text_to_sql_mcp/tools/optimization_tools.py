"""Query optimization tools: index listing + heuristic optimization suggestions."""
from db_utils import fetch_all
from mcp_instance import mcp
from security import classify_statement


@mcp.tool()
def list_indexes(table_name: str, schema: str = "public") -> list[dict]:
    """List indexes defined on a table (name, definition, uniqueness)."""
    sql = """
        SELECT
            i.relname AS index_name,
            idx.indisunique AS is_unique,
            idx.indisprimary AS is_primary,
            pg_get_indexdef(idx.indexrelid) AS index_definition
        FROM pg_index idx
        JOIN pg_class i ON i.oid = idx.indexrelid
        JOIN pg_class t ON t.oid = idx.indrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE t.relname = %s AND n.nspname = %s
        ORDER BY i.relname
    """
    return fetch_all(sql, (table_name, schema))


@mcp.tool()
def optimize_query(sql: str) -> dict:
    """Analyze a query's EXPLAIN plan and pg_stat_statements history (if the
    pg_stat_statements extension is installed) and return heuristic optimization
    suggestions (missing indexes on filter/join columns, sequential scans on
    large tables, use of SELECT *, etc.).
    """
    statement_kind = classify_statement(sql)
    if statement_kind not in ("DQL", "OTHER"):
        return {"error": f"optimize_query only supports read statements; detected '{statement_kind}'."}

    plan_rows = fetch_all(f"EXPLAIN (FORMAT JSON) {sql}")
    plan = plan_rows[0]["QUERY PLAN"][0] if plan_rows else None

    suggestions: list[str] = []
    plan_text = str(plan)
    if "Seq Scan" in plan_text:
        suggestions.append(
            "Sequential scan detected - consider adding an index on the filter/join columns "
            "used by the scanned table."
        )
    if "select *" in sql.lower() or "select  *" in sql.lower():
        suggestions.append("Avoid SELECT * - list only the columns you need to reduce I/O.")
    if "Sort" in plan_text and "index" not in plan_text.lower():
        suggestions.append("An explicit Sort step was found - an index matching the ORDER BY clause may avoid it.")

    stats_rows: list[dict] = []
    try:
        stats_rows = fetch_all(
            """
            SELECT calls, total_exec_time, mean_exec_time, rows
            FROM pg_stat_statements
            WHERE query = %s
            LIMIT 1
            """,
            (sql,),
        )
    except Exception:  # noqa: BLE001 - extension may not be installed/enabled
        stats_rows = []

    if not suggestions:
        suggestions.append("No obvious issues detected from the plan shape; consider reviewing selectivity of filters.")

    return {
        "plan": plan,
        "pg_stat_statements": stats_rows[0] if stats_rows else None,
        "suggestions": suggestions,
    }
