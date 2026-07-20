"""Pydantic schemas for customer Postgres database connections."""
from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class DatabaseConnectionCreate(BaseModel):
    alias: str = Field(min_length=1, max_length=120)
    host: str
    port: int = 5432
    db_name: str
    username: str
    password: str
    sslmode: str = "prefer"


class DatabaseConnectionUpdate(BaseModel):
    alias: str | None = None
    host: str | None = None
    port: int | None = None
    db_name: str | None = None
    username: str | None = None
    password: str | None = None
    sslmode: str | None = None
    is_active: bool | None = None


class DatabaseConnectionResponse(BaseModel):
    id: int
    alias: str
    host: str
    port: int
    db_name: str
    username: str
    sslmode: str
    is_active: bool
    last_checked_at: datetime.datetime | None = None
    last_check_status: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class LargestTable(BaseModel):
    table_name: str
    size_bytes: int


class DatabaseMetrics(BaseModel):
    """Approximate, Postgres-native metrics (no OS-level access)."""

    cpu_usage_approx_pct: float | None = None
    cpu_usage_note: str = "Approximated from active backend count + transaction rate (no OS-level CPU access)"
    memory_cache_hit_ratio_pct: float | None = None
    memory_usage_note: str = "Approximated via shared_buffers cache hit ratio (blks_hit / (blks_hit+blks_read))"
    disk_io_blocks_read_per_sec: float | None = None
    disk_io_buffers_written_per_sec: float | None = None
    disk_io_note: str = "Approximated from pg_stat_database / pg_stat_bgwriter deltas over ~1s"
    disk_usage_bytes: int | None = None
    transactions_per_sec: float | None = None
    active_connections: int | None = None
    total_connections: int | None = None
    max_connections: int | None = None
    largest_tables: list[LargestTable] = Field(default_factory=list)
    fetched_at: datetime.datetime


class TestConnectionResult(BaseModel):
    success: bool
    message: str
