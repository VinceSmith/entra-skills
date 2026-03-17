"""Entra Graph MCP Server — FastMCP implementation.

Provides tools for coding agents to manage Entra identities via Microsoft Graph.
Auth: DefaultAzureCredential (dev: Azure CLI, prod: managed identity).
Mode: ENTRA_MCP_MODE=read-only (default) or ENTRA_MCP_MODE=full.
"""

from __future__ import annotations

import os

from fastmcp import FastMCP

mcp = FastMCP(
    "Entra Graph MCP Server",
    description="Microsoft Entra identity management via Microsoft Graph API",
)

ENTRA_MCP_MODE = os.environ.get("ENTRA_MCP_MODE", "read-only")


def _is_write_enabled() -> bool:
    return ENTRA_MCP_MODE == "full"
