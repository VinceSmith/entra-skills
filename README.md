# Entra Identity Management — Skills, Agents & MCP Servers

> Comprehensive coding agent toolkit for Microsoft Entra identity management.
> Developed locally, merged into [microsoft/skills](https://github.com/microsoft/skills) for distribution.

## What's Inside

| Resource | Count | Description |
|----------|-------|-------------|
| **Skills** | 14 | Domain-specific knowledge for Entra identity management (6 enhanced + 8 new) |
| **MCP Servers** | 2 | Live tools — Python (Graph operations) + TypeScript (CLI/infra) |
| **Custom Agents** | 3 | Role-specific agents (admin, security auditor, app wizard) |
| **Instruction Files** | 2 | Cross-cutting conventions and security guardrails |

## Entra Domains Covered

| Domain | Skill | MCP Server | Status |
|--------|-------|------------|--------|
| App registrations & service principals | `entra-app-registration` (enhance) | Python | Phase 1 |
| Agent Identity (Blueprint/BlueprintPrincipal) | `entra-agent-id` + `entra-agent-id-runtime` (review) | Python | Phase 1 |
| User & group management | `entra-users-groups` | Python | Phase 2 |
| RBAC role assignments | `azure-rbac` (enhance) | Python | Phase 1 |
| Conditional Access policies | `entra-conditional-access` | TypeScript | Phase 2 |
| Managed Identity configuration | `entra-managed-identity` | TypeScript | Phase 2 |
| Workload Identity Federation | `entra-workload-identity-federation` | TypeScript | Phase 2 |
| Authentication flows (MSAL, OAuth2, OBO) | `entra-msal-deep-dive` + `azure-identity-*` (enhance) | — | Phase 2 |
| Admin consent & API permissions | `entra-admin-consent-permissions` | Python | Phase 2 |
| Audit logs & sign-in logs | `entra-audit-signin-logs` | Python | Phase 2 |
| Secret/certificate lifecycle | `entra-secret-certificate-lifecycle` | TypeScript | Phase 2 |

## Repository Structure

```
.github/
├── skills/                          # Skill definitions (SKILL.md + references/)
│   ├── entra-app-registration/      # Phase 1: Enhance existing
│   ├── entra-agent-id/              # Phase 1: Review/align
│   ├── entra-agent-id-runtime/      # Phase 1: Review/align
│   ├── azure-rbac/                  # Phase 1: Enhance existing
│   ├── azure-identity-py/           # Phase 1: Enhance existing
│   ├── azure-identity-dotnet/       # Phase 1: Review/align
│   ├── entra-users-groups/          # Phase 2: New
│   ├── entra-conditional-access/    # Phase 2: New
│   ├── entra-managed-identity/      # Phase 2: New
│   ├── entra-workload-identity-federation/  # Phase 2: New
│   ├── entra-admin-consent-permissions/     # Phase 2: New
│   ├── entra-audit-signin-logs/     # Phase 2: New
│   ├── entra-secret-certificate-lifecycle/  # Phase 2: New
│   └── entra-msal-deep-dive/        # Phase 2: New
│
├── agents/                          # Custom agent personas
│   ├── entra-admin.agent.md         # Phase 5: Identity Administrator
│   ├── entra-security-auditor.agent.md  # Phase 5: Security Auditor
│   └── entra-app-wizard.agent.md    # Phase 5: App Registration Wizard
│
├── instructions/                    # Cross-cutting instruction files
│   ├── entra-conventions.instructions.md    # Phase 6
│   └── entra-security.instructions.md       # Phase 6
│
└── copilot-instructions.md          # Repo-level agent instructions

skills/                              # Symlinks for categorization
└── core/
    └── entra/                       # Category symlinks → .github/skills/*

mcp-servers/                         # MCP server implementations
├── entra-graph-py/                  # Phase 3: Python FastMCP (Graph operations)
│   ├── src/
│   ├── tests/
│   ├── pyproject.toml
│   └── README.md
└── entra-infra-ts/                  # Phase 4: TypeScript MCP SDK (CLI/infra)
    ├── src/
    ├── tests/
    ├── package.json
    └── README.md

tests/                               # Test harness (mirrors microsoft/skills)
└── scenarios/                       # Per-skill test scenarios
    └── <skill-name>/
        └── scenarios.yaml

docs/                                # Generated documentation
├── PLAN.md                          # Phased delivery plan
└── BACKLOG.md                       # Task tracking

AGENTS.md                            # Agent configuration for this repo
.gitignore
```

## Phases

| Phase | Focus | Depends On | Deliverables |
|-------|-------|------------|--------------|
| **1** | Enhance existing skills | — | 6 skills brought to consistent standard |
| **2** | New skills | Phase 1 conventions | 8 new SKILL.md files |
| **3** | Python MCP server | Phase 2 knowledge | FastMCP server with ~16 Graph tools |
| **4** | TypeScript MCP server | Phase 2 knowledge | MCP SDK server with ~12 CLI/infra tools |
| **5** | Custom agents | Phases 2–4 | 3 agent personas |
| **6** | Instructions & integration | Phases 1–5 | 2 instruction files, cross-skill testing |

## Merge Strategy

This repo is developed locally and merged into `microsoft/skills`:
- Skills → `.github/skills/` (flat, with language suffixes for SDK-specific variants)
- Agents → `.github/agents/`
- Instructions → `.github/instructions/` or plugin-level
- MCP servers → separate package or `.github/plugins/` bundle
- Tests → `tests/scenarios/<skill>/`
- Acceptance criteria → `.github/skills/<skill>/references/acceptance-criteria.md`

Category: `entra` (already a recognized category in microsoft/skills)

## License

MIT
