"""CRUD endpoints for customer Postgres database connections + on-demand metrics."""
from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.models import User
from db.database import get_db
from models.database_schemas import (
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseConnectionUpdate,
    DatabaseMetrics,
    TestConnectionResult,
)
from services import db_connection_service, mcp_client_service
from services.auth_service import get_current_user

router = APIRouter(prefix="/database-connections", tags=["database-connections"])


@router.post("", response_model=DatabaseConnectionResponse, status_code=201)
def create_database_connection(
    payload: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatabaseConnectionResponse:
    conn = db_connection_service.create_connection(db, current_user.id, payload)
    ok, message = db_connection_service.test_connection(conn)
    if not ok:
        # Only keep reachable databases: discard the just-created row so an
        # unreachable database never shows up as a card.
        db_connection_service.delete_connection(db, current_user.id, conn.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not connect to database: {message}")
    conn.last_checked_at = datetime.datetime.now(datetime.timezone.utc)
    conn.last_check_status = "ok"
    db.commit()
    db.refresh(conn)
    return DatabaseConnectionResponse.model_validate(conn)


@router.get("", response_model=list[DatabaseConnectionResponse])
def list_database_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DatabaseConnectionResponse]:
    conns = db_connection_service.list_connections(db, current_user.id)
    return [DatabaseConnectionResponse.model_validate(c) for c in conns]


@router.get("/{connection_id}", response_model=DatabaseConnectionResponse)
def get_database_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatabaseConnectionResponse:
    conn = db_connection_service.get_connection(db, current_user.id, connection_id)
    return DatabaseConnectionResponse.model_validate(conn)


@router.put("/{connection_id}", response_model=DatabaseConnectionResponse)
def update_database_connection(
    connection_id: int,
    payload: DatabaseConnectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatabaseConnectionResponse:
    conn = db_connection_service.update_connection(db, current_user.id, connection_id, payload)
    mcp_client_service.evict(conn.id)
    return DatabaseConnectionResponse.model_validate(conn)


@router.delete("/{connection_id}", status_code=204, response_model=None)
def delete_database_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    db_connection_service.delete_connection(db, current_user.id, connection_id)
    mcp_client_service.evict(connection_id)


@router.post("/{connection_id}/test", response_model=TestConnectionResult)
def test_database_connection(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TestConnectionResult:
    conn = db_connection_service.get_connection(db, current_user.id, connection_id)
    ok, message = db_connection_service.test_connection(conn)
    conn.last_checked_at = datetime.datetime.now(datetime.timezone.utc)
    conn.last_check_status = "ok" if ok else "error"
    db.commit()
    return TestConnectionResult(success=ok, message=message)


@router.get("/{connection_id}/metrics", response_model=DatabaseMetrics)
async def get_database_metrics(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatabaseMetrics:
    conn = db_connection_service.get_connection(db, current_user.id, connection_id)
    try:
        result = await mcp_client_service.call_tool(conn, "get_db_metrics", {})
        disk_result = await mcp_client_service.call_tool(conn, "get_disk_usage", {})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"MCP metrics call failed: {exc}") from exc

    return DatabaseMetrics(
        cpu_usage_approx_pct=result.get("cpu_usage_approx_pct"),
        memory_cache_hit_ratio_pct=result.get("memory_cache_hit_ratio_pct"),
        disk_io_blocks_read_per_sec=result.get("disk_io_blocks_read_per_sec"),
        disk_io_buffers_written_per_sec=result.get("disk_io_buffers_written_per_sec"),
        disk_usage_bytes=disk_result.get("disk_usage_bytes"),
        transactions_per_sec=result.get("transactions_per_sec"),
        active_connections=result.get("active_connections"),
        total_connections=result.get("total_connections"),
        max_connections=result.get("max_connections"),
        largest_tables=disk_result.get("largest_tables") or [],
        fetched_at=datetime.datetime.now(datetime.timezone.utc),
    )
