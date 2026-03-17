---
name: entra-msal-deep-dive
description: "Deep MSAL integration patterns — MSAL Python, MSAL.NET, MSAL.js, token caching (persistent, distributed), confidential vs public client, proof-of-possession tokens, claims challenge, B2C."
---

# MSAL Deep Dive

> **Status:** Phase 2 — New skill

## Scope

- MSAL library selection: Python (`msal`), .NET (`Microsoft.Identity.Client`), JavaScript (`@azure/msal-browser`, `@azure/msal-node`)
- Confidential client vs public client application patterns
- Token caching: in-memory, persistent file, distributed (Redis, SQL)
- Proof-of-possession (PoP) tokens
- Claims challenge and Continuous Access Evaluation (CAE)
- Incremental consent / dynamic consent
- B2C custom policy integration
- ROPC flow (and why to avoid it)
- Client assertions (certificate-based auth)
- Token lifetime and refresh patterns
- Conditional Access claims challenge

## TODO

- [ ] Full SKILL.md content
- [ ] MSAL Python: complete patterns (confidential + public client + caching)
- [ ] MSAL .NET: complete patterns with DI integration
- [ ] MSAL.js: browser + Node.js patterns
- [ ] Token cache serialization: file, Redis, SQL examples
- [ ] Decision tree: when to use MSAL directly vs azure-identity
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Higher-level wrapper:** `azure-identity-py`, `azure-identity-dotnet` (use these first; MSAL when you need more control)
- **Related:** `entra-app-registration` (MSAL needs client config from app registration)
- **Related:** `entra-agent-id-runtime` (Agent Identity token exchange uses MSAL caching patterns)
- **See also:** `entra-admin-consent-permissions` (consent affects what tokens MSAL can acquire)
