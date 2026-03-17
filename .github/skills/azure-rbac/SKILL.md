---
name: azure-rbac
description: "Azure RBAC role assignment for Entra identities — role definition matrices, scope hierarchy, least-privilege role selection, custom roles, deny assignments, Bicep + CLI patterns. WHEN: what role should I assign, least privilege role, RBAC role for, role to read blobs, role for managed identity, custom role definition, assign role to identity, permissions to assign roles, deny assignment."
---

# Azure RBAC for Entra Identities

Assign the right Azure RBAC role to Entra identities (users, groups, service principals, managed identities) with least-privilege access.

## Before You Start

Use `azure__documentation` MCP tool to find role definitions. Use `azure__extension_cli_generate` for CLI commands and custom roles. Use `azure__bicepschema` for Bicep patterns.

## Scope Hierarchy

Roles are inherited downward. Assign at the **narrowest scope** that meets requirements.

```
Management Group
  └── Subscription
        └── Resource Group
              └── Resource (individual storage account, key vault, etc.)
```

| Scope Level | When to Use | Example |
|-------------|-------------|---------|
| Management Group | Org-wide policies, compliance | Security Reader across all subscriptions |
| Subscription | Team-wide access | Contributor for a dev team subscription |
| Resource Group | Project-level access | Storage Blob Data Reader for an app's RG |
| Resource | Least-privilege single resource | Key Vault Secrets User on one vault |

## Common Identity Roles

### Entra Directory Roles (for managing Entra itself)

| Role | Scope | Use Case |
|------|-------|----------|
| **User Administrator** | Entra directory | Manage users and groups |
| **Application Administrator** | Entra directory | Manage app registrations and SPs |
| **Cloud Application Administrator** | Entra directory | Like App Admin but cannot manage app proxy |
| **Privileged Role Administrator** | Entra directory | Manage Entra role assignments |
| **Conditional Access Administrator** | Entra directory | Manage CA policies |
| **Security Reader** | Entra directory | View security info, sign-in reports |
| **Global Reader** | Entra directory | Read everything, write nothing |

### Azure Resource Roles (for accessing Azure resources)

| Role | ID | Permissions | Common Use |
|------|----|-------------|------------|
| **Reader** | `acdd72a7-...` | Read all resources | Monitoring, dashboards |
| **Contributor** | `b24988ac-...` | Read/write (no RBAC changes) | Developers |
| **Owner** | `8e3af657-...` | Full access including RBAC | Subscription admins |
| **User Access Administrator** | `18d7d88d-...` | Manage role assignments only | RBAC delegation |

### Data Plane Roles (for accessing data within resources)

| Role | Use Case | Replaces |
|------|----------|----------|
| **Storage Blob Data Reader** | Read blobs | Storage account keys |
| **Storage Blob Data Contributor** | Read/write/delete blobs | Storage account keys |
| **Storage Queue Data Contributor** | Read/write queue messages | Storage account keys |
| **Key Vault Secrets User** | Read secrets | Access policies |
| **Key Vault Crypto User** | Encrypt/decrypt with keys | Access policies |
| **Key Vault Certificates Officer** | Manage certificates | Access policies |
| **Azure Service Bus Data Receiver** | Receive messages | Connection strings |
| **Azure Service Bus Data Sender** | Send messages | Connection strings |
| **Azure Event Hubs Data Receiver** | Receive events | Connection strings |
| **Cosmos DB Account Reader** | Read Cosmos data | Account keys |

## Assigning Roles

### Service Principal vs Managed Identity

| Aspect | Service Principal | Managed Identity |
|--------|------------------|------------------|
| **Create** | Auto-created from app registration | `az identity create` or Bicep |
| **Credential** | Secret, cert, or federated | None (automatic) |
| **Assign role to** | SP's object ID | MI's principal ID |
| **Best for** | External/cross-tenant, CI/CD with WIF | Azure-hosted workloads |
| **Find principal ID** | `az ad sp show --id $APP_ID --query id` | `az identity show --name mi-name --query principalId` |

### Azure CLI

```bash
# Assign role to service principal
az role assignment create \
  --assignee-object-id $(az ad sp show --id $APP_ID --query id -o tsv) \
  --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$SA"

# Assign role to managed identity
MI_PRINCIPAL_ID=$(az identity show -n mi-myapp -g $RG --query principalId -o tsv)
az role assignment create \
  --assignee-object-id $MI_PRINCIPAL_ID \
  --assignee-principal-type ServicePrincipal \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.KeyVault/vaults/$KV"

# Assign role to group
az role assignment create \
  --assignee-object-id $GROUP_ID \
  --assignee-principal-type Group \
  --role "Reader" \
  --scope "/subscriptions/$SUB_ID/resourceGroups/$RG"

# List role assignments for a principal
az role assignment list --assignee $PRINCIPAL_ID --all -o table
```

