# Entra Skills — Phased Delivery Plan

## Phase 1: Skill Library — Audit & Enhance Existing

**Goal:** Bring 6 existing skills to a consistent, comprehensive standard.

### Step 1.1: Define skill conventions
- [ ] Create `entra-conventions.instructions.md` skeleton with standard sections
- [ ] Define: Scope, Prerequisites, Workflow, API Reference, Code Examples (Python + .NET), Troubleshooting, Cross-Skill References, Security Considerations
- [ ] Define trigger keyword format and cross-reference linking pattern

### Step 1.2: Enhance `entra-app-registration`
- **Current state:** Medium depth, delegates to external reference files
- [ ] Add multi-tenant registration patterns
- [ ] Add detailed delegated vs application permission guidance
- [ ] Add secret rotation automation patterns
- [ ] Add federated credential setup (cross-ref WIF skill)
- [ ] Add Python + .NET code examples
- [ ] Add troubleshooting section (common errors)
- [ ] Add acceptance criteria (`references/acceptance-criteria.md`)

### Step 1.3: Enhance `azure-rbac`
- **Current state:** 3 lines + MCP tool dispatcher — needs most work
- [ ] Add role definition reference matrix (common identity roles)
- [ ] Add scope hierarchy guidance (management group → subscription → RG → resource)
- [ ] Add service principal vs managed identity assignment differences
- [ ] Add custom role creation patterns
- [ ] Add deny assignments
- [ ] Add Bicep + CLI examples for common assignments
- [ ] Add audit & compliance considerations
- [ ] Add acceptance criteria

### Step 1.4: Enhance `azure-identity-py`
- **Current state:** Good but less detailed than .NET version
- [ ] Add sovereign cloud configuration
- [ ] Add token caching strategies (persistent + in-memory)
- [ ] Add logging/diagnostics configuration
- [ ] Add error handling with exception types
- [ ] Add retry policy configuration
- [ ] Add acceptance criteria

### Step 1.5: Review `entra-agent-id` + `entra-agent-id-runtime`
- **Current state:** Already comprehensive (user-authored)
- [ ] Audit for consistency with new conventions
- [ ] Add cross-references to new skills (WIF, admin consent, audit logs)
- [ ] Verify preview API endpoint accuracy (evolving APIs)
- [ ] Add acceptance criteria

### Step 1.6: Review `azure-identity-dotnet`
- **Current state:** Very comprehensive
- [ ] Audit for consistency with new conventions
- [ ] Add WIF section or cross-reference to new WIF skill
- [ ] Add acceptance criteria

---

## Phase 2: Skill Library — 8 New Skills

**Goal:** Cover the 8 Entra domains with no current skill. Steps 2.1–2.8 are independent — parallelizable.

### Step 2.1: `entra-users-groups` (NEW)
- [ ] YAML frontmatter (name, description)
- [ ] Scope: User CRUD, group CRUD, group memberships, dynamic groups, nested groups, B2B guests
- [ ] APIs: Microsoft Graph `/users`, `/groups`, `/members`, `/owners`
- [ ] Code examples: Python (`msgraph-sdk`) + .NET (`Microsoft.Graph`)
- [ ] Cross-refs: `entra-app-registration`, `azure-rbac`
- [ ] Security: permission scoping, PII handling
- [ ] Acceptance criteria + test scenarios

### Step 2.2: `entra-conditional-access` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: Policy lifecycle (CRUD), common templates, named locations, auth contexts, grant/session controls, what-if analysis
- [ ] APIs: Microsoft Graph `/identity/conditionalAccess/policies`
- [ ] Code examples: Python + .NET + Azure CLI
- [ ] Cross-refs: `entra-app-registration`, `entra-users-groups`
- [ ] Acceptance criteria + test scenarios

### Step 2.3: `entra-managed-identity` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: System-assigned vs user-assigned MI, creation & assignment to Azure resources, MI + RBAC, federated credentials for WIF
- [ ] APIs: ARM REST, Azure CLI, Bicep
- [ ] Code examples: Bicep, CLI, Python, .NET
- [ ] Cross-refs: `azure-rbac`, `azure-identity-py`, `azure-identity-dotnet`
- [ ] Acceptance criteria + test scenarios

