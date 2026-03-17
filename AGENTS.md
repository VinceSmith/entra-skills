# Entra Identity Skills

A comprehensive toolkit of skills, MCP servers, and custom agents for Microsoft Entra identity management. Developed for merge into [microsoft/skills](https://github.com/microsoft/skills).

## Fresh Information First

Before generating code that interacts with Entra ID, load the relevant skill:
- App registrations → `entra-app-registration`
- Agent Identity → `entra-agent-id` + `entra-agent-id-runtime`
- Users/groups → `entra-users-groups`
- RBAC → `azure-rbac`
- Auth SDKs → `azure-identity-py` or `azure-identity-dotnet`
- CA policies → `entra-conditional-access`
- Managed Identity → `entra-managed-identity`
- WIF → `entra-workload-identity-federation`
- Admin consent → `entra-admin-consent-permissions`
- Audit/sign-in logs → `entra-audit-signin-logs`
- Secret rotation → `entra-secret-certificate-lifecycle`
- MSAL patterns → `entra-msal-deep-dive`
- Identity Governance → `entra-identity-governance`
- Authentication Methods → `entra-authentication-methods`
- Verified ID → `entra-verified-id`
- External ID / CIAM → `entra-external-id`
- Private Access / ZTNA → `entra-private-access`
- ID Protection → `entra-id-protection`
- Workload Identity → `entra-workload-id`

## Core Principles

1. **Least privilege** — Always recommend minimum permissions
2. **MI > WIF > Certs > Secrets** — Prefer credential-free authentication
3. **Never hardcode** — Use `DefaultAzureCredential` and environment variables
4. **Confirm writes** — All write operations need user confirmation
5. **Audit trail** — Identity operations should be traceable

## Skills

21 skills in `.github/skills/` covering all Entra identity domains.

## MCP Servers

| Server | Language | Scope |
|--------|----------|-------|
| `entra-graph-py` | Python (FastMCP) | Graph API: users, groups, apps, logs, RBAC, Agent ID, governance, ID protection, workload ID, auth methods |
| `entra-infra-ts` | TypeScript (MCP SDK) | Infrastructure: managed identity, WIF, CA, secrets |

## Custom Agents

| Agent | Persona | Access Level |
|-------|---------|-------------|
| `entra-admin` | Identity Administrator | Full (read + write with confirmation) |
| `entra-security-auditor` | Security Analyst | Read-only |
| `entra-app-wizard` | Developer Guide | App registration tools only |

## Conventions

See `.github/instructions/entra-conventions.instructions.md` and `.github/instructions/entra-security.instructions.md`.

## Do's and Don'ts

### Do
- Use `DefaultAzureCredential` for all Azure SDK clients
- Prefer managed identity over secrets
- Follow the auth hierarchy: MI → WIF → cert → secret
- Add cross-references when skills relate to each other
- Test skills by asking Copilot to generate code using them

### Don't
- Hardcode credentials in any code example
- Use `*.All` wildcard permissions
- Create CA policies in `enabled` state (use `reportOnly` first)
- Skip acceptance criteria for new skills
