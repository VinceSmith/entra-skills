"""User & group management tools."""

from __future__ import annotations

from msgraph.generated.models.reference_create import ReferenceCreate
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from msgraph.generated.groups.groups_request_builder import GroupsRequestBuilder

from .graph_client import get_graph_client
from .server import mcp, _is_write_enabled


@mcp.tool()
async def entra_list_users(
    search: str = "",
    department: str = "",
    top: int = 25,
) -> str:
    """Search/filter Entra ID users. Supports display name search and department filter.

    Args:
        search: Display name search string (startsWith match).
        department: Filter by department name (exact match).
        top: Max results to return (default 25, max 999).
    """
    client = get_graph_client()
    filters = []
    if search:
        filters.append(f"startswith(displayName,'{search}')")
    if department:
        filters.append(f"department eq '{department}'")
    filter_str = " and ".join(filters) if filters else None

    query = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
        filter=filter_str,
        select=["id", "displayName", "userPrincipalName", "mail", "department", "jobTitle", "accountEnabled"],
        top=min(top, 999),
        orderby=["displayName"],
    )
    config = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(query_parameters=query)
    if search:
        config.headers.add("ConsistencyLevel", "eventual")

    result = await client.users.get(request_configuration=config)
    if not result or not result.value:
        return "No users found."

    lines = [f"Found {len(result.value)} user(s):"]
    for u in result.value:
        status = "enabled" if u.account_enabled else "disabled"
        lines.append(f"- {u.display_name} ({u.user_principal_name}) [{status}] dept={u.department or 'N/A'}")
    return "\n".join(lines)


@mcp.tool()
async def entra_get_user(user_id: str) -> str:
    """Get a user's profile by ID or userPrincipalName.

    Args:
        user_id: User object ID or userPrincipalName (e.g. user@contoso.com).
    """
    client = get_graph_client()
    user = await client.users.by_user_id(user_id).get()
    if not user:
        return f"User '{user_id}' not found."
    return (
        f"Display Name: {user.display_name}\n"
        f"UPN: {user.user_principal_name}\n"
        f"Mail: {user.mail or 'N/A'}\n"
        f"Department: {user.department or 'N/A'}\n"
        f"Job Title: {user.job_title or 'N/A'}\n"
        f"Account Enabled: {user.account_enabled}\n"
        f"ID: {user.id}"
    )


@mcp.tool()
async def entra_list_groups(
    search: str = "",
    group_type: str = "",
    top: int = 25,
) -> str:
    """Search/filter Entra ID groups.

    Args:
        search: Display name search (startsWith match).
        group_type: Filter: 'security', 'microsoft365', or '' for all.
        top: Max results (default 25).
    """
    client = get_graph_client()
    filters = []
    if search:
        filters.append(f"startswith(displayName,'{search}')")
    if group_type == "security":
        filters.append("securityEnabled eq true and mailEnabled eq false")
    elif group_type == "microsoft365":
        filters.append("groupTypes/any(g:g eq 'Unified')")
    filter_str = " and ".join(filters) if filters else None

    query = GroupsRequestBuilder.GroupsRequestBuilderGetQueryParameters(
        filter=filter_str,
        select=["id", "displayName", "description", "groupTypes", "securityEnabled", "mailEnabled"],
        top=min(top, 999),
        orderby=["displayName"],
    )
    config = GroupsRequestBuilder.GroupsRequestBuilderGetRequestConfiguration(query_parameters=query)
    if search:
        config.headers.add("ConsistencyLevel", "eventual")

    result = await client.groups.get(request_configuration=config)
    if not result or not result.value:
        return "No groups found."

    lines = [f"Found {len(result.value)} group(s):"]
    for g in result.value:
        gtype = "M365" if g.group_types and "Unified" in g.group_types else "Security"
        lines.append(f"- {g.display_name} [{gtype}] {g.description or ''} (id={g.id})")
    return "\n".join(lines)


@mcp.tool()
async def entra_get_group_members(group_id: str, top: int = 50) -> str:
    """List members of a group.

    Args:
        group_id: Group object ID.
        top: Max members to return (default 50).
    """
    client = get_graph_client()
    result = await client.groups.by_group_id(group_id).members.get()
    if not result or not result.value:
        return "No members found."

    lines = [f"Group {group_id} has {len(result.value)} member(s):"]
    for m in result.value:
        name = getattr(m, "display_name", None) or m.id
        lines.append(f"- {name} (id={m.id})")
    return "\n".join(lines)


@mcp.tool()
async def entra_add_group_member(group_id: str, user_id: str) -> str:
    """Add a user to a group. Requires ENTRA_MCP_MODE=full.

    Args:
        group_id: Group object ID.
        user_id: User object ID to add.
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    client = get_graph_client()
    ref = ReferenceCreate(
        odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}",
    )
    await client.groups.by_group_id(group_id).members.ref.post(ref)
    return f"Added user {user_id} to group {group_id}."


@mcp.tool()
async def entra_remove_group_member(group_id: str, user_id: str) -> str:
    """Remove a user from a group. Requires ENTRA_MCP_MODE=full.

    Args:
        group_id: Group object ID.
        user_id: User object ID to remove.
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    client = get_graph_client()
    await client.groups.by_group_id(group_id).members.by_directory_object_id(user_id).ref.delete()
    return f"Removed user {user_id} from group {group_id}."
