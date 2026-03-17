# Entra Skills — Phased Delivery Plan

## Phase 1: Skill Library — Audit & Enhance Existing ✅

**Goal:** Bring 6 existing skills to a consistent, comprehensive standard.

### Step 1.1: Define skill conventions
- [x] Create `entra-conventions.instructions.md` skeleton with standard sections
- [x] Define: Scope, Prerequisites, Workflow, API Reference, Code Examples (Python + .NET), Troubleshooting, Cross-Skill References, Security Considerations
- [x] Define trigger keyword format and cross-reference linking pattern

### Step 1.2: Enhance `entra-app-registration`
- **Current state:** Medium depth, delegates to external reference files
- [x] Add multi-tenant registration patterns
- [x] Add detailed delegated vs application permission guidance
- [x] Add secret rotation automation patterns
- [x] Add federated credential setup (cross-ref WIF skill)
- [x] Add Python + .NET code examples
- [x] Add troubleshooting section (common errors)
- [x] Add acceptance criteria (`references/acceptance-criteria.md`)

### Step 1.3: Enhance `azure-rbac`
- **Current state:** 3 lines + MCP tool dispatcher — needs most work
- [x] Add role definition reference matrix (common identity roles)
- [x] Add scope hierarchy guidance (management group → subscription → RG → resource)
- [x] Add service principal vs managed identity assignment differences
- [x] Add custom role creation patterns
- [x] Add deny assignments
- [x] Add Bicep + CLI examples for common assignments
- [x] Add audit & compliance considerations
- [x] Add acceptance criteria

### Step 1.4: Enhance `azure-identity-py`
- **Current state:** Good but less detailed than .NET version
- [x] Add sovereign cloud configuration
- [x] Add token caching strategies (persistent + in-memory)
- [x] Add logging/diagnostics configuration
- [x] Add error handling with exception types
- [x] Add retry policy configuration
- [x] Add acceptance criteria

### Step 1.5: Review `entra-agent-id` + `entra-agent-id-runtime`
- **Current state:** Already comprehensive (user-authored)
- [x] Audit for consistency with new conventions
- [x] Add cross-references to new skills (WIF, admin consent, audit logs)
- [x] Verify preview API endpoint accuracy (evolving APIs)
- [x] Add acceptance criteria

### Step 1.6: Review `azure-identity-dotnet`
- **Current state:** Very comprehensive
- [x] Audit for consistency with new conventions
- [x] Add WIF section or cross-reference to new WIF skill
- [x] Add acceptance criteria

---

## Phase 2: Skill Library — 8 New Skills ✅

**Goal:** Cover the 8 Entra domains with no current skill. Steps 2.1–2.8 are independent — parallelizable.

### Step 2.1: `entra-users-groups` (NEW)
- [x] YAML frontmatter (name, description)
- [x] Scope: User CRUD, group CRUD, group memberships, dynamic groups, nested groups, B2B guests
- [x] APIs: Microsoft Graph `/users`, `/groups`, `/members`, `/owners`
- [x] Code examples: Python (`msgraph-sdk`) + .NET (`Microsoft.Graph`)
- [x] Cross-refs: `entra-app-registration`, `azure-rbac`
- [x] Security: permission scoping, PII handling
- [x] Acceptance criteria + test scenarios

### Step 2.2: `entra-conditional-access` (NEW)
- [x] YAML frontmatter
- [x] Scope: Policy lifecycle (CRUD), common templates, named locations, auth contexts, grant/session controls, what-if analysis
- [x] APIs: Microsoft Graph `/identity/conditionalAccess/policies`
- [x] Code examples: Python + .NET + Azure CLI
- [x] Cross-refs: `entra-app-registration`, `entra-users-groups`
- [x] Acceptance criteria + test scenarios

### Step 2.3: `entra-managed-identity` (NEW)
- [x] YAML frontmatter
- [x] Scope: System-assigned vs user-assigned MI, creation & assignment to Azure resources, MI + RBAC, federated credentials for WIF
- [x] APIs: ARM REST, Azure CLI, Bicep
- [x] Code examples: Bicep, CLI, Python, .NET
- [x] Cross-refs: `azure-rbac`, `azure-identity-py`, `azure-identity-dotnet`
- [x] Acceptance criteria + test scenarios

### Step 2.4: `entra-workload-identity-federation` (NEW)
- [x] YAML frontmatter
- [x] Scope: Cross-cloud (AWS→Azure, GCP→Azure), GitHub Actions OIDC, K8s WIF, trust policy, claim mapping, security boundaries
- [x] APIs: Microsoft Graph `/applications/{id}/federatedIdentityCredentials`
- [x] Code examples: CLI + Bicep + Python + .NET
- [x] Cross-refs: `entra-app-registration`, `entra-managed-identity`
- [x] Acceptance criteria + test scenarios

