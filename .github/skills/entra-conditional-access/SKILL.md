---
name: entra-conditional-access
description: "Entra ID Conditional Access policy management — policy lifecycle, common templates, named locations, authentication contexts, grant/session controls, what-if analysis via Microsoft Graph."
---

# Entra Conditional Access

> **Status:** Phase 2 — New skill

## Scope

- Conditional Access policy CRUD (create, read, update, delete)
- Common policy templates (require MFA, block legacy auth, require compliant device)
- Named locations (IP ranges, countries)
- Authentication contexts and authentication strengths
- Grant controls (MFA, compliant device, Entra joined, app protection)
- Session controls (sign-in frequency, persistent browser, MCAS)
- What-if analysis (test policy impact before enabling)
- Report-only mode for safe rollout

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List policies | `GET /identity/conditionalAccess/policies` | `Policy.Read.All` |
| Create policy | `POST /identity/conditionalAccess/policies` | `Policy.ReadWrite.ConditionalAccess` |
| Named locations | `GET /identity/conditionalAccess/namedLocations` | `Policy.Read.All` |
| What-if | `POST /identity/conditionalAccess/evaluate` | `Policy.Read.All` |

## TODO

- [ ] Full SKILL.md content with code examples
- [ ] Common policy template library (10+ templates)
- [ ] Migration guide: legacy MFA → CA policies
- [ ] Emergency access account exclusion patterns
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Related:** `entra-app-registration` (target apps in policies)
- **Related:** `entra-users-groups` (target users/groups)
- **See also:** `entra-audit-signin-logs` (CA policy evaluation in sign-in logs)
