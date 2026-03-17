---
name: entra-users-groups
description: "Entra ID user and group management — CRUD operations, group memberships, dynamic groups, nested groups, B2B guest users, bulk operations via Microsoft Graph."
---

# Entra Users & Groups

> **Status:** Phase 2 — New skill

## Scope

- User lifecycle: create, read, update, delete, disable/enable
- Group lifecycle: security groups, Microsoft 365 groups, dynamic membership groups
- Group membership management: add/remove members, list members/owners
- Nested group resolution
- B2B guest user invitations and management
- Bulk operations (batch API)
- License assignment via group membership

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List users | `GET /users` | `User.Read.All` |
| Get user | `GET /users/{id}` | `User.Read.All` |
| Create user | `POST /users` | `User.ReadWrite.All` |
| List groups | `GET /groups` | `Group.Read.All` |
| Get group members | `GET /groups/{id}/members` | `GroupMember.Read.All` |
| Add group member | `POST /groups/{id}/members/$ref` | `GroupMember.ReadWrite.All` |
| Invite guest | `POST /invitations` | `User.Invite.All` |

## TODO

- [ ] Full SKILL.md content with code examples (Python `msgraph-sdk` + .NET `Microsoft.Graph`)
- [ ] Dynamic group membership rule patterns
- [ ] Bulk operation patterns (batch API with `$batch`)
- [ ] PII handling guidance
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Related:** `entra-app-registration` (app needs User/Group permissions)
- **Related:** `azure-rbac` (groups are often role assignment targets)
- **See also:** `entra-admin-consent-permissions` (permission grants for user/group access)