### Step 2.5: `entra-admin-consent-permissions` (NEW)
- [x] YAML frontmatter
- [x] Scope: Admin consent workflow, tenant-wide/per-user consent, permission grant lifecycle, API permission scoping, pre-authorization
- [x] APIs: Microsoft Graph `/oauth2PermissionGrants`, `/appRoleAssignments`
- [x] Code examples: CLI + Python + .NET + PowerShell
- [x] Cross-refs: `entra-app-registration`, `entra-agent-id`, `entra-agent-id-runtime`
- [x] Acceptance criteria + test scenarios

### Step 2.6: `entra-audit-signin-logs` (NEW)
- [x] YAML frontmatter
- [x] Scope: Audit log queries, sign-in log queries, KQL patterns for Log Analytics, risk events, identity protection
- [x] APIs: Microsoft Graph `/auditLogs/directoryAudits`, `/auditLogs/signIns`, `/identityProtection/riskDetections`
- [x] Code examples: Python + .NET + KQL
- [x] Cross-refs: `azure-kusto`, all other Entra skills
- [x] Acceptance criteria + test scenarios

### Step 2.7: `entra-secret-certificate-lifecycle` (NEW)
- [x] YAML frontmatter
- [x] Scope: Secret expiry monitoring, cert rotation, Key Vault auto-rotation, bulk credential inventory, federated credential as alternative
- [x] APIs: Microsoft Graph `/applications/{id}/passwordCredentials`, `/keyCredentials`, Key Vault REST
- [x] Code examples: Python + .NET + CLI + PowerShell
- [x] Cross-refs: `entra-app-registration`, `entra-managed-identity`, `entra-workload-identity-federation`
- [x] Acceptance criteria + test scenarios

### Step 2.8: `entra-msal-deep-dive` (NEW)
- [x] YAML frontmatter
- [x] Scope: MSAL Python + MSAL.js + MSAL .NET, token caching (persistent, distributed), confidential/public client, proof-of-possession, claims challenge, B2C
- [x] Code examples: 3 languages with complete patterns
- [x] Cross-refs: `azure-identity-py`, `azure-identity-dotnet`, `entra-agent-id-runtime`, `entra-app-registration`
- [x] Acceptance criteria + test scenarios

---

## Phase 3: MCP Server — Graph Identity Operations (Python/FastMCP) ✅

**Goal:** Live tools for coding agents to manage Entra identities via Microsoft Graph.

### Step 3.1: Project scaffolding
- [x] FastMCP project structure in `mcp-servers/entra-graph-py/`
- [x] Auth: `azure-identity` + `DefaultAzureCredential`
- [x] Graph SDK: `msgraph-sdk`
- [x] Configurable permissions mode: `read-only` vs `full`
- [x] README + pyproject.toml + CI config

### Step 3.2: User & group tools
- [x] `entra_list_users` — search/filter users
- [x] `entra_get_user` — user profile by ID or UPN
- [x] `entra_list_groups` — search/filter groups
- [x] `entra_get_group_members` — list group members
- [x] `entra_add_group_member` — add user to group (confirmation required)
- [x] `entra_remove_group_member` — remove user from group (confirmation required)
- [ ] Unit tests

### Step 3.3: App registration tools
- [x] `entra_list_apps` — search/filter app registrations
- [x] `entra_get_app` — app details by ID or display name
- [x] `entra_list_app_permissions` — configured API permissions
- [x] `entra_check_credential_expiry` — secret/cert expiry check
- [x] `entra_create_app_registration` — guided creation (confirmation required)
- [ ] Unit tests

### Step 3.4: Identity diagnostics tools
- [x] `entra_get_signin_logs` — query sign-in logs
- [x] `entra_get_audit_logs` — query audit logs
- [x] `entra_check_user_risk` — identity protection risk status
- [x] `entra_evaluate_conditional_access` — what-if policy evaluation
- [ ] Unit tests

### Step 3.5: RBAC tools
- [x] `entra_list_role_assignments` — role assignments for a principal
- [x] `entra_find_role` — least-privilege role for an action
- [x] `entra_assign_role` — assign role (confirmation required)
- [ ] Unit tests

### Step 3.6: Agent Identity tools
- [x] `entra_create_agent_blueprint` — create Agent Identity Blueprint
- [x] `entra_create_agent_identity` — provision agent from blueprint
- [x] `entra_get_agent_token` — token exchange (autonomous or OBO)
- [ ] Unit tests

