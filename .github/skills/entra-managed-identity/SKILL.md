---
name: entra-managed-identity
description: "Azure Managed Identity configuration — system-assigned vs user-assigned MI, resource assignment, MI + RBAC patterns, federated identity credentials, eliminating secrets."
---

# Entra Managed Identity

> **Status:** Phase 2 — New skill

## Scope

- System-assigned vs user-assigned managed identity tradeoffs
- Creating user-assigned managed identities
- Assigning MI to Azure resources (App Service, Functions, Container Apps, VMs, AKS)
- MI + RBAC patterns (what roles MI needs for common scenarios)
- Federated identity credentials on user-assigned MI (for WIF)
- MI as the preferred alternative to secrets
- Token acquisition with MI (azure-identity SDK)
- Troubleshooting MI token issues

## Key Resources

| Operation | Method | Example |
|-----------|--------|---------|
| Create user-assigned MI | Bicep / CLI | `az identity create` |
| Assign to App Service | Bicep / CLI | `az webapp identity assign` |
| Assign RBAC role | Bicep / CLI | `az role assignment create` |
| Use in code | SDK | `ManagedIdentityCredential()` |

## TODO

- [ ] Full SKILL.md content
- [ ] Bicep patterns for MI creation + role assignment
- [ ] Per-service assignment examples (App Service, Functions, Container Apps, AKS, VM)
- [ ] Common role assignment matrix (Storage, Key Vault, SQL, Service Bus, Event Hubs)
- [ ] Troubleshooting: IMDS endpoint, token acquisition failures
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Related:** `azure-rbac` (MI needs role assignments)
- **Related:** `azure-identity-py`, `azure-identity-dotnet` (consuming MI tokens)
- **See also:** `entra-workload-identity-federation` (federated credentials on MI)
- **See also:** `entra-secret-certificate-lifecycle` (MI eliminates secrets)
