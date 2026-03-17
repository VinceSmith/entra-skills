---
name: entra-audit-signin-logs
description: "Entra ID audit and sign-in log analysis — directory audit queries, sign-in log queries (interactive, non-interactive, service principal), KQL patterns, risk events, identity protection."
---

# Entra Audit & Sign-In Logs

> **Status:** Phase 2 — New skill

## Scope

- Audit log queries: directory changes, app changes, group changes, role changes
- Sign-in log queries: interactive, non-interactive, service principal, managed identity
- KQL patterns for Azure Monitor / Log Analytics integration
- Risk events and identity protection risk detections
- Filtering and pagination patterns (large result sets)
- Export and retention configuration
- Common investigation scenarios (who changed what, failed sign-in patterns)

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| Directory audits | `GET /auditLogs/directoryAudits` | `AuditLog.Read.All` |
| Sign-in logs | `GET /auditLogs/signIns` | `AuditLog.Read.All` |
| Risk detections | `GET /identityProtection/riskDetections` | `IdentityRiskEvent.Read.All` |
| Risky users | `GET /identityProtection/riskyUsers` | `IdentityRiskyUser.Read.All` |

## TODO

- [ ] Full SKILL.md content
- [ ] Common investigation KQL queries (10+ patterns)
- [ ] Sign-in failure analysis patterns
- [ ] Agent Attribution: identifying agent vs user actions in logs
- [ ] Log Analytics workspace integration
- [ ] Python + .NET + KQL code examples
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Related:** `azure-kusto` (KQL query patterns)
- **Related:** All other Entra skills (what gets logged)
- **See also:** `entra-conditional-access` (CA policy evaluation in sign-in logs)
