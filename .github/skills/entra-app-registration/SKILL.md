---
name: entra-app-registration
description: "Full lifecycle of Entra ID app registrations: creation, authentication setup, API permissions, client credentials, OAuth 2.0 flows, multi-tenant patterns, secret rotation, and federated credentials. USE FOR: create app registration, register Azure AD app, configure OAuth, set up authentication, add API permissions, generate service principal, MSAL example, console app auth, Entra ID setup, multi-tenant app, federated credential. DO NOT USE FOR: Azure RBAC (use azure-rbac), managed identity (use entra-managed-identity), audit logs (use entra-audit-signin-logs)."
---

# Entra App Registration

Full lifecycle management of Microsoft Entra ID app registrations — from creation through authentication setup, API permissions, credential management, and multi-tenant patterns.

## Before You Start

Search `microsoft-docs` MCP for the latest Entra app registration documentation:
- Query: "Microsoft Entra app registration overview"
- Verify: API endpoints and parameter names match current behavior

## Key Concepts

| Concept | Description |
|---------|-------------|
| **App Registration** | Configuration that allows an app to use Microsoft identity platform |
| **Application (Client) ID** | Unique identifier for your application |
| **Tenant ID** | Unique identifier for your Entra tenant/directory |
| **Client Secret** | Password for the application (confidential clients only) |
| **Redirect URI** | URL where authentication responses are sent |
| **API Permissions** | Access scopes your app requests |
| **Service Principal** | Identity created in a tenant when you register/consent to an app |
| **Federated Credential** | Trust relationship with external identity provider (eliminates secrets) |

## Application Types

| Type | OAuth Flow | Credential Type | Example |
|------|-----------|----------------|---------|
| **Web Application** | Authorization Code + PKCE | Confidential (secret/cert) | ASP.NET Core, FastAPI |
| **Single Page App (SPA)** | Authorization Code + PKCE | Public | React, Angular, Vue |
| **Mobile/Native App** | Authorization Code + PKCE | Public | .NET MAUI, React Native |
| **Daemon/Service** | Client Credentials | Confidential (secret/cert/federated) | Background jobs, APIs |
| **CLI Tool** | Device Code | Public | Admin scripts |
| **Agent Identity** | Client Credentials + fmi_path | Confidential | AI agents (→ `entra-agent-id`) |

## Core Workflow

### Step 1: Register the Application

**Azure CLI:**
```bash
# Single-tenant app
az ad app create \
  --display-name "my-api" \
  --sign-in-audience "AzureADMyOrg"

# Multi-tenant app
az ad app create \
  --display-name "my-saas-app" \
  --sign-in-audience "AzureADMultipleOrgs"

# Get the app ID
APP_ID=$(az ad app list --display-name "my-api" --query "[0].appId" -o tsv)
```

**Bicep:**
```bicep
resource appRegistration 'Microsoft.Graph/applications@v1.0' = {
  displayName: 'my-api'
  uniqueName: 'my-api-${uniqueString(resourceGroup().id)}'
  signInAudience: 'AzureADMyOrg'

  web: {
    redirectUris: ['https://myapp.azurewebsites.net/.auth/login/aad/callback']
    implicitGrantSettings: {
      enableIdTokenIssuance: true
    }
  }

  requiredResourceAccess: [
    {
      resourceAppId: '00000003-0000-0000-c000-000000000000' // Microsoft Graph
      resourceAccess: [
        {
          id: 'e1fe6dd8-ba31-4d61-89e7-88639da4683d' // User.Read
          type: 'Scope'
        }
      ]
    }
  ]
}

// Service principal (required for the app to be usable in the tenant)
resource servicePrincipal 'Microsoft.Graph/servicePrincipals@v1.0' = {
  appId: appRegistration.appId
}
```

**Python (Microsoft Graph SDK):**
```python
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.application import Application
from msgraph.generated.models.web_application import WebApplication

credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)
graph = GraphServiceClient(credential)

app = Application(
    display_name="my-api",
    sign_in_audience="AzureADMyOrg",
    web=WebApplication(
        redirect_uris=["https://myapp.azurewebsites.net/.auth/login/aad/callback"],
    ),
)
result = await graph.applications.post(app)
```

### Step 2: Configure Authentication