---

## Phase 4: MCP Server — CLI & Infrastructure (TypeScript/MCP SDK) ✅

**Goal:** Infrastructure-level operations, npx-distributable.

### Step 4.1: Project scaffolding
- [x] TypeScript MCP SDK project in `mcp-servers/entra-infra-ts/`
- [x] Wraps Azure CLI (`az`)
- [x] npm package structure for npx distribution
- [x] README + package.json + tsconfig.json

### Step 4.2: Managed Identity tools
- [x] `entra_create_user_assigned_mi`
- [x] `entra_assign_mi_to_resource`
- [x] `entra_configure_mi_rbac`
- [ ] Unit tests

### Step 4.3: WIF tools
- [x] `entra_create_federated_credential`
- [x] `entra_list_federated_credentials`
- [x] `entra_validate_wif_trust`
- [ ] Unit tests

### Step 4.4: Conditional Access tools
- [x] `entra_list_ca_policies`
- [x] `entra_get_ca_policy`
- [x] `entra_create_ca_policy` (confirmation required)
- [x] `entra_what_if_ca`
- [ ] Unit tests

### Step 4.5: Secret/cert lifecycle tools
- [x] `entra_scan_expiring_secrets`
- [x] `entra_rotate_secret` (confirmation required)
- [x] `entra_setup_keyvault_rotation`
- [ ] Unit tests

---

## Phase 5: Custom Agents ✅

**Goal:** Specialized agent personas orchestrating skills + MCP tools.

### Step 5.1: `entra-admin.agent.md` — Identity Administrator
- [x] Persona definition: Senior identity admin
- [x] Skills: All entra-* skills
- [x] MCP: Both servers (full access)
- [x] Use cases: User/group management, app registration, permission management
- [x] Safety: All write operations require explicit user confirmation
- [ ] Test scenarios

### Step 5.2: `entra-security-auditor.agent.md` — Security Auditor
- [x] Persona definition: Security analyst for posture assessment
- [x] Skills: audit-signin-logs, secret-lifecycle, conditional-access, rbac
- [x] MCP: Read-only subset only
- [x] Use cases: Expiring secrets, sign-in anomalies, CA policy gaps
- [x] Safety: No write tools accessible
- [ ] Test scenarios

### Step 5.3: `entra-app-wizard.agent.md` — App Registration Wizard
- [x] Persona definition: Guided wizard for developers new to Entra
- [x] Skills: app-registration, msal-deep-dive, admin-consent-permissions
- [x] MCP: App registration tools only
- [x] Use cases: Register API, set up SPA auth, configure Graph permissions
- [x] Safety: Step-by-step guided flow with explanations
- [ ] Test scenarios

---

## Phase 6: Instructions & Integration ✅ (instructions complete, testing remaining)

### Step 6.1: `entra-conventions.instructions.md`
- [x] Naming conventions for Entra resources
- [x] Permission scoping guidelines (least privilege)
- [x] Secret management hierarchy: MI → WIF → certs → secrets
- [x] Code patterns: always DefaultAzureCredential, never hardcode

### Step 6.2: `entra-security.instructions.md`
- [x] Security guardrails: no wildcard permissions, no long-lived secrets
- [x] Required conditional access patterns
- [x] Audit logging requirements
- [x] Compliance references (SOC2, FedRAMP)

### Step 6.3: Cross-skill integration testing
- [ ] Verify all cross-references resolve correctly
- [ ] Test MCP servers with each custom agent
- [ ] Validate instruction files are applied during code generation
- [ ] End-to-end scenario tests: ask agent to perform identity tasks

---

## Decisions Log

| Decision | Rationale |
|----------|-----------|
| ADO MCP server is separate | Work tool, not part of this Entra effort |
| Skill library first (Phases 1–2) | MCP servers depend on correct skill knowledge |
| Two MCP servers: Python + TypeScript | Python for Graph SDK richness, TypeScript for npx/CLI distribution |
| All 11 Entra domains in scope | Phased delivery manages complexity |
| Existing agent-id skills: review, don't rewrite | User-authored, already comprehensive |
| Monorepo structure | Skills need to cross-reference MCP tools; easier to test holistically |
| Category: `entra` | Already recognized in microsoft/skills |
| Merge target: microsoft/skills | Local dev → PR to microsoft/skills for distribution |

## Open Questions

- [ ] **Test tenant:** Dedicated Entra test tenant for MCP server development?
- [ ] **Distribution:** npm + PyPI for MCP servers when going public, or GitHub-only initially?
- [ ] **Plugin bundle:** Should Entra skills be a plugin (`azure-entra`) or individual skills in `.github/skills/`?
