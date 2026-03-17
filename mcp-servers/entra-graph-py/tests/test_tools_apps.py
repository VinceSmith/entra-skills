"""Tests for app registration tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_apps import (
    entra_check_credential_expiry,
    entra_create_app_registration,
    entra_get_app,
    entra_list_app_permissions,
    entra_list_apps,
)


def _make_app(
    oid="obj-1",
    app_id="app-1",
    name="TestApp",
    audience="AzureADMyOrg",
    passwords=None,
    keys=None,
):
    app = MagicMock()
    app.id = oid
    app.app_id = app_id
    app.display_name = name
    app.sign_in_audience = audience
    app.created_date_time = "2025-01-01T00:00:00Z"
    app.publisher_domain = "contoso.com"
    app.password_credentials = passwords or []
    app.key_credentials = keys or []
    app.required_resource_access = []
    return app


def _make_cred(display_name="secret-1", days_until_expiry=10):
    cred = MagicMock()
    cred.display_name = display_name
    cred.end_date_time = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)
    return cred


@pytest.mark.asyncio
async def test_list_apps(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = [_make_app(), _make_app("obj-2", "app-2", "AnotherApp")]
    mock_graph_client.applications.get = AsyncMock(return_value=result_obj)

    result = await entra_list_apps()
    assert "Found 2 app(s):" in result
    assert "TestApp" in result


@pytest.mark.asyncio
async def test_get_app_by_object_id(mock_graph_client):
    app = _make_app()
    mock_graph_client.applications.by_application_id.return_value.get = AsyncMock(return_value=app)

    result = await entra_get_app("obj-1")
    assert "TestApp" in result
    assert "app-1" in result


@pytest.mark.asyncio
async def test_get_app_fallback_to_app_id(mock_graph_client):
    mock_graph_client.applications.by_application_id.return_value.get = AsyncMock(side_effect=Exception("not found"))
    app = _make_app()
    fallback = MagicMock()
    fallback.value = [app]
    mock_graph_client.applications.get = AsyncMock(return_value=fallback)

    result = await entra_get_app("app-1")
    assert "TestApp" in result


@pytest.mark.asyncio
async def test_check_credential_expiry_finds_expiring(mock_graph_client):
    expiring_secret = _make_cred("old-secret", days_until_expiry=5)
    app = _make_app(passwords=[expiring_secret])
    mock_graph_client.applications.by_application_id.return_value.get = AsyncMock(return_value=app)

    result = await entra_check_credential_expiry("obj-1", days_warning=30)
    assert "EXPIRING SOON" in result
    assert "old-secret" in result


@pytest.mark.asyncio
async def test_check_credential_expiry_finds_expired(mock_graph_client):
    expired = _make_cred("dead-secret", days_until_expiry=-5)
    app = _make_app(passwords=[expired])
    mock_graph_client.applications.by_application_id.return_value.get = AsyncMock(return_value=app)

    result = await entra_check_credential_expiry("obj-1", days_warning=30)
    assert "EXPIRED" in result


@pytest.mark.asyncio
async def test_check_credential_expiry_clean(mock_graph_client):
    fresh = _make_cred("new-secret", days_until_expiry=365)
    app = _make_app(passwords=[fresh])
    mock_graph_client.applications.by_application_id.return_value.get = AsyncMock(return_value=app)

    result = await entra_check_credential_expiry("obj-1", days_warning=30)
    assert "No credentials expiring" in result


@pytest.mark.asyncio
async def test_create_app_blocked_in_readonly(mock_graph_client):
    result = await entra_create_app_registration("MyNewApp")
    assert "ENTRA_MCP_MODE=full" in result


@pytest.mark.asyncio
async def test_create_app_works_in_full_mode(mock_graph_client, full_mode):
    created = _make_app(name="MyNewApp")
    mock_graph_client.applications.post = AsyncMock(return_value=created)

    result = await entra_create_app_registration("MyNewApp")
    assert "Created app registration" in result
    assert "MyNewApp" in result


@pytest.mark.asyncio
async def test_list_app_permissions(mock_graph_client):
    rra = MagicMock()
    rra.resource_app_id = "00000003-0000-0000-c000-000000000000"
    perm = MagicMock()
    perm.type = "Role"
    perm.id = "perm-1"
    rra.resource_access = [perm]

    app = _make_app()
    app.required_resource_access = [rra]
    mock_graph_client.applications.by_application_id.return_value.get = AsyncMock(return_value=app)

    result = await entra_list_app_permissions("obj-1")
    assert "Application" in result
    assert "perm-1" in result
