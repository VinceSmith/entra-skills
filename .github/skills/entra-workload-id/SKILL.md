---
name: entra-workload-id
description: "Entra Workload ID — holistic non-human identity management: service principal lifecycle, Workload Identity Premium (CA, risk, access reviews), credentials, permissions, sign-in analysis, and posture management."
---

# Entra Workload ID

Holistic management of non-human (workload) identities in Entra ID — service principals, managed identities, and federated credentials. Covers lifecycle, Conditional Access for workloads, risk detection, credential hygiene, permission inventory, sign-in analysis, and posture management.

> **Distinction:** This skill covers **workload identity management and posture**. For federation trust configuration (GitHub Actions OIDC, AWS/GCP→Azure), see `entra-workload-identity-federation`. For managed identity provisioning, see `entra-managed-identity`.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List service principals | `GET /servicePrincipals` | `Application.Read.All` |
| Get service principal | `GET /servicePrincipals/{id}` | `Application.Read.All` |
| Create service principal | `POST /servicePrincipals` | `Application.ReadWrite.All` |
| Update service principal | `PATCH /servicePrincipals/{id}` | `Application.ReadWrite.All` |
| Delete service principal | `DELETE /servicePrincipals/{id}` | `Application.ReadWrite.All` |
| SP password credentials | `GET /servicePrincipals/{id}` → `passwordCredentials` | `Application.Read.All` |
| Add SP password | `POST /servicePrincipals/{id}/addPassword` | `Application.ReadWrite.All` |
| Remove SP password | `POST /servicePrincipals/{id}/removePassword` | `Application.ReadWrite.All` |
| SP app role assignments | `GET /servicePrincipals/{id}/appRoleAssignments` | `Application.Read.All` |
| OAuth2 permission grants | `GET /oauth2PermissionGrants?$filter=clientId eq '{spId}'` | `DelegatedPermissionGrant.ReadWrite.All` |
| SP sign-in logs | `GET /auditLogs/signIns?$filter=signInEventTypes/any(t: t eq 'servicePrincipal')` | `AuditLog.Read.All` |
| Risky service principals | `GET /identityProtection/riskyServicePrincipals` | `IdentityRiskyServicePrincipal.Read.All` |
| CA policies (workload) | `GET /identity/conditionalAccess/policies` | `Policy.Read.All` |

## Service Principal Types

| Type | `servicePrincipalType` | Created By |
|------|----------------------|------------|
| Application | `Application` | App registration (Entra or external) |
| Managed Identity | `ManagedIdentity` | Azure resource (system/user-assigned MI) |
| Legacy | `Legacy` | Older integrations, ADAL-based apps |
| Social IdP | `SocialIdp` | External identity providers (B2C) |

> **Enterprise app vs app registration:** An app registration is the global definition (`/applications`); the service principal (`/servicePrincipals`) is the local tenant instance. One app registration can have SPs in multiple tenants.

## Service Principal Lifecycle

### List All Service Principals with Type Filter

```python
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient
from msgraph.generated.service_principals.service_principals_request_builder import (
    ServicePrincipalsRequestBuilder,
)

credential = DefaultAzureCredential()
graph_client = GraphServiceClient(credential)

# List application-type SPs (excludes managed identities, legacy)
query = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
    filter="servicePrincipalType eq 'Application'",
    select=["id", "displayName", "appId", "servicePrincipalType", "accountEnabled"],
    top=100,
    orderby=["displayName"],
)
config = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
result = await graph_client.service_principals.get(request_configuration=config)
for sp in result.value:
    status = "enabled" if sp.account_enabled else "DISABLED"
    print(f"[{status}] {sp.display_name} ({sp.app_id})")
```

### Create Service Principal from App Registration

```python
from msgraph.generated.models.service_principal import ServicePrincipal

sp = ServicePrincipal(
    app_id="<app-client-id>",  # From app registration
    display_name="MyApp - Production",
    account_enabled=True,
    tags=["WindowsAzureActiveDirectoryIntegratedApp"],
)
created = await graph_client.service_principals.post(sp)
print(f"Created SP: {created.id} ({created.display_name})")
```

