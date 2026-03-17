---
name: entra-admin-consent-permissions
description: "Entra ID admin consent and API permissions — admin consent workflow, tenant-wide consent, per-user consent, permission grant lifecycle, pre-authorization, delegated vs application scoping."
---

# Entra Admin Consent & Permissions

> **Status:** Phase 2 — New skill

## Scope

- Admin consent workflow (admin consent endpoint URL construction)
- Tenant-wide consent vs per-user consent
- Permission grant lifecycle: request → review → grant → revoke
- Delegated permissions vs application permissions (when to use which)
- API permission scoping (least privilege selection)
- Pre-authorization (allow trusted apps without consent prompt)
- Incremental/dynamic consent patterns
- Permission classification (low/medium/high risk)
- Reviewing and revoking existing grants

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List permission grants | `GET /oauth2PermissionGrants` | `DelegatedPermissionGrant.ReadWrite.All` |
| Grant delegated permission | `POST /oauth2PermissionGrants` | `DelegatedPermissionGrant.ReadWrite.All` |
| List app role assignments | `GET /servicePrincipals/{id}/appRoleAssignments` | `Application.Read.All` |
| Grant app role | `POST /servicePrincipals/{id}/appRoleAssignments` | `AppRoleAssignment.ReadWrite.All` |
| Admin consent URL | `https://login.microsoftonline.com/{tenant}/adminconsent?client_id={id}` | — |

## TODO

- [ ] Full SKILL.md content
- [ ] Decision tree: delegated vs application permissions
- [ ] Common permission sets for typical scenarios (read mail, manage groups, etc.)
- [ ] Admin consent endpoint construction patterns
- [ ] Pre-authorization for first-party + Agent Identity scenarios
- [ ] PowerShell + CLI + Python + .NET examples
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Related:** `entra-app-registration` (permissions are configured on app registrations)
- **Related:** `entra-agent-id` (Agent Identity consent patterns)
- **Related:** `entra-agent-id-runtime` (OBO flow requires delegated consent)
- **See also:** `entra-users-groups` (user consent settings)
