---
name: entra-secret-certificate-lifecycle
description: "Entra ID secret and certificate lifecycle management — expiry monitoring, rotation patterns, Key Vault auto-rotation, bulk credential inventory, federated credentials as alternative."
---

# Entra Secret & Certificate Lifecycle

Managing secrets and certificates across app registrations — monitoring expiry, rotating credentials safely, leveraging Key Vault auto-rotation, and migrating to credential-free alternatives (MI, WIF). Auth hierarchy: MI → WIF → cert → **secret** (least preferred).

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List app credentials | `GET /applications/{id}` → `passwordCredentials`, `keyCredentials` | `Application.Read.All` |
| Add secret | `POST /applications/{id}/addPassword` | `Application.ReadWrite.All` |
| Remove secret | `POST /applications/{id}/removePassword` | `Application.ReadWrite.All` |
| Add certificate | `PATCH /applications/{id}` → `keyCredentials` | `Application.ReadWrite.All` |
| List SP credentials | `GET /servicePrincipals/{id}` → `passwordCredentials`, `keyCredentials` | `Application.Read.All` |

## Credential Inventory: Scan All Apps

### Python: Find Expiring Secrets

```python
from datetime import datetime, timedelta, timezone

warning_threshold = datetime.now(timezone.utc) + timedelta(days=30)
expired_threshold = datetime.now(timezone.utc)

apps = await graph_client.applications.get()
expiring_creds = []

for app in apps.value:
    # Check password credentials (secrets)
    for cred in (app.password_credentials or []):
        if cred.end_date_time and cred.end_date_time < warning_threshold:
            expiring_creds.append({
                "app": app.display_name,
                "app_id": app.app_id,
                "type": "secret",
                "key_id": str(cred.key_id),
                "expires": cred.end_date_time.isoformat(),
                "expired": cred.end_date_time < expired_threshold,
            })

    # Check key credentials (certificates)
    for cred in (app.key_credentials or []):
        if cred.end_date_time and cred.end_date_time < warning_threshold:
            expiring_creds.append({
                "app": app.display_name,
                "app_id": app.app_id,
                "type": "certificate",
                "key_id": str(cred.key_id),
                "expires": cred.end_date_time.isoformat(),
                "expired": cred.end_date_time < expired_threshold,
            })

for c in expiring_creds:
    status = "EXPIRED" if c["expired"] else "EXPIRING SOON"
    print(f"[{status}] {c['app']} ({c['type']}): expires {c['expires']}")
```

### .NET: Find Expiring Secrets

```csharp
var apps = await graphClient.Applications.GetAsync(config =>
{
    config.QueryParameters.Select = new[] {
        "displayName", "appId", "passwordCredentials", "keyCredentials"
    };
});

var warningDate = DateTimeOffset.UtcNow.AddDays(30);
foreach (var app in apps.Value)
{
    foreach (var cred in app.PasswordCredentials ?? [])
    {
        if (cred.EndDateTime < warningDate)
        {
            Console.WriteLine($"[EXPIRING] {app.DisplayName} secret expires {cred.EndDateTime}");
        }
    }
    foreach (var cred in app.KeyCredentials ?? [])
    {
        if (cred.EndDateTime < warningDate)
        {
            Console.WriteLine($"[EXPIRING] {app.DisplayName} cert expires {cred.EndDateTime}");
        }
    }
}
```

## Secret Rotation (Zero-Downtime)

### Pattern: Add New → Update Config → Remove Old

```python
from msgraph.generated.applications.item.add_password.add_password_post_request_body import (
    AddPasswordPostRequestBody,
)
from msgraph.generated.models.password_credential import PasswordCredential

# Step 1: Add new secret (keep old one active)
new_secret_body = AddPasswordPostRequestBody(
    password_credential=PasswordCredential(
        display_name=f"rotated-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        end_date_time=datetime.now(timezone.utc) + timedelta(days=180),
    ),
)
new_cred = await graph_client.applications.by_application_id(app_object_id).add_password.post(
    new_secret_body
)
new_secret_value = new_cred.secret_text  # Only available at creation time!

# Step 2: Update consuming services with new secret
# (deploy new config, update Key Vault, etc.)

# Step 3: Remove old secret (after confirming new secret works)
from msgraph.generated.applications.item.remove_password.remove_password_post_request_body import (
    RemovePasswordPostRequestBody,
)
remove_body = RemovePasswordPostRequestBody(key_id=old_key_id)
await graph_client.applications.by_application_id(app_object_id).remove_password.post(
    remove_body
)
```

