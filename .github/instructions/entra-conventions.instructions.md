---
applyTo: "**/*.{py,cs,ts,js,bicep,json,yaml,yml}"
---

# Entra Identity Conventions

These conventions apply when generating code that interacts with Microsoft Entra ID.

## Authentication Hierarchy (Most to Least Preferred)

1. **Managed Identity** — No credentials to manage; use when running on Azure
2. **Workload Identity Federation** — No secrets; use for CI/CD and cross-cloud
3. **Certificate** — More secure than secrets; use when MI/WIF aren't possible
4. **Client secret** — Last resort; must have rotation policy

## Code Patterns

### Always
- Use `DefaultAzureCredential` (or language equivalent) — never hardcode credentials
- Reuse credential instances across the application lifetime
- Use async variants where available
- Handle `AuthenticationFailedException` / `ClientAuthenticationError` explicitly

### Never
- Hardcode client secrets, certificates, or tokens in source code
- Use `*.All` (wildcard) Graph permissions — specify exact scopes
- Use ROPC (Resource Owner Password Credentials) flow
- Store tokens in local storage (browsers) or plain text files
- Disable certificate validation

## Naming Conventions

| Resource | Pattern | Example |
|----------|---------|---------|
| App registration | `{org}-{app}-{environment}` | `contoso-api-prod` |
| Service principal | Auto-created from app registration | — |
| User-assigned MI | `mi-{app}-{environment}` | `mi-webapp-prod` |
| Security group | `sg-{purpose}` | `sg-api-readers` |
| Custom role | `{org} {description}` | `Contoso Blob Reader` |

## Permission Scoping

- Request the **minimum permissions** needed for each operation
- Prefer **delegated permissions** when a user context is available
- Use **application permissions** only for daemon/service scenarios
- Document why each permission is needed (in code comments or config)

## Secret Management

- Set secret expiry to **90 days maximum** (prefer 30 days)
- Implement automated rotation before expiry
- Use Key Vault for secret storage when secrets are unavoidable
- Monitor expiry with alerts (≤30 days warning)
