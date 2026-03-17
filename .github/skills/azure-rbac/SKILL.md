---
name: azure-rbac
description: "Azure RBAC role assignment for Entra identities — role definition matrices, scope hierarchy, least-privilege role selection, custom roles, deny assignments, Bicep + CLI patterns."
---

# Azure RBAC

> **Status:** Phase 1 — Enhance existing skill from `~/.agents/skills/azure-rbac/`

## TODO: Enhancement Checklist

- [ ] Import existing content from `~/.agents/skills/azure-rbac/SKILL.md`
- [ ] Add role definition reference matrix (common identity roles)
- [ ] Add scope hierarchy guidance (management group → subscription → RG → resource)
- [ ] Add service principal vs managed identity assignment differences
- [ ] Add custom role creation patterns (JSON + CLI + Bicep)
- [ ] Add deny assignments
- [ ] Add Bicep + CLI examples for common assignments
- [ ] Add audit & compliance considerations
- [ ] Align with skill conventions

## Cross-References

- **Feeds into:** All Azure deployment skills (resources need role assignments)
- **Related:** `azure-identity-py`, `azure-identity-dotnet` (SPs/MIs that get roles)
- **See also:** `entra-managed-identity` (MI needs RBAC), `entra-agent-id` (Agent SP needs roles)
