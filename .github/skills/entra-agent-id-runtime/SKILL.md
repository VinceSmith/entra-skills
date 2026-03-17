---
name: entra-agent-id-runtime
description: |
  Runtime token exchange patterns for Entra Agent Identity — autonomous (app-only) and OBO (delegated) flows.
  Covers the 2-step exchange (parent token → Graph token), Blueprint API configuration for OBO,
  delegated permission grants, per-agent permission scoping, and Foundry vs self-managed comparison.
  Triggers: "agent identity token", "agent id runtime", "fmi_path", "agent identity OBO",
  "agent identity autonomous", "agent identity exchange", "blueprint token exchange",
  "agent identity delegated", "foundry vs self-managed agent identity".
---

# Entra Agent ID — Runtime Token Exchange

How to use Agent Identities at runtime to call Microsoft Graph (or any API) with
autonomous (app-only) or OBO (delegated) permissions.

> **Prerequisite**: Blueprint, BlueprintPrincipal, and Agent Identities must already exist.
> See the `entra-agent-id` skill for provisioning.

## Key Insight

Agent Identity token exchange is a **pure Entra feature**, not a Foundry feature.
Any code running anywhere (App Service, Container Apps, local machine, or Foundry)
can exchange Blueprint credentials for Agent Identity-scoped Graph tokens using the
standard `/oauth2/v2.0/token` endpoint. Foundry's MI+WIF is convenience automation
on top of this same mechanism.

## Two Exchange Modes

```
Blueprint (client_credentials + fmi_path)
    │
    ├──→ Autonomous: client_assertion exchange → app-only Graph token
    │       Agent acts as itself with application permissions
    │
    └──→ OBO: client_assertion + user_assertion → delegated Graph token
            Agent acts on behalf of a user with delegated permissions
```

Both modes produce a Graph token where `sub` = Agent Identity's appId,
giving each agent a distinct identity in audit logs.

## Step 1: Parent Token (Shared by Both Modes)

The parent token uses `client_credentials` with a special `fmi_path` parameter
pointing to the Agent Identity.

```python
import json
import urllib.parse
import urllib.request

TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

def get_parent_token(tenant_id: str, blueprint_app_id: str,
                     blueprint_secret: str, agent_identity_id: str) -> str:
    """Get a parent token scoped to a specific Agent Identity."""
    params = {
        "grant_type": "client_credentials",
        "client_id": blueprint_app_id,
        "client_secret": blueprint_secret,
        "scope": "api://AzureADTokenExchange/.default",
        "fmi_path": agent_identity_id,  # Agent Identity's appId
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL.format(tenant=tenant_id), data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]
```

### Parent Token Claims

| Claim | Value |
|-------|-------|
| `aud` | `api://AzureADTokenExchange` |
| `iss` | `https://login.microsoftonline.com/{tenant}/v2.0` |
| `sub` | Blueprint's SP object ID |
| `appid` | Blueprint's appId |
| `idtyp` | `app` |

This token **cannot** call Graph directly — it's an intermediate used as
`client_assertion` in the next step.

## Step 2a: Autonomous Exchange (App-Only)

Exchanges the parent token for an app-only Graph token.