### Step 2.4: `entra-workload-identity-federation` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: Cross-cloud (AWS→Azure, GCP→Azure), GitHub Actions OIDC, K8s WIF, trust policy, claim mapping, security boundaries
- [ ] APIs: Microsoft Graph `/applications/{id}/federatedIdentityCredentials`
- [ ] Code examples: CLI + Bicep + Python + .NET
- [ ] Cross-refs: `entra-app-registration`, `entra-managed-identity`
- [ ] Acceptance criteria + test scenarios

### Step 2.5: `entra-admin-consent-permissions` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: Admin consent workflow, tenant-wide/per-user consent, permission grant lifecycle, API permission scoping, pre-authorization
- [ ] APIs: Microsoft Graph `/oauth2PermissionGrants`, `/appRoleAssignments`
- [ ] Code examples: CLI + Python + .NET + PowerShell
- [ ] Cross-refs: `entra-app-registration`, `entra-agent-id`, `entra-agent-id-runtime`
- [ ] Acceptance criteria + test scenarios

### Step 2.6: `entra-audit-signin-logs` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: Audit log queries, sign-in log queries, KQL patterns for Log Analytics, risk events, identity protection
- [ ] APIs: Microsoft Graph `/auditLogs/directoryAudits`, `/auditLogs/signIns`, `/identityProtection/riskDetections`
- [ ] Code examples: Python + .NET + KQL
- [ ] Cross-refs: `azure-kusto`, all other Entra skills
- [ ] Acceptance criteria + test scenarios

### Step 2.7: `entra-secret-certificate-lifecycle` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: Secret expiry monitoring, cert rotation, Key Vault auto-rotation, bulk credential inventory, federated credential as alternative
- [ ] APIs: Microsoft Graph `/applications/{id}/passwordCredentials`, `/keyCredentials`, Key Vault REST
- [ ] Code examples: Python + .NET + CLI + PowerShell
- [ ] Cross-refs: `entra-app-registration`, `entra-managed-identity`, `entra-workload-identity-federation`
- [ ] Acceptance criteria + test scenarios

### Step 2.8: `entra-msal-deep-dive` (NEW)
- [ ] YAML frontmatter
- [ ] Scope: MSAL Python + MSAL.js + MSAL .NET, token caching (persistent, distributed), confidential/public client, proof-of-possession, claims challenge, B2C
- [ ] Code examples: 3 languages with complete patterns
- [ ] Cross-refs: `azure-identity-py`, `azure-identity-dotnet`, `entra-agent-id-runtime`, `entra-app-registration`
- [ ] Acceptance criteria + test scenarios

---

## Phase 3: MCP Server — Graph Identity Operations (Python/FastMCP)

**Goal:** Live tools for coding agents to manage Entra identities via Microsoft Graph.

### Step 3.1: Project scaffolding
- [ ] FastMCP project structure in `mcp-servers/entra-graph-py/`
- [ ] Auth: `azure-identity` + `DefaultAzureCredential`
- [ ] Graph SDK: `msgraph-sdk`
- [ ] Configurable permissions mode: `read-only` vs `full`
- [ ] README + pyproject.toml + CI config

### Step 3.2: User & group tools
- [ ] `entra_list_users` — search/filter users
- [ ] `entra_get_user` — user profile by ID or UPN
- [ ] `entra_list_groups` — search/filter groups
- [ ] `entra_get_group_members` — list group members
- [ ] `entra_add_group_member` — add user to group (confirmation required)
- [ ] `entra_remove_group_member` — remove user from group (confirmation required)
- [ ] Unit tests

### Step 3.3: App registration tools
- [ ] `entra_list_apps` — search/filter app registrations
- [ ] `entra_get_app` — app details by ID or display name
- [ ] `entra_list_app_permissions` — configured API permissions
- [ ] `entra_check_credential_expiry` — secret/cert expiry check
- [ ] `entra_create_app_registration` — guided creation (confirmation required)
- [ ] Unit tests

