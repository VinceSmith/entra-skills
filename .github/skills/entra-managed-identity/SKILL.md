---
name: entra-managed-identity
description: "Azure Managed Identity configuration — system-assigned vs user-assigned MI, resource assignment, MI + RBAC patterns, federated identity credentials, eliminating secrets."
---

# Entra Managed Identity

Managed Identity (MI) is the **preferred authentication method** for Azure-hosted workloads. MI eliminates credentials entirely — Azure manages the identity lifecycle, token issuance, and rotation. Auth hierarchy: **MI → WIF → cert → secret**.

## System-Assigned vs User-Assigned

| Aspect | System-Assigned | User-Assigned |
|--------|----------------|---------------|
| Lifecycle | Tied to resource — deleted when resource is deleted | Independent — exists until explicitly deleted |
| Sharing | One identity per resource | One identity shared across multiple resources |
| Creation | Enable on the resource | Create separately, assign to resources |
| Use case | Single resource, simple scenarios | Shared identity, pre-provisioning, WIF |
| Federated credentials | Not supported | Supported (for WIF) |

**Recommendation:** Use **user-assigned MI** for production workloads (survives resource recreation, supports WIF, shareable).

## Creating User-Assigned Managed Identity

### Bicep

```bicep
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-myapp-prod'
  location: resourceGroup().location
  tags: {
    environment: 'production'
    application: 'myapp'
  }
}

output principalId string = managedIdentity.properties.principalId
output clientId string = managedIdentity.properties.clientId
output resourceId string = managedIdentity.id
```

### CLI

```bash
az identity create \
  --name mi-myapp-prod \
  --resource-group rg-myapp \
  --location eastus2
```

## Assigning MI to Azure Resources

### App Service / Functions (Bicep)

```bicep
resource appService 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-myapi'
  location: resourceGroup().location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    // ...
  }
}
```

### Container Apps (Bicep)

```bicep
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-myapi'
  location: resourceGroup().location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    // ...
  }
}
```

### AKS (Bicep)

```bicep
resource aks 'Microsoft.ContainerService/managedClusters@2024-01-01' = {
  name: 'aks-myapp'
  location: resourceGroup().location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    // ...
  }
}
```

### CLI — Assign to Existing Resource

```bash
# App Service
az webapp identity assign \
  --name app-myapi \
  --resource-group rg-myapp \
  --identities /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.ManagedIdentity/userAssignedIdentities/mi-myapp-prod

# Container Apps
az containerapp identity assign \
  --name ca-myapi \
  --resource-group rg-myapp \
  --user-assigned mi-myapp-prod

# VM
az vm identity assign \
  --name vm-myapp \
  --resource-group rg-myapp \
  --identities mi-myapp-prod
```

## MI + RBAC Role Assignment Patterns

After assigning MI to a resource, grant it only the roles it needs:

### Common Role Matrix

| Target Resource | Role | Scope | Use Case |
|----------------|------|-------|----------|
| Key Vault | `Key Vault Secrets User` | Vault | Read secrets |
| Key Vault | `Key Vault Certificates Officer` | Vault | Manage certificates |
| Storage Account | `Storage Blob Data Reader` | Account/Container | Read blobs |
| Storage Account | `Storage Blob Data Contributor` | Account/Container | Read/write blobs |
| SQL Database | N/A (use contained user) | Database | SQL access |
| Service Bus | `Azure Service Bus Data Receiver` | Namespace/Queue | Receive messages |
| Service Bus | `Azure Service Bus Data Sender` | Namespace/Queue | Send messages |
| Event Hubs | `Azure Event Hubs Data Receiver` | Namespace/Hub | Receive events |
| Cosmos DB | `Cosmos DB Built-in Data Reader` | Account | Read data |
| App Configuration | `App Configuration Data Reader` | Store | Read config |

### Bicep Role Assignment

```bicep
@description('Role definition ID for Key Vault Secrets User')
var keyVaultSecretsUserRole = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '4633458b-17de-408a-b874-0445c86b69e6'
)

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentity.id, keyVaultSecretsUserRole)
  scope: keyVault
  properties: {
    principalId: managedIdentity.properties.principalId
    roleDefinitionId: keyVaultSecretsUserRole
    principalType: 'ServicePrincipal'
  }
}
```

## Using MI in Code

### Python

```python
from azure.identity import ManagedIdentityCredential, DefaultAzureCredential

# User-assigned MI (explicit)
credential = ManagedIdentityCredential(client_id="<mi-client-id>")

# DefaultAzureCredential (auto-detects MI in Azure)
credential = DefaultAzureCredential(
    managed_identity_client_id="<mi-client-id>"  # For user-assigned
)

# Use with any Azure SDK client
from azure.keyvault.secrets import SecretClient
client = SecretClient(vault_url="https://myvault.vault.azure.net", credential=credential)
secret = client.get_secret("my-secret")
```

### .NET

```csharp
using Azure.Identity;
using Azure.Security.KeyVault.Secrets;

// User-assigned MI
var credential = new ManagedIdentityCredential(
    ManagedIdentityId.FromUserAssignedClientId("<mi-client-id>"));

// Use with any Azure SDK client
var client = new SecretClient(
    new Uri("https://myvault.vault.azure.net"),
    credential);
var secret = await client.GetSecretAsync("my-secret");
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ManagedIdentityCredential authentication unavailable` | MI not assigned to resource | Enable MI or assign user-assigned MI |
| `AADSTS700024: Client assertion is not within its valid time range` | IMDS clock skew | Restart the resource; check NTP |
| Token works locally but not in Azure | Using `DefaultAzureCredential` without MI config | Set `AZURE_CLIENT_ID` env var to user-assigned MI client ID |
| `403 Forbidden` from target service | Missing RBAC role assignment | Assign correct role at correct scope |
| `EnvironmentCredential authentication unavailable` in Azure | Environment variables set that conflict with MI | Remove `AZURE_CLIENT_SECRET` env var in Azure |

## Security Considerations

- **Prefer user-assigned MI** for production (survives resource recreation, auditable)
- **Scope RBAC tightly** — assign roles at the narrowest scope (resource, not subscription)
- **Set `principalType: 'ServicePrincipal'`** in Bicep role assignments to avoid race conditions
- **Avoid system-assigned MI** when resources may be recreated (new MI = new principal = broken role assignments)
- **Use `DefaultAzureCredential`** with explicit `managed_identity_client_id` to avoid ambiguity

## Cross-References

- **→ `azure-rbac`** — Role assignment for MI principals
- **→ `azure-identity-py`** — `ManagedIdentityCredential` usage in Python
- **→ `azure-identity-dotnet`** — `ManagedIdentityCredential` usage in .NET
- **→ `entra-workload-identity-federation`** — Federated credentials on user-assigned MI
- **→ `entra-secret-certificate-lifecycle`** — MI eliminates the need for secret management
- **→ `entra-app-registration`** — MI is an alternative to app registration + secret for Azure workloads
