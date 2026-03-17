"""App registration management tools."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from msgraph.generated.applications.applications_request_builder import ApplicationsRequestBuilder
from msgraph.generated.models.application import Application
from msgraph.generated.models.web_application import WebApplication
from msgraph.generated.models.required_resource_access import RequiredResourceAccess

from .graph_client import get_graph_client
from .server import mcp, _is_write_enabled


@mcp.tool()
async def entra_list_apps(search: str = "", top: int = 25) -> str:
    """Search/filter Entra app registrations.

    Args:
        search: Display name search (startsWith match).
        top: Max results (default 25).
    """
    client = get_graph_client()
    filter_str = f"startswith(displayName,'{search}')" if search else None

    query = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetQueryParameters(
        filter=filter_str,
        select=["id", "appId", "displayName", "signInAudience", "createdDateTime"],
        top=min(top, 999),
        orderby=["displayName"],
    )
    config = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetRequestConfiguration(query_parameters=query)
    if search:
        config.headers.add("ConsistencyLevel", "eventual")

    result = await client.applications.get(request_configuration=config)
    if not result or not result.value:
        return "No app registrations found."

    lines = [f"Found {len(result.value)} app(s):"]
    for app in result.value:
        lines.append(f"- {app.display_name} (appId={app.app_id}, audience={app.sign_in_audience})")
    return "\n".join(lines)


@mcp.tool()
async def entra_get_app(app_id: str) -> str:
    """Get detailed app registration info by object ID or appId.

    Args:
        app_id: Application object ID or client ID (appId).
    """
    client = get_graph_client()
    # Try by object ID first, fall back to filter by appId
    try:
        app = await client.applications.by_application_id(app_id).get()
    except Exception:
        query = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetQueryParameters(
            filter=f"appId eq '{app_id}'",
        )
        config = ApplicationsRequestBuilder.ApplicationsRequestBuilderGetRequestConfiguration(query_parameters=query)
        result = await client.applications.get(request_configuration=config)
        if not result or not result.value:
            return f"App '{app_id}' not found."
        app = result.value[0]

    cred_count = len(app.password_credentials or []) + len(app.key_credentials or [])
    return (
        f"Display Name: {app.display_name}\n"
        f"App (Client) ID: {app.app_id}\n"
        f"Object ID: {app.id}\n"
        f"Sign-in Audience: {app.sign_in_audience}\n"
        f"Created: {app.created_date_time}\n"
        f"Credentials: {cred_count} (secrets + certificates)\n"
        f"Publisher Domain: {app.publisher_domain or 'N/A'}"
    )


@mcp.tool()
async def entra_list_app_permissions(app_object_id: str) -> str:
    """List configured API permissions for an app registration.

    Args:
        app_object_id: Application object ID.
    """
    client = get_graph_client()
    app = await client.applications.by_application_id(app_object_id).get()
    if not app:
        return f"App '{app_object_id}' not found."

    if not app.required_resource_access:
        return f"App '{app.display_name}' has no configured API permissions."

    lines = [f"Permissions for '{app.display_name}':"]
    for rra in app.required_resource_access:
        resource_id = rra.resource_app_id
        for perm in rra.resource_access or []:
            perm_type = "Application" if perm.type == "Role" else "Delegated"
            lines.append(f"- Resource: {resource_id} | {perm_type} | ID: {perm.id}")
    return "\n".join(lines)


@mcp.tool()
async def entra_check_credential_expiry(
    app_object_id: str = "",
    days_warning: int = 30,
) -> str:
    """Check secret/certificate expiry for app registrations.

    Args:
        app_object_id: Specific app object ID, or empty to scan all apps.
        days_warning: Days threshold for expiry warning (default 30).
    """
    client = get_graph_client()
    now = datetime.now(timezone.utc)
    warning_date = now + timedelta(days=days_warning)

    if app_object_id:
        app = await client.applications.by_application_id(app_object_id).get()
        apps_list = [app] if app else []
    else:
        result = await client.applications.get()
        apps_list = result.value if result and result.value else []

    findings: list[str] = []
    for app in apps_list:
        for cred in app.password_credentials or []:
            if cred.end_date_time and cred.end_date_time < warning_date:
                status = "EXPIRED" if cred.end_date_time < now else "EXPIRING SOON"
                findings.append(
                    f"[{status}] {app.display_name} — secret '{cred.display_name or 'unnamed'}' "
                    f"expires {cred.end_date_time.date()}"
                )
        for cred in app.key_credentials or []:
            if cred.end_date_time and cred.end_date_time < warning_date:
                status = "EXPIRED" if cred.end_date_time < now else "EXPIRING SOON"
                findings.append(
                    f"[{status}] {app.display_name} — certificate '{cred.display_name or 'unnamed'}' "
                    f"expires {cred.end_date_time.date()}"
                )

    if not findings:
        return f"No credentials expiring within {days_warning} days."
    return f"Found {len(findings)} credential(s) expiring:\n" + "\n".join(findings)


@mcp.tool()
async def entra_create_app_registration(
    display_name: str,
    sign_in_audience: str = "AzureADMyOrg",
    redirect_uri: str = "",
) -> str:
    """Create a new app registration. Requires ENTRA_MCP_MODE=full.

    Args:
        display_name: Name for the app registration.
        sign_in_audience: AzureADMyOrg (single-tenant), AzureADMultipleOrgs, or AzureADandPersonalMicrosoftAccount.
        redirect_uri: Optional redirect URI for web platform.
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    client = get_graph_client()
    app = Application(
        display_name=display_name,
        sign_in_audience=sign_in_audience,
    )
    if redirect_uri:
        app.web = WebApplication(redirect_uris=[redirect_uri])

    result = await client.applications.post(app)
    return (
        f"Created app registration:\n"
        f"  Display Name: {result.display_name}\n"
        f"  App (Client) ID: {result.app_id}\n"
        f"  Object ID: {result.id}\n"
        f"  Audience: {result.sign_in_audience}\n"
        f"\nNext steps: Add credentials (prefer MI/WIF over secrets) and configure API permissions."
    )
