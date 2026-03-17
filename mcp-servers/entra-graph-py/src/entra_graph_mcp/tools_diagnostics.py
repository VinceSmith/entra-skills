"""Identity diagnostics tools — sign-in logs, audit logs, risk detection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from msgraph.generated.audit_logs.directory_audits.directory_audits_request_builder import (
    DirectoryAuditsRequestBuilder,
)
from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import SignInsRequestBuilder

from .graph_client import get_graph_client
from .server import mcp


@mcp.tool()
async def entra_get_signin_logs(
    user_id: str = "",
    app_name: str = "",
    failed_only: bool = False,
    hours: int = 24,
    top: int = 50,
) -> str:
    """Query Entra sign-in logs. Requires AuditLog.Read.All permission and P1 license.

    Args:
        user_id: Filter by user ID or UPN.
        app_name: Filter by application display name.
        failed_only: Show only failed sign-ins.
        hours: How far back to query (default 24 hours).
        top: Max results (default 50).
    """
    client = get_graph_client()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    filters = [f"createdDateTime ge {since}"]

    if user_id:
        filters.append(f"userId eq '{user_id}'")
    if app_name:
        filters.append(f"appDisplayName eq '{app_name}'")
    if failed_only:
        filters.append("status/errorCode ne 0")

    query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
        filter=" and ".join(filters),
        select=["userDisplayName", "appDisplayName", "ipAddress", "status",
                "location", "conditionalAccessStatus", "createdDateTime"],
        top=min(top, 999),
        orderby=["createdDateTime desc"],
    )
    config = SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(query_parameters=query)
    result = await client.audit_logs.sign_ins.get(request_configuration=config)

    if not result or not result.value:
        return "No sign-in logs found matching criteria."

    lines = [f"Found {len(result.value)} sign-in(s):"]
    for s in result.value:
        error = s.status.error_code if s.status else 0
        status = "OK" if error == 0 else f"FAILED({error})"
        city = s.location.city if s.location and s.location.city else "?"
        lines.append(
            f"- {s.created_date_time} | {s.user_display_name or 'N/A'} | "
            f"{s.app_display_name or 'N/A'} | {status} | {s.ip_address or '?'} ({city})"
        )
    return "\n".join(lines)


@mcp.tool()
async def entra_get_audit_logs(
    activity: str = "",
    hours: int = 24,
    top: int = 50,
) -> str:
    """Query Entra directory audit logs. Requires AuditLog.Read.All permission.

    Args:
        activity: Filter by activity display name (e.g. 'Add application').
        hours: How far back to query (default 24 hours).
        top: Max results (default 50).
    """
    client = get_graph_client()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    filters = [f"activityDateTime ge {since}"]

    if activity:
        filters.append(f"activityDisplayName eq '{activity}'")

    query = DirectoryAuditsRequestBuilder.DirectoryAuditsRequestBuilderGetQueryParameters(
        filter=" and ".join(filters),
        top=min(top, 999),
        orderby=["activityDateTime desc"],
    )
    config = DirectoryAuditsRequestBuilder.DirectoryAuditsRequestBuilderGetRequestConfiguration(
        query_parameters=query,
    )
    result = await client.audit_logs.directory_audits.get(request_configuration=config)

    if not result or not result.value:
        return "No audit log entries found."

    lines = [f"Found {len(result.value)} audit entry(ies):"]
    for a in result.value:
        initiated = "system"
        if a.initiated_by:
            if a.initiated_by.user and a.initiated_by.user.user_principal_name:
                initiated = a.initiated_by.user.user_principal_name
            elif a.initiated_by.app and a.initiated_by.app.display_name:
                initiated = a.initiated_by.app.display_name
        target = ""
        if a.target_resources and len(a.target_resources) > 0:
            target = f" → {a.target_resources[0].display_name or a.target_resources[0].id}"
        lines.append(f"- {a.activity_date_time} | {a.activity_display_name} | by: {initiated}{target}")
    return "\n".join(lines)


@mcp.tool()
async def entra_check_user_risk(user_id: str = "", top: int = 25) -> str:
    """Check Identity Protection risky users. Requires P2 license and IdentityRiskyUser.Read.All.

    Args:
        user_id: Specific user ID, or empty to list all risky users.
        top: Max results (default 25).
    """
    client = get_graph_client()
    if user_id:
        user = await client.identity_protection.risky_users.by_risky_user_id(user_id).get()
        if not user:
            return f"User '{user_id}' not found in risky users."
        return (
            f"User: {user.user_display_name}\n"
            f"Risk Level: {user.risk_level}\n"
            f"Risk State: {user.risk_state}\n"
            f"Risk Detail: {user.risk_detail}\n"
            f"Last Updated: {user.risk_last_updated_date_time}"
        )

    result = await client.identity_protection.risky_users.get()
    if not result or not result.value:
        return "No risky users detected."

    lines = [f"Found {len(result.value)} risky user(s):"]
    for u in result.value:
        lines.append(f"- {u.user_display_name} | Risk: {u.risk_level} | State: {u.risk_state}")
    return "\n".join(lines)


@mcp.tool()
async def entra_evaluate_conditional_access(user_id: str, app_id: str) -> str:
    """Evaluate what CA policies would apply for a user+app combination.
    Returns sign-in log entries showing CA evaluation results.

    Args:
        user_id: User ID or UPN.
        app_id: Application (client) ID.
    """
    client = get_graph_client()
    query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
        filter=f"userId eq '{user_id}' and appId eq '{app_id}'",
        select=["userDisplayName", "appDisplayName", "conditionalAccessStatus",
                "appliedConditionalAccessPolicies", "createdDateTime"],
        top=10,
        orderby=["createdDateTime desc"],
    )
    config = SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(query_parameters=query)
    result = await client.audit_logs.sign_ins.get(request_configuration=config)

    if not result or not result.value:
        return "No recent sign-in data for this user+app combination. Try signing in first."

    lines = [f"CA evaluation for recent sign-ins ({len(result.value)}):"]
    for s in result.value:
        lines.append(f"\nSign-in at {s.created_date_time} — CA Status: {s.conditional_access_status}")
        for p in s.applied_conditional_access_policies or []:
            lines.append(f"  Policy: {p.display_name} — Result: {p.result}")
    return "\n".join(lines)
