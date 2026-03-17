---
name: entra-agent-id-runtime
description: "Runtime token exchange for Entra Agent Identities — autonomous (app-only) and OBO (delegated) flows, Blueprint API configuration, per-agent permission scoping, and Foundry vs self-managed comparison."
---

# Entra Agent ID Runtime

> **Status:** Phase 1 — Review/align existing skill from `~/.agents/skills/entra-agent-id-runtime/`

## TODO: Review Checklist

- [ ] Import existing content from `~/.agents/skills/entra-agent-id-runtime/SKILL.md`
- [ ] Audit for consistency with new conventions
- [ ] Add cross-references to new skills
- [ ] Verify token exchange endpoints (preview APIs evolve)
- [ ] Align standard sections format

## Cross-References

- **Depends on:** `entra-agent-id` (provisioning must happen first)
- **Related:** `azure-identity-py`, `entra-msal-deep-dive` (token caching)
- **See also:** `entra-admin-consent-permissions` (OBO consent grants)
