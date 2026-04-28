---
name: entra-agent-id
description: |
  Microsoft Entra Agent ID (preview) for creating OAuth2-capable AI agent identities via Microsoft Graph beta API.
  Covers Agent Identity Blueprints, BlueprintPrincipals, Agent Identities, required permissions, sponsors, and Workload Identity Federation.
  Triggers: "agent identity", "agent id", "Agent Identity Blueprint", "BlueprintPrincipal", "entra agent", "agent identity provisioning", "Graph agent identity".
---

# Microsoft Entra Agent ID

Create and manage OAuth2-capable identities for AI agents using Microsoft Graph beta API.

> **Preview API** — All Agent Identity endpoints are under `/beta` only. Not available in `/v1.0`.

## Before You Start

Search `microsoft-docs` MCP for the latest Agent ID documentation:
- Query: "Microsoft Entra agent identity setup"
- Verify: API parameters match current preview behavior

## Conceptual Model

```
Agent Identity Blueprint (application)        ← one per agent type/project
  └── BlueprintPrincipal (service principal)   ← MUST be created explicitly
        ├── Agent Identity (SP): agent-1       ← one per agent instance
        ├── Agent Identity (SP): agent-2
        └── Agent Identity (SP): agent-3
```

## Prerequisites

### PowerShell (recommended for interactive setup)

```powershell
# Requires PowerShell 7+
Install-Module Microsoft.Graph.Beta.Applications -Scope CurrentUser -Force
```

### Python (for programmatic provisioning)

```bash
pip install azure-identity requests
```

### Required Entra Roles

One of: **Agent Identity Developer**, **Agent Identity Administrator**, or **Application Administrator**.

## Environment Variables

```bash
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<app-registration-client-id>
AZURE_CLIENT_SECRET=<app-registration-secret>
```

## Authentication

> **⚠️ `DefaultAzureCredential` is NOT supported.** Azure CLI tokens contain
> `Directory.AccessAsUser.All`, which Agent Identity APIs explicitly reject (403).
> You MUST use a dedicated app registration with `client_credentials` flow or
> connect via `Connect-MgGraph` with explicit delegated scopes.

### PowerShell (delegated permissions)

```powershell
Connect-MgGraph -Scopes @(
    "AgentIdentityBlueprint.Create",
    "AgentIdentityBlueprint.ReadWrite.All",
    "AgentIdentityBlueprintPrincipal.Create",
    "User.Read"
)
Set-MgRequestContext -ApiVersion beta

$currentUser = (Get-MgContext).Account
$userId = (Get-MgUser -UserId $currentUser).Id
```

### Python (application permissions)

```python
import os
import requests
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)
token = credential.get_token("https://graph.microsoft.com/.default")

GRAPH = "https://graph.microsoft.com/beta"
headers = {
    "Authorization": f"Bearer {token.token}",
    "Content-Type": "application/json",
    "OData-Version": "4.0",  # Required for all Agent Identity API calls
}
```

## Core Workflow

### Step 1: Create Agent Identity Blueprint

Sponsors are required and **must be User objects** — ServicePrincipals and Groups are rejected.

```python
import subprocess

# Get sponsor user ID (client_credentials has no user context, so use az CLI)
result = subprocess.run(
    ["az", "ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"],
    capture_output=True, text=True, check=True,
)
user_id = result.stdout.strip()

blueprint_body = {
    "@odata.type": "Microsoft.Graph.AgentIdentityBlueprint",
    "displayName": "My Agent Blueprint",
    "sponsors@odata.bind": [
        f"https://graph.microsoft.com/beta/users/{user_id}"
    ],
}
resp = requests.post(f"{GRAPH}/applications", headers=headers, json=blueprint_body)
resp.raise_for_status()

blueprint = resp.json()
app_id = blueprint["appId"]
blueprint_obj_id = blueprint["id"]
```

### Step 2: Create BlueprintPrincipal

> **This step is mandatory.** Creating a Blueprint does NOT auto-create its
> service principal. Without this, Agent Identity creation fails with:
> `400: The Agent Blueprint Principal for the Agent Blueprint does not exist.`

```python
sp_body = {
    "@odata.type": "Microsoft.Graph.AgentIdentityBlueprintPrincipal",
    "appId": app_id,
}
resp = requests.post(f"{GRAPH}/servicePrincipals", headers=headers, json=sp_body)
resp.raise_for_status()
```

If implementing idempotent scripts, check for and create the BlueprintPrincipal
even when the Blueprint already exists (a previous run may have created the Blueprint
but crashed before creating the SP).

