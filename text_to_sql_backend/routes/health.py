"""Health/readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from db.database import engine

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz() -> dict:
    return {"service": "text_to_sql_backend", "status": "ok"}


@router.get("/readyz")
def readyz() -> dict:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"service": "text_to_sql_backend", "status": "ready"}
    except Exception as exc:  # noqa: BLE001
        return {"service": "text_to_sql_backend", "status": "not_ready", "error": str(exc)}
