---
name: entra-conditional-access
description: "Entra ID Conditional Access policy management — policy lifecycle, common templates, named locations, authentication contexts, grant/session controls, what-if analysis via Microsoft Graph."
---

# Entra Conditional Access

Conditional Access (CA) policies are the core of Entra ID's zero-trust enforcement — evaluate signals (user, device, location, app, risk) and enforce controls (MFA, block, compliant device). Always create in `reportOnly` state first.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List policies | `GET /identity/conditionalAccess/policies` | `Policy.Read.All` |
| Create policy | `POST /identity/conditionalAccess/policies` | `Policy.ReadWrite.ConditionalAccess` |
| Update policy | `PATCH /identity/conditionalAccess/policies/{id}` | `Policy.ReadWrite.ConditionalAccess` |
| Delete policy | `DELETE /identity/conditionalAccess/policies/{id}` | `Policy.ReadWrite.ConditionalAccess` |
| Named locations | `GET /identity/conditionalAccess/namedLocations` | `Policy.Read.All` |
| Auth strengths | `GET /identity/conditionalAccess/authenticationStrength/policies` | `Policy.Read.All` |
| What-if | `POST /identity/conditionalAccess/evaluate` | `Policy.Read.All` |

## Policy Lifecycle

1. **Design** — Define signals (who, what, where, risk) and controls (grant/block/session)
2. **Create in `reportOnly`** — Policy evaluates but does not enforce; sign-in logs show what-if results
3. **Monitor** — Review CA insights in sign-in logs for 1-2 weeks
4. **Enable** — Change state to `enabled` after validation
5. **Audit** — Ongoing monitoring via sign-in logs and CA workbook

> **CRITICAL:** Never create a CA policy in `enabled` state directly. Always use `reportOnly` first.

## Common Policy Templates

### 1. Require MFA for All Users

```python
from msgraph.generated.models.conditional_access_policy import ConditionalAccessPolicy
from msgraph.generated.models.conditional_access_conditions import ConditionalAccessConditions
from msgraph.generated.models.conditional_access_users import ConditionalAccessUsers
from msgraph.generated.models.conditional_access_applications import ConditionalAccessApplications
from msgraph.generated.models.conditional_access_grant_controls import ConditionalAccessGrantControls

policy = ConditionalAccessPolicy(
    display_name="CA001: Require MFA for all users",
    state="reportOnly",  # ALWAYS start in reportOnly
    conditions=ConditionalAccessConditions(
        users=ConditionalAccessUsers(
            include_users=["All"],
            exclude_groups=["<emergency-access-group-id>"],  # Always exclude break-glass
        ),
        applications=ConditionalAccessApplications(
            include_applications=["All"],
        ),
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="OR",
        built_in_controls=["mfa"],
    ),
)
result = await graph_client.identity.conditional_access.policies.post(policy)
```

### 2. Block Legacy Authentication

```python
from msgraph.generated.models.conditional_access_condition_set import ConditionalAccessConditionSet
from msgraph.generated.models.conditional_access_client_applications import ConditionalAccessClientApplications

policy = ConditionalAccessPolicy(
    display_name="CA002: Block legacy authentication",
    state="reportOnly",
    conditions=ConditionalAccessConditions(
        users=ConditionalAccessUsers(include_users=["All"]),
        applications=ConditionalAccessApplications(include_applications=["All"]),
        client_app_types=["exchangeActiveSync", "other"],
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="OR",
        built_in_controls=["block"],
    ),
)
```

### 3. Require Compliant Device for Sensitive Apps

```python
policy = ConditionalAccessPolicy(
    display_name="CA003: Require compliant device for Office 365",
    state="reportOnly",
    conditions=ConditionalAccessConditions(
        users=ConditionalAccessUsers(include_users=["All"]),
        applications=ConditionalAccessApplications(
            include_applications=["Office365"],
        ),
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="OR",
        built_in_controls=["compliantDevice"],
    ),
)
```

### 4. Block Access from Untrusted Locations

```python
policy = ConditionalAccessPolicy(
    display_name="CA004: Block access outside trusted locations",
    state="reportOnly",
    conditions=ConditionalAccessConditions(
        users=ConditionalAccessUsers(include_users=["All"]),
        applications=ConditionalAccessApplications(include_applications=["All"]),
        locations=ConditionalAccessLocations(
            include_locations=["All"],
            exclude_locations=["AllTrusted"],
        ),
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="OR",
        built_in_controls=["block"],
    ),
)
```