### Discover: List & Find Existing Blueprints

> **⚠️ Footgun:** Blueprints are stored as `application` objects but **do NOT
> appear in the default `/applications` collection**. A query like
> `GET /applications?$filter=displayName eq 'my-blueprint'` returns an empty
> `value` array — silently — even when the blueprint exists. You must use the
> derived-type cast collection.

```bash
# List ALL blueprints in the tenant
GET https://graph.microsoft.com/beta/applications/microsoft.graph.agentIdentityBlueprint

# Find one by displayName (filter works on the cast collection)
GET https://graph.microsoft.com/beta/applications/microsoft.graph.agentIdentityBlueprint?$filter=displayName eq 'my-blueprint'

# Get a single blueprint by object id (cast not required for direct GET by id)
GET https://graph.microsoft.com/beta/applications/{blueprint-object-id}
```

```powershell
# PowerShell + az CLI
$res = az rest --method GET `
  --url "https://graph.microsoft.com/beta/applications/microsoft.graph.agentIdentityBlueprint" `
  --headers "OData-Version=4.0" -o json | ConvertFrom-Json
$res.value | Select-Object displayName, appId, id
```

### Update a Blueprint (PATCH)

Used for adding `requiredResourceAccess` (delegated/app permission scopes the
agent will request), updating `identifierUris`, tags, etc. PATCH targets the
plain `/applications/{id}` URL — the type cast is **not** required on the
resource segment, but the body should still include the `@odata.type`
discriminator for any nested complex types when the property requires it.

```python
# Example: add Microsoft Graph User.Read delegated permission to a blueprint
GRAPH_APP_ID    = "00000003-0000-0000-c000-000000000000"
USER_READ_SCOPE = "e1fe6dd8-ba31-4d61-89e7-88639da4683d"  # delegated

# 1. GET current requiredResourceAccess so you don't clobber existing entries
existing = requests.get(
    f"{GRAPH}/applications/{blueprint_obj_id}?$select=requiredResourceAccess",
    headers=headers,
).json()
rra = existing.get("requiredResourceAccess", [])

# 2. Merge the new scope into the Microsoft Graph entry
graph_entry = next((r for r in rra if r["resourceAppId"] == GRAPH_APP_ID), None)
if graph_entry is None:
    rra.append({
        "resourceAppId": GRAPH_APP_ID,
        "resourceAccess": [{"id": USER_READ_SCOPE, "type": "Scope"}],
    })
else:
    if not any(a["id"] == USER_READ_SCOPE for a in graph_entry["resourceAccess"]):
        graph_entry["resourceAccess"].append({"id": USER_READ_SCOPE, "type": "Scope"})

# 3. PATCH back (whole array — Graph replaces, doesn't merge)
requests.patch(
    f"{GRAPH}/applications/{blueprint_obj_id}",
    headers=headers,
    json={"requiredResourceAccess": rra},
).raise_for_status()
```

> **PATCH replaces, doesn't merge.** Always GET → mutate → PATCH the full
> `requiredResourceAccess` array. Sending only the new entry will wipe everything else.

