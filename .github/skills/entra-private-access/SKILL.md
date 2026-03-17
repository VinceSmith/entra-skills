---
name: entra-private-access
description: "Entra Private Access (Global Secure Access) — Zero Trust Network Access replacing VPN, traffic forwarding profiles, Quick Access apps, per-app ZTNA, connector groups, app segments, traffic logs via Microsoft Graph beta."
---

# Entra Private Access

Entra Private Access is the **Zero Trust Network Access (ZTNA)** component of Microsoft's Security Service Edge (SSE) solution, replacing traditional VPN with identity-centric, per-app access to private resources. It works alongside Entra Internet Access under the **Global Secure Access** umbrella. Core components: Global Secure Access client (on devices), connector groups (on-premises), and app segments (defining reachable destinations).

> **Note:** Most APIs below use the Microsoft Graph **beta** endpoint and are subject to change.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List forwarding profiles | `GET /beta/networkAccess/forwardingProfiles` | `NetworkAccess.Read.All` |
| Update forwarding profile | `PATCH /beta/networkAccess/forwardingProfiles/{id}` | `NetworkAccess.ReadWrite.All` |
| List forwarding policies | `GET /beta/networkAccess/forwardingProfiles/{id}/policies` | `NetworkAccess.Read.All` |
| Get Quick Access app | `GET /beta/networkAccess/connectivity/remoteNetworks` | `NetworkAccess.Read.All` |
| List app segments | `GET /beta/applications/{appId}/onPremisesPublishing/segmentsConfiguration/applicationSegments` | `NetworkAccess.ReadWrite.All` |
| Create app segment | `POST /beta/applications/{appId}/onPremisesPublishing/segmentsConfiguration/applicationSegments` | `NetworkAccess.ReadWrite.All` |
| List connector groups | `GET /beta/onPremisesPublishingProfiles/provisioning/connectorGroups` | `Directory.ReadWrite.All` |
| List connectors | `GET /beta/onPremisesPublishingProfiles/provisioning/connectorGroups/{id}/members` | `Directory.ReadWrite.All` |
| Get connector health | `GET /beta/onPremisesPublishingProfiles/provisioning/connectors/{id}` | `Directory.ReadWrite.All` |
| Traffic logs | `GET /beta/networkAccess/logs/traffic` | `NetworkAccessPolicy.Read.All` |

## Traffic Forwarding Profiles

Three profiles control which traffic the Global Secure Access client captures:

| Profile | Purpose | Default State |
|---------|---------|---------------|
| **Private access** | Routes traffic to private apps through connectors | Disabled |
| **Microsoft 365** | Routes M365 traffic through SSE | Disabled |
| **Internet access** | Routes all internet traffic through SSE | Disabled |

Enable profiles individually — start with **private access** for ZTNA scenarios.

```python
import httpx
from azure.identity.aio import DefaultAzureCredential

GRAPH_BETA = "https://graph.microsoft.com/beta"

async def list_forwarding_profiles() -> list[dict]:
    """List all traffic forwarding profiles and their state."""
    credential = DefaultAzureCredential()
    token = await credential.get_token("https://graph.microsoft.com/.default")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BETA}/networkAccess/forwardingProfiles",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        resp.raise_for_status()
        return resp.json().get("value", [])
    await credential.close()
```

## Quick Access Application

Quick Access is the **default enterprise app** that provides broad private-network access. Define app segments to specify which FQDNs, IPs, or CIDR ranges are reachable.

### App Segment Types

| Type | Example | Use Case |
|------|---------|----------|
| FQDN | `erp.contoso.local` | Specific internal hostname |
| IP address | `10.1.2.3` | Single host by IP |
| IP/CIDR | `10.1.0.0/16` | Subnet range |

Each segment includes **port ranges** and **protocol** (`tcp`, `udp`, or both).

### Create an App Segment

```python
async def create_app_segment(
    app_object_id: str,
    destination_host: str,
    ports: list[str],
    protocol: str = "tcp",
) -> dict:
    """Add an app segment to a Quick Access or Private Access app.

    Args:
        app_object_id: Object ID of the enterprise app.
        destination_host: FQDN or IP/CIDR (e.g. 'erp.contoso.local' or '10.1.0.0/16').
        ports: Port ranges (e.g. ['443', '8080-8090']).
        protocol: 'tcp', 'udp', or 'tcp,udp'.
    """
    credential = DefaultAzureCredential()
    token = await credential.get_token("https://graph.microsoft.com/.default")

    # Determine destination type
    if "/" in destination_host:
        dest_type = "ipRangeCidr"
    elif destination_host.replace(".", "").isdigit():
        dest_type = "ip"
    else:
        dest_type = "fqdn"

    body = {
        "destinationHost": destination_host,
        "destinationType": dest_type,
        "ports": ports,
        "protocol": protocol,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{GRAPH_BETA}/applications/{app_object_id}"
            "/onPremisesPublishing/segmentsConfiguration/applicationSegments",
            headers={
                "Authorization": f"Bearer {token.token}",
                "Content-Type": "application/json",
            },
            json=body,
        )
        resp.raise_for_status()
        return resp.json()
    await credential.close()
```