## Workload Identity Premium Features

Requires **Workload Identities Premium** license (separate from Entra ID P1/P2).

### Conditional Access for Workload Identities

```python
from msgraph.generated.models.conditional_access_policy import ConditionalAccessPolicy
from msgraph.generated.models.conditional_access_conditions import ConditionalAccessConditions
from msgraph.generated.models.conditional_access_client_applications import ConditionalAccessClientApplications
from msgraph.generated.models.conditional_access_applications import ConditionalAccessApplications
from msgraph.generated.models.conditional_access_grant_controls import ConditionalAccessGrantControls
from msgraph.generated.models.conditional_access_locations import ConditionalAccessLocations
from msgraph.generated.models.conditional_access_location_condition import ConditionalAccessLocationCondition

# CA policy: block workload identity sign-ins from outside trusted locations
policy = ConditionalAccessPolicy(
    display_name="CA-WL001: Block workloads from untrusted locations",
    state="reportOnly",  # ALWAYS start in reportOnly
    conditions=ConditionalAccessConditions(
        client_applications=ConditionalAccessClientApplications(
            include_service_principals=["<sp-object-id>"],  # Target specific SPs
            # Or use service principal filter: servicePrincipalFilter
        ),
        applications=ConditionalAccessApplications(
            include_applications=["All"],
        ),
        locations=ConditionalAccessLocationCondition(
            include_locations=["All"],
            exclude_locations=["<trusted-named-location-id>"],
        ),
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="OR",
        built_in_controls=["block"],
    ),
)
created = await graph_client.identity.conditional_access.policies.post(policy)
print(f"Created CA policy: {created.id} (state: {created.state})")
```

> **CRITICAL:** Never create CA policies in `enabled` state directly. Always use `reportOnly` first and monitor for 1–2 weeks.

### Risky Service Principal Detection

```python
risky_sps = await graph_client.identity_protection.risky_service_principals.get()
for rsp in risky_sps.value:
    print(
        f"[{rsp.risk_state}] {rsp.display_name} — "
        f"level: {rsp.risk_level}, detail: {rsp.risk_detail}, "
        f"last updated: {rsp.risk_last_updated_date_time}"
    )
```

## Service Principal Credentials

### Inventory SP Credentials (Secrets + Certificates)

```python
from datetime import datetime, timedelta, timezone

warning_threshold = datetime.now(timezone.utc) + timedelta(days=30)
now = datetime.now(timezone.utc)

sps = await graph_client.service_principals.get()
credential_report = []

for sp in sps.value:
    for cred in (sp.password_credentials or []):
        if cred.end_date_time:
            credential_report.append({
                "sp": sp.display_name,
                "sp_id": sp.id,
                "type": "secret",
                "key_id": str(cred.key_id),
                "expires": cred.end_date_time.isoformat(),
                "status": "EXPIRED" if cred.end_date_time < now
                          else "EXPIRING" if cred.end_date_time < warning_threshold
                          else "OK",
            })
    for cred in (sp.key_credentials or []):
        if cred.end_date_time:
            credential_report.append({
                "sp": sp.display_name,
                "sp_id": sp.id,
                "type": "certificate",
                "key_id": str(cred.key_id),
                "expires": cred.end_date_time.isoformat(),
                "status": "EXPIRED" if cred.end_date_time < now
                          else "EXPIRING" if cred.end_date_time < warning_threshold
                          else "OK",
            })

for c in credential_report:
    if c["status"] != "OK":
        print(f"[{c['status']}] {c['sp']} ({c['type']}): expires {c['expires']}")
```

> For federated identity credentials (WIF) as a secret-free alternative, see `entra-workload-identity-federation`.

### .NET: List SP Credentials

