"""Query execution tools: DQL (SELECT), DDL/DML (CREATE/ALTER/DROP/INSERT/UPDATE/DELETE),
and execution-time measurement. Executed directly with no confirmation step."""
import time

from db_utils import execute_statement, fetch_all
from mcp_instance import mcp
from security import classify_statement


@mcp.tool()
def execute_query(sql: str) -> dict:
    """Execute a read-only (DQL) SQL statement and return the result rows.

    Rows are capped (see MAX_ROWS_RETURNED) to avoid overwhelming the model/response.
    """
    statement_kind = classify_statement(sql)
    if statement_kind not in ("DQL", "OTHER"):
        return {
            "error": f"execute_query only accepts read (SELECT/WITH) statements; "
            f"detected '{statement_kind}'. Use execute_ddl_dml instead."
        }
    rows = fetch_all(sql)
    return {"row_count": len(rows), "rows": rows}


@mcp.tool()
def execute_ddl_dml(sql: str) -> dict:
    """Execute a DDL (CREATE/ALTER/DROP/TRUNCATE) or DML (INSERT/UPDATE/DELETE) statement.

    Executes immediately (autocommit) with no confirmation step. Returns the
    server status message and affected row count.
    """
    statement_kind = classify_statement(sql)
    result = execute_statement(sql)
    result["statement_kind"] = statement_kind
    return result


@mcp.tool()
def get_query_execution_time(sql: str) -> dict:
    """Measure wall-clock execution time (ms) of a SQL statement.

    For DQL statements the query is actually executed (rows are fetched but not
    returned, only counted) so timing reflects real execution + fetch.
    """
    statement_kind = classify_statement(sql)
    start = time.perf_counter()
    if statement_kind == "DQL" or statement_kind == "OTHER":
        rows = fetch_all(sql)
        row_count = len(rows)
    else:
        result = execute_statement(sql)
        row_count = result.get("rowcount", 0)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {"statement_kind": statement_kind, "elapsed_ms": round(elapsed_ms, 2), "row_count": row_count}