After PATCHing, the **agent identity SP** still needs an `oauth2PermissionGrant`
for the new scope to actually issue tokens (see Best Practice #10).

`type` values inside `resourceAccess`:
- `"Scope"` → delegated permission
- `"Role"` → application permission

Find scope/role IDs:
```bash
# Delegated (oauth2PermissionScopes) and app (appRoles) on the target API's SP
az ad sp show --id 00000003-0000-0000-c000-000000000000 \
  --query "{delegated: oauth2PermissionScopes[?value=='User.Read'].id, app: appRoles[?value=='User.Read.All'].id}"
```

### Step 3: Create Agent Identities

```python
agent_body = {
    "@odata.type": "Microsoft.Graph.AgentIdentity",
    "displayName": "my-agent-instance-1",
    "agentIdentityBlueprintId": app_id,
    "sponsors@odata.bind": [
        f"https://graph.microsoft.com/beta/users/{user_id}"
    ],
}
resp = requests.post(f"{GRAPH}/servicePrincipals", headers=headers, json=agent_body)
resp.raise_for_status()
agent = resp.json()
```

## API Reference

| Operation | Method | Endpoint | OData Type |
|-----------|--------|----------|------------|
| Create Blueprint | `POST` | `/applications` | `Microsoft.Graph.AgentIdentityBlueprint` |
| List Blueprints | `GET` | `/applications/microsoft.graph.agentIdentityBlueprint` | (type cast required — plain `/applications` returns empty) |
| Find Blueprint by name | `GET` | `/applications/microsoft.graph.agentIdentityBlueprint?$filter=displayName eq '...'` | (filter only works on cast collection) |
| Get Blueprint by id | `GET` | `/applications/{id}` | — |
| Update Blueprint (perms, URIs, tags) | `PATCH` | `/applications/{id}` | — (PATCH replaces arrays — GET → mutate → PATCH) |
| Create BlueprintPrincipal | `POST` | `/servicePrincipals` | `Microsoft.Graph.AgentIdentityBlueprintPrincipal` |
| Create Agent Identity | `POST` | `/servicePrincipals` | `Microsoft.Graph.AgentIdentity` |
| List Agent Identities | `GET` | `/servicePrincipals?$filter=...` | — |
| Delete Agent Identity | `DELETE` | `/servicePrincipals/{id}` | — |
| Delete Blueprint | `DELETE` | `/applications/{id}` | — |

All endpoints use base URL: `https://graph.microsoft.com/beta`

## Required Permissions

| Permission | Purpose |
|-----------|---------|
| `Application.ReadWrite.All` | Blueprint CRUD (application objects) |
| `AgentIdentityBlueprint.Create` | Create new Blueprints |
| `AgentIdentityBlueprint.ReadWrite.All` | Read/update Blueprints |
| `AgentIdentityBlueprintPrincipal.Create` | Create BlueprintPrincipals |
| `AgentIdentity.Create.All` | Create Agent Identities |
| `AgentIdentity.ReadWrite.All` | Read/update Agent Identities |

There are **18 Agent Identity-specific** Graph application permissions. Discover all:
```bash
az ad sp show --id 00000003-0000-0000-c000-000000000000 \
  --query "appRoles[?contains(value, 'AgentIdentity')].{id:id, value:value}" -o json
```

Grant admin consent (required for application permissions):
```bash
az ad app permission admin-consent --id <client-id>
```

> Admin consent may fail with 404 if the service principal hasn't replicated. Retry with 10–40s backoff.

## Cleanup

```python
# Delete Agent Identity
requests.delete(f"{GRAPH}/servicePrincipals/{agent['id']}", headers=headers)

# Delete BlueprintPrincipal (get SP ID first)
sps = requests.get(
    f"{GRAPH}/servicePrincipals?$filter=appId eq '{app_id}'",
    headers=headers,
).json()
for sp in sps.get("value", []):
    requests.delete(f"{GRAPH}/servicePrincipals/{sp['id']}", headers=headers)

# Delete Blueprint
requests.delete(f"{GRAPH}/applications/{blueprint_obj_id}", headers=headers)
```

## Best Practices

1. **Always create BlueprintPrincipal after Blueprint** — not auto-created; implement idempotent checks on both
2. **Use User objects as sponsors** — ServicePrincipals and Groups are rejected
3. **Handle permission propagation delays** — after admin consent, wait 30–120s; retry with backoff on 403
4. **Include `OData-Version: 4.0` header** on every Graph request
5. **Use Workload Identity Federation for production auth** — for local dev, use a client secret on the Blueprint (see [references/oauth2-token-flow.md](references/oauth2-token-flow.md))
6. **Set `identifierUris` on Blueprint** before using OAuth2 scoping (`api://{app-id}`)
7. **Never use Azure CLI tokens** for API calls — they contain `Directory.AccessAsUser.All` which is hard-rejected
8. **Check for existing resources** before creating — implement idempotent provisioning

## References

| File | Contents |
|------|----------|
| [references/oauth2-token-flow.md](references/oauth2-token-flow.md) | Production (Managed Identity + WIF) and local dev (client secret) token flows |
| [references/known-limitations.md](references/known-limitations.md) | 29 known issues organized by category (from official preview known-issues page) |

### External Links

| Resource | URL |
|----------|-----|
| Official Setup Guide | https://learn.microsoft.com/en-us/entra/agent-id/identity-platform/agent-id-setup-instructions |
| AI-Guided Setup | https://learn.microsoft.com/en-us/entra/agent-id/identity-platform/agent-id-ai-guided-setup |

## Cross-References

- **→ `entra-agent-id-runtime`** — Runtime token exchange (autonomous + OBO flows)
- **→ `entra-app-registration`** — Blueprint is a special app registration
- **→ `azure-identity-py`** — Python provisioning scripts use ClientSecretCredential
- **→ `entra-admin-consent-permissions`** — Agent Identity consent grants
- **→ `entra-workload-identity-federation`** — Production auth via MI + WIF
- **→ `entra-audit-signin-logs`** — Agent actions appear with agent's identity in logs
