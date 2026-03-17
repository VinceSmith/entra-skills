---
name: entra-admin-consent-permissions
description: "Entra ID admin consent and API permissions — admin consent workflow, tenant-wide consent, per-user consent, permission grant lifecycle, pre-authorization, delegated vs application scoping."
---

# Entra Admin Consent & Permissions

API permissions in Entra ID control what data an app can access. Understanding delegated vs application permissions, consent workflows, and least-privilege selection is essential for secure app design.

## Delegated vs Application Permissions

| Aspect | Delegated | Application |
|--------|-----------|-------------|
| **Context** | User is signed in | No user present (daemon/service) |
| **Effective access** | Intersection of app permission AND user's access | Full permission granted to app |
| **Consent** | User can consent (low privilege) or admin consents | Admin consent always required |
| **Token** | Contains user claims (`sub`, `upn`, etc.) | Contains app claims only |
| **Use case** | Web apps, SPAs, APIs acting on behalf of users | Background services, automation, agent services |
| **Graph example** | `Mail.Read` (read MY mail) | `Mail.Read` (read ALL users' mail) |

### Decision Tree

```
Does a user interact with the app?
├── Yes → Use Delegated permissions
│   ├── Low-risk data? → User consent is sufficient
│   └── Sensitive data? → Require admin consent
└── No → Use Application permissions
    └── Always requires admin consent
```

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List delegated grants | `GET /oauth2PermissionGrants` | `DelegatedPermissionGrant.ReadWrite.All` |
| Grant delegated permission | `POST /oauth2PermissionGrants` | `DelegatedPermissionGrant.ReadWrite.All` |
| Revoke delegated grant | `DELETE /oauth2PermissionGrants/{id}` | `DelegatedPermissionGrant.ReadWrite.All` |
| List app role assignments | `GET /servicePrincipals/{id}/appRoleAssignments` | `Application.Read.All` |
| Grant app role | `POST /servicePrincipals/{id}/appRoleAssignments` | `AppRoleAssignment.ReadWrite.All` |
| Remove app role | `DELETE /servicePrincipals/{id}/appRoleAssignments/{id}` | `AppRoleAssignment.ReadWrite.All` |
| List app permissions | `GET /applications/{id}` → `requiredResourceAccess` | `Application.Read.All` |

## Admin Consent Workflow

### Admin Consent URL

```
https://login.microsoftonline.com/{tenant-id}/adminconsent?client_id={app-client-id}&redirect_uri={redirect-uri}&scope=https://graph.microsoft.com/.default
```

Parameters:
- `{tenant-id}` — Target tenant (or `common` for multi-tenant)
- `{app-client-id}` — Application (client) ID
- `{redirect-uri}` — Where to redirect after consent (must be registered)

### Grant Tenant-Wide Admin Consent (Python)

```python
from msgraph.generated.models.o_auth2_permission_grant import OAuth2PermissionGrant

# Grant delegated permissions tenant-wide
grant = OAuth2PermissionGrant(
    client_id=service_principal_id,       # SP of your app
    consent_type="AllPrincipals",         # Tenant-wide
    resource_id=graph_sp_id,             # SP of Microsoft Graph
    scope="User.Read Mail.Read",         # Space-delimited scopes
)
await graph_client.oauth2_permission_grants.post(grant)
```

### Grant Application Permission (Python)

```python
from msgraph.generated.models.app_role_assignment import AppRoleAssignment

assignment = AppRoleAssignment(
    principal_id=service_principal_id,     # SP of your app
    resource_id=graph_sp_id,              # SP of Microsoft Graph
    app_role_id=user_read_all_role_id,    # The specific app role ID
)
await graph_client.service_principals.by_service_principal_id(
    service_principal_id
).app_role_assignments.post(assignment)
```

### Grant Admin Consent (.NET)

```csharp
// Delegated permission grant (tenant-wide)
var grant = new OAuth2PermissionGrant
{
    ClientId = servicePrincipalId,
    ConsentType = "AllPrincipals",
    ResourceId = graphSpId,
    Scope = "User.Read Mail.Read",
};
await graphClient.Oauth2PermissionGrants.PostAsync(grant);

// Application permission grant
var appRole = new AppRoleAssignment
{
    PrincipalId = Guid.Parse(servicePrincipalId),
    ResourceId = Guid.Parse(graphSpId),
    AppRoleId = Guid.Parse(userReadAllRoleId),
};
await graphClient.ServicePrincipals[servicePrincipalId]
    .AppRoleAssignments.PostAsync(appRole);
```

## Common Permission Sets

### Standard User-Facing App

```
Delegated: User.Read, Mail.Read, Calendars.Read
```

### Group Management Tool

```
Application: Group.ReadWrite.All, GroupMember.ReadWrite.All, User.Read.All
```

### Agent Identity (Scoped)

```
Delegated (per-agent via Agent ID): Tasks.ReadWrite, Mail.Send, Calendars.ReadWrite
```

### Security Audit Tool

```
Application: AuditLog.Read.All, Directory.Read.All, IdentityRiskEvent.Read.All
```

## Permission Classification

| Risk Level | Examples | Consent Required |
|-----------|----------|-----------------|
| **Low** | `User.Read`, `openid`, `profile`, `email` | User consent OK |
| **Medium** | `Mail.Read`, `Calendars.Read`, `Files.Read` | User or admin consent |
| **High** | `Mail.ReadWrite`, `Files.ReadWrite.All` | Admin consent recommended |
| **Critical** | `Directory.ReadWrite.All`, `RoleManagement.ReadWrite.Directory` | Admin consent required |

> **Never request `*.All` wildcard permissions** when a scoped alternative exists.

## Pre-Authorization

Allow trusted first-party apps to access your API without consent prompts:

```python
# On the API app registration, pre-authorize client apps
from msgraph.generated.models.application import Application
from msgraph.generated.models.pre_authorized_application import PreAuthorizedApplication

app_update = Application(
    api=ApiApplication(
        pre_authorized_applications=[
            PreAuthorizedApplication(
                app_id="<trusted-client-app-id>",
                delegated_permission_ids=["<scope-id-1>", "<scope-id-2>"],
            ),
        ],
    ),
)
await graph_client.applications.by_application_id(app_object_id).patch(app_update)
```

## Reviewing and Revoking Grants

### List All Delegated Grants for an App

```python
grants = await graph_client.oauth2_permission_grants.get()
app_grants = [g for g in grants.value if g.client_id == service_principal_id]
for grant in app_grants:
    print(f"Type: {grant.consent_type}, Scope: {grant.scope}")
```

### Revoke Delegated Grant

```python
await graph_client.oauth2_permission_grants.by_o_auth2_permission_grant_id(
    grant_id
).delete()
```

### List Application Role Assignments

```python
assignments = await graph_client.service_principals.by_service_principal_id(
    service_principal_id
).app_role_assignments.get()
for a in assignments.value:
    print(f"Role: {a.app_role_id}, Resource: {a.resource_display_name}")
```

## Incremental / Dynamic Consent

For delegated flows, request additional scopes as needed:

```python
# Initial login — request minimal scopes
scopes = ["User.Read"]

# Later, when user accesses mail feature — request additional scope
scopes = ["User.Read", "Mail.Read"]
# MSAL will prompt for incremental consent only for new scopes
```

## Security Considerations

- **Least privilege** — request minimum scopes needed for each feature
- **Use delegated permissions** when a user is present — limits blast radius to user's access
- **Avoid `*.All` application permissions** unless the app genuinely needs tenant-wide access
- **Review grants regularly** — use the Enterprise Applications consent review in portal
- **Pre-authorize trusted apps** instead of granting broad permissions
- **Agent Identity scoping** — use per-agent delegated grants for fine-grained control

## Cross-References

- **→ `entra-app-registration`** — Permissions are configured on app registrations
- **→ `entra-agent-id`** — Agent Identity consent and per-agent scoping
- **→ `entra-agent-id-runtime`** — OBO flow requires delegated consent grants
- **→ `entra-users-groups`** — User consent settings in tenant configuration
- **→ `entra-conditional-access`** — CA policies can require admin consent for risky apps
- **→ `entra-audit-signin-logs`** — Consent grants appear in audit logs
