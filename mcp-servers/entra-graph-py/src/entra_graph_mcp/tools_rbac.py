"""RBAC tools — role assignments and role lookup."""

from __future__ import annotations

from .graph_client import get_graph_client, get_credential
from .server import mcp, _is_write_enabled


# Common Azure RBAC roles for Entra identity scenarios
COMMON_ROLES = {
    "Reader": "acdd72a7-3385-48ef-bd42-f606fba81ae7",
    "Contributor": "b24988ac-6180-42a0-ab88-20f7382dd24c",
    "Key Vault Secrets User": "4633458b-17de-408a-b874-0445c86b69e6",
    "Key Vault Secrets Officer": "b86a8fe4-44ce-4948-aee5-eccb2c155cd7",
    "Storage Blob Data Reader": "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1",
    "Storage Blob Data Contributor": "ba92f5b4-2d11-453d-a403-e96b0029c9fe",
    "Azure Service Bus Data Receiver": "4f6d3b9b-027b-4f4c-9142-0e5a2a2247e0",
    "Azure Service Bus Data Sender": "69a216fc-b8fb-44d8-bc22-1f3c2cd27a39",
    "Cosmos DB Built-in Data Reader": "fbdf93bf-df7d-467e-a4d2-9458aa1360c8",
    "App Configuration Data Reader": "516239f1-63e1-4d78-a4de-a74fb236a071",
}


@mcp.tool()
async def entra_list_role_assignments(principal_id: str) -> str:
    """List Azure RBAC role assignments for a principal (user, group, SP, MI).

    Args:
        principal_id: Object ID of the principal.
    """
    client = get_graph_client()
    # Use Graph to get directory role assignments (Entra roles)
    result = await client.service_principals.by_service_principal_id(principal_id).app_role_assignments.get()

    if not result or not result.value:
        return f"No app role assignments found for principal {principal_id}."

    lines = [f"Role assignments for {principal_id}:"]
    for a in result.value:
        lines.append(
            f"- Role: {a.app_role_id} → Resource: {a.resource_display_name} "
            f"(created: {a.created_date_time})"
        )
    return "\n".join(lines)


@mcp.tool()
async def entra_find_role(action: str) -> str:
    """Find the least-privilege Azure RBAC role for a given action.

    Args:
        action: Description of what you need (e.g. 'read blobs', 'send service bus messages').
    """
    action_lower = action.lower()
    matches = []

    role_actions = {
        "Key Vault Secrets User": ["read secrets", "get secret", "key vault read", "vault secret"],
        "Key Vault Secrets Officer": ["manage secrets", "create secret", "delete secret", "rotate secret"],
        "Storage Blob Data Reader": ["read blobs", "download blob", "list blobs", "storage read"],
        "Storage Blob Data Contributor": ["write blobs", "upload blob", "delete blob", "storage write"],
        "Azure Service Bus Data Receiver": ["receive messages", "service bus read", "consume queue"],
        "Azure Service Bus Data Sender": ["send messages", "service bus write", "publish queue"],
        "Cosmos DB Built-in Data Reader": ["read cosmos", "query cosmos", "cosmos read"],
        "App Configuration Data Reader": ["read config", "app config", "configuration read"],
        "Reader": ["read resources", "view resources", "list resources"],
        "Contributor": ["create resources", "manage resources", "deploy resources"],
    }

    for role_name, keywords in role_actions.items():
        for keyword in keywords:
            if keyword in action_lower or action_lower in keyword:
                role_id = COMMON_ROLES[role_name]
                matches.append(f"- **{role_name}** (ID: {role_id})")
                break

    if not matches:
        return (
            f"No common role found for '{action}'. "
            "Check https://learn.microsoft.com/azure/role-based-access-control/built-in-roles "
            "for the full list of Azure RBAC roles."
        )

    return f"Recommended role(s) for '{action}':\n" + "\n".join(matches)


@mcp.tool()
async def entra_assign_role(
    principal_id: str,
    role_definition_id: str,
    scope: str,
) -> str:
    """Assign an Azure RBAC role. Requires ENTRA_MCP_MODE=full.

    Uses Azure CLI under the hood since Graph SDK doesn't cover ARM role assignments.

    Args:
        principal_id: Object ID of the principal (user, group, SP, or MI).
        role_definition_id: Role definition ID (GUID).
        scope: Azure resource scope (e.g. /subscriptions/{sub}/resourceGroups/{rg}).
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    import subprocess

    result = subprocess.run(
        [
            "az", "role", "assignment", "create",
            "--assignee-object-id", principal_id,
            "--assignee-principal-type", "ServicePrincipal",
            "--role", role_definition_id,
            "--scope", scope,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        return f"Error assigning role: {result.stderr.strip()}"
    return f"Role {role_definition_id} assigned to {principal_id} at scope {scope}."
