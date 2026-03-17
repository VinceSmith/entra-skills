---
applyTo: "**/*.{py,cs,ts,js,bicep,json,yaml,yml}"
---

# Entra Security Guardrails

Security rules for code interacting with Microsoft Entra ID. These are non-negotiable.

## Hard Rules

### Credentials
- **NEVER** commit secrets, certificates, or tokens to source control
- **NEVER** log tokens, secrets, or certificate private keys
- **NEVER** pass credentials as command-line arguments (visible in process lists)
- **ALWAYS** use environment variables or Key Vault for secret configuration
- **ALWAYS** set `.gitignore` to exclude `.env`, `*.pfx`, `*.pem`, `*.key` files

### Permissions
- **NEVER** request `Directory.ReadWrite.All` unless absolutely required and admin-consented
- **NEVER** use `*.All` wildcard permissions — specify exact scopes
- **NEVER** grant admin consent without documenting the justification
- **ALWAYS** follow least-privilege: request only the permissions the app actually uses

### Token Handling
- **NEVER** store access tokens in browser `localStorage` (use `sessionStorage` or in-memory only)
- **NEVER** pass tokens in URL query parameters (they appear in logs and browser history)
- **ALWAYS** validate token `aud` (audience) and `iss` (issuer) claims
- **ALWAYS** handle token expiry and refresh gracefully

### Conditional Access
- **ALWAYS** exclude emergency access (break-glass) accounts from blocking CA policies
- **NEVER** create CA policies in `enabled` state directly — use `reportOnly` first
- **ALWAYS** test CA policies with what-if analysis before enabling

## Compliance References

- **SOC 2 Type II** — CC6.1 (Logical access), CC6.3 (Role-based access)
- **ISO 27001** — A.9.2 (User access management), A.9.4 (Access control)
- **NIST 800-53** — AC-2 (Account management), AC-6 (Least privilege)
- **CIS Azure Benchmark** — Section 1 (Identity and Access Management)

## Audit Requirements

- All write operations to Entra (app registration changes, group membership changes, role assignments, consent grants) are automatically logged in Entra audit logs
- Code should include structured logging for identity operations (who, what, when, why)
- Agent operations should be attributable — use Agent Identity where possible so agent actions are distinguishable from user actions in audit logs
