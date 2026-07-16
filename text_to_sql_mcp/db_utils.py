"""Small shared helpers for executing SQL against the pooled connection and
shaping results as JSON-serializable dicts/lists.
"""
from __future__ import annotations

import datetime
import decimal
from typing import Any

import psycopg2.extras

from config import settings
from connection import get_connection


def _truncate(text: str) -> str:
    limit = settings.MAX_CELL_CHARS
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated, {len(text) - limit} more characters]"


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (bytes, bytearray, memoryview)):
        return _truncate(bytes(value).hex())
    if isinstance(value, str):
        return _truncate(value)
    return value


def fetch_all(sql: str, params: tuple | None = None, row_limit: int | None = None) -> list[dict]:
    """Run a read query and return up to `row_limit` rows as a list of dicts."""
    limit = row_limit or settings.MAX_ROWS_RETURNED
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"SET statement_timeout = {settings.QUERY_TIMEOUT_SECONDS * 1000}")
            cur.execute(sql, params)
            rows = cur.fetchmany(limit) if cur.description is not None else []
            return [{k: _json_safe(v) for k, v in row.items()} for row in rows]


def execute_statement(sql: str, params: tuple | None = None) -> dict:
    """Run a DDL/DML statement (autocommit) and return status/rowcount."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SET statement_timeout = {settings.QUERY_TIMEOUT_SECONDS * 1000}")
            cur.execute(sql, params)
            return {"status": cur.statusmessage, "rowcount": cur.rowcount}
