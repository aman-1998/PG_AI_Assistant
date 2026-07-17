"""Entry point for text_to_sql_mcp: a standalone MCP server exposing Postgres
tools over streamable HTTP. Independently runnable on its own port; has no
dependency on the backend's MySQL control-plane store.

Run with:  python server.py
(or:       uvicorn server:app --host 0.0.0.0 --port 8020)
"""
from __future__ import annotations

import logging

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Mount, Route

from config import settings
from context import ConnectionTokenMiddleware
from mcp_instance import mcp

# Import tool modules purely for their @mcp.tool() registration side-effects.
from tools import (  # noqa: F401
    ddl_tools,
    er_diagram_tools,
    explain_tools,
    export_tools,
    metrics_tools,
    optimization_tools,
    query_tools,
    schema_tools,
    sql_script_tools,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("text_to_sql_mcp")

# FastMCP's built-in ASGI app for the streamable-http transport.
_mcp_asgi_app = mcp.streamable_http_app()

# Plain unauthenticated download route for CSV/JSON exports (see tools/export_tools.py),
# mounted ahead of the MCP app so it takes priority over the catch-all "/" mount.
# Everything else still goes through ConnectionTokenMiddleware -> the MCP app.
#
# NOTE: FastMCP's streamable_http_app() carries its own `lifespan` (it starts
# self.session_manager.run() on startup, which initializes the anyio TaskGroup
# the streamable-http transport needs per request). Wrapping it in a new outer
# Starlette app does NOT automatically propagate that lifespan to the mounted
# sub-app, so it must be passed through explicitly here - otherwise every MCP
# request fails with "RuntimeError: Task group is not initialized."
app = Starlette(
    routes=[
        Route("/exports/{file_id}", export_tools.download_export, methods=["GET"]),
        Route("/diagrams/{file_id}", er_diagram_tools.download_diagram, methods=["GET"]),
        Route("/sql-scripts/{file_id}", sql_script_tools.download_sql_script, methods=["GET"]),
        Mount("/", app=ConnectionTokenMiddleware(_mcp_asgi_app)),
    ],
    lifespan=lambda app: mcp.session_manager.run(),
)


if __name__ == "__main__":
    logger.info("Starting text_to_sql_mcp on %s:%s", settings.HOST, settings.PORT)
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
