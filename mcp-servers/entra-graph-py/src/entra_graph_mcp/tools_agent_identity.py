"""Agent Identity tools — Blueprint and Agent Identity management via Graph beta API."""

from __future__ import annotations

import json

import httpx

from .graph_client import get_credential
from .server import mcp, _is_write_enabled

GRAPH_BETA = "https://graph.microsoft.com/beta"


async def _graph_beta_request(method: str, path: str, body: dict | None = None) -> dict:
    """Make an authenticated request to the Graph beta API."""
    credential = get_credential()
    token = credential.get_token("https://graph.microsoft.com/.default")

    headers = {
        "Authorization": f"Bearer {token.token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        if method == "GET":
            resp = await client.get(f"{GRAPH_BETA}{path}", headers=headers)
        elif method == "POST":
            resp = await client.post(f"{GRAPH_BETA}{path}", headers=headers, json=body)
        else:
            raise ValueError(f"Unsupported method: {method}")

        resp.raise_for_status()
        return resp.json() if resp.content else {}


@mcp.tool()
async def entra_create_agent_blueprint(
    display_name: str,
    description: str = "",
    sponsor_id: str = "",
) -> str:
    """Create an Agent Identity Blueprint (preview, beta API). Requires ENTRA_MCP_MODE=full.

    A Blueprint is a special app registration template for agent identities.

    Args:
        display_name: Blueprint display name.
        description: Blueprint description.
        sponsor_id: Object ID of the sponsoring service principal (required for governance).
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    body: dict = {
        "displayName": display_name,
    }
    if description:
        body["description"] = description
    if sponsor_id:
        body["sponsors"] = [{"@odata.id": f"{GRAPH_BETA}/servicePrincipals/{sponsor_id}"}]

    result = await _graph_beta_request("POST", "/agentIdentityBlueprints", body)
    return (
        f"Created Agent Identity Blueprint:\n"
        f"  ID: {result.get('id')}\n"
        f"  Display Name: {result.get('displayName')}\n"
        f"  App ID: {result.get('appId')}\n"
        f"\nNext: Create Agent Identities from this Blueprint with entra_create_agent_identity."
    )


@mcp.tool()
async def entra_create_agent_identity(
    blueprint_id: str,
    display_name: str,
    description: str = "",
) -> str:
    """Create an Agent Identity from a Blueprint (preview, beta API). Requires ENTRA_MCP_MODE=full.

    Args:
        blueprint_id: Blueprint object ID.
        display_name: Agent identity display name.
        description: Agent description.
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    body: dict = {
        "displayName": display_name,
    }
    if description:
        body["description"] = description

    result = await _graph_beta_request(
        "POST",
        f"/agentIdentityBlueprints/{blueprint_id}/agentIdentities",
        body,
    )
    return (
        f"Created Agent Identity:\n"
        f"  ID: {result.get('id')}\n"
        f"  Display Name: {result.get('displayName')}\n"
        f"  Service Principal ID: {result.get('servicePrincipalId')}\n"
        f"\nThe agent now has its own Entra identity for OAuth2 flows."
    )


@mcp.tool()
async def entra_get_agent_token(
    agent_sp_id: str,
    flow: str = "autonomous",
    user_assertion: str = "",
    scopes: str = "https://graph.microsoft.com/.default",
) -> str:
    """Exchange tokens for an Agent Identity. Returns token metadata (not the raw token).

    Args:
        agent_sp_id: Service principal ID of the agent identity.
        flow: 'autonomous' (app-only) or 'obo' (on-behalf-of user).
        user_assertion: Required for OBO flow — the incoming user token.
        scopes: Target scopes (default: Graph .default).
    """
    if flow == "obo" and not user_assertion:
        return "Error: OBO flow requires user_assertion parameter."

    # For security, we report what would happen rather than returning raw tokens
    return (
        f"Token exchange for agent {agent_sp_id}:\n"
        f"  Flow: {flow}\n"
        f"  Target scopes: {scopes}\n"
        f"  Method: {'client_credentials' if flow == 'autonomous' else 'on_behalf_of'}\n"
        f"\nTo execute the token exchange in code, use MSAL:\n"
        f"  - Autonomous: ConfidentialClientApplication.acquire_token_for_client()\n"
        f"  - OBO: ConfidentialClientApplication.acquire_token_on_behalf_of()\n"
        f"\nSee the entra-agent-id-runtime skill for complete patterns."
    )
