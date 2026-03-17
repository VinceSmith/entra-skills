"""Shared fixtures for MCP server tests."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# All modules that import get_graph_client
_GRAPH_CLIENT_TARGETS = [
    "entra_graph_mcp.tools_users_groups.get_graph_client",
    "entra_graph_mcp.tools_apps.get_graph_client",
    "entra_graph_mcp.tools_diagnostics.get_graph_client",
    "entra_graph_mcp.tools_rbac.get_graph_client",
]

_CREDENTIAL_TARGETS = [
    "entra_graph_mcp.tools_rbac.get_credential",
    "entra_graph_mcp.tools_agent_identity.get_credential",
]


@pytest.fixture(autouse=True)
def _read_only_mode(monkeypatch: pytest.MonkeyPatch):
    """Default to read-only mode for safety."""
    monkeypatch.setattr("entra_graph_mcp.server.ENTRA_MCP_MODE", "read-only")


@pytest.fixture()
def full_mode(monkeypatch: pytest.MonkeyPatch):
    """Enable write mode for tests that need it."""
    monkeypatch.setattr("entra_graph_mcp.server.ENTRA_MCP_MODE", "full")


@pytest.fixture()
def mock_graph_client():
    """Patch get_graph_client in all tool modules.

    Uses MagicMock (not AsyncMock) because intermediate Graph SDK calls
    (.users, .by_user_id()) are synchronous — only terminal .get()/.post()
    are async and must be individually set to AsyncMock in each test.
    """
    client = MagicMock()
    patches = [patch(target, return_value=client) for target in _GRAPH_CLIENT_TARGETS]
    for p in patches:
        p.start()
    yield client
    for p in patches:
        p.stop()


@pytest.fixture()
def mock_credential():
    """Patch get_credential in all tool modules."""
    cred = MagicMock()
    token = MagicMock()
    token.token = "mock-access-token"
    cred.get_token.return_value = token
    patches = [patch(target, return_value=cred) for target in _CREDENTIAL_TARGETS]
    for p in patches:
        p.start()
    yield cred
    for p in patches:
        p.stop()
