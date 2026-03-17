# Backlog — Entra Identity Skills

Tracked items for the Entra identity management toolkit.
See [PLAN.md](PLAN.md) for the phased delivery plan with full task checklists.

## Current Focus: Phase 1 — Enhance Existing Skills

### Ready to Start
| ID | Task | Phase | Skill | Priority |
|----|------|-------|-------|----------|
| P1-1 | Define skill conventions template | 1.1 | All | High |
| P1-2 | Enhance `entra-app-registration` | 1.2 | entra-app-registration | High |
| P1-3 | Enhance `azure-rbac` | 1.3 | azure-rbac | High |
| P1-4 | Enhance `azure-identity-py` | 1.4 | azure-identity-py | Medium |
| P1-5 | Review `entra-agent-id` + `entra-agent-id-runtime` | 1.5 | entra-agent-id* | Medium |
| P1-6 | Review `azure-identity-dotnet` | 1.6 | azure-identity-dotnet | Low |

### Up Next: Phase 2 — New Skills (all parallelizable)
| ID | Task | Phase | Skill | Priority |
|----|------|-------|-------|----------|
| P2-1 | Create `entra-users-groups` | 2.1 | entra-users-groups | High |
| P2-2 | Create `entra-conditional-access` | 2.2 | entra-conditional-access | Medium |
| P2-3 | Create `entra-managed-identity` | 2.3 | entra-managed-identity | High |
| P2-4 | Create `entra-workload-identity-federation` | 2.4 | entra-workload-identity-federation | High |
| P2-5 | Create `entra-admin-consent-permissions` | 2.5 | entra-admin-consent-permissions | Medium |
| P2-6 | Create `entra-audit-signin-logs` | 2.6 | entra-audit-signin-logs | Medium |
| P2-7 | Create `entra-secret-certificate-lifecycle` | 2.7 | entra-secret-certificate-lifecycle | Medium |
| P2-8 | Create `entra-msal-deep-dive` | 2.8 | entra-msal-deep-dive | Medium |

### Later: Phases 3–6
| ID | Task | Phase | Component | Priority |
|----|------|-------|-----------|----------|
| P3-1 | Scaffold Python MCP server | 3.1 | entra-graph-py | — |
| P3-2 | User & group tools | 3.2 | entra-graph-py | — |
| P3-3 | App registration tools | 3.3 | entra-graph-py | — |
| P3-4 | Identity diagnostics tools | 3.4 | entra-graph-py | — |
| P3-5 | RBAC tools | 3.5 | entra-graph-py | — |
| P3-6 | Agent Identity tools | 3.6 | entra-graph-py | — |
| P4-1 | Scaffold TypeScript MCP server | 4.1 | entra-infra-ts | — |
| P4-2 | Managed Identity tools | 4.2 | entra-infra-ts | — |
| P4-3 | WIF tools | 4.3 | entra-infra-ts | — |
| P4-4 | Conditional Access tools | 4.4 | entra-infra-ts | — |
| P4-5 | Secret/cert lifecycle tools | 4.5 | entra-infra-ts | — |
| P5-1 | Finalize entra-admin agent | 5.1 | Agents | — |
| P5-2 | Finalize entra-security-auditor agent | 5.2 | Agents | — |
| P5-3 | Finalize entra-app-wizard agent | 5.3 | Agents | — |
| P6-1 | Finalize entra-conventions instructions | 6.1 | Instructions | — |
| P6-2 | Finalize entra-security instructions | 6.2 | Instructions | — |
| P6-3 | Cross-skill integration testing | 6.3 | All | — |

## Open Questions

- [ ] Test tenant for MCP server development?
- [ ] npm + PyPI distribution when going public?
- [ ] Plugin bundle (`azure-entra`) or individual skills?
