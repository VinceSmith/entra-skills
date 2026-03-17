---
name: entra-msal-deep-dive
description: "Deep MSAL integration patterns — MSAL Python, MSAL.NET, MSAL.js, token caching (persistent, distributed), confidential vs public client, proof-of-possession tokens, claims challenge, B2C."
---

# MSAL Deep Dive

MSAL (Microsoft Authentication Library) is the lower-level auth library underneath `azure-identity`. Use MSAL directly when you need control over token caching, proof-of-possession, claims challenges, B2C policies, or the On-Behalf-Of flow. For most Azure SDK scenarios, prefer `azure-identity-py` or `azure-identity-dotnet` instead.

## When to Use MSAL vs Azure Identity

| Scenario | Use | Library |
|----------|-----|---------|
| Azure SDK client auth | Azure Identity | `azure-identity` / `Azure.Identity` |
| Graph SDK auth | Azure Identity | `azure-identity` (wraps MSAL internally) |
| Custom token cache (Redis, SQL) | MSAL | `msal` / `Microsoft.Identity.Client` |
| Proof-of-possession tokens | MSAL | `msal` / `Microsoft.Identity.Client` |
| Claims challenge / CAE | MSAL | `msal` / `Microsoft.Identity.Client` |
| B2C custom policies | MSAL | `msal` / `Microsoft.Identity.Client` |
| OBO flow with caching | MSAL | `msal` / `Microsoft.Identity.Client` |
| SPA / browser auth | MSAL | `@azure/msal-browser` |
| Node.js server auth | MSAL | `@azure/msal-node` |

## MSAL Python

### Installation

```bash
pip install msal
```

### Confidential Client (Server-Side)

```python
import msal

app = msal.ConfidentialClientApplication(
    client_id="<client-id>",
    authority="https://login.microsoftonline.com/<tenant-id>",
    client_credential="<client-secret>",
)

# Client credentials flow (app-only)
result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
if "access_token" in result:
    token = result["access_token"]
else:
    print(f"Error: {result.get('error_description')}")
```

### Public Client (Desktop / CLI)

```python
app = msal.PublicClientApplication(
    client_id="<client-id>",
    authority="https://login.microsoftonline.com/<tenant-id>",
)

# Interactive login
result = app.acquire_token_interactive(scopes=["User.Read", "Mail.Read"])

# Device code flow
flow = app.initiate_device_flow(scopes=["User.Read"])
print(flow["message"])  # "Go to https://microsoft.com/devicelogin and enter code..."
result = app.acquire_token_by_device_flow(flow)
```

### On-Behalf-Of Flow

```python
app = msal.ConfidentialClientApplication(
    client_id="<api-client-id>",
    authority="https://login.microsoftonline.com/<tenant-id>",
    client_credential="<api-client-secret>",
)

# Exchange incoming user token for a downstream token
result = app.acquire_token_on_behalf_of(
    user_assertion=incoming_access_token,
    scopes=["https://graph.microsoft.com/User.Read"],
)
```

### Silent Token Acquisition (Cache First)

```python
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(
        scopes=["User.Read"],
        account=accounts[0],
    )
    if not result:
        # Cache miss — fall back to interactive
        result = app.acquire_token_interactive(scopes=["User.Read"])
```

## MSAL .NET

### Installation

```bash
dotnet add package Microsoft.Identity.Client
dotnet add package Microsoft.Identity.Web  # For ASP.NET Core integration
```

### Confidential Client

```csharp
using Microsoft.Identity.Client;

var app = ConfidentialClientApplicationBuilder
    .Create("<client-id>")
    .WithClientSecret("<client-secret>")
    .WithAuthority(AzureCloudInstance.AzurePublic, "<tenant-id>")
    .Build();

var result = await app.AcquireTokenForClient(
    new[] { "https://graph.microsoft.com/.default" })
    .ExecuteAsync();

string token = result.AccessToken;
```

### Public Client with Embedded Browser

```csharp
var app = PublicClientApplicationBuilder
    .Create("<client-id>")
    .WithAuthority(AzureCloudInstance.AzurePublic, "<tenant-id>")
    .WithRedirectUri("http://localhost")
    .Build();

var result = await app.AcquireTokenInteractive(
    new[] { "User.Read" })
    .ExecuteAsync();
```

### On-Behalf-Of (.NET)

```csharp
var app = ConfidentialClientApplicationBuilder
    .Create("<api-client-id>")
    .WithClientSecret("<secret>")
    .WithAuthority(AzureCloudInstance.AzurePublic, "<tenant-id>")
    .Build();

var result = await app.AcquireTokenOnBehalfOf(
    new[] { "https://graph.microsoft.com/User.Read" },
    new UserAssertion(incomingAccessToken))
    .ExecuteAsync();
```

## MSAL.js (Browser)

### Installation

```bash
npm install @azure/msal-browser
```

### SPA Interactive Login

