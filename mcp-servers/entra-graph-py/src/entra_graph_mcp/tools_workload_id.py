"""Workload Identity tools — service principal management, permissions, and posture."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx
from msgraph.generated.service_principals.service_principals_request_builder import (
    ServicePrincipalsRequestBuilder,
)

from .graph_client import get_credential, get_graph_client
from .server import mcp, _is_write_enabled

GRAPH_BETA = "https://graph.microsoft.com/beta"


async def _graph_beta_request(method: str, path: str, body: dict | None = None) -> dict:
    """Execute a request against the Microsoft Graph beta endpoint."""
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
async def entra_list_service_principals(
    search: str = "",
    sp_type: str = "",
    top: int = 25,
) -> str:
    """Search/filter Entra service principals.

    Args:
        search: Display name search (startsWith match).
        sp_type: Filter by type: Application, ManagedIdentity, Legacy, SocialIdp, or empty for all.
        top: Max results (default 25).
    """
    client = get_graph_client()

    filters: list[str] = []
    if search:
        filters.append(f"startswith(displayName,'{search}')")
    if sp_type:
        filters.append(f"servicePrincipalType eq '{sp_type}'")
    filter_str = " and ".join(filters) if filters else None

    query = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
        filter=filter_str,
        select=["id", "appId", "displayName", "servicePrincipalType"],
        top=min(top, 999),
        orderby=["displayName"],
    )
    config = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
        query_parameters=query,
    )
    if search:
        config.headers.add("ConsistencyLevel", "eventual")

    result = await client.service_principals.get(request_configuration=config)
    if not result or not result.value:
        return "No service principals found."

    lines = [f"Found {len(result.value)} service principal(s):"]
    for sp in result.value:
        lines.append(
            f"- {sp.display_name} | type={sp.service_principal_type} "
            f"| appId={sp.app_id} | id={sp.id}"
        )
    return "\n".join(lines)


@mcp.tool()
async def entra_get_sp_permissions(sp_id: str) -> str:
    """List permissions (app role assignments and OAuth2 grants) for a service principal.

    Args:
        sp_id: Service principal object ID.
    """
    client = get_graph_client()

    # App role assignments (application permissions)
    role_result = await client.service_principals.by_service_principal_id(
        sp_id,
    ).app_role_assignments.get()

    # OAuth2 permission grants (delegated permissions)
    oauth_result = await client.service_principals.by_service_principal_id(
        sp_id,
    ).oauth2_permission_grants.get()

    lines = [f"Permissions for service principal {sp_id}:"]

    # Application permissions
    roles = role_result.value if role_result and role_result.value else []
    lines.append(f"\nApplication permissions ({len(roles)}):")
    if roles:
        for r in roles:
            lines.append(
                f"- Role: {r.app_role_id} → {r.resource_display_name} "
                f"(created: {r.created_date_time})"
            )
    else:
        lines.append("  (none)")

    # Delegated permissions
    grants = oauth_result.value if oauth_result and oauth_result.value else []
    lines.append(f"\nDelegated permissions ({len(grants)}):")
    if grants:
        for g in grants:
            lines.append(
                f"- Resource: {g.resource_id} | Scope: {g.scope} "
                f"| ConsentType: {g.consent_type}"
            )
    else:
        lines.append("  (none)")

    return "\n".join(lines)


@mcp.tool()
async def entra_find_stale_service_principals(
    days_inactive: int = 90,
    top: int = 25,
) -> str:
    """Find service principals with no sign-in activity in the last N days.

    Uses the beta API for sign-in activity reports.

    Args:
        days_inactive: Days of inactivity threshold (default 90).
        top: Max results (default 25).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_inactive)

    # Fetch sign-in activity from beta endpoint
    data = await _graph_beta_request(
        "GET",
        f"/reports/servicePrincipalSignInActivities?$top={min(top * 2, 200)}",
    )
    activities = data.get("value", [])

    stale: list[dict] = []
    for entry in activities:
        last_sign_in = entry.get("lastSignInActivity", {}).get("lastSignInDateTime")
        if last_sign_in:
            last_dt = datetime.fromisoformat(last_sign_in.replace("Z", "+00:00"))
            if last_dt < cutoff:
                stale.append({
                    "appId": entry.get("appId", "N/A"),
                    "lastSignIn": last_dt.date().isoformat(),
                })
        else:
            # No sign-in recorded at all — treat as stale
            stale.append({
                "appId": entry.get("appId", "N/A"),
                "lastSignIn": "never",
            })

        if len(stale) >= top:
            break

    if not stale:
        return f"No service principals inactive for >{days_inactive} days."

    lines = [f"Found {len(stale)} stale service principal(s) (>{days_inactive} days inactive):"]
    for s in stale:
        lines.append(f"- appId={s['appId']} | lastSignIn={s['lastSignIn']}")
    return "\n".join(lines)


@mcp.tool()
async def entra_workload_identity_posture(top: int = 50) -> str:
    """Run a workload identity posture scan across application-type service principals.

    Checks credential count, credential expiry, permission count, and flags issues.

    Args:
        top: Max service principals to scan (default 50).
    """
    client = get_graph_client()
    now = datetime.now(timezone.utc)

    # Fetch application-type service principals
    query = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
        filter="servicePrincipalType eq 'Application'",
        select=[
            "id", "appId", "displayName",
            "passwordCredentials", "keyCredentials",
        ],
        top=min(top, 999),
    )
    config = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
        query_parameters=query,
    )
    result = await client.service_principals.get(request_configuration=config)
    sps = result.value if result and result.value else []

    total = len(sps)
    expired_creds_count = 0
    over_privileged_count = 0
    summary_lines: list[str] = []

    for sp in sps:
        # Check credentials
        passwords = sp.password_credentials or []
        certs = sp.key_credentials or []
        all_creds = passwords + certs
        cred_count = len(all_creds)

        has_expired = any(
            c.end_date_time and c.end_date_time < now
            for c in all_creds
        )
        if has_expired:
            expired_creds_count += 1

        # Check app role assignments (permission count)
        role_result = await client.service_principals.by_service_principal_id(
            sp.id,
        ).app_role_assignments.get()
        role_count = len(role_result.value) if role_result and role_result.value else 0

        if role_count > 10:
            over_privileged_count += 1

        # Flag issues
        issues: list[str] = []
        if has_expired:
            issues.append("EXPIRED_CRED")
        if role_count > 10:
            issues.append(f"OVER_PRIVILEGED({role_count} roles)")
        if cred_count == 0:
            issues.append("NO_CREDENTIALS")

        if issues:
            summary_lines.append(
                f"- {sp.display_name} (appId={sp.app_id}): "
                + ", ".join(issues)
            )

    report = [
        "=== Workload Identity Posture Report ===",
        f"Service principals scanned: {total}",
        f"SPs with expired credentials: {expired_creds_count}",
        f"Over-privileged SPs (>10 app roles): {over_privileged_count}",
    ]

    if summary_lines:
        report.append(f"\nFlagged service principals ({len(summary_lines)}):")
        report.extend(summary_lines)
    else:
        report.append("\nNo issues found.")

    return "\n".join(report)
