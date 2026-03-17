---
name: azure-identity-py
description: |
  Azure Identity SDK for Python authentication. Use for DefaultAzureCredential, managed identity, service principals, token caching, sovereign clouds, async support, logging, and error handling.
  Triggers: "azure-identity", "DefaultAzureCredential", "authentication python", "managed identity python", "service principal python", "credential python".
package: azure-identity
---

# Azure Identity SDK for Python

Authentication library for Azure SDK clients using Microsoft Entra ID (formerly Azure AD).

## Installation

```bash
pip install azure-identity
```

## Environment Variables

```bash
# Service Principal (for production/CI)
AZURE_TENANT_ID=<your-tenant-id>
AZURE_CLIENT_ID=<your-client-id>
AZURE_CLIENT_SECRET=<your-client-secret>

# User-assigned Managed Identity (optional)
AZURE_CLIENT_ID=<managed-identity-client-id>
```

## DefaultAzureCredential

The recommended credential for most scenarios. Tries multiple authentication methods in order:

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Works in local dev AND production without code changes
credential = DefaultAzureCredential()

client = BlobServiceClient(
    account_url="https://<account>.blob.core.windows.net",
    credential=credential,
)
```

### Credential Chain Order

| Order | Credential | Environment |
|-------|-----------|-------------|
| 1 | EnvironmentCredential | CI/CD, containers |
| 2 | WorkloadIdentityCredential | Kubernetes |
| 3 | ManagedIdentityCredential | Azure VMs, App Service, Functions |
| 4 | SharedTokenCacheCredential | Windows only |
| 5 | VisualStudioCodeCredential | VS Code with Azure extension |
| 6 | AzureCliCredential | `az login` |
| 7 | AzurePowerShellCredential | `Connect-AzAccount` |
| 8 | AzureDeveloperCliCredential | `azd auth login` |

### Customizing DefaultAzureCredential

```python
credential = DefaultAzureCredential(
    exclude_environment_credential=True,
    exclude_shared_token_cache_credential=True,
    managed_identity_client_id="<user-assigned-mi-client-id>",
)

# Enable interactive browser (disabled by default)
credential = DefaultAzureCredential(
    exclude_interactive_browser_credential=False,
)
```

## Specific Credential Types

### ManagedIdentityCredential

For Azure-hosted resources (VMs, App Service, Functions, AKS):

```python
from azure.identity import ManagedIdentityCredential

# System-assigned managed identity
credential = ManagedIdentityCredential()

# User-assigned managed identity
credential = ManagedIdentityCredential(
    client_id="<user-assigned-mi-client-id>",
)
```

### ClientSecretCredential

```python
import os
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)
```

### ClientCertificateCredential

```python
from azure.identity import ClientCertificateCredential

credential = ClientCertificateCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    certificate_path="/path/to/cert.pem",
)
```

### ChainedTokenCredential

Custom credential chain:

```python
from azure.identity import (
    ChainedTokenCredential,
    ManagedIdentityCredential,
    AzureCliCredential,
)

# Try managed identity first, fall back to CLI
credential = ChainedTokenCredential(
    ManagedIdentityCredential(client_id="<user-assigned-mi-client-id>"),
    AzureCliCredential(),
)
```

### AzureCliCredential

```python
from azure.identity import AzureCliCredential

credential = AzureCliCredential()
```

## Credential Types Reference

| Credential | Use Case | Auth Method |
|------------|----------|-------------|
| `DefaultAzureCredential` | Most scenarios | Auto-detect |
| `ManagedIdentityCredential` | Azure-hosted apps | Managed Identity |
| `ClientSecretCredential` | Service principal | Client secret |
| `ClientCertificateCredential` | Service principal | Certificate |
| `WorkloadIdentityCredential` | Kubernetes | Federated token |
| `AzureCliCredential` | Local development | Azure CLI |
| `AzureDeveloperCliCredential` | Local development | Azure Developer CLI |
| `InteractiveBrowserCredential` | User sign-in | Browser OAuth |
| `DeviceCodeCredential` | Headless/SSH | Device code flow |
| `OnBehalfOfCredential` | API calling another API | OBO flow |

## Getting Tokens Directly

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()

# Get token for a specific scope
token = credential.get_token("https://management.azure.com/.default")
print(f"Token expires: {token.expires_on}")

# For Azure Database for PostgreSQL
token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")

# For Microsoft Graph
token = credential.get_token("https://graph.microsoft.com/.default")
```

