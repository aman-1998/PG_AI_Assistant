"""Postgres connection pooling, keyed by the decrypted per-request connection
params (host/port/dbname/user/password/sslmode). Each distinct customer
database gets its own small pool; pools are evicted after CONNECTION_POOL_TTL_SECONDS
of inactivity, mirroring the reference app's MCP client cache pattern.
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

from config import settings
from context import get_current_connection_params

_pools: dict[str, dict] = {}
_lock = threading.Lock()


def _pool_key(params: dict) -> str:
    fingerprint = {
        "host": params["host"],
        "port": params["port"],
        "dbname": params["dbname"],
        "user": params["user"],
        "sslmode": params.get("sslmode", "prefer"),
    }
    return hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode("utf-8")).hexdigest()


def _evict_stale_pools() -> None:
    now = time.time()
    stale_keys = [
        key
        for key, entry in _pools.items()
        if (now - entry["ts"]) > settings.CONNECTION_POOL_TTL_SECONDS
    ]
    for key in stale_keys:
        entry = _pools.pop(key)
        try:
            entry["pool"].closeall()
        except Exception:  # noqa: BLE001
            pass


def _get_pool(params: dict) -> ThreadedConnectionPool:
    key = _pool_key(params)
    with _lock:
        _evict_stale_pools()
        entry = _pools.get(key)
        if entry is not None:
            entry["ts"] = time.time()
            return entry["pool"]

        pool = ThreadedConnectionPool(
            minconn=1,
            maxconn=5,
            host=params["host"],
            port=params["port"],
            dbname=params["dbname"],
            user=params["user"],
            password=params["password"],
            sslmode=params.get("sslmode", "prefer"),
            connect_timeout=settings.QUERY_TIMEOUT_SECONDS,
        )
        _pools[key] = {"pool": pool, "ts": time.time()}
        return pool


@contextmanager
def get_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Yield a pooled psycopg2 connection for the current request's target DB."""
    params = get_current_connection_params()
    pool = _get_pool(params)
    conn = pool.getconn()
    try:
        conn.autocommit = True
        yield conn
    finally:
        pool.putconn(conn)


def close_all_pools() -> None:
    with _lock:
        for entry in _pools.values():
            try:
                entry["pool"].closeall()
            except Exception:  # noqa: BLE001
                pass
        _pools.clear()