## Per-App Private Access (Granular ZTNA)

For **granular** zero-trust access, create individual enterprise apps per private resource instead of using Quick Access. Each app gets its own:
- App segments (FQDNs/IPs + ports)
- Conditional Access policy
- User/group assignment
- Connector group assignment

This provides **least-privilege network access** — users only reach the specific resources they need.

### Typical Per-App Setup

1. Create an enterprise app in Entra ID (see `entra-app-registration`)
2. Configure `onPremisesPublishing` with connector group assignment
3. Add app segments (destinations + ports + protocol)
4. Assign users/groups to the app
5. Create a CA policy targeting the app (see `entra-conditional-access`)

## Connector Groups

Private Network Connectors run on Windows servers inside your network and tunnel traffic from the cloud to on-premises resources. Connectors are organized into **groups** for redundancy and network segmentation.

### Check Connector Health

```python
async def list_connector_groups_with_health() -> list[dict]:
    """List connector groups and the health status of each connector."""
    credential = DefaultAzureCredential()
    token = await credential.get_token("https://graph.microsoft.com/.default")
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BETA}/onPremisesPublishingProfiles/provisioning/connectorGroups"
            "?$expand=members",
            headers={"Authorization": f"Bearer {token.token}"},
        )
        resp.raise_for_status()
        groups = resp.json().get("value", [])

    results = []
    for group in groups:
        connectors = group.get("members", [])
        results.append({
            "groupName": group["displayName"],
            "groupId": group["id"],
            "connectors": [
                {
                    "machineName": c.get("machineName"),
                    "status": c.get("status"),  # active | inactive
                    "externalIp": c.get("externalIp"),
                }
                for c in connectors
            ],
        })
    await credential.close()
    return results
```

### CLI — List Connector Groups

```bash
az rest --method GET \
  --url "https://graph.microsoft.com/beta/onPremisesPublishingProfiles/provisioning/connectorGroups" \
  --headers "Content-Type=application/json"
```

## Traffic Logs

Global Secure Access logs all tunneled traffic. Use these logs for connection monitoring, troubleshooting, and compliance.

```python
async def query_traffic_logs(
    top: int = 50,
    filter_expr: str | None = None,
) -> list[dict]:
    """Query Global Secure Access traffic logs.

    Args:
        top: Number of records to return.
        filter_expr: OData filter (e.g. "action eq 'blocked'").
    """
    credential = DefaultAzureCredential()
    token = await credential.get_token("https://graph.microsoft.com/.default")

    params: dict[str, str | int] = {"$top": top}
    if filter_expr:
        params["$filter"] = filter_expr

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GRAPH_BETA}/networkAccess/logs/traffic",
            headers={"Authorization": f"Bearer {token.token}"},
            params=params,
        )
        resp.raise_for_status()
        return resp.json().get("value", [])
    await credential.close()
```

### CLI — Query Traffic Logs

```bash
az rest --method GET \
  --url "https://graph.microsoft.com/beta/networkAccess/logs/traffic?\$top=20" \
  --headers "Content-Type=application/json"
```

## Deployment Flow

| Step | Action | Tooling |
|------|--------|---------|
| 1 | Enable Global Secure Access in the Entra admin center | Portal / Graph API |
| 2 | Install Private Network Connectors on Windows servers in each network segment | MSI installer |
| 3 | Create connector groups and assign connectors | Graph API / Portal |
| 4 | Configure Quick Access (broad) or per-app access (granular) | Graph API / Portal |
| 5 | Add app segments — FQDNs, IPs, ports, protocols | Graph API |
| 6 | Assign users/groups to the enterprise apps | Graph API (see `entra-users-groups`) |
| 7 | Deploy the Global Secure Access client to devices via Intune/GPO | Intune / SCCM |
| 8 | Create Conditional Access policies targeting Global Secure Access traffic | Graph API (see `entra-conditional-access`) |

## Security Considerations

- **Connector placement:** Deploy connectors in the same network segment as target resources — avoid routing through unnecessary network hops.
- **Connector redundancy:** Minimum two connectors per group for high availability.
- **Least-privilege access:** Prefer per-app access over Quick Access to limit lateral movement.
- **CA policies:** Always apply Conditional Access to private access apps — enforce MFA, device compliance, and risk checks.
- **Network segmentation:** Use separate connector groups for different security zones (prod vs. dev).
- **Beta API caution:** Graph beta endpoints may change without notice — pin API versions in production, add defensive error handling.
- **Credentials:** Never hardcode tokens or secrets. Use `DefaultAzureCredential` for all token acquisition.

## Cross-References

| Skill | Relevance |
|-------|-----------|
| `entra-conditional-access` | CA policies targeting Global Secure Access traffic forwarding profiles and private access apps |
| `entra-app-registration` | Enterprise app configuration for Quick Access and per-app private access |
| `entra-users-groups` | User/group assignment to private access apps for scoped access |
| `entra-audit-signin-logs` | Sign-in logs for private access apps — connection success/failure analysis |
| `entra-managed-identity` | Managed identity for connector VMs and automation service principals |
