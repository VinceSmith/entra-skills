"""Tests for ID Protection and Authentication Methods tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_id_protection import (
    entra_confirm_user_compromised,
    entra_create_temporary_access_pass,
    entra_dismiss_user_risk,
    entra_list_risk_detections,
    entra_list_risky_service_principals,
    entra_list_user_auth_methods,
)


@pytest.fixture()
def mock_httpx():
    """Patch httpx.AsyncClient for beta API calls."""
    mock_response = MagicMock()
    mock_response.content = b'{"value": []}'
    mock_response.json.return_value = {"value": []}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("entra_graph_mcp.tools_id_protection.httpx.AsyncClient", return_value=mock_client):
        yield mock_client, mock_response


# --- Risk Detections ---


@pytest.mark.asyncio
async def test_list_risk_detections_empty(mock_credential, mock_httpx):
    _, mock_response = mock_httpx
    mock_response.json.return_value = {"value": []}

    result = await entra_list_risk_detections()
    assert "No risk detections" in result


@pytest.mark.asyncio
async def test_list_risk_detections_with_results(mock_credential, mock_httpx):
    _, mock_response = mock_httpx
    mock_response.json.return_value = {
        "value": [
            {
                "riskLevel": "high",
                "riskEventType": "unfamiliarFeatures",
                "userDisplayName": "Alice",
                "ipAddress": "10.0.0.1",
                "riskState": "atRisk",
                "detectedDateTime": "2025-06-01T10:00:00Z",
            },
        ],
    }

    result = await entra_list_risk_detections()
    assert "Found 1 risk detection(s):" in result
    assert "high" in result
    assert "unfamiliarFeatures" in result


# --- Confirm User Compromised ---


@pytest.mark.asyncio
async def test_confirm_user_compromised_blocked():
    result = await entra_confirm_user_compromised("user-1")
    assert "Error: Write" in result


@pytest.mark.asyncio
async def test_confirm_user_compromised_success(mock_credential, full_mode, mock_httpx):
    _, mock_response = mock_httpx
    mock_response.content = b""
    mock_response.json.return_value = {}

    result = await entra_confirm_user_compromised("user-1")
    assert "confirmed as compromised" in result


# --- Dismiss User Risk ---


@pytest.mark.asyncio
async def test_dismiss_user_risk_blocked():
    result = await entra_dismiss_user_risk("user-1")
    assert "Error: Write" in result


@pytest.mark.asyncio
async def test_dismiss_user_risk_success(mock_credential, full_mode, mock_httpx):
    _, mock_response = mock_httpx
    mock_response.content = b""
    mock_response.json.return_value = {}

    result = await entra_dismiss_user_risk("user-1")
    assert "Risk dismissed" in result


# --- Risky Service Principals ---


@pytest.mark.asyncio
async def test_list_risky_service_principals_empty(mock_credential, mock_httpx):
    _, mock_response = mock_httpx
    mock_response.json.return_value = {"value": []}

    result = await entra_list_risky_service_principals()
    assert "No risky service principals" in result


@pytest.mark.asyncio
async def test_list_risky_service_principals_with_results(mock_credential, mock_httpx):
    _, mock_response = mock_httpx
    mock_response.json.return_value = {
        "value": [
            {
                "displayName": "CompromisedSP",
                "appId": "sp-app-1",
                "riskLevel": "high",
                "riskState": "atRisk",
            },
        ],
    }

    result = await entra_list_risky_service_principals()
    assert "Found 1 risky service principal(s):" in result
    assert "CompromisedSP" in result


# --- Authentication Methods ---


@pytest.mark.asyncio
async def test_list_user_auth_methods(mock_graph_client):
    method = MagicMock()
    method.id = "m1"
    method.odata_type = "#microsoft.graph.phoneAuthenticationMethod"

    methods_result = MagicMock()
    methods_result.value = [method]
    mock_graph_client.users.by_user_id.return_value.authentication.methods.get = AsyncMock(
        return_value=methods_result,
    )

    result = await entra_list_user_auth_methods("user-1")
    assert "phone" in result
    assert "m1" in result


# --- Temporary Access Pass ---


@pytest.mark.asyncio
async def test_create_tap_blocked():
    result = await entra_create_temporary_access_pass("user-1")
    assert "Error: Write" in result


@pytest.mark.asyncio
async def test_create_tap_success(mock_graph_client, full_mode):
    tap_result = MagicMock()
    tap_result.temporary_access_pass = "ABC123XYZ"
    tap_result.lifetime_in_minutes = 60
    tap_result.is_usable_once = True
    tap_result.created_date_time = "2025-06-01T10:00:00Z"
    mock_graph_client.users.by_user_id.return_value.authentication.temporary_access_pass_methods.post = AsyncMock(
        return_value=tap_result,
    )

    result = await entra_create_temporary_access_pass("user-1")
    assert "ABC123XYZ" in result
    assert "60" in result
