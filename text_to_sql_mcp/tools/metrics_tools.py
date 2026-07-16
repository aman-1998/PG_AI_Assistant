"""Approximate DB health/metrics tools, computed purely from Postgres-native
statistics views (no OS-level access). Two snapshots ~1s apart are used to
compute per-second deltas/rates. See text_to_sql_backend's DatabaseMetrics
schema for how these values are surfaced on the dashboard cards.
"""
import time

from db_utils import fetch_all
from mcp_instance import mcp


def _bgwriter_buffers_written() -> int:
    """Total buffers written by checkpointer/bgwriter/backends.

    Postgres 17 split pg_stat_bgwriter: checkpoint stats moved to
    pg_stat_checkpointer (buffers_written) and backend-fsync stats moved out
    entirely, while buffers_clean stayed on pg_stat_bgwriter. Older versions
    (<17) keep buffers_checkpoint/buffers_clean/buffers_backend all on
    pg_stat_bgwriter. Detect available columns/views dynamically so this
    works across Postgres versions.
    """
    total = 0
    bgwriter_cols = fetch_all(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'pg_catalog' AND table_name = 'pg_stat_bgwriter'"
    )
    colnames = {c["column_name"] for c in bgwriter_cols}
    wanted = [c for c in ("buffers_checkpoint", "buffers_clean", "buffers_backend") if c in colnames]
    if wanted:
        row = fetch_all(f"SELECT {', '.join(wanted)} FROM pg_stat_bgwriter")[0]
        total += sum(v for v in row.values() if v)

    checkpointer_exists = fetch_all(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = 'pg_catalog' AND table_name = 'pg_stat_checkpointer'"
    )
    if checkpointer_exists:
        cp_rows = fetch_all("SELECT buffers_written FROM pg_stat_checkpointer")
        if cp_rows:
            total += cp_rows[0]["buffers_written"] or 0
    return total


def _snapshot() -> dict:
    db_stats = fetch_all(
        "SELECT xact_commit, xact_rollback, blks_read, blks_hit "
        "FROM pg_stat_database WHERE datname = current_database()"
    )[0]
    buffers_written = _bgwriter_buffers_written()
    return {
        "ts": time.perf_counter(),
        "xact_total": db_stats["xact_commit"] + db_stats["xact_rollback"],
        "blks_read": db_stats["blks_read"],
        "blks_hit": db_stats["blks_hit"],
        "buffers_written": buffers_written,
    }


@mcp.tool()
def get_db_metrics(sample_interval_seconds: float = 1.0) -> dict:
    """Return approximate CPU/Memory/Disk-I/O metrics for the connected database.

    All values are proxies derived from Postgres statistics views:
      - cpu_usage_approx_pct: active backends as a % of max_connections (load proxy)
      - memory_cache_hit_ratio_pct: shared_buffers cache hit ratio over the sample window
      - disk_io_blocks_read_per_sec / disk_io_buffers_written_per_sec: I/O rate over the sample window
      - active_connections: current backend count in 'active' state
    """
    before = _snapshot()
    time.sleep(max(0.1, min(sample_interval_seconds, 5.0)))
    after = _snapshot()
    elapsed = max(after["ts"] - before["ts"], 0.001)

    delta_xact = after["xact_total"] - before["xact_total"]
    delta_read = after["blks_read"] - before["blks_read"]
    delta_hit = after["blks_hit"] - before["blks_hit"]
    delta_written = after["buffers_written"] - before["buffers_written"]

    if (delta_hit + delta_read) > 0:
        cache_hit_ratio = (delta_hit / (delta_hit + delta_read)) * 100
    else:
        cache_hit_ratio = None

    activity = fetch_all(
        "SELECT count(*) FILTER (WHERE state = 'active') AS active_connections, "
        "count(*) AS total_connections FROM pg_stat_activity WHERE datname = current_database()"
    )[0]
    max_conn_row = fetch_all("SHOW max_connections")
    max_connections = int(max_conn_row[0]["max_connections"]) if max_conn_row else None

    cpu_usage_approx_pct = None
    if max_connections:
        cpu_usage_approx_pct = round(min(100.0, (activity["active_connections"] / max_connections) * 100), 2)

    return {
        "cpu_usage_approx_pct": cpu_usage_approx_pct,
        "memory_cache_hit_ratio_pct": round(cache_hit_ratio, 2) if cache_hit_ratio is not None else None,
        "disk_io_blocks_read_per_sec": round(delta_read / elapsed, 2),
        "disk_io_buffers_written_per_sec": round(delta_written / elapsed, 2),
        "transactions_per_sec": round(delta_xact / elapsed, 2),
        "active_connections": activity["active_connections"],
        "total_connections": activity["total_connections"],
        "max_connections": max_connections,
    }


@mcp.tool()
def get_disk_usage() -> dict:
    """Return the current database's on-disk size and its 10 largest tables."""
    db_size = fetch_all("SELECT pg_database_size(current_database()) AS size_bytes")[0]
    largest_tables = fetch_all(
        """
        SELECT
            schemaname || '.' || relname AS table_name,
            pg_total_relation_size(relid) AS size_bytes
        FROM pg_catalog.pg_statio_user_tables
        ORDER BY pg_total_relation_size(relid) DESC
        LIMIT 10
        """
    )
    return {"disk_usage_bytes": db_size["size_bytes"], "largest_tables": largest_tables}