| App Type | Redirect URI Pattern | Token Settings |
|----------|---------------------|----------------|
| Web app | `https://myapp.com/.auth/login/aad/callback` | Enable ID tokens |
| SPA | `http://localhost:3000` (dev), `https://myapp.com` (prod) | — |
| Mobile | `myapp://auth` or `http://localhost` | — |
| Daemon | None needed | — |
| CLI | `http://localhost` | — |

### Step 3: Configure API Permissions

**Delegated vs Application Permissions:**

| Aspect | Delegated | Application |
|--------|-----------|-------------|
| **User context** | Yes — acts on behalf of signed-in user | No — acts as the app itself |
| **Consent** | User or admin consent | Admin consent required |
| **Use when** | User is present (web apps, SPAs) | No user (daemons, services) |
| **Graph example** | `User.Read` (read signed-in user) | `User.Read.All` (read any user) |
| **Effective permissions** | Intersection of app permissions AND user's own permissions | Exactly the permissions granted |

**Common Microsoft Graph Permission Sets:**

| Scenario | Delegated Permissions | Application Permissions |
|----------|----------------------|------------------------|
| Read user profile | `User.Read` | `User.Read.All` |
| Send email | `Mail.Send` | `Mail.Send` |
| Manage groups | `Group.ReadWrite.All` | `Group.ReadWrite.All` |
| Read calendar | `Calendars.Read` | `Calendars.Read` |
| Read files | `Files.Read.All` | `Files.Read.All` |

```bash
# Add delegated permission (User.Read)
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions e1fe6dd8-ba31-4d61-89e7-88639da4683d=Scope

# Add application permission (User.Read.All)
az ad app permission add \
  --id $APP_ID \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions df021288-bdef-4463-88db-98f22de89214=Role

# Grant admin consent (requires admin role)
az ad app permission admin-consent --id $APP_ID
```

### Step 4: Create Credentials

**Credential selection (most to least preferred):**
1. **Managed Identity** — No credentials needed (→ `entra-managed-identity`)
2. **Federated Credential** — No secrets to rotate (→ `entra-workload-identity-federation`)
3. **Certificate** — More secure than secrets
4. **Client Secret** — Last resort; set 90-day max expiry

```bash
# Create client secret (90-day expiry)
az ad app credential reset \
  --id $APP_ID \
  --years 0 \
  --end-date "$(date -d '+90 days' +%Y-%m-%d)"

# Create federated credential for GitHub Actions
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-deploy",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:myorg/myrepo:ref:refs/heads/main",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

### Step 5: Implement Authentication in Code

**Python (azure-identity — recommended):**
```python
from azure.identity import DefaultAzureCredential
from msgraph import GraphServiceClient

# Works in local dev (Azure CLI) AND production (managed identity)
credential = DefaultAzureCredential()
graph = GraphServiceClient(credential)
```

**Python (MSAL — when you need more control):**
```python
import msal

app = msal.ConfidentialClientApplication(
    client_id=os.environ["AZURE_CLIENT_ID"],
    authority=f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}",
    client_credential=os.environ["AZURE_CLIENT_SECRET"],
)

# Client credentials flow (daemon/service)
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])

# Authorization code flow (web app)
result = app.acquire_token_by_authorization_code(
    code=auth_code,
    scopes=["User.Read"],
    redirect_uri="https://myapp.com/callback",
)
```

**.NET (Azure.Identity — recommended):**
```csharp
using Azure.Identity;
using Microsoft.Graph;

var credential = new DefaultAzureCredential();
var graphClient = new GraphServiceClient(credential);
```

**.NET (MSAL — when you need more control):**
```csharp
using Microsoft.Identity.Client;

var app = ConfidentialClientApplicationBuilder
    .Create(Environment.GetEnvironmentVariable("AZURE_CLIENT_ID"))
    .WithClientSecret(Environment.GetEnvironmentVariable("AZURE_CLIENT_SECRET"))
    .WithAuthority(AzureCloudInstance.AzurePublic, tenantId)
    .Build();

var result = await app.AcquireTokenForClient(
    new[] { "https://graph.microsoft.com/.default" })
    .ExecuteAsync();
```

## Multi-Tenant Patterns

### Supported Account Types

| Value | Meaning | Use Case |
|-------|---------|----------|
| `AzureADMyOrg` | Single tenant | Internal LOB apps |
| `AzureADMultipleOrgs` | Any Entra tenant | SaaS, ISV apps |
| `AzureADandPersonalMicrosoftAccount` | Entra + personal (Outlook.com) | Consumer-facing |
| `PersonalMicrosoftAccount` | Personal only | Consumer apps |

### Multi-Tenant Registration

```bash
az ad app create \
  --display-name "my-saas-api" \
  --sign-in-audience "AzureADMultipleOrgs" \
  --web-redirect-uris "https://myapp.com/callback"
