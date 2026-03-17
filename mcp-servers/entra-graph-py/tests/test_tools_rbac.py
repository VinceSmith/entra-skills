"""Tests for RBAC tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_rbac import (
    entra_assign_role,
    entra_find_role,
    entra_list_role_assignments,
)


@pytest.mark.asyncio
async def test_list_role_assignments(mock_graph_client):
    assignment = MagicMock()
    assignment.app_role_id = "role-1"
    assignment.resource_display_name = "Microsoft Graph"
    assignment.created_date_time = "2025-06-01"
    result_obj = MagicMock()
    result_obj.value = [assignment]
    mock_graph_client.service_principals.by_service_principal_id.return_value.app_role_assignments.get = AsyncMock(
        return_value=result_obj
    )

    result = await entra_list_role_assignments("sp-1")
    assert "Role assignments for sp-1" in result
    assert "Microsoft Graph" in result


@pytest.mark.asyncio
async def test_list_role_assignments_empty(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.service_principals.by_service_principal_id.return_value.app_role_assignments.get = AsyncMock(
        return_value=result_obj
    )

    result = await entra_list_role_assignments("sp-1")
    assert "No app role assignments" in result


@pytest.mark.asyncio
async def test_find_role_blobs():
    result = await entra_find_role("read blobs")
    assert "Storage Blob Data Reader" in result


@pytest.mark.asyncio
async def test_find_role_service_bus():
    result = await entra_find_role("send messages to service bus")
    assert "Azure Service Bus Data Sender" in result


@pytest.mark.asyncio
async def test_find_role_no_match():
    result = await entra_find_role("manage quantum flux capacitors")
    assert "No common role found" in result
    assert "learn.microsoft.com" in result


@pytest.mark.asyncio
async def test_assign_role_blocked_in_readonly(mock_graph_client):
    result = await entra_assign_role("sp-1", "role-1", "/subscriptions/sub")
    assert "ENTRA_MCP_MODE=full" in result


@pytest.mark.asyncio
async def test_assign_role_works_in_full_mode(mock_graph_client, full_mode):
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout='{"id":"a1"}', stderr="")
        result = await entra_assign_role("sp-1", "role-1", "/subscriptions/sub")

    assert "Role role-1 assigned to sp-1" in result
    mock_run.assert_called_once()
