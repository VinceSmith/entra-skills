---
name: entra-app-registration
description: "Full lifecycle of Entra ID app registrations: creation, authentication setup, API permissions, client credentials, OAuth 2.0 flows, multi-tenant patterns, secret rotation, and federated credentials."
---

# Entra App Registration

> **Status:** Phase 1 — Enhance existing skill from `~/.agents/skills/entra-app-registration/`

## TODO: Enhancement Checklist

- [ ] Import existing content from `~/.agents/skills/entra-app-registration/SKILL.md`
- [ ] Add multi-tenant registration patterns
- [ ] Add detailed delegated vs application permission guidance
- [ ] Add secret rotation automation patterns
- [ ] Add federated credential setup (cross-ref → `entra-workload-identity-federation`)
- [ ] Add Python code examples (`msgraph-sdk`, `msal`)
- [ ] Add .NET code examples (`Microsoft.Graph`, `Microsoft.Identity.Client`)
- [ ] Add troubleshooting section (common errors with Graph API)
- [ ] Align with skill conventions (standard sections)
- [ ] Add cross-references to related skills

## Cross-References

- **Feeds into:** `entra-agent-id` (Blueprint is a special app registration)
- **Related:** `azure-identity-py`, `azure-identity-dotnet` (SDK integration)
- **See also:** `entra-admin-consent-permissions` (permission grants), `entra-secret-certificate-lifecycle` (credential management)