```

**Key considerations:**
- Service principals are auto-created in each tenant on first consent
- Admin consent URL: `https://login.microsoftonline.com/{tenant}/adminconsent?client_id={app_id}`
- Use `/common` or `/organizations` authority (not a specific tenant ID)
- Validate `tid` (tenant ID) claim in tokens to enforce tenant restrictions

## OAuth 2.0 Flows Reference

| Flow | Use Case | MSAL Method |
|------|----------|-------------|
| **Authorization Code + PKCE** | Web apps, SPAs, mobile | `acquire_token_by_authorization_code()` |
| **Client Credentials** | Daemons, services | `acquire_token_for_client()` |
| **Device Code** | CLI tools, IoT | `acquire_token_by_device_flow()` |
| **On-Behalf-Of** | API calling another API | `acquire_token_on_behalf_of()` |
| **Refresh Token** | Silent token renewal | Handled automatically by MSAL |

## Security Best Practices

1. **Never hardcode secrets** — Use environment variables, Key Vault, or managed identity
2. **Rotate secrets** — 90-day max expiry; automate rotation (→ `entra-secret-certificate-lifecycle`)
3. **Use certificates over secrets** — More secure for production confidential clients
4. **Least privilege permissions** — Request only the specific permissions your app needs
5. **Prefer managed identity** — For Azure-hosted apps, no credentials to manage (→ `entra-managed-identity`)
6. **Use federated credentials** — For CI/CD and cross-cloud, no secrets (→ `entra-workload-identity-federation`)
7. **Validate tokens** — Always validate issuer, audience, and expiration
8. **HTTPS only** — All redirect URIs must use HTTPS (except localhost for development)
9. **Monitor sign-ins** — Use Entra sign-in logs for anomaly detection (→ `entra-audit-signin-logs`)

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `AADSTS700016: Application not found` | Wrong client ID or app not in tenant | Verify `AZURE_CLIENT_ID` matches app registration |
| `AADSTS7000218: Invalid client secret` | Secret expired or wrong value | Rotate secret; ensure no trailing whitespace |
| `AADSTS65001: User needs to consent` | Missing consent for permissions | Run admin consent: `az ad app permission admin-consent` |
| `AADSTS50011: Reply URL mismatch` | Redirect URI doesn't match registration | Add exact URI to app registration |
| `AADSTS700024: Client assertion invalid` | Certificate mismatch or expired | Upload correct certificate; check expiry |
| `AADSTS50013: Assertion failed signature` | Wrong token audience or issuer | For WIF: verify `issuer`, `subject`, `audience` match exactly |
| `AADSTS90002: Tenant not found` | Wrong tenant ID | Verify `AZURE_TENANT_ID`; for multi-tenant use `/organizations` |

## CLI Quick Reference

| Command | Purpose |
|---------|---------|
| `az ad app create` | Create new app registration |
| `az ad app list --display-name "x"` | Find app by name |
| `az ad app show --id $APP_ID` | Show app details |
| `az ad app permission add` | Add API permission |
| `az ad app permission admin-consent` | Grant admin consent |
| `az ad app credential reset` | Create new client secret |
| `az ad app credential list` | List credentials (secrets + certs) |
| `az ad app federated-credential create` | Add federated credential |
| `az ad sp create --id $APP_ID` | Create service principal |
| `az ad sp list --filter "appId eq '$APP_ID'"` | Find SP by app ID |
| `az ad app delete --id $APP_ID` | Delete app registration |

## Cross-References

- **→ `entra-agent-id`** — Blueprint is a special app registration for AI agents
- **→ `azure-identity-py` / `azure-identity-dotnet`** — SDK integration for authentication
- **→ `entra-msal-deep-dive`** — Advanced MSAL patterns (caching, PoP tokens, B2C)
- **→ `entra-admin-consent-permissions`** — Permission grant lifecycle and admin consent
- **→ `entra-secret-certificate-lifecycle`** — Secret rotation and certificate management
- **→ `entra-managed-identity`** — Eliminate credentials with managed identity
- **→ `entra-workload-identity-federation`** — Eliminate secrets with federated credentials
