"""Shared FastMCP server instance. Tool modules import `mcp` from here and
register themselves via the `@mcp.tool()` decorator; server.py imports the
tool modules (for their registration side-effects) and mounts the resulting
app under uvicorn.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("text-to-sql-postgres-mcp")
