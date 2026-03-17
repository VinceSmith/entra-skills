"""Identity Governance tools — access reviews, entitlement management, lifecycle workflows, PIM."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import httpx

from .graph_client import get_credential, get_graph_client
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


# ---------------------------------------------------------------------------
# Access Reviews (v1.0 Graph SDK)
# ---------------------------------------------------------------------------


@mcp.tool()
async def entra_list_access_reviews(top: int = 25) -> str:
    """List access review definitions. Requires AccessReview.Read.All permission.

    Args:
        top: Max results (default 25).
    """
    client = get_graph_client()
    result = await client.identity_governance.access_reviews.definitions.get()

    if not result or not result.value:
        return "No access review definitions found."

    reviews = result.value[:top]
    lines = [f"Found {len(reviews)} access review definition(s):"]
    for r in reviews:
        scope_type = ""
        if r.scope and hasattr(r.scope, "odata_type"):
            scope_type = r.scope.odata_type or ""
        lines.append(
            f"- {r.id} | {r.display_name} | Status: {r.status} | Scope: {scope_type}"
        )
    return "\n".join(lines)


@mcp.tool()
async def entra_create_access_review(
    display_name: str,
    scope_type: str,
    scope_id: str,
    reviewer_ids: str,
    duration_days: int = 14,
) -> str:
    """Create an access review definition. Requires AccessReview.ReadWrite.All. Uses beta API.

    Args:
        display_name: Review display name.
        scope_type: 'group' or 'application'.
        scope_id: Object ID of the group or application to review.
        reviewer_ids: Comma-separated object IDs of reviewers.
        duration_days: Review duration in days (default 14).
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    if scope_type not in ("group", "application"):
        return "Error: scope_type must be 'group' or 'application'."

    reviewers = []
    for rid in reviewer_ids.split(","):
        rid = rid.strip()
        if rid:
            reviewers.append({
                "query": f"/users/{rid}",
                "queryType": "MicrosoftGraph",
            })

    if not reviewers:
        return "Error: At least one reviewer ID is required."

    start_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

    body: dict = {
        "displayName": display_name,
        "scope": {
            "@odata.type": f"#microsoft.graph.accessReviewQueryScope",
            "query": f"/groups/{scope_id}/members" if scope_type == "group"
            else f"/servicePrincipals/{scope_id}/appRoleAssignedTo",
            "queryType": "MicrosoftGraph",
        },
        "reviewers": reviewers,
        "settings": {
            "mailNotificationsEnabled": True,
            "justificationRequiredOnApproval": True,
            "defaultDecisionEnabled": False,
            "defaultDecision": "None",
            "instanceDurationInDays": duration_days,
            "recurrence": {
                "pattern": None,
                "range": {
                    "type": "numbered",
                    "startDate": start_date[:10],
                    "numberOfOccurrences": 1,
                },
            },
        },
    }

    result = await _graph_beta_request(
        "POST", "/identityGovernance/accessReviews/definitions", body,
    )
    return (
        f"Created access review:\n"
        f"  ID: {result.get('id')}\n"
        f"  Display Name: {result.get('displayName')}\n"
        f"  Status: {result.get('status')}\n"
        f"  Scope: {scope_type} ({scope_id})\n"
        f"  Duration: {duration_days} days"
    )


# ---------------------------------------------------------------------------
# Entitlement Management — Access Packages (v1.0 Graph SDK)
# ---------------------------------------------------------------------------