```python
def exchange_autonomous(agent_identity_id: str, parent_token: str) -> dict:
    """Exchange parent token for app-only Graph token."""
    params = {
        "grant_type": "client_credentials",
        "client_id": agent_identity_id,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": parent_token,
        "scope": "https://graph.microsoft.com/.default",
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL.format(tenant=tenant_id), data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

The resulting token has `roles` containing the application permissions granted
to the Agent Identity SP (via `appRoleAssignments`).

## Step 2b: OBO Exchange (Delegated)

Exchanges the parent token + a user token for a delegated Graph token.

```python
def exchange_obo(agent_identity_id: str, parent_token: str,
                 user_token: str) -> dict:
    """Exchange parent + user token for delegated Graph token."""
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "client_id": agent_identity_id,
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": parent_token,
        "assertion": user_token,
        "requested_token_use": "on_behalf_of",
        "scope": "https://graph.microsoft.com/.default",
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(
        TOKEN_URL.format(tenant=tenant_id), data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

The resulting token has `scp` containing the delegated permissions consented
for this Agent Identity (via `oauth2PermissionGrants`).

## Blueprint API Configuration (Required for OBO)

OBO requires the Blueprint to be configured as an API that users can
acquire tokens for. Without this, the user token can't target the Blueprint
as its audience and `AADSTS50013: Assertion failed signature validation` occurs.

```python
import uuid

def configure_blueprint_for_obo(token: str, blueprint_obj_id: str,
                                 blueprint_app_id: str, client_app_id: str):
    """Configure Blueprint as an API for OBO token flow."""
    scope_id = str(uuid.uuid4())
    patch = {
        "identifierUris": [f"api://{blueprint_app_id}"],
        "api": {
            "requestedAccessTokenVersion": 2,
            "oauth2PermissionScopes": [{
                "id": scope_id,
                "adminConsentDescription": "Allow the app to access the agent API on behalf of the user.",
                "adminConsentDisplayName": "Access agent API",
                "userConsentDescription": "Allow the app to access the agent API on your behalf.",
                "userConsentDisplayName": "Access agent API",
                "value": "access_as_user",
                "type": "User",
                "isEnabled": True,
            }],
            "preAuthorizedApplications": [{
                "appId": client_app_id,
                "permissionIds": [scope_id],
            }],
        },
        "optionalClaims": {
            "accessToken": [{
                "name": "idtyp",
                "source": None,
                "essential": False,
                "additionalProperties": ["include_user_token"],
            }]
        },
    }
    # PATCH https://graph.microsoft.com/beta/applications/{blueprint_obj_id}
```

### OBO User Token Requirements

The user token (the `assertion` parameter) must:

1. **Target the Blueprint as audience** — scope: `api://{blueprint_app_id}/access_as_user`
2. **NOT target Graph directly** — `aud: https://graph.microsoft.com` will fail
3. Come from a client app that is **pre-authorized** on the Blueprint

```python
from azure.identity import InteractiveBrowserCredential

credential = InteractiveBrowserCredential(
    tenant_id=tenant_id,
    client_id=client_app_id,  # The client app, NOT the Blueprint
    redirect_uri="http://localhost:8400",
)
# Scope targets the Blueprint, not Graph:
user_token = credential.get_token(f"api://{blueprint_app_id}/access_as_user")
```

## Delegated Permission Grants (Per-Agent Scoping)

Each Agent Identity can have different delegated permissions — this is the
key governance feature. Grants are created via `oauth2PermissionGrants` API
(programmatic admin consent).

```python
MS_GRAPH_SP_ID = "..."  # Object ID of Microsoft Graph SP in your tenant

def grant_delegated_permissions(admin_token: str, agent_sp_id: str,
                                 scopes: str):
    """Grant delegated permissions to an Agent Identity."""
    from datetime import datetime, timedelta, timezone
    expiry = (datetime.now(timezone.utc) + timedelta(days=3650)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    body = {
        "clientId": agent_sp_id,      # Agent Identity SP object ID
        "consentType": "AllPrincipals",
        "resourceId": MS_GRAPH_SP_ID,  # Graph SP object ID
        "scope": scopes,               # Space-separated: "User.Read Mail.Send"
        "expiryTime": expiry,          # Required by beta API
    }
    # POST https://graph.microsoft.com/beta/oauth2PermissionGrants
```

### Per-Agent Scope Example

```python
AGENT_SCOPES = {
    "it-agent":    "User.Read User.ReadBasic.All Tasks.ReadWrite",
    "comms-agent": "User.Read User.ReadBasic.All Mail.Send Calendars.ReadWrite",
}
```

## Critical Rules

### Scope Rules
- **Both exchanges MUST use `/.default`** — individual scopes like `User.Read Mail.Send` will fail
- Azure AD returns whichever permissions were actually consented for that Agent Identity
- For autonomous: permissions come from `appRoleAssignments` on the Agent Identity SP
- For OBO: permissions come from `oauth2PermissionGrants` on the Agent Identity SP

### Agent Identity Restrictions
- **`Group.ReadWrite.All` cannot be granted** to agent identities (delegated)
- `Tasks.ReadWrite` alone covers Planner task operations (no Group scope needed)
- Not all Graph scopes are allowed — test each scope individually if you hit errors

### Auth Constraints
- **`DefaultAzureCredential` / Azure CLI tokens are rejected** by Agent ID provisioning APIs (they contain `Directory.AccessAsUser.All`)
- Browser-based admin consent URLs **do not work** for agent identities — use `oauth2PermissionGrants` API for programmatic consent
- `expiryTime` is **required** on beta API `oauth2PermissionGrants` POST (not required on v1.0)

### Cross-Tenant
- `fmi_path` exchange **works cross-tenant** — tested and verified
- **Critical rule**: Step 1 (parent token) MUST target the **Agent Identity's home tenant**, not the Blueprint's home tenant
- If you hit the Blueprint's home tenant for step 1, step 2 fails with `AADSTS700211: No matching federated identity record found` because the parent token issuer doesn't match the Agent Identity's federation config
- Blueprint credentials CAN create Agent Identities in foreign tenants
- Blueprint credentials CAN exchange for tokens scoped to foreign-tenant identities
- The Blueprint must be multi-tenant (`signInAudience: AzureADMultipleOrgs`) and have a SP provisioned in the target tenant

## Complete Provider Class

```python
class AgentIdProvider:
    """
    Pluggable token provider for Agent Identity.
    Supports both autonomous (app-only) and OBO (delegated) modes.
    """

    TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    def __init__(self, agent_identity_id: str, mode: str = "obo",
                 user_token_provider=None, tenant_id: str = "",
                 blueprint_app_id: str = "", blueprint_secret: str = ""):
        self.agent_identity_id = agent_identity_id
        self.mode = mode  # "autonomous" or "obo"
        self.user_token_provider = user_token_provider
        # tenant_id must be the AGENT IDENTITY's home tenant (not the Blueprint's)
        # For cross-tenant: Blueprint multi-tenant app authenticates to foreign tenant
        self.tenant_id = tenant_id
        self.blueprint_app_id = blueprint_app_id
        self.blueprint_secret = blueprint_secret
        self._cached_token = None
        self._cached_expires_on = 0
        self._token_url = self.TOKEN_URL.format(tenant=self.tenant_id)

        if mode == "obo" and not user_token_provider:
            raise ValueError("OBO mode requires a user_token_provider")

    def _post_token(self, params: dict) -> dict:
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(
            self._token_url, data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())

    def _get_parent_token(self) -> str:
        params = {
            "grant_type": "client_credentials",
            "client_id": self.blueprint_app_id,
            "client_secret": self.blueprint_secret,
            "scope": "api://AzureADTokenExchange/.default",
            "fmi_path": self.agent_identity_id,
        }
        return self._post_token(params)["access_token"]

    def _exchange_autonomous(self, parent_token: str) -> dict:
        return self._post_token({
            "grant_type": "client_credentials",
            "client_id": self.agent_identity_id,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": parent_token,
            "scope": "https://graph.microsoft.com/.default",
        })

    def _exchange_obo(self, parent_token: str, user_token: str) -> dict:
        return self._post_token({
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "client_id": self.agent_identity_id,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": parent_token,
            "assertion": user_token,
            "requested_token_use": "on_behalf_of",
            "scope": "https://graph.microsoft.com/.default",
        })

    def __call__(self) -> str:
        import time
        if self._cached_token and self._cached_expires_on > time.time() + 120:
            return self._cached_token

        parent = self._get_parent_token()
        if self.mode == "obo":
            result = self._exchange_obo(parent, self.user_token_provider())
        else:
            result = self._exchange_autonomous(parent)

        self._cached_token = result["access_token"]
        self._cached_expires_on = time.time() + result.get("expires_in", 3600)
        return self._cached_token
```

## Foundry vs Self-Managed Agent Identity

Agent Identity works identically whether provisioned by Foundry or by your own code.
The `fmi_path` token exchange is a standard Entra endpoint.

| Aspect | Foundry-Managed | Self-Managed |
|--------|----------------|--------------|
| **Provisioning** | Automatic (Foundry creates Blueprint + identities) | You write a setup script |
| **Credential type** | Managed Identity (no secrets) | Client secret or certificate (you manage rotation) |
| **Runtime exchange** | MI → WIF → parent → Graph token | Secret → parent → Graph token |
| **OBO support** | Not exposed by Foundry runtime | Full support (you configure the Blueprint API) |
| **Delegated permissions** | Not supported | Full support via oauth2PermissionGrants |
| **Multi-tenant exchange** | Unknown (likely same pattern) | Works — step 1 must target Agent Identity's home tenant |
| **Per-agent scoping** | Foundry sets uniform permissions | You control per-agent permissions |
| **Audit trail** | Same (Agent Identity sub in tokens) | Same (Agent Identity sub in tokens) |
| **Governance model** | Same (Blueprint + sponsors) | Same (Blueprint + sponsors) |
| **Runs where** | Only inside Foundry runtime | Anywhere (App Service, Container Apps, local, Foundry) |

### When to Use Each

| Scenario | Recommendation |
|----------|---------------|
| Simple app-only agent in Foundry | Foundry-managed (zero config) |
| Agent needs OBO / delegated flow | Self-managed (Foundry doesn't expose OBO) |
| Agent runs outside Foundry | Self-managed (only option) |
| Agent needs per-identity permission boundaries | Self-managed (more control) |
| Minimize secret management | Foundry-managed (MI has no secrets) |
| Agent needs both model access + Graph access | Foundry for model, self-managed for Graph (hybrid) |

### Hybrid Pattern

An agent in Foundry can use Foundry's built-in MI for AI model access while
using its own Blueprint credentials for Graph access with full OBO support:

```
Foundry Agent
├── AI model calls: Foundry MI → AI Services (automatic)
└── Graph calls: Self-managed Blueprint → Agent Identity → OBO/autonomous
```

This gives you model hosting convenience + full auth flexibility.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `AADSTS50013: Assertion failed signature validation` | User token targets Graph instead of Blueprint | Change scope to `api://{blueprint_app_id}/access_as_user` |
| `AADSTS65001: consent_required` | Requesting a scope not in oauth2PermissionGrants, or requesting individual scopes instead of `.default` | Use `https://graph.microsoft.com/.default` and verify grants |
| `AADSTS82001` | Used wrong grant type (RFC 8693 token-exchange) | Use `fmi_path` + `client_assertion` pattern, not RFC 8693 |
| `AADSTS700211: No matching federated identity record` | Step 1 parent token issued by wrong tenant | Step 1 must target the Agent Identity's home tenant, not the Blueprint's home tenant |
| `403 Authorization_RequestDenied` | Missing delegated scope (e.g., `User.ReadBasic.All` for user lookups) | Add scope to oauth2PermissionGrants |
| `Group.ReadWrite.All` rejected | Scope not allowed for agent identities | Use `Tasks.ReadWrite` for Planner; drop Group scope |
| `PropertyNotCompatibleWithAgentIdentity` | Tried to add secret/cert to Agent Identity SP | Credentials go on the Blueprint only |
| `Agent Blueprint Principal does not exist` | BlueprintPrincipal not created | POST to /servicePrincipals with AgentIdentityBlueprintPrincipal type |

## Supplementary Learnings (Cross-Skill)

Practical findings from building Agent Identity-backed agents that supplement
other skill files. Organized by the skill they relate to.

### azure-identity-py: WAM Bypass and MSAL Patterns

**Windows Authentication Manager (WAM) blocks multi-tenant az login in VS Code.**
When switching tenants with `az login --tenant {id}` in VS Code's built-in terminal,
WAM intercepts the auth flow and may redirect to the wrong tenant.

```powershell
# Fix: disable WAM broker before az login
$env:AZURE_CORE_ENABLE_BROKER_ON_WINDOWS = "false"
az login --tenant {target-tenant-id} --allow-no-subscriptions
```

**MSAL `PublicClientApplication` for Agent ID provisioning writes.**
Agent ID APIs reject tokens containing `Directory.AccessAsUser.All` (present in all
`az cli` and `DefaultAzureCredential` tokens). For write operations (create Blueprint,
set permissions), use MSAL directly with only the scopes you need:

```python
import msal

app = msal.PublicClientApplication(
    "14d82eec-204b-4c2f-b7e8-296a70dab67e",  # Graph PowerShell client ID
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    token_cache=cache,  # SerializableTokenCache for persistence
)
result = app.acquire_token_interactive(
    scopes=["Application.ReadWrite.All"],  # Only what you need — no Directory.AccessAsUser.All
)
```

**Token cache persistence with MSAL:**
```python
cache = msal.SerializableTokenCache()
cache_path = Path("token_cache.bin")
if cache_path.exists():
    cache.deserialize(cache_path.read_text())
# ... use cache ...
if cache.has_state_changed:
    cache_path.write_text(cache.serialize())
```

### microsoft-foundry: Auth Architecture Insights

**Foundry auto-creates 4 service principals** when you create a project.
These include the project identity and model deployment identities. They are
visible in Entra under Enterprise Applications.

**Foundry is PaaS-level for auth, not SaaS:**
- No Easy Auth equivalent (no drop-in auth middleware for agent endpoints)
- No delegated/OBO flow exposed through the runtime
- No multi-tenant agent deployment support
- Agent Identity is always app-only through the auto-managed MI

**Foundry's Agent Identity is convenience automation on Entra primitives.**
Everything Foundry creates (Blueprint, BlueprintPrincipal, Agent Identity, WIF)
uses standard Graph beta APIs. The `fmi_path` token exchange is a standard
`/oauth2/v2.0/token` endpoint feature, not a Foundry-specific endpoint. You can
replicate the entire identity chain outside Foundry with your own setup script.

**When Foundry + self-managed auth overlap:** An agent hosted in Foundry can use
Foundry's MI for AI model access while using a self-managed Blueprint for Graph
access with full OBO support. This is the recommended hybrid pattern until Foundry
exposes delegated flows natively.

### agent-framework-azure-ai-py: SDK Entry Point

**`AzureAIClient` is the current entry point** (as of `agent-framework-azure-ai==1.0.0rc4`):
```python
from agent_framework.azure import AzureAIClient
from azure.identity import DefaultAzureCredential

async with AzureAIClient(
    endpoint=project_endpoint,
    credential=DefaultAzureCredential(),
).as_agent(
    name="My-Agent",
    instructions="...",
    tools=[tool_functions],
    model=model_deployment,
) as agent:
    session = await agent.create_session()
    async for chunk in agent.run("user message", session=session, stream=True):
        print(chunk, end="", flush=True)
```

This replaces the older `AzureAIAgentsProvider` pattern documented in some skill files.

### entra-agent-id: Cross-Tenant Experiment Results

Tested making a Blueprint multi-tenant to create and use Agent Identities in a
foreign tenant. Results:

| Step | Outcome |
|------|---------|
| Change Blueprint `signInAudience` to `AzureADMultipleOrgs` | Works (requires beta API PATCH) |
| Set `identifierUris` on multi-tenant Blueprint | Works |
| Add client secret to Blueprint | Works |
| Add `requiredResourceAccess` (Graph permissions) | Works |
| Admin consent in foreign tenant | Partially works (SP may already exist from failed attempt; use `appRoleAssignments` API directly) |
| Create Agent Identity in foreign tenant | Works (Blueprint client_credentials can create identities cross-tenant) |
| `fmi_path` step 1 against **Agent Identity's tenant** → step 2 exchange | **Works** — full Graph access as Agent Identity |
| `fmi_path` step 1 against **Blueprint's tenant** → step 2 exchange | **Fails** (`AADSTS700211`) — parent token issuer mismatch |
| RFC 8693 token exchange (wrong grant type) | **Fails** (`AADSTS82001`) — wrong mechanism entirely |

**Conclusion:** Cross-tenant Agent Identity exchange works. The critical rule is that
step 1 (parent token) must be requested from the **Agent Identity's home tenant**, not
the Blueprint's home tenant. The Blueprint authenticates to the foreign tenant (because
it's multi-tenant), and the resulting parent token has the correct issuer to match
the Agent Identity's federation config.

**`AADSTS650051` workaround:** If admin consent fails because the SP already exists
from a previous partial consent attempt, grant permissions directly via
`appRoleAssignments` API on the existing SP instead of re-running consent:

```python
# POST /servicePrincipals/{sp_id}/appRoleAssignments
body = {
    "principalId": sp_id,
    "resourceId": graph_sp_id,
    "appRoleId": role_id,  # e.g., User.Read.All role ID
}
```

### entra-app-registration: Blueprint as API App

Configuring a Blueprint for OBO requires the same API configuration as any
OAuth2 resource application:

1. `identifierUris`: `["api://{blueprint_app_id}"]`
2. `oauth2PermissionScopes`: `access_as_user` scope
3. `preAuthorizedApplications`: authorize your client app's appId
4. `optionalClaims`: `idtyp` with `include_user_token` on `accessToken`

Without all four, OBO exchange fails with `AADSTS50013: Assertion failed signature validation`.

The user token for OBO must target the Blueprint as audience (`api://{blueprint_app_id}/access_as_user`),
NOT Graph directly. The OBO exchange then converts it to a Graph-scoped token.

## Verified Working Example

The `onboarding-orchestrator` project demonstrates all patterns:
- `auth_providers.py` — `AgentIdProvider` class (autonomous + OBO)
- `scripts/setup_agent_ids.py` — Full provisioning (7 steps: Builder app → permissions → Blueprint → API config → Agent Identities → delegated grants)
- `scripts/test_agent_id.py` — Token exchange diagnostics
- 3 Agent Identities with different delegated scopes (IT: Tasks, People: Tasks, Comms: Mail+Calendar)
- Real Graph calls: Planner tasks, email, calendar events — all via Agent Identity tokens

## Cross-References

- **→ `entra-agent-id`** — Provisioning: Blueprints, BlueprintPrincipals, Agent Identities
- **→ `entra-app-registration`** — Blueprint is a special app registration with API config
- **→ `azure-identity-py`** — ClientSecretCredential / ClientCertificateCredential for CCA
- **→ `entra-msal-deep-dive`** — MSAL OBO flow, token caching, proof-of-possession
- **→ `entra-admin-consent-permissions`** — Tenant-wide vs per-user consent for agent scopes
- **→ `entra-workload-identity-federation`** — MI + WIF alternative to client secrets
- **→ `entra-audit-signin-logs`** — Agent sign-in logs, service principal audit entries