```csharp
using Azure.Identity;
using Microsoft.Graph;

var credential = new DefaultAzureCredential();
var graphClient = new GraphServiceClient(credential);

var sps = await graphClient.ServicePrincipals.GetAsync(config =>
{
    config.QueryParameters.Select = new[] { "id", "displayName", "passwordCredentials", "keyCredentials" };
    config.QueryParameters.Top = 100;
});

foreach (var sp in sps.Value)
{
    foreach (var pwd in sp.PasswordCredentials ?? [])
        Console.WriteLine($"{sp.DisplayName} | secret | expires {pwd.EndDateTime:u}");
    foreach (var key in sp.KeyCredentials ?? [])
        Console.WriteLine($"{sp.DisplayName} | cert   | expires {key.EndDateTime:u}");
}
```

## Service Principal Permissions

### Get SP Permissions (Delegated + Application)

```python
sp_id = "<service-principal-object-id>"

# Application permissions (app role assignments)
app_roles = await graph_client.service_principals.by_service_principal_id(
    sp_id
).app_role_assignments.get()

print("=== Application Permissions ===")
for ar in app_roles.value:
    print(f"  {ar.resource_display_name}: {ar.id} (principal: {ar.principal_display_name})")

# Delegated permissions (OAuth2 permission grants)
from msgraph.generated.oauth2_permission_grants.oauth2_permission_grants_request_builder import (
    Oauth2PermissionGrantsRequestBuilder,
)

query = Oauth2PermissionGrantsRequestBuilder.Oauth2PermissionGrantsRequestBuilderGetQueryParameters(
    filter=f"clientId eq '{sp_id}'",
)
config = Oauth2PermissionGrantsRequestBuilder.Oauth2PermissionGrantsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
grants = await graph_client.oauth2_permission_grants.get(request_configuration=config)

print("=== Delegated Permissions ===")
for g in grants.value:
    consent = "admin" if g.consent_type == "AllPrincipals" else "user"
    print(f"  Resource: {g.resource_id} | Scopes: {g.scope} | Consent: {consent}")
```

### Detect Over-Privileged Workloads

```python
high_risk_permissions = {
    "Application.ReadWrite.All", "Directory.ReadWrite.All",
    "RoleManagement.ReadWrite.Directory", "Mail.ReadWrite",
    "Sites.ReadWrite.All", "Files.ReadWrite.All",
}

sps = await graph_client.service_principals.get()
for sp in sps.value:
    roles = await graph_client.service_principals.by_service_principal_id(
        sp.id
    ).app_role_assignments.get()
    dangerous = [r for r in (roles.value or []) if r.resource_display_name in high_risk_permissions]
    if dangerous:
        print(f"⚠ {sp.display_name} has {len(dangerous)} high-risk app role assignments")
```

## Service Principal Sign-In Analysis

### Query SP Sign-In Logs

```python
from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import (
    SignInsRequestBuilder,
)

query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
    filter=(
        "signInEventTypes/any(t: t eq 'servicePrincipal') "
        "and createdDateTime ge 2025-01-01T00:00:00Z"
    ),
    top=50,
    orderby=["createdDateTime desc"],
    select=["id", "createdDateTime", "appDisplayName", "servicePrincipalId",
            "ipAddress", "status", "location", "resourceDisplayName"],
)
config = SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
signins = await graph_client.audit_logs.sign_ins.get(request_configuration=config)
for s in signins.value:
    status = "OK" if s.status.error_code == 0 else f"FAIL({s.status.error_code})"
    print(f"{s.created_date_time} | {s.app_display_name} | {status} | {s.ip_address}")
```

### Find Stale Service Principals (No Recent Sign-Ins)

