---
name: entra-secret-certificate-lifecycle
description: "Entra ID secret and certificate lifecycle management — expiry monitoring, rotation patterns, Key Vault auto-rotation, bulk credential inventory, federated credentials as alternative."
---

# Entra Secret & Certificate Lifecycle

> **Status:** Phase 2 — New skill

## Scope

- Secret expiry monitoring (approaching expiry detection)
- Certificate rotation patterns (create new → update config → remove old)
- Key Vault integration for automatic rotation
- Bulk credential inventory across all app registrations
- Federated credentials as secret-free alternative
- Managed identity as the preferred approach (no credentials to manage)
- Notification and alerting patterns
- Compliance: rotation frequency requirements

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List app credentials | `GET /applications/{id}` (passwordCredentials, keyCredentials) | `Application.Read.All` |
| Add secret | `POST /applications/{id}/addPassword` | `Application.ReadWrite.All` |
| Remove secret | `POST /applications/{id}/removePassword` | `Application.ReadWrite.All` |
| Add certificate | `PATCH /applications/{id}` (keyCredentials) | `Application.ReadWrite.All` |

## TODO

- [ ] Full SKILL.md content
- [ ] PowerShell script: scan all apps for expiring secrets (< 30 days)
- [ ] Key Vault rotation policy configuration (Bicep + CLI)
- [ ] Rotation runbook (zero-downtime secret rotation)
- [ ] Migration guide: secrets → federated credentials
- [ ] Migration guide: secrets → managed identity
- [ ] Python + .NET + PowerShell examples
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Related:** `entra-app-registration` (credentials are on app registrations)
- **Related:** `entra-managed-identity` (MI eliminates secrets)
- **Related:** `entra-workload-identity-federation` (WIF eliminates secrets)
- **See also:** `entra-audit-signin-logs` (credential changes in audit logs)
