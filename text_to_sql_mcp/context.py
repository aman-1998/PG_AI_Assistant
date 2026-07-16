"""Per-request connection-token propagation.

Streamable HTTP MCP tool calls arrive as plain HTTP requests. A thin Starlette
middleware extracts the `X-DB-Conn-Token` header before the request reaches
the MCP ASGI app and stores the decoded connection params in a contextvar so
tool functions (which have no direct access to the raw HTTP request) can read
which customer Postgres database to talk to.
"""
from __future__ import annotations

import contextvars

from starlette.types import ASGIApp, Receive, Scope, Send

from config import settings
from security import InvalidConnectionTokenError, decode_connection_token

_current_connection_params: contextvars.ContextVar[dict | None] = contextvars.ContextVar(
    "current_connection_params", default=None
)


def get_current_connection_params() -> dict:
    params = _current_connection_params.get()
    if params is None:
        raise InvalidConnectionTokenError(
            f"Missing or invalid '{settings.DB_CONN_TOKEN_HEADER}' header on this request"
        )
    return params


class ConnectionTokenMiddleware:
    """ASGI middleware: decrypt X-DB-Conn-Token header -> contextvar per request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        header_name = settings.DB_CONN_TOKEN_HEADER.lower().encode("latin-1")
        token_bytes = headers.get(header_name)

        params = None
        if token_bytes:
            try:
                params = decode_connection_token(token_bytes.decode("latin-1"))
            except InvalidConnectionTokenError:
                params = None

        token_ctx = _current_connection_params.set(params)
        try:
            await self.app(scope, receive, send)
        finally:
            _current_connection_params.reset(token_ctx)