```python
from datetime import datetime, timedelta, timezone

stale_threshold = datetime.now(timezone.utc) - timedelta(days=90)

# Get all application-type SPs
query = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetQueryParameters(
    filter="servicePrincipalType eq 'Application' and accountEnabled eq true",
    select=["id", "displayName", "appId"],
    top=999,
)
config = ServicePrincipalsRequestBuilder.ServicePrincipalsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
all_sps = await graph_client.service_principals.get(request_configuration=config)

# Get SPs that HAVE signed in recently
recent_filter = f"signInEventTypes/any(t: t eq 'servicePrincipal') and createdDateTime ge {stale_threshold.strftime('%Y-%m-%dT%H:%M:%SZ')}"
signin_query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
    filter=recent_filter, select=["servicePrincipalId"], top=999,
)
signin_config = SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
    query_parameters=signin_query,
)
recent_signins = await graph_client.audit_logs.sign_ins.get(request_configuration=signin_config)
active_sp_ids = {s.service_principal_id for s in recent_signins.value}

# SPs with no recent sign-in activity
stale_sps = [sp for sp in all_sps.value if sp.id not in active_sp_ids]
print(f"Found {len(stale_sps)} stale SPs (no sign-in in {90} days):")
for sp in stale_sps:
    print(f"  {sp.display_name} ({sp.app_id})")
```

## Workload Identity Posture Management

### Posture Checklist

| Check | Risk | Remediation |
|-------|------|-------------|
| SPs with expired credentials | Potential orphan | Remove expired creds; disable if unused |
| SPs with no sign-ins > 90 days | Stale identity | Disable or delete after verification |
| SPs with `*.ReadWrite.All` permissions | Over-privilege | Scope down to least-privilege permissions |
| SPs without CA policy coverage | Uncontrolled access | Apply workload CA policies |
| SPs with secrets (not certs/WIF/MI) | Credential risk | Migrate to WIF or managed identity |
| Risky service principals | Active threat | Investigate, rotate credentials, restrict |
| SPs without owners | Governance gap | Assign owners for accountability |

### Full Posture Scan

```python
async def workload_identity_posture_scan(graph_client):
    """Run a comprehensive posture assessment of all workload identities."""
    issues = []
    sps = await graph_client.service_principals.get()

    for sp in sps.value:
        if sp.service_principal_type != "Application":
            continue

        # Check for expired credentials
        for cred in (sp.password_credentials or []):
            if cred.end_date_time and cred.end_date_time < datetime.now(timezone.utc):
                issues.append(("EXPIRED_CRED", sp.display_name, f"Secret expired {cred.end_date_time}"))

        # Check for missing owners
        owners = await graph_client.service_principals.by_service_principal_id(
            sp.id
        ).owners.get()
        if not owners.value:
            issues.append(("NO_OWNER", sp.display_name, "No owners assigned"))

        # Check for secrets (prefer certs/WIF/MI)
        if sp.password_credentials:
            issues.append(("USES_SECRETS", sp.display_name, f"{len(sp.password_credentials)} secret(s)"))

    # Check risky SPs
    risky = await graph_client.identity_protection.risky_service_principals.get()
    for rsp in risky.value:
        if rsp.risk_level in ("high", "medium"):
            issues.append(("RISKY_SP", rsp.display_name, f"Risk: {rsp.risk_level}"))

    return issues
```

## Security Considerations

- **Least privilege** — Scope SP permissions to the minimum required; avoid `*.ReadWrite.All`
- **MI → WIF → cert → secret** — Prefer managed identity; use secrets only as last resort
- **Never hardcode credentials** — Use `DefaultAzureCredential` for all SDK clients
- **CA for workloads** — Apply Conditional Access policies to restrict workload sign-in locations/conditions
- **Stale cleanup** — Regularly audit and disable SPs with no recent activity
- **Owner accountability** — Every SP should have at least one owner for governance
- **Credential rotation** — Monitor expiry; automate rotation via Key Vault where possible
- **Report-only first** — Always create CA policies in `reportOnly` state before enabling

## Cross-References

| Skill | Relationship |
|-------|-------------|
| `entra-app-registration` | App registrations that create service principals |
| `entra-workload-identity-federation` | Federated credentials — WIF trust configuration plumbing |
| `entra-managed-identity` | Managed identity as a type of workload identity |
| `entra-secret-certificate-lifecycle` | Credential rotation patterns for SPs |
| `entra-audit-signin-logs` | SP sign-in log analysis and KQL patterns |
| `entra-conditional-access` | CA policy authoring for workload identities |
| `entra-admin-consent-permissions` | API permission grants and admin consent for SPs |