> **CRITICAL:** `secret_text` is only returned at creation time. Store it in Key Vault immediately.

## Key Vault Integration

### Store Secret in Key Vault After Rotation

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
kv_client = SecretClient(vault_url="https://myvault.vault.azure.net", credential=credential)

# Store the new secret
kv_client.set_secret(
    name="myapp-client-secret",
    value=new_secret_value,
    content_type="application/x-entra-client-secret",
    tags={
        "app-id": app_client_id,
        "rotated": datetime.now(timezone.utc).isoformat(),
    },
)
```

### Key Vault Auto-Rotation Policy (Bicep)

```bicep
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: 'kv-myapp'
}

resource secret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'myapp-client-secret'
  properties: {
    attributes: {
      enabled: true
      exp: dateTimeAdd(utcNow(), 'P180D')  // 180 days
    }
  }
}
```

### CLI: Key Vault Rotation Policy

```bash
az keyvault secret rotation-policy update \
  --vault-name kv-myapp \
  --name myapp-client-secret \
  --value '{
    "lifetimeActions": [{
      "trigger": { "timeBeforeExpiry": "P30D" },
      "action": { "type": "Notify" }
    }],
    "attributes": {
      "expiryTime": "P180D"
    }
  }'
```

## Certificate Rotation

### Generate Certificate and Upload

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:2048 \
  -keyout key.pem -out cert.pem \
  -sha256 -days 365 -nodes \
  -subj "/CN=myapp.contoso.com"

# Convert to PFX
openssl pkcs12 -export -out cert.pfx -inkey key.pem -in cert.pem

# Upload to Key Vault
az keyvault certificate import \
  --vault-name kv-myapp \
  --name myapp-cert \
  --file cert.pfx
```

### Upload Certificate to App Registration

```python
import base64

# Read certificate
with open("cert.pem", "rb") as f:
    cert_data = f.read()

from msgraph.generated.models.application import Application
from msgraph.generated.models.key_credential import KeyCredential

app_update = Application(
    key_credentials=[
        KeyCredential(
            display_name="myapp-cert-2025",
            type="AsymmetricX509Cert",
            usage="Verify",
            key=base64.b64encode(cert_data).decode(),
            end_date_time=datetime.now(timezone.utc) + timedelta(days=365),
        ),
    ],
)
# Note: PATCH replaces all keyCredentials — include existing ones to keep them
await graph_client.applications.by_application_id(app_object_id).patch(app_update)
```

## Migration Paths

### Secrets → Federated Credentials (WIF)

For GitHub Actions, Kubernetes, or cross-cloud workloads:
1. Create a federated identity credential on the app registration (see `entra-workload-identity-federation`)
2. Update the workload to use OIDC token exchange instead of client secret
3. Remove the secret from the app registration
4. Delete the secret from Key Vault

### Secrets → Managed Identity

For Azure-hosted workloads:
1. Create or enable managed identity on the resource (see `entra-managed-identity`)
2. Assign RBAC roles to the MI
3. Update code to use `DefaultAzureCredential` or `ManagedIdentityCredential`
4. Remove the secret from the app registration
5. Delete the secret from Key Vault

## Monitoring & Alerting

### KQL: Credential Expiry Report

```kql
AuditLogs
| where TimeGenerated > ago(30d)
| where OperationName has_any ("Certificates and secrets", "addPassword", "removePassword")
| project TimeGenerated, 
    Operation = OperationName,
    Actor = coalesce(tostring(InitiatedBy.user.userPrincipalName), 
                     tostring(InitiatedBy.app.displayName)),
    TargetApp = tostring(TargetResources[0].displayName)
| order by TimeGenerated desc
```

## Security Considerations

- **Never hardcode secrets** — use Key Vault or environment variables
- **Set maximum secret lifetime** — 180 days recommended, never more than 1 year
- **Prefer certificates over secrets** — certificates are harder to exfiltrate
- **Prefer MI and WIF over both** — no credentials to manage at all
- **Monitor credential changes** in audit logs — unexpected changes are a red flag
- **`secret_text` is returned only once** — if you miss it, you must create a new secret

## Cross-References

- **→ `entra-app-registration`** — Credentials belong to app registrations
- **→ `entra-managed-identity`** — MI eliminates secrets entirely
- **→ `entra-workload-identity-federation`** — WIF eliminates secrets for external workloads
- **→ `entra-audit-signin-logs`** — Credential changes appear in audit logs
- **→ `azure-identity-py`** — `ClientSecretCredential` / `ClientCertificateCredential`
- **→ `azure-identity-dotnet`** — .NET credential classes for secrets and certificates
