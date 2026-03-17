"""Tests for workload identity tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_workload_id import (
    entra_find_stale_service_principals,
    entra_get_sp_permissions,
    entra_list_service_principals,
    entra_workload_identity_posture,
)


def _make_sp(
    oid="sp1",
    app_id="app1",
    name="TestApp",
    sp_type="Application",
    passwords=None,
    keys=None,
):
    sp = MagicMock()
    sp.id = oid
    sp.app_id = app_id
    sp.display_name = name
    sp.service_principal_type = sp_type
    sp.password_credentials = passwords or []
    sp.key_credentials = keys or []
    return sp


def _make_role(role_id="role1", resource_name="Microsoft Graph", created="2025-01-01"):
    role = MagicMock()
    role.app_role_id = role_id
    role.resource_display_name = resource_name
    role.created_date_time = created
    return role


def _make_grant(resource_id="res1", scope="User.Read", consent_type="Principal"):
    grant = MagicMock()
    grant.resource_id = resource_id
    grant.scope = scope
    grant.consent_type = consent_type
    return grant


@pytest.fixture()
def mock_httpx():
    mock_response = MagicMock()
    mock_response.content = b'{"value": []}'
    mock_response.json.return_value = {"value": []}
    mock_response.raise_for_status = MagicMock()
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    with patch("entra_graph_mcp.tools_workload_id.httpx.AsyncClient", return_value=mock_client):
        yield mock_client, mock_response


# --- entra_list_service_principals ---


@pytest.mark.asyncio
async def test_list_service_principals_empty(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.service_principals.get = AsyncMock(return_value=result_obj)

    result = await entra_list_service_principals()
    assert "No service principals" in result


@pytest.mark.asyncio
async def test_list_service_principals_with_results(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = [
        _make_sp("sp1", "app1", "AppOne", "Application"),
        _make_sp("sp2", "app2", "AppTwo", "ManagedIdentity"),
    ]
    mock_graph_client.service_principals.get = AsyncMock(return_value=result_obj)

    result = await entra_list_service_principals()
    assert "Found 2 service principal(s):" in result
    assert "AppOne" in result
    assert "AppTwo" in result
    assert "Application" in result
    assert "ManagedIdentity" in result


# --- entra_get_sp_permissions ---


@pytest.mark.asyncio
async def test_get_sp_permissions(mock_graph_client):
    role_result = MagicMock()
    role_result.value = [_make_role()]
    mock_graph_client.service_principals.by_service_principal_id.return_value.app_role_assignments.get = AsyncMock(
        return_value=role_result,
    )

    oauth_result = MagicMock()
    oauth_result.value = [_make_grant()]
    mock_graph_client.service_principals.by_service_principal_id.return_value.oauth2_permission_grants.get = AsyncMock(
        return_value=oauth_result,
    )

    result = await entra_get_sp_permissions("sp1")
    assert "Application permissions (1):" in result
    assert "Microsoft Graph" in result
    assert "Delegated permissions (1):" in result
    assert "User.Read" in result


@pytest.mark.asyncio
async def test_get_sp_permissions_empty(mock_graph_client):
    role_result = MagicMock()
    role_result.value = []
    mock_graph_client.service_principals.by_service_principal_id.return_value.app_role_assignments.get = AsyncMock(
        return_value=role_result,
    )

    oauth_result = MagicMock()
    oauth_result.value = []
    mock_graph_client.service_principals.by_service_principal_id.return_value.oauth2_permission_grants.get = AsyncMock(
        return_value=oauth_result,
    )

    result = await entra_get_sp_permissions("sp1")
    assert "(none)" in result


# --- entra_find_stale_service_principals ---


@pytest.mark.asyncio
async def test_find_stale_sps_empty(mock_credential, mock_httpx):
    _mock_client, _mock_response = mock_httpx

    result = await entra_find_stale_service_principals()
    assert "No service principals inactive" in result


@pytest.mark.asyncio
async def test_find_stale_sps_with_results(mock_credential, mock_httpx):
    _mock_client, mock_response = mock_httpx
    old_date = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    mock_response.content = b'{"value": [{"appId": "stale-app-1", "lastSignInActivity": {"lastSignInDateTime": "' + old_date.encode() + b'"}}]}'
    mock_response.json.return_value = {
        "value": [
            {
                "appId": "stale-app-1",
                "lastSignInActivity": {"lastSignInDateTime": old_date},
            },
        ],
    }

    result = await entra_find_stale_service_principals()
    assert "stale-app-1" in result
    assert "stale service principal(s)" in result


# --- entra_workload_identity_posture ---


@pytest.mark.asyncio
async def test_workload_identity_posture_no_issues(mock_graph_client):
    fresh_cred = MagicMock()
    fresh_cred.end_date_time = datetime.now(timezone.utc) + timedelta(days=365)
    sp = _make_sp(passwords=[fresh_cred])

    sp_result = MagicMock()
    sp_result.value = [sp]
    mock_graph_client.service_principals.get = AsyncMock(return_value=sp_result)

    role_result = MagicMock()
    role_result.value = [_make_role()]  # 1 role, well under threshold
    mock_graph_client.service_principals.by_service_principal_id.return_value.app_role_assignments.get = AsyncMock(
        return_value=role_result,
    )

    result = await entra_workload_identity_posture()
    assert "No issues found" in result


@pytest.mark.asyncio
async def test_workload_identity_posture_flagged(mock_graph_client):
    expired_cred = MagicMock()
    expired_cred.end_date_time = datetime.now(timezone.utc) - timedelta(days=30)
    sp = _make_sp(name="Expired App", passwords=[expired_cred])

    sp_result = MagicMock()
    sp_result.value = [sp]
    mock_graph_client.service_principals.get = AsyncMock(return_value=sp_result)

    role_result = MagicMock()
    role_result.value = [_make_role(f"role-{i}") for i in range(12)]  # >10 roles
    mock_graph_client.service_principals.by_service_principal_id.return_value.app_role_assignments.get = AsyncMock(
        return_value=role_result,
    )

    result = await entra_workload_identity_posture()
    assert "EXPIRED_CRED" in result
    assert "OVER_PRIVILEGED" in result
    assert "Expired App" in result