### 5. Require MFA for Risky Sign-Ins

```python
policy = ConditionalAccessPolicy(
    display_name="CA005: Require MFA for medium+ risk sign-ins",
    state="reportOnly",
    conditions=ConditionalAccessConditions(
        users=ConditionalAccessUsers(include_users=["All"]),
        applications=ConditionalAccessApplications(include_applications=["All"]),
        sign_in_risk_levels=["medium", "high"],
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="OR",
        built_in_controls=["mfa"],
    ),
)
```

## Named Locations

### Create IP-Based Trusted Location

```python
from msgraph.generated.models.ip_named_location import IpNamedLocation
from msgraph.generated.models.i_pv4_cidr_range import IPv4CidrRange

location = IpNamedLocation(
    display_name="Corporate Office - Redmond",
    is_trusted=True,
    ip_ranges=[
        IPv4CidrRange(odata_type="#microsoft.graph.iPv4CidrRange", cidr_address="203.0.113.0/24"),
        IPv4CidrRange(odata_type="#microsoft.graph.iPv4CidrRange", cidr_address="198.51.100.0/24"),
    ],
)
await graph_client.identity.conditional_access.named_locations.post(location)
```

### Create Country-Based Location

```python
from msgraph.generated.models.country_named_location import CountryNamedLocation

location = CountryNamedLocation(
    display_name="Allowed Countries",
    countries_and_regions=["US", "CA", "GB"],
    include_unknown_countries_and_regions=False,
)
await graph_client.identity.conditional_access.named_locations.post(location)
```

## Grant Controls Reference

| Control | Value | Description |
|---------|-------|-------------|
| Require MFA | `mfa` | Multi-factor authentication |
| Block access | `block` | Deny access entirely |
| Compliant device | `compliantDevice` | Intune-compliant device |
| Domain joined | `domainJoinedDevice` | Hybrid Azure AD joined |
| Approved app | `approvedApplication` | Intune approved client app |
| App protection | `compliantApplication` | Intune app protection policy |
| Password change | `passwordChange` | Force password change (for risky users) |

## Session Controls

| Control | Effect |
|---------|--------|
| Sign-in frequency | How often users must re-authenticate (e.g., every 1 hour) |
| Persistent browser | Whether session persists after browser close |
| MCAS (Defender for Cloud Apps) | Route session through Cloud App Security proxy |
| Disable resilience defaults | Disable token extension during outages |

## Emergency Access Accounts

**Every CA policy that targets "All users" MUST exclude at least one emergency access (break-glass) account or group.** This prevents lockout when CA policies malfunction.

Pattern:
1. Create 2 cloud-only emergency access accounts (no MFA, no CA)
2. Create a security group containing these accounts
3. Exclude this group from all blocking/MFA CA policies
4. Monitor sign-in logs for these accounts — any usage is an alert

## .NET Example: List All Policies

```csharp
var policies = await graphClient.Identity.ConditionalAccess.Policies.GetAsync();
foreach (var policy in policies.Value)
{
    Console.WriteLine($"{policy.DisplayName} — State: {policy.State}");
}
```

## What-If Analysis

Test policy impact before enabling:

```python
# Review sign-in logs for reportOnly policy results
from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import SignInsRequestBuilder

query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
    filter="conditionalAccessStatus eq 'reportOnlyNotApplied' or conditionalAccessStatus eq 'reportOnlySuccess'",
    top=50,
    select=["userDisplayName", "appDisplayName", "conditionalAccessStatus", "appliedConditionalAccessPolicies"],
)
sign_ins = await graph_client.audit_logs.sign_ins.get(
    request_configuration=SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
        query_parameters=query,
    )
)
```

## Security Considerations

- **Report-only first** — Always. No exceptions.
- **Break-glass exclusion** — Every blocking policy must exclude emergency access accounts
- **Avoid All Users + Block** without a location or risk condition — can lock out entire tenant
- **Review regularly** — Stale policies with outdated group targets create gaps
- **Test with What-If** — Before enabling, validate expected behavior

## Cross-References

- **→ `entra-app-registration`** — Target apps in CA policies by Application ID
- **→ `entra-users-groups`** — Target users/groups; dynamic groups for CA targeting
- **→ `entra-audit-signin-logs`** — CA policy evaluation results in sign-in logs
- **→ `entra-managed-identity`** — MI sign-ins may be subject to CA policies
- **→ `entra-msal-deep-dive`** — Claims challenge when CA requires step-up auth