### Bicep

```bicep
// Role assignment for a managed identity
param principalId string
param storageAccountName string

var storageBlobDataReaderRoleId = '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, principalId, storageBlobDataReaderRoleId)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      storageBlobDataReaderRoleId
    )
    principalId: principalId
    principalType: 'ServicePrincipal' // Use for MI and SP; 'Group' for groups
  }
}
```

### .NET

```csharp
using Azure.Identity;
using Azure.ResourceManager;
using Azure.ResourceManager.Authorization;
using Azure.ResourceManager.Authorization.Models;

var credential = new DefaultAzureCredential();
var client = new ArmClient(credential);

var scope = new ResourceIdentifier(
    $"/subscriptions/{subId}/resourceGroups/{rgName}");
var roleDefinitionId = new ResourceIdentifier(
    $"/subscriptions/{subId}/providers/Microsoft.Authorization/roleDefinitions/2a2b9908-6ea1-4ae2-8e65-a410df84e7d1");

var roleAssignment = new RoleAssignmentCreateOrUpdateContent(
    roleDefinitionId, principalId)
{
    PrincipalType = RoleManagementPrincipalType.ServicePrincipal,
};

await client.GetRoleAssignments(scope)
    .CreateOrUpdateAsync(WaitUntil.Completed, Guid.NewGuid().ToString(), roleAssignment);
```

## Custom Roles

When no built-in role matches, create a custom role.

```bash
# Create custom role definition
az role definition create --role-definition '{
  "Name": "Contoso Blob Reader",
  "Description": "Read blobs and list containers only",
  "Actions": [],
  "DataActions": [
    "Microsoft.Storage/storageAccounts/blobServices/containers/read",
    "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
  ],
  "NotDataActions": [],
  "AssignableScopes": ["/subscriptions/'$SUB_ID'"]
}'
```

```bicep
resource customRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: guid(subscription().id, 'contoso-blob-reader')
  properties: {
    roleName: 'Contoso Blob Reader'
    description: 'Read blobs and list containers only'
    type: 'CustomRole'
    permissions: [
      {
        actions: []
        dataActions: [
          'Microsoft.Storage/storageAccounts/blobServices/containers/read'
          'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read'
        ]
      }
    ]
    assignableScopes: [
      subscription().id
    ]
  }
}
```

## Deny Assignments

Deny assignments **block** actions even if a role assignment grants them. They can only be created by Azure Blueprints and managed applications (not directly by users).

```bash
# List deny assignments
az role assignment list --include-deny-assignments --all
```

## Prerequisites for Granting Roles

To assign RBAC roles, you need a role with `Microsoft.Authorization/roleAssignments/write`:

| Role | Scope | Use Case |
|------|-------|----------|
| **User Access Administrator** | Any | Least privilege for role assignment only |
| **Owner** | Any | Full access including role assignment |
| **Role Based Access Control Administrator** | Any | Manage role assignments with conditions |
| Custom role with `Microsoft.Authorization/roleAssignments/write` | Scoped | Constrained delegation |

## Audit & Compliance

- Role assignments appear in **Azure Activity Log** (not Entra audit logs)
- Use `az monitor activity-log list --resource-type Microsoft.Authorization/roleAssignments` to query
- Set up **Azure Policy** to enforce required role assignments or block overprivileged ones
- Use **PIM (Privileged Identity Management)** for just-in-time elevation of standing roles

## Best Practices

1. **Assign to groups, not individuals** — Easier to manage; add/remove users from groups
2. **Use narrowest scope** — Resource-level over resource group; resource group over subscription
3. **Prefer data plane roles** — Use "Storage Blob Data Reader" not "Reader" for blob access
4. **Avoid Owner/Contributor at subscription** — Too broad; use specific roles
5. **Use PIM for elevated access** — Just-in-time activation for admin roles
6. **Audit regularly** — `az role assignment list --all` to find unnecessary assignments
7. **Specify `principalType`** — Always include in CLI/Bicep to avoid lookup delays

## Cross-References

- **→ `entra-managed-identity`** — Create managed identities that need RBAC roles
- **→ `azure-identity-py` / `azure-identity-dotnet`** — Code that consumes the roles via tokens
- **→ `entra-app-registration`** — Service principals that need RBAC roles
- **→ `entra-agent-id`** — Agent Identity SPs that need RBAC roles
- **→ `entra-audit-signin-logs`** — Monitor role assignment changes
