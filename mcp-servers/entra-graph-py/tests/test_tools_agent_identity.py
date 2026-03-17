"""Tests for Agent Identity tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_agent_identity import (
    entra_create_agent_blueprint,
    entra_create_agent_identity,
    entra_get_agent_token,
)


@pytest.mark.asyncio
async def test_create_blueprint_blocked_in_readonly():
    result = await entra_create_agent_blueprint("my-blueprint")
    assert "ENTRA_MCP_MODE=full" in result


@pytest.mark.asyncio
async def test_create_blueprint_works_in_full_mode(full_mode, mock_credential):
    mock_response = {"id": "bp-1", "displayName": "my-blueprint", "appId": "app-bp-1"}
    with patch("entra_graph_mcp.tools_agent_identity._graph_beta_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        result = await entra_create_agent_blueprint("my-blueprint", description="test", sponsor_id="sp-1")

    assert "Created Agent Identity Blueprint" in result
    assert "bp-1" in result
    mock_req.assert_called_once()


@pytest.mark.asyncio
async def test_create_agent_identity_blocked_in_readonly():
    result = await entra_create_agent_identity("bp-1", "my-agent")
    assert "ENTRA_MCP_MODE=full" in result


@pytest.mark.asyncio
async def test_create_agent_identity_works_in_full_mode(full_mode, mock_credential):
    mock_response = {"id": "agent-1", "displayName": "my-agent", "servicePrincipalId": "sp-agent-1"}
    with patch("entra_graph_mcp.tools_agent_identity._graph_beta_request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = mock_response
        result = await entra_create_agent_identity("bp-1", "my-agent")

    assert "Created Agent Identity" in result
    assert "agent-1" in result
    assert "sp-agent-1" in result


@pytest.mark.asyncio
async def test_get_agent_token_autonomous():
    result = await entra_get_agent_token("sp-1", flow="autonomous")
    assert "autonomous" in result
    assert "client_credentials" in result
    assert "entra-agent-id-runtime" in result


@pytest.mark.asyncio
async def test_get_agent_token_obo_requires_assertion():
    result = await entra_get_agent_token("sp-1", flow="obo")
    assert "Error" in result
    assert "user_assertion" in result


@pytest.mark.asyncio
async def test_get_agent_token_obo_with_assertion():
    result = await entra_get_agent_token("sp-1", flow="obo", user_assertion="eyJ...")
    assert "obo" in result.lower() or "on_behalf_of" in result