### Step 3.4: Identity diagnostics tools
- [ ] `entra_get_signin_logs` — query sign-in logs
- [ ] `entra_get_audit_logs` — query audit logs
- [ ] `entra_check_user_risk` — identity protection risk status
- [ ] `entra_evaluate_conditional_access` — what-if policy evaluation
- [ ] Unit tests

### Step 3.5: RBAC tools
- [ ] `entra_list_role_assignments` — role assignments for a principal
- [ ] `entra_find_role` — least-privilege role for an action
- [ ] `entra_assign_role` — assign role (confirmation required)
- [ ] Unit tests

### Step 3.6: Agent Identity tools
- [ ] `entra_create_agent_blueprint` — create Agent Identity Blueprint
- [ ] `entra_create_agent_identity` — provision agent from blueprint
- [ ] `entra_get_agent_token` — token exchange (autonomous or OBO)
- [ ] Unit tests

---

## Phase 4: MCP Server — CLI & Infrastructure (TypeScript/MCP SDK)

**Goal:** Infrastructure-level operations, npx-distributable.

### Step 4.1: Project scaffolding
- [ ] TypeScript MCP SDK project in `mcp-servers/entra-infra-ts/`
- [ ] Wraps Azure CLI (`az`)
- [ ] npm package structure for npx distribution
- [ ] README + package.json + tsconfig.json

### Step 4.2: Managed Identity tools
- [ ] `entra_create_user_assigned_mi`
- [ ] `entra_assign_mi_to_resource`
- [ ] `entra_configure_mi_rbac`
- [ ] Unit tests

### Step 4.3: WIF tools
- [ ] `entra_create_federated_credential`
- [ ] `entra_list_federated_credentials`
- [ ] `entra_validate_wif_trust`
- [ ] Unit tests

### Step 4.4: Conditional Access tools
- [ ] `entra_list_ca_policies`
- [ ] `entra_get_ca_policy`
- [ ] `entra_create_ca_policy` (confirmation required)
- [ ] `entra_what_if_ca`
- [ ] Unit tests

### Step 4.5: Secret/cert lifecycle tools
- [ ] `entra_scan_expiring_secrets`
- [ ] `entra_rotate_secret` (confirmation required)
- [ ] `entra_setup_keyvault_rotation`
- [ ] Unit tests

---

## Phase 5: Custom Agents

**Goal:** Specialized agent personas orchestrating skills + MCP tools.

### Step 5.1: `entra-admin.agent.md` — Identity Administrator
- [ ] Persona definition: Senior identity admin
- [ ] Skills: All entra-* skills
- [ ] MCP: Both servers (full access)
- [ ] Use cases: User/group management, app registration, permission management
- [ ] Safety: All write operations require explicit user confirmation
- [ ] Test scenarios

### Step 5.2: `entra-security-auditor.agent.md` — Security Auditor
- [ ] Persona definition: Security analyst for posture assessment
- [ ] Skills: audit-signin-logs, secret-lifecycle, conditional-access, rbac
- [ ] MCP: Read-only subset only
- [ ] Use cases: Expiring secrets, sign-in anomalies, CA policy gaps
- [ ] Safety: No write tools accessible
- [ ] Test scenarios

### Step 5.3: `entra-app-wizard.agent.md` — App Registration Wizard
- [ ] Persona definition: Guided wizard for developers new to Entra
- [ ] Skills: app-registration, msal-deep-dive, admin-consent-permissions
- [ ] MCP: App registration tools only
- [ ] Use cases: Register API, set up SPA auth, configure Graph permissions
- [ ] Safety: Step-by-step guided flow with explanations
- [ ] Test scenarios

---

## Phase 6: Instructions & Integration

### Step 6.1: `entra-conventions.instructions.md`
- [ ] Naming conventions for Entra resources
- [ ] Permission scoping guidelines (least privilege)
- [ ] Secret management hierarchy: MI → WIF → certs → secrets
- [ ] Code patterns: always DefaultAzureCredential, never hardcode

### Step 6.2: `entra-security.instructions.md`
- [ ] Security guardrails: no wildcard permissions, no long-lived secrets
- [ ] Required conditional access patterns
- [ ] Audit logging requirements
- [ ] Compliance references (SOC2, FedRAMP)

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
