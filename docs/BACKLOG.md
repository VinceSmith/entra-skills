# Backlog — Entra Identity Skills

Tracked items for the Entra identity management toolkit.
See [PLAN.md](PLAN.md) for the phased delivery plan with full task checklists.

## Completed

### Phase 1 — Enhance Existing Skills ✅
| ID | Task | Status |
|----|------|--------|
| P1-1 | Define skill conventions template | ✅ Done |
| P1-2 | Enhance `entra-app-registration` | ✅ Done |
| P1-3 | Enhance `azure-rbac` | ✅ Done |
| P1-4 | Enhance `azure-identity-py` | ✅ Done |
| P1-5 | Review `entra-agent-id` + `entra-agent-id-runtime` | ✅ Done |
| P1-6 | Review `azure-identity-dotnet` | ✅ Done |

### Phase 2 — New Skills ✅
| ID | Task | Status |
|----|------|--------|
| P2-1 | Create `entra-users-groups` | ✅ Done |
| P2-2 | Create `entra-conditional-access` | ✅ Done |
| P2-3 | Create `entra-managed-identity` | ✅ Done |
| P2-4 | Create `entra-workload-identity-federation` | ✅ Done |
| P2-5 | Create `entra-admin-consent-permissions` | ✅ Done |
| P2-6 | Create `entra-audit-signin-logs` | ✅ Done |
| P2-7 | Create `entra-secret-certificate-lifecycle` | ✅ Done |
| P2-8 | Create `entra-msal-deep-dive` | ✅ Done |

### Phase 3 — Python MCP Server ✅
| ID | Task | Status |
|----|------|--------|
| P3-1 | Scaffold Python MCP server | ✅ Done |
| P3-2 | User & group tools (6 tools) | ✅ Done |
| P3-3 | App registration tools (5 tools) | ✅ Done |
| P3-4 | Identity diagnostics tools (4 tools) | ✅ Done |
| P3-5 | RBAC tools (3 tools) | ✅ Done |
| P3-6 | Agent Identity tools (3 tools) | ✅ Done |

### Phase 4 — TypeScript MCP Server ✅
| ID | Task | Status |
|----|------|--------|
| P4-1 | Scaffold TypeScript MCP server | ✅ Done |
| P4-2 | Managed Identity tools (3 tools) | ✅ Done |
| P4-3 | WIF tools (3 tools) | ✅ Done |
| P4-4 | Conditional Access tools (4 tools) | ✅ Done |
| P4-5 | Secret/cert lifecycle tools (3 tools) | ✅ Done |

### Phase 5 — Custom Agents ✅
| ID | Task | Status |
|----|------|--------|
| P5-1 | Finalize entra-admin agent | ✅ Done |
| P5-2 | Finalize entra-security-auditor agent | ✅ Done |
| P5-3 | Finalize entra-app-wizard agent | ✅ Done |

### Phase 6 — Instructions & Integration (partial)
| ID | Task | Status |
|----|------|--------|
| P6-1 | Finalize entra-conventions instructions | ✅ Done |
| P6-2 | Finalize entra-security instructions | ✅ Done |
| P6-3 | Cross-skill integration testing | ⏳ Remaining |

## Remaining Work

| ID | Task | Priority | Notes |
|----|------|----------|-------|
| P6-3 | Integration testing | Medium | Test MCP servers with agents, validate cross-refs |
| UT-1 | Python MCP unit tests | Medium | pytest mocks for Graph SDK calls |
| UT-2 | TypeScript MCP unit tests | Medium | vitest mocks for az CLI calls |
| TS-1 | Agent test scenarios | Low | Manual test scripts per agent persona |

## Summary

- **34 MCP tools** implemented (21 Python + 13 TypeScript)
- **14 skills** covering all Entra identity domains
- **3 custom agents** with distinct personas and access levels
- **2 instruction files** for conventions and security guardrails

## Open Questions

- [ ] Test tenant for MCP server development?
- [ ] npm + PyPI distribution when going public?
- [ ] Plugin bundle (`azure-entra`) or individual skills?
