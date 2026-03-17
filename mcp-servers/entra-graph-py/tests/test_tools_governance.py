"""Tests for identity governance tools."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_governance import (
    entra_activate_pim_role,
    entra_create_access_review,
    entra_list_access_packages,
    entra_list_access_reviews,
    entra_list_lifecycle_workflows,
    entra_list_pim_role_assignments,
)

# Tests use conftest.py fixtures: mock_graph_client, mock_credential, full_mode
# mock_graph_client is MagicMock — intermediate calls are sync, terminal .get()/.post() must be AsyncMock
# Beta API tools use httpx — mock via unittest.mock.patch


@pytest.fixture()
def mock_httpx():
    mock_response = MagicMock()
    mock_response.content = b'{"id": "123", "status": "Active"}'
    mock_response.json.return_value = {"id": "123", "status": "Active"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("entra_graph_mcp.tools_governance.httpx.AsyncClient", return_value=mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# Access Reviews (Graph SDK)
# ---------------------------------------------------------------------------


async def test_list_access_reviews_empty(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.identity_governance.access_reviews.definitions.get = AsyncMock(
        return_value=result_obj,
    )
    result = await entra_list_access_reviews()
    assert "No access review" in result


async def test_list_access_reviews_with_results(mock_graph_client):
    r1 = MagicMock()
    r1.id = "rev-1"
    r1.display_name = "Quarterly Review"
    r1.status = "InProgress"
    r1.scope = MagicMock()
    r1.scope.odata_type = "#microsoft.graph.accessReviewQueryScope"

    r2 = MagicMock()
    r2.id = "rev-2"
    r2.display_name = "Annual Review"
    r2.status = "Completed"
    r2.scope = MagicMock()
    r2.scope.odata_type = "#microsoft.graph.accessReviewQueryScope"

    result_obj = MagicMock()
    result_obj.value = [r1, r2]
    mock_graph_client.identity_governance.access_reviews.definitions.get = AsyncMock(
        return_value=result_obj,
    )
    result = await entra_list_access_reviews()
    assert "Quarterly Review" in result
    assert "Annual Review" in result
    assert "2" in result


# ---------------------------------------------------------------------------
# Create Access Review (beta httpx, write operation)
# ---------------------------------------------------------------------------


async def test_create_access_review_read_only_blocked():
    result = await entra_create_access_review(
        display_name="Test Review",
        scope_type="group",
        scope_id="grp-1",
        reviewer_ids="user-1",
    )
    assert "Error: Write" in result


async def test_create_access_review_success(mock_credential, mock_httpx, full_mode):
    mock_response = MagicMock()
    mock_response.content = b'{"id": "rev-new", "displayName": "Test Review", "status": "NotStarted"}'
    mock_response.json.return_value = {
        "id": "rev-new",
        "displayName": "Test Review",
        "status": "NotStarted",
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx.post = AsyncMock(return_value=mock_response)

    result = await entra_create_access_review(
        display_name="Test Review",
        scope_type="group",
        scope_id="grp-1",
        reviewer_ids="user-1",
    )
    assert "rev-new" in result
    assert "Test Review" in result


# ---------------------------------------------------------------------------
# Access Packages (Graph SDK)
# ---------------------------------------------------------------------------


async def test_list_access_packages_empty(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.identity_governance.entitlement_management.access_packages.get = AsyncMock(
        return_value=result_obj,
    )
    result = await entra_list_access_packages()
    assert "No access packages" in result


async def test_list_access_packages_with_results(mock_graph_client):
    p1 = MagicMock()
    p1.id = "pkg-1"
    p1.display_name = "Developer Access"
    p1.catalog_id = "cat-1"
    p1.modified_date_time = "2025-06-01"

    p2 = MagicMock()
    p2.id = "pkg-2"
    p2.display_name = "Admin Access"
    p2.catalog_id = "cat-1"
    p2.modified_date_time = "2025-07-01"

    result_obj = MagicMock()
    result_obj.value = [p1, p2]
    mock_graph_client.identity_governance.entitlement_management.access_packages.get = AsyncMock(
        return_value=result_obj,
    )
    result = await entra_list_access_packages()
    assert "Developer Access" in result
    assert "Admin Access" in result
    assert "2" in result


# ---------------------------------------------------------------------------
# Lifecycle Workflows (beta httpx)
# ---------------------------------------------------------------------------


async def test_list_lifecycle_workflows(mock_credential, mock_httpx):
    mock_response = MagicMock()
    mock_response.content = b'...'
    mock_response.json.return_value = {
        "value": [
            {
                "id": "wf-1",
                "displayName": "Onboarding Workflow",
                "category": "joiner",
                "isEnabled": True,
                "lastModifiedDateTime": "2025-05-01",
            },
            {
                "id": "wf-2",
                "displayName": "Offboarding Workflow",
                "category": "leaver",
                "isEnabled": False,
                "lastModifiedDateTime": "2025-06-01",
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx.get = AsyncMock(return_value=mock_response)

    result = await entra_list_lifecycle_workflows()
    assert "Onboarding Workflow" in result
    assert "Offboarding Workflow" in result
    assert "2" in result


# ---------------------------------------------------------------------------
# PIM Role Assignments (beta httpx)
# ---------------------------------------------------------------------------


async def test_list_pim_role_assignments(mock_credential, mock_httpx):
    mock_response = MagicMock()
    mock_response.content = b'...'
    mock_response.json.return_value = {
        "value": [
            {
                "principalId": "user-1",
                "roleDefinitionId": "role-1",
                "directoryScopeId": "/",
                "startDateTime": "2025-06-01",
                "endDateTime": "2025-12-31",
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx.get = AsyncMock(return_value=mock_response)

    result = await entra_list_pim_role_assignments(principal_id="user-1")
    assert "user-1" in result
    assert "role-1" in result


# ---------------------------------------------------------------------------
# Activate PIM Role (beta httpx, write operation)
# ---------------------------------------------------------------------------


async def test_activate_pim_role_blocked():
    result = await entra_activate_pim_role(
        role_definition_id="role-1",
        principal_id="user-1",
        justification="Need access",
    )
    assert "Error: Write" in result


async def test_activate_pim_role_no_justification(mock_credential, full_mode):
    result = await entra_activate_pim_role(
        role_definition_id="role-1",
        principal_id="user-1",
        justification="",
    )
    assert "Error: Justification" in result


async def test_activate_pim_role_success(mock_credential, mock_httpx, full_mode):
    mock_response = MagicMock()
    mock_response.content = b'...'
    mock_response.json.return_value = {
        "id": "req-1",
        "roleDefinitionId": "role-1",
        "principalId": "user-1",
        "status": "Provisioned",
    }
    mock_response.raise_for_status = MagicMock()
    mock_httpx.post = AsyncMock(return_value=mock_response)

    result = await entra_activate_pim_role(
        role_definition_id="role-1",
        principal_id="user-1",
        justification="Incident response",
    )
    assert "req-1" in result
    assert "role-1" in result
    assert "Provisioned" in result
    assert "Incident response" in result
