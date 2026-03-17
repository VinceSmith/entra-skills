---
name: entra-agent-id
description: "Microsoft Entra Agent ID (preview) — create OAuth2-capable AI agent identities via Microsoft Graph beta API. Blueprints, BlueprintPrincipals, agent identity provisioning, permissions, and WIF."
---

# Entra Agent ID

> **Status:** Phase 1 — Review/align existing skill from `~/.agents/skills/entra-agent-id/`

## TODO: Review Checklist

- [ ] Import existing content from `~/.agents/skills/entra-agent-id/SKILL.md`
- [ ] Audit for consistency with new conventions
- [ ] Add cross-references to new skills (WIF, admin consent, audit logs)
- [ ] Verify preview API endpoint accuracy (beta APIs evolve)
- [ ] Align standard sections format

## Cross-References

- **Depends on:** `entra-app-registration` (initial Blueprint app registration)
- **Feeds into:** `entra-agent-id-runtime` (runtime token exchange)
- **Related:** `azure-identity-py`, `azure-identity-dotnet` (provisioning auth)
- **See also:** `entra-admin-consent-permissions` (Agent Identity consent)