## Async Support

```python
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient

async def main():
    credential = DefaultAzureCredential()

    async with BlobServiceClient(
        account_url="https://<account>.blob.core.windows.net",
        credential=credential,
    ) as client:
        # ... async operations
        pass

    await credential.close()
```

> **Note:** `TokenCachePersistenceOptions` is NOT available in `azure.identity.aio` — import from `azure.identity`.

## Sovereign Clouds

```python
from azure.identity import DefaultAzureCredential, AzureAuthorityHosts

# Azure Government
credential = DefaultAzureCredential(
    authority=AzureAuthorityHosts.AZURE_GOVERNMENT,
)

# Azure China (21Vianet)
credential = DefaultAzureCredential(
    authority=AzureAuthorityHosts.AZURE_CHINA,
)

# Available authority hosts:
# AzureAuthorityHosts.AZURE_PUBLIC_CLOUD (default)
# AzureAuthorityHosts.AZURE_GOVERNMENT
# AzureAuthorityHosts.AZURE_CHINA
```

## Token Caching

### In-Memory (Default)

All credentials cache tokens in-memory by default. No configuration needed.

### Persistent Token Cache

```python
from azure.identity import TokenCachePersistenceOptions, DefaultAzureCredential

# Enable persistent cache (encrypted, OS-level keychain)
cache_options = TokenCachePersistenceOptions(
    name="my_app_cache",              # Cache name (isolated per app)
    allow_unencrypted_storage=False,   # Require encryption (default)
)

credential = DefaultAzureCredential(
    cache_persistence_options=cache_options,
)
```

Persistent cache uses OS-level encrypted storage:
- **Windows:** DPAPI-encrypted file
- **macOS:** Keychain
- **Linux:** libsecret / keyring (requires `libsecret` installed)

> Requires `pip install azure-identity[persistence]` for persistent cache support.

## Logging and Diagnostics

```python
import logging

# Enable azure-identity debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("azure.identity")
logger.setLevel(logging.DEBUG)

# For production — log warnings only
logger.setLevel(logging.WARNING)
```

Enable HTTP request/response logging (for debugging token endpoints):

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential(logging_enable=True)
```

## Error Handling

```python
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import ClientAuthenticationError

credential = DefaultAzureCredential()

try:
    token = credential.get_token("https://management.azure.com/.default")
except ClientAuthenticationError as e:
    # All credential types exhausted or specific credential failed
    print(f"Authentication failed: {e.message}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Exception Types

| Exception | When | Example |
|-----------|------|---------|
| `ClientAuthenticationError` | Credential fails to authenticate | Wrong secret, expired cert, MI unavailable |
| `CredentialUnavailableError` | Credential cannot run in current environment | No managed identity endpoint on local machine |

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `DefaultAzureCredential failed to retrieve a token` | No credential in chain worked | Run `az login` locally; set env vars in CI |
| `ManagedIdentityCredential: IMDS endpoint unavailable` | Not running on Azure | Use `DefaultAzureCredential` which falls through |
| `ClientSecretCredential: AADSTS7000218` | Secret expired | Rotate secret (→ `entra-secret-certificate-lifecycle`) |
| `EnvironmentCredential: incomplete configuration` | Missing env vars | Set `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |

## Best Practices

1. **Use DefaultAzureCredential** for code that runs locally and in Azure
2. **Never hardcode credentials** — use environment variables or managed identity
3. **Prefer managed identity** in production Azure deployments
4. **Use ChainedTokenCredential** when you need a custom credential order
5. **Close async credentials** explicitly or use context managers
6. **Set AZURE_CLIENT_ID** for user-assigned managed identities
7. **Exclude unused credentials** to speed up DefaultAzureCredential chain
8. **Reuse credential instances** — they are thread-safe and cache tokens
9. **Enable logging** during development for debugging auth failures

## Cross-References

- **Mirror of:** `azure-identity-dotnet` (same concepts, different language)
- **Higher-level than:** `entra-msal-deep-dive` (use MSAL when azure-identity isn't enough)
- **Used by:** `entra-agent-id` (provisioning scripts use ClientSecretCredential)
- **Related:** `entra-managed-identity` (MI tokens consumed via this SDK)
- **Related:** `entra-app-registration` (app registrations create the credentials this SDK uses)
