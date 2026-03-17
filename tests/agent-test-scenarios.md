# Agent Test Scenarios

Manual test scripts for validating each custom agent persona against the MCP tools and skills.

## Entra Admin Agent

### Scenario 1: User Lookup & Group Management
**Prompt:** "Find all users in the Engineering department and add alice@contoso.com to the sg-engineers group"
**Expected behavior:**
1. Agent calls `entra_list_users` with `department="Engineering"`
2. Agent identifies alice@contoso.com in results
3. Agent calls `entra_list_groups` with `search="sg-engineers"` to get group ID
4. Agent explains the write operation and asks for confirmation
5. After confirmation, agent calls `entra_add_group_member` with group_id and user_id
6. Agent confirms the operation succeeded

**Validates:** User search, group lookup, write confirmation flow, `tools_users_groups` module

### Scenario 2: App Registration Security Audit
**Prompt:** "Check all app registrations for expiring secrets and show me which ones need attention"
**Expected behavior:**
1. Agent calls `entra_check_credential_expiry` with empty `app_object_id` (scan all)
2. Agent presents findings sorted by severity (EXPIRED before EXPIRING SOON)
3. For each finding, agent recommends: rotate to Key Vault, or migrate to MI/WIF
4. Agent references `entra-secret-certificate-lifecycle` skill for rotation patterns

**Validates:** Credential scanning, security recommendations, skill cross-references

### Scenario 3: RBAC Role Assignment
**Prompt:** "My managed identity mi-webapp-prod needs to read blobs from storage account sa-data-prod"
**Expected behavior:**
1. Agent calls `entra_find_role` with "read blobs" to identify `Storage Blob Data Reader`
2. Agent explains the role and its permissions
3. Agent asks for the storage account resource ID / scope
4. Agent explains the write operation and asks for confirmation
5. After confirmation, calls `entra_assign_role` with principal_id, role_definition_id, scope
6. Agent confirms and suggests verifying with `entra_list_role_assignments`

**Validates:** Least-privilege role lookup, RBAC assignment flow, write confirmation

### Scenario 4: Managed Identity Setup (Cross-Server)
**Prompt:** "Create a user-assigned managed identity for my web app and give it Key Vault access"
**Expected behavior:**
1. Agent asks for resource group and app name
2. Agent calls `entra_create_user_assigned_mi` (TypeScript MCP)
3. Agent calls `entra_assign_mi_to_resource` with the webapp (TypeScript MCP)
4. Agent calls `entra_find_role` with "read secrets" (Python MCP)
5. Agent calls `entra_configure_mi_rbac` with the MI and Key Vault scope (TypeScript MCP)
6. All write operations get user confirmation

**Validates:** Cross-MCP-server orchestration, MI lifecycle, RBAC assignment

### Scenario 5: Agent Identity Provisioning
**Prompt:** "Create an Agent Identity Blueprint for my help desk agent with a sponsor"
**Expected behavior:**
1. Agent asks for blueprint name, description, and sponsor service principal
2. Agent calls `entra_create_agent_blueprint`
3. Agent explains next steps: create agent identities from blueprint
4. If asked, calls `entra_create_agent_identity` from the blueprint
5. Agent references `entra-agent-id` and `entra-agent-id-runtime` skills for token exchange patterns

**Validates:** Agent Identity beta API tools, skill cross-references, write confirmation

---

## Entra Security Auditor Agent

### Scenario 6: Comprehensive Security Scan
**Prompt:** "Run a full security audit of our Entra tenant"
**Expected behavior:**
1. Agent calls `entra_scan_expiring_secrets` (TypeScript MCP) — credential health
2. Agent calls `entra_get_signin_logs` with `failed_only=True` — failed sign-ins
3. Agent calls `entra_check_user_risk` — risky users
4. Agent calls `entra_list_ca_policies` (TypeScript MCP) — CA coverage
5. Agent presents findings prioritized: Critical → High → Medium → Low
6. For each finding, provides remediation recommendation
7. Agent does NOT attempt any write operations

**Validates:** Read-only enforcement, multi-tool orchestration, severity prioritization

### Scenario 7: Sign-in Anomaly Investigation
**Prompt:** "Investigate suspicious sign-ins for user bob@contoso.com in the last 48 hours"
**Expected behavior:**
1. Agent calls `entra_get_signin_logs` with `user_id` and `hours=48`
2. Agent calls `entra_check_user_risk` with bob's user ID
3. Agent calls `entra_evaluate_conditional_access` for bob
4. Agent analyzes patterns: locations, IPs, failure codes, CA results
5. Agent provides risk assessment and recommends next steps
6. If remediation needed, agent directs user to Entra Admin agent

**Validates:** Log analysis, risk correlation, proper agent handoff

### Scenario 8: CA Policy Gap Analysis
**Prompt:** "Are there any gaps in our Conditional Access coverage?"
**Expected behavior:**
1. Agent calls `entra_list_ca_policies` — get all policies
2. For each policy, calls `entra_get_ca_policy` — get conditions/controls
3. Agent analyzes: Are all users covered? Any apps excluded? MFA enforced?
4. Agent identifies gaps (e.g., no policy for guest users, legacy auth not blocked)
5. References SOC2/ISO 27001 requirements from `entra-security.instructions.md`

**Validates:** CA policy analysis, compliance awareness, read-only tools only

---

## Entra App Wizard Agent

### Scenario 9: New Web App Authentication Setup
**Prompt:** "I need to set up authentication for my Python FastAPI web app that calls Microsoft Graph"
**Expected behavior:**
1. Agent asks clarifying questions: single-tenant? what Graph operations?
2. Agent recommends: authorization code flow, delegated permissions
3. Agent walks through app registration step-by-step:
   a. Creates registration with `entra_create_app_registration`
   b. Explains redirect URI configuration
   c. Recommends using `DefaultAzureCredential` in dev, MI in prod
4. Agent provides complete FastAPI + MSAL code example
5. Agent explains how to add Graph permissions and request consent
6. Agent references `entra-msal-deep-dive` for advanced patterns

**Validates:** Step-by-step guidance, code generation, skill references, write confirmation

### Scenario 10: SPA Authentication Discovery
**Prompt:** "How do I add Entra login to my React single-page application?"
**Expected behavior:**
1. Agent identifies SPA → recommends auth code flow with PKCE
2. Agent explains why implicit flow is deprecated
3. Agent walks through registration: SPA platform, redirect URIs
4. Agent provides MSAL.js code example with `PublicClientApplication`
5. Agent warns: never store tokens in localStorage
6. Agent references `entra-security.instructions.md` token handling rules

**Validates:** Security-first guidance, correct flow selection, code examples

---

## Cross-Agent Scenarios

### Scenario 11: Auditor-to-Admin Handoff
**Prompt to Auditor:** "There are 5 expired secrets in production apps"
**Expected:** Auditor identifies the apps, recommends rotation, tells user to switch to Entra Admin agent for the actual rotation.
**Then to Admin:** "Rotate the expired secrets for contoso-api-prod"
**Expected:** Admin calls `entra_rotate_secret`, stores in Key Vault, removes old secret.

### Scenario 12: Wizard-to-Admin Handoff
**Prompt to Wizard:** "I created the app registration. Now I need to set up a managed identity for my deployed app."
**Expected:** Wizard says this is outside its scope (app registration tools only), recommends Entra Admin agent for MI setup.
