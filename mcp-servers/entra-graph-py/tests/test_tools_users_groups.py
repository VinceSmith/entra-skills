"""Tests for user & group tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from entra_graph_mcp.tools_users_groups import (
    entra_add_group_member,
    entra_get_group_members,
    entra_get_user,
    entra_list_groups,
    entra_list_users,
    entra_remove_group_member,
)


def _make_user(uid="u1", name="Alice", upn="alice@contoso.com", dept="Eng", enabled=True):
    u = MagicMock()
    u.id = uid
    u.display_name = name
    u.user_principal_name = upn
    u.mail = f"{name.lower()}@contoso.com"
    u.department = dept
    u.job_title = "Engineer"
    u.account_enabled = enabled
    return u


def _make_group(gid="g1", name="SG-Team", desc="Team group", unified=False):
    g = MagicMock()
    g.id = gid
    g.display_name = name
    g.description = desc
    g.group_types = ["Unified"] if unified else []
    g.security_enabled = not unified
    g.mail_enabled = unified
    return g


@pytest.mark.asyncio
async def test_list_users_returns_results(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = [_make_user(), _make_user("u2", "Bob", "bob@contoso.com")]
    mock_graph_client.users.get = AsyncMock(return_value=result_obj)

    result = await entra_list_users()
    assert "Found 2 user(s):" in result
    assert "Alice" in result
    assert "Bob" in result


@pytest.mark.asyncio
async def test_list_users_empty(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = []
    mock_graph_client.users.get = AsyncMock(return_value=result_obj)

    result = await entra_list_users()
    assert "No users found" in result


@pytest.mark.asyncio
async def test_get_user(mock_graph_client):
    user = _make_user()
    mock_graph_client.users.by_user_id.return_value.get = AsyncMock(return_value=user)

    result = await entra_get_user("alice@contoso.com")
    assert "Alice" in result
    assert "alice@contoso.com" in result


@pytest.mark.asyncio
async def test_list_groups_returns_results(mock_graph_client):
    result_obj = MagicMock()
    result_obj.value = [_make_group(), _make_group("g2", "M365-Team", unified=True)]
    mock_graph_client.groups.get = AsyncMock(return_value=result_obj)

    result = await entra_list_groups()
    assert "Found 2 group(s):" in result
    assert "SG-Team" in result
    assert "M365" in result


@pytest.mark.asyncio
async def test_get_group_members(mock_graph_client):
    member = MagicMock()
    member.id = "u1"
    member.display_name = "Alice"
    result_obj = MagicMock()
    result_obj.value = [member]
    mock_graph_client.groups.by_group_id.return_value.members.get = AsyncMock(return_value=result_obj)

    result = await entra_get_group_members("g1")
    assert "1 member(s)" in result
    assert "Alice" in result


@pytest.mark.asyncio
async def test_add_group_member_blocked_in_readonly(mock_graph_client):
    result = await entra_add_group_member("g1", "u1")
    assert "ENTRA_MCP_MODE=full" in result


@pytest.mark.asyncio
async def test_add_group_member_works_in_full_mode(mock_graph_client, full_mode):
    mock_graph_client.groups.by_group_id.return_value.members.ref.post = AsyncMock()

    result = await entra_add_group_member("g1", "u1")
    assert "Added user u1 to group g1" in result


@pytest.mark.asyncio
async def test_remove_group_member_blocked_in_readonly(mock_graph_client):
    result = await entra_remove_group_member("g1", "u1")
    assert "ENTRA_MCP_MODE=full" in result


@pytest.mark.asyncio
async def test_remove_group_member_works_in_full_mode(mock_graph_client, full_mode):
    mock_graph_client.groups.by_group_id.return_value.members.by_directory_object_id.return_value.ref.delete = AsyncMock()

    result = await entra_remove_group_member("g1", "u1")
    assert "Removed user u1 from group g1" in result
