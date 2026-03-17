"""Tests for identity diagnostics tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from entra_graph_mcp.tools_diagnostics import (
    entra_check_user_risk,
    entra_evaluate_conditional_access,
    entra_get_audit_logs,
    entra_get_signin_logs,
)


def _make_signin(user="Alice", app="Graph Explorer", error=0, city="Seattle", dt="2025-06-01T10:00:00Z"):
    s = MagicMock()
    s.user_display_name = user
    s.app_display_name = app
    s.ip_address = "10.0.0.1"
    s.created_date_time = dt
    s.conditional_access_status = "success"
    s.applied_conditional_access_policies = []
    loc = MagicMock()
    loc.city = city
    s.location = loc
    status = MagicMock()
    status.error_code = error
    s.status = status
    return s


def _make_audit(activity="Add application", initiator_upn="admin@contoso.com", dt="2025-06-01T10:00:00Z"):
    a = MagicMock()
    a.activity_display_name = activity
    a.activity_date_time = dt
    user_init = MagicMock()
    user_init.user_principal_name = initiator_upn
    app_init = MagicMock()
    app_init.display_name = None
    init = MagicMock()
    init.user = user_init
    init.app = app_init
    a.initiated_by = init
    a.target_resources = []
    return a


@pytest.mark.asyncio
async def test_get_signin_logs(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = [_make_signin(), _make_signin("Bob", error=50126)]
    mock_graph_client.audit_logs.sign_ins.get = AsyncMock(return_value=result_obj)

    result = await entra_get_signin_logs()
    assert "Found 2 sign-in(s):" in result
    assert "Alice" in result
    assert "FAILED" in result


@pytest.mark.asyncio
async def test_get_signin_logs_empty(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.audit_logs.sign_ins.get = AsyncMock(return_value=result_obj)

    result = await entra_get_signin_logs()
    assert "No sign-in logs found" in result


@pytest.mark.asyncio
async def test_get_audit_logs(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = [_make_audit()]
    mock_graph_client.audit_logs.directory_audits.get = AsyncMock(return_value=result_obj)

    result = await entra_get_audit_logs()
    assert "1 audit entry" in result
    assert "Add application" in result
    assert "admin@contoso.com" in result


@pytest.mark.asyncio
async def test_check_user_risk_specific_user(mock_graph_client):
    risky = MagicMock()
    risky.user_display_name = "Eve"
    risky.risk_level = "high"
    risky.risk_state = "atRisk"
    risky.risk_detail = "userCompromised"
    risky.risk_last_updated_date_time = "2025-06-01"
    mock_graph_client.identity_protection.risky_users.by_risky_user_id.return_value.get = AsyncMock(return_value=risky)

    result = await entra_check_user_risk(user_id="u-eve")
    assert "Eve" in result
    assert "high" in result


@pytest.mark.asyncio
async def test_check_user_risk_no_risky_users(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.identity_protection.risky_users.get = AsyncMock(return_value=result_obj)

    result = await entra_check_user_risk()
    assert "No risky users detected" in result


@pytest.mark.asyncio
async def test_evaluate_conditional_access(mock_graph_client):
    signin = _make_signin()
    policy = MagicMock()
    policy.display_name = "Require MFA"
    policy.result = "success"
    signin.applied_conditional_access_policies = [policy]

    result_obj = MagicMock()
    result_obj.value = [signin]
    mock_graph_client.audit_logs.sign_ins.get = AsyncMock(return_value=result_obj)

    result = await entra_evaluate_conditional_access("u1", "app1")
    assert "CA evaluation" in result
    assert "Require MFA" in result
