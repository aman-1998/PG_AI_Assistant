"""CRUD for customer Postgres database connections + connection-token builder.

The connection token is an AES-encrypted, expiring JSON payload containing the
raw connection parameters needed by text_to_sql_mcp to open a psycopg2
connection. It is sent as a request header (X-DB-Conn-Token) on every MCP
tool call so the MCP server can remain fully stateless with respect to the
control plane (it never talks to the control-plane Postgres store).
"""
from __future__ import annotations

import datetime
import json

import psycopg2
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import DatabaseConnection
from models.database_schemas import DatabaseConnectionCreate, DatabaseConnectionUpdate
from services.encryption_util import decrypt_text, encrypt_text


def create_connection(db: Session, user_id: int, payload: DatabaseConnectionCreate) -> DatabaseConnection:
    existing = (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.user_id == user_id, DatabaseConnection.alias == payload.alias)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Alias already in use")

    conn = DatabaseConnection(
        user_id=user_id,
        alias=payload.alias,
        host=payload.host,
        port=payload.port,
        db_name=payload.db_name,
        username=payload.username,
        encrypted_password=encrypt_text(payload.password, settings.DATA_ENCRYPTION_KEY),
        sslmode=payload.sslmode,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def list_connections(db: Session, user_id: int) -> list[DatabaseConnection]:
    return db.query(DatabaseConnection).filter(DatabaseConnection.user_id == user_id).order_by(DatabaseConnection.created_at).all()


def get_connection(db: Session, user_id: int, connection_id: int) -> DatabaseConnection:
    conn = (
        db.query(DatabaseConnection)
        .filter(DatabaseConnection.id == connection_id, DatabaseConnection.user_id == user_id)
        .first()
    )
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found")
    return conn


def update_connection(
    db: Session, user_id: int, connection_id: int, payload: DatabaseConnectionUpdate
) -> DatabaseConnection:
    conn = get_connection(db, user_id, connection_id)
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("password", None)
    for field, value in data.items():
        setattr(conn, field, value)
    if password:
        conn.encrypted_password = encrypt_text(password, settings.DATA_ENCRYPTION_KEY)
    db.commit()
    db.refresh(conn)
    return conn


def delete_connection(db: Session, user_id: int, connection_id: int) -> None:
    conn = get_connection(db, user_id, connection_id)
    db.delete(conn)
    db.commit()


def _decrypted_password(conn: DatabaseConnection) -> str:
    return decrypt_text(conn.encrypted_password, settings.DATA_ENCRYPTION_KEY)


def test_connection(conn: DatabaseConnection, timeout_seconds: int = 5) -> tuple[bool, str]:
    """Attempt a short-lived psycopg2 connection to validate the stored credentials."""
    try:
        pg_conn = psycopg2.connect(
            host=conn.host,
            port=conn.port,
            dbname=conn.db_name,
            user=conn.username,
            password=_decrypted_password(conn),
            sslmode=conn.sslmode,
            connect_timeout=timeout_seconds,
        )
        pg_conn.close()
        return True, "Connection successful"
    except Exception as exc:  # noqa: BLE001 - surface the underlying reason to the caller
        return False, str(exc)


def build_connection_token(conn: DatabaseConnection) -> str:
    """Build the encrypted, short-TTL token passed to text_to_sql_mcp per request."""
    expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        seconds=settings.DB_CONNECTION_TOKEN_TTL_SECONDS
    )
    payload = {
        "host": conn.host,
        "port": conn.port,
        "dbname": conn.db_name,
        "user": conn.username,
        "password": _decrypted_password(conn),
        "sslmode": conn.sslmode,
        "connection_id": conn.id,
        "exp": expires_at.isoformat(),
    }
    return encrypt_text(json.dumps(payload), settings.DB_CONNECTION_TOKEN_SECRET)
