"""ID Protection and Authentication Methods tools — risk detections, risky users/SPs, auth methods, TAP."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx

from .graph_client import get_graph_client, get_credential
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


# --- Risk Detections ---


@mcp.tool()
async def entra_list_risk_detections(
    risk_level: str = "",
    hours: int = 168,
    top: int = 50,
) -> str:
    """List Entra ID Protection risk detections. Requires IdentityRiskEvent.Read.All.

    Args:
        risk_level: Filter by risk level (low, medium, high). Empty for all.
        hours: How far back to query (default 168 = 7 days).
        top: Max results (default 50).
    """
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    filters = [f"detectedDateTime ge {since}"]

    if risk_level:
        filters.append(f"riskLevel eq '{risk_level}'")

    filter_str = " and ".join(filters)
    path = (
        f"/identityProtection/riskDetections"
        f"?$filter={filter_str}&$top={min(top, 999)}&$orderby=detectedDateTime desc"
    )
    result = await _graph_beta_request("GET", path)

    items = result.get("value", [])
    if not items:
        return "No risk detections found matching criteria."

    lines = [f"Found {len(items)} risk detection(s):"]
    for d in items:
        lines.append(
            f"- [{d.get('riskLevel', '?')}] {d.get('riskEventType', '?')} | "
            f"User: {d.get('userDisplayName', 'N/A')} | "
            f"IP: {d.get('ipAddress', 'N/A')} | "
            f"State: {d.get('riskState', '?')} | "
            f"Detected: {d.get('detectedDateTime', '?')}"
        )
    return "\n".join(lines)


# --- Risky Users ---


@mcp.tool()
async def entra_confirm_user_compromised(user_id: str) -> str:
    """Confirm a user as compromised in ID Protection. Requires ENTRA_MCP_MODE=full.

    This sets the user's risk level to high and triggers any Conditional Access
    policies that respond to user risk.

    Args:
        user_id: Object ID of the user to confirm compromised.
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    await _graph_beta_request(
        "POST",
        "/identityProtection/riskyUsers/confirmCompromised",
        {"userIds": [user_id]},
    )
    return f"User {user_id} confirmed as compromised. Risk level set to high."


@mcp.tool()
async def entra_dismiss_user_risk(user_id: str) -> str:
    """Dismiss a user's risk in ID Protection. Requires ENTRA_MCP_MODE=full.

    Use after investigating and determining the risk is a false positive or resolved.

    Args:
        user_id: Object ID of the user whose risk to dismiss.
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    await _graph_beta_request(
        "POST",
        "/identityProtection/riskyUsers/dismiss",
        {"userIds": [user_id]},
    )
    return f"Risk dismissed for user {user_id}."


# --- Risky Service Principals (beta) ---


@mcp.tool()
async def entra_list_risky_service_principals(top: int = 25) -> str:
    """List risky service principals from ID Protection (beta API). Requires IdentityRiskyServicePrincipal.Read.All.

    Args:
        top: Max results (default 25).
    """
    result = await _graph_beta_request(
        "GET",
        f"/identityProtection/riskyServicePrincipals?$top={min(top, 999)}&$orderby=riskLastUpdatedDateTime desc",
    )

    items = result.get("value", [])
    if not items:
        return "No risky service principals found."

    lines = [f"Found {len(items)} risky service principal(s):"]
    for sp in items:
        lines.append(
            f"- {sp.get('displayName', 'N/A')} | "
            f"AppId: {sp.get('appId', 'N/A')} | "
            f"Risk: {sp.get('riskLevel', 'N/A')} | "
            f"State: {sp.get('riskState', 'N/A')}"
        )
    return "\n".join(lines)


# --- Authentication Methods ---


@mcp.tool()
async def entra_list_user_auth_methods(user_id: str) -> str:
    """List authentication methods registered for a user. Requires UserAuthenticationMethod.Read.All.

    Args:
        user_id: Object ID or UPN of the user.
    """
    client = get_graph_client()
    result = await client.users.by_user_id(user_id).authentication.methods.get()

    if not result or not result.value:
        return f"No authentication methods found for user {user_id}."

    lines = [f"Authentication methods for {user_id}:"]
    for m in result.value:
        odata_type = getattr(m, "odata_type", "") or ""
        # Extract friendly method type from OData type (e.g. #microsoft.graph.passwordAuthenticationMethod → password)
        method_type = odata_type.rsplit(".", 1)[-1].replace("AuthenticationMethod", "") if odata_type else "unknown"
        lines.append(f"- {method_type} (id={m.id})")
    return "\n".join(lines)


@mcp.tool()
async def entra_create_temporary_access_pass(
    user_id: str,
    lifetime_minutes: int = 60,
    is_usable_once: bool = True,
) -> str:
    """Create a Temporary Access Pass (TAP) for a user. Requires ENTRA_MCP_MODE=full.

    The TAP value is only available at creation time. In production, communicate
    the TAP to the user through a secure channel.

    Args:
        user_id: Object ID or UPN of the user.
        lifetime_minutes: How long the TAP is valid (default 60 minutes).
        is_usable_once: Whether the TAP can only be used once (default True).
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    client = get_graph_client()
    from msgraph.generated.models.temporary_access_pass_authentication_method import (
        TemporaryAccessPassAuthenticationMethod,
    )

    tap = TemporaryAccessPassAuthenticationMethod(
        lifetime_in_minutes=lifetime_minutes,
        is_usable_once=is_usable_once,
    )

    result = await client.users.by_user_id(user_id).authentication.temporary_access_pass_methods.post(body=tap)
    return (
        f"Temporary Access Pass created for {user_id}:\n"
        f"  TAP: {result.temporary_access_pass}\n"
        f"  Lifetime: {result.lifetime_in_minutes} minutes\n"
        f"  Usable once: {result.is_usable_once}\n"
        f"  Created: {result.created_date_time}\n"
        f"\nNote: Communicate this TAP to the user through a secure channel."
    )