@mcp.tool()
async def entra_list_access_packages(catalog_id: str = "", top: int = 25) -> str:
    """List entitlement management access packages. Requires EntitlementManagement.Read.All.

    Args:
        catalog_id: Optional catalog ID to filter packages.
        top: Max results (default 25).
    """
    client = get_graph_client()
    result = await client.identity_governance.entitlement_management.access_packages.get()

    if not result or not result.value:
        return "No access packages found."

    packages = result.value
    if catalog_id:
        packages = [p for p in packages if getattr(p, "catalog_id", None) == catalog_id]

    packages = packages[:top]
    if not packages:
        return f"No access packages found for catalog '{catalog_id}'."

    lines = [f"Found {len(packages)} access package(s):"]
    for p in packages:
        catalog = getattr(p, "catalog_id", "N/A")
        lines.append(
            f"- {p.id} | {p.display_name} | Catalog: {catalog} | "
            f"Modified: {getattr(p, 'modified_date_time', 'N/A')}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lifecycle Workflows (beta API)
# ---------------------------------------------------------------------------


@mcp.tool()
async def entra_list_lifecycle_workflows(top: int = 25) -> str:
    """List Identity Governance lifecycle workflows. Requires LifecycleWorkflows.Read.All.

    Args:
        top: Max results (default 25).
    """
    result = await _graph_beta_request(
        "GET", f"/identityGovernance/lifecycleWorkflows/workflows?$top={top}",
    )

    workflows = result.get("value", [])
    if not workflows:
        return "No lifecycle workflows found."

    lines = [f"Found {len(workflows)} lifecycle workflow(s):"]
    for w in workflows:
        last_run = w.get("lastModifiedDateTime", "N/A")
        lines.append(
            f"- {w.get('id')} | {w.get('displayName')} | "
            f"Category: {w.get('category', 'N/A')} | "
            f"State: {w.get('isEnabled', False)} | "
            f"Last Modified: {last_run}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# PIM Role Assignments (beta API)
# ---------------------------------------------------------------------------


@mcp.tool()
async def entra_list_pim_role_assignments(
    principal_id: str = "",
    role_filter: str = "",
    top: int = 25,
) -> str:
    """List eligible PIM role assignment schedule instances. Requires RoleEligibilitySchedule.Read.Directory.

    Args:
        principal_id: Optional principal ID to filter assignments.
        role_filter: Optional role definition ID to filter by role.
        top: Max results (default 25).
    """
    filters = []
    if principal_id:
        filters.append(f"principalId eq '{principal_id}'")
    if role_filter:
        filters.append(f"roleDefinitionId eq '{role_filter}'")

    path = f"/roleManagement/directory/roleEligibilityScheduleInstances?$top={top}"
    if filters:
        path += f"&$filter={' and '.join(filters)}"

    result = await _graph_beta_request("GET", path)

    assignments = result.get("value", [])
    if not assignments:
        return "No eligible PIM role assignments found."

    lines = [f"Found {len(assignments)} eligible PIM role assignment(s):"]
    for a in assignments:
        lines.append(
            f"- Principal: {a.get('principalId')} | "
            f"Role: {a.get('roleDefinitionId')} | "
            f"Scope: {a.get('directoryScopeId', '/')} | "
            f"Start: {a.get('startDateTime', 'N/A')} | "
            f"End: {a.get('endDateTime', 'N/A')}"
        )
    return "\n".join(lines)


@mcp.tool()
async def entra_activate_pim_role(
    role_definition_id: str,
    principal_id: str,
    justification: str,
    duration_hours: int = 8,
) -> str:
    """Activate a PIM eligible role assignment. Requires RoleAssignmentSchedule.ReadWrite.Directory.

    Args:
        role_definition_id: The role definition ID to activate.
        principal_id: The principal (user/SP) ID requesting activation.
        justification: Business justification for activation (required).
        duration_hours: Activation duration in hours (default 8).
    """
    if not _is_write_enabled():
        return "Error: Write operations require ENTRA_MCP_MODE=full."

    if not justification.strip():
        return "Error: Justification is required for PIM role activation."

    start = datetime.now(timezone.utc)
    expiration = start + timedelta(hours=duration_hours)

    body = {
        "action": "selfActivate",
        "principalId": principal_id,
        "roleDefinitionId": role_definition_id,
        "directoryScopeId": "/",
        "justification": justification,
        "scheduleInfo": {
            "startDateTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expiration": {
                "type": "afterDuration",
                "duration": f"PT{duration_hours}H",
            },
        },
    }

    result = await _graph_beta_request(
        "POST", "/roleManagement/directory/roleAssignmentScheduleRequests", body,
    )
    return (
        f"PIM role activation requested:\n"
        f"  ID: {result.get('id')}\n"
        f"  Role: {result.get('roleDefinitionId')}\n"
        f"  Principal: {result.get('principalId')}\n"
        f"  Status: {result.get('status')}\n"
        f"  Duration: {duration_hours}h\n"
        f"  Justification: {justification}"
    )