```typescript
import { PublicClientApplication, InteractionType } from "@azure/msal-browser";

const msalConfig = {
  auth: {
    clientId: "<client-id>",
    authority: "https://login.microsoftonline.com/<tenant-id>",
    redirectUri: "http://localhost:3000",
  },
};

const msalInstance = new PublicClientApplication(msalConfig);
await msalInstance.initialize();

// Login
const loginResponse = await msalInstance.loginPopup({
  scopes: ["User.Read"],
});

// Acquire token silently (from cache)
const tokenResponse = await msalInstance.acquireTokenSilent({
  scopes: ["User.Read"],
  account: loginResponse.account,
});
```

## Token Caching

### Python: Persistent File Cache

```python
import json
from pathlib import Path

cache = msal.SerializableTokenCache()
cache_path = Path("token_cache.json")

# Load existing cache
if cache_path.exists():
    cache.deserialize(cache_path.read_text())

app = msal.ConfidentialClientApplication(
    client_id="<client-id>",
    authority="https://login.microsoftonline.com/<tenant-id>",
    client_credential="<client-secret>",
    token_cache=cache,
)

# After token operations, persist cache
if cache.has_state_changed:
    cache_path.write_text(cache.serialize())
```

### .NET: Distributed Token Cache (Redis)

```csharp
using Microsoft.Identity.Web.TokenCacheProviders.Distributed;

builder.Services.AddDistributedMemoryCache(); // Or AddStackExchangeRedisCache
builder.Services.AddMicrosoftIdentityWebApiAuthentication(builder.Configuration)
    .EnableTokenAcquisitionToCallDownstreamApi()
    .AddDistributedTokenCaches();
```

### .NET: In-Memory Cache (Default)

```csharp
// MSAL uses in-memory cache by default — no config needed
// For production web apps, always use distributed cache
```

## Claims Challenge & Continuous Access Evaluation (CAE)

When a Conditional Access policy requires step-up auth, Graph returns a 401 with a `claims` header:

```python
import json
import base64

try:
    # Make Graph call
    result = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    result.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 401:
        # Extract claims challenge
        www_auth = e.response.headers.get("WWW-Authenticate", "")
        # Parse claims from the header
        claims = extract_claims_from_header(www_auth)

        # Re-acquire token with claims challenge
        result = app.acquire_token_interactive(
            scopes=["User.Read"],
            claims_challenge=claims,
        )
```

## Proof-of-Possession (PoP) Tokens

PoP tokens are bound to a specific HTTP request, preventing token replay:

```csharp
var result = await app.AcquireTokenForClient(
    new[] { "https://graph.microsoft.com/.default" })
    .WithProofOfPossession(new PoPAuthenticationConfiguration(
        new Uri("https://graph.microsoft.com/v1.0/me")))
    .ExecuteAsync();

// result.AccessToken is now a PoP token bound to that URL
// Use Authorization: PoP <token> (not Bearer)
```

## B2C Custom Policies

```python
# B2C uses a different authority format
b2c_authority = "https://contoso.b2clogin.com/contoso.onmicrosoft.com/B2C_1_signupsignin"

app = msal.PublicClientApplication(
    client_id="<b2c-client-id>",
    authority=b2c_authority,
)

result = app.acquire_token_interactive(
    scopes=["<b2c-api-scope>"],
)
```

## Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `AADSTS65001: User has not consented` | Missing consent for requested scopes | Trigger admin consent or use incremental consent |
| `AADSTS70011: Invalid scope` | Scope format wrong or not configured | Check scope format: `api://{id}/scope` for custom APIs |
| `AADSTS50013: Assertion failed signature validation` | OBO token targeting wrong audience | OBO token must target `api://{api-client-id}/.default` |
| `AADSTS700016: Application not found` | Wrong client ID or tenant | Verify app registration exists in the correct tenant |
| `AADSTS7000218: Request body must contain client_assertion` | Confidential client missing credential | Provide client secret, certificate, or assertion |

## Security Considerations

- **Protect token caches** — encrypt persistent caches, use DPAPI or Key Vault for secrets
- **Never log tokens** — access tokens are bearer credentials
- **Use short-lived tokens** — default 60-75 min lifetime is appropriate; don't extend
- **Prefer confidential clients** for server-side — secret stays on server, never exposed to browser
- **CAE-enabled tokens** are longer-lived but revocable — enable CAE for better security + UX

## Cross-References

- **→ `azure-identity-py`** — Higher-level wrapper; use MSAL when you need more control
- **→ `azure-identity-dotnet`** — Higher-level wrapper for .NET
- **→ `entra-app-registration`** — MSAL needs client config (ID, redirect URIs, scopes)
- **→ `entra-agent-id-runtime`** — Agent Identity OBO uses MSAL caching patterns
- **→ `entra-admin-consent-permissions`** — Consent affects what tokens MSAL can acquire
- **→ `entra-conditional-access`** — CA policies trigger claims challenges in MSAL
