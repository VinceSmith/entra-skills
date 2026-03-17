---
name: entra-id-protection
description: "Entra ID Protection — risk detections, risky users, risky service principals, investigation workflows, remediation actions, incident response via Microsoft Graph."
---

# Entra ID Protection

Entra ID Protection detects identity-based risks in real-time and offline, surfaces risky users and service principals, and enables automated or manual remediation. This skill covers the full investigation-to-remediation lifecycle: querying risk detections, triaging risky identities, correlating with sign-in logs, and executing remediation actions.

> **Relationship to `entra-audit-signin-logs`:** That skill covers basic risk detection and risky user queries. This skill goes deeper — remediation actions, investigation workflows, risky service principals, risk policy guidance, and incident response patterns.

> **License:** Risk detections require **Entra ID P2**. Risky service principals require **Workload Identity Premium**.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List risk detections | `GET /identityProtection/riskDetections` | `IdentityRiskEvent.Read.All` |
| Get risk detection | `GET /identityProtection/riskDetections/{id}` | `IdentityRiskEvent.Read.All` |
| List risky users | `GET /identityProtection/riskyUsers` | `IdentityRiskyUser.Read.All` |
| Get risky user | `GET /identityProtection/riskyUsers/{id}` | `IdentityRiskyUser.Read.All` |
| List user risk history | `GET /identityProtection/riskyUsers/{id}/history` | `IdentityRiskyUser.Read.All` |
| Confirm user compromised | `POST /identityProtection/riskyUsers/confirmCompromised` | `IdentityRiskyUser.ReadWrite.All` |
| Dismiss user risk | `POST /identityProtection/riskyUsers/dismiss` | `IdentityRiskyUser.ReadWrite.All` |
| List risky service principals | `GET /identityProtection/riskyServicePrincipals` | `IdentityRiskyServicePrincipal.Read.All` |
| Confirm SP compromised | `POST /identityProtection/riskyServicePrincipals/confirmCompromised` | `IdentityRiskyServicePrincipal.ReadWrite.All` |
| Dismiss SP risk | `POST /identityProtection/riskyServicePrincipals/dismiss` | `IdentityRiskyServicePrincipal.ReadWrite.All` |

## Risk Detection Types

| Risk Type | Timing | Description |
|-----------|--------|-------------|
| `unfamiliarFeatures` | Offline | Sign-in with unfamiliar properties |
| `anonymizedIPAddress` | Real-time | Sign-in from anonymous IP (Tor, VPN) |
| `maliciousIPAddress` | Offline | Sign-in from known malicious IP |
| `leakedCredentials` | Offline | Credentials found in breach database |
| `impossibleTravel` | Offline | Sign-ins from geographically distant locations in short time |
| `passwordSpray` | Offline | Multiple accounts targeted with common passwords |
| `anomalousToken` | Real-time | Unusual token characteristics (lifetime, issuer) |
| `tokenIssuerAnomaly` | Offline | Unusual SAML token issuer pattern |
| `suspiciousBrowser` | Offline | Suspicious browser activity inferred from sign-in pattern |
| `mcasImpossibleTravel` | Offline | Detected by Microsoft Defender for Cloud Apps |
| `malwareLinkedIPAddress` | Offline | Sign-in from IP associated with malware-infected device |

## List High-Risk Detections (Last 7 Days)

```python
from datetime import datetime, timedelta, timezone
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient
from msgraph.generated.identity_protection.risk_detections.risk_detections_request_builder import (
    RiskDetectionsRequestBuilder,
)

credential = DefaultAzureCredential()
graph_client = GraphServiceClient(credential)

since = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")

query = RiskDetectionsRequestBuilder.RiskDetectionsRequestBuilderGetQueryParameters(
    filter=f"riskLevel eq 'high' and detectedDateTime ge {since}",
    top=100,
    orderby=["detectedDateTime desc"],
    select=["id", "riskEventType", "riskLevel", "riskState", "detectedDateTime",
            "userDisplayName", "userPrincipalName", "ipAddress", "location"],
)
config = RiskDetectionsRequestBuilder.RiskDetectionsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
detections = await graph_client.identity_protection.risk_detections.get(
    request_configuration=config,
)
for d in detections.value:
    print(f"{d.detected_date_time} | {d.risk_event_type} | "
          f"{d.user_display_name} | {d.ip_address} | {d.risk_level}")
```

## Risky Users

### Get All Risky Users (Medium or Higher)

```python
from msgraph.generated.identity_protection.risky_users.risky_users_request_builder import (
    RiskyUsersRequestBuilder,
)

query = RiskyUsersRequestBuilder.RiskyUsersRequestBuilderGetQueryParameters(
    filter="riskLevel eq 'medium' or riskLevel eq 'high'",
    orderby=["riskLastUpdatedDateTime desc"],
    select=["id", "userDisplayName", "userPrincipalName", "riskLevel",
            "riskState", "riskDetail", "riskLastUpdatedDateTime"],
)
config = RiskyUsersRequestBuilder.RiskyUsersRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
risky = await graph_client.identity_protection.risky_users.get(
    request_configuration=config,
)
for user in risky.value:
    print(f"{user.user_display_name} | Risk: {user.risk_level} | "
          f"State: {user.risk_state} | Detail: {user.risk_detail}")
```

### Confirm User Compromised

```python
from msgraph.generated.identity_protection.risky_users.confirm_compromised.confirm_compromised_post_request_body import (
    ConfirmCompromisedPostRequestBody,
)

# CRITICAL: Only confirm after investigation. This raises user risk to "high"
# and triggers any risk-based CA policies (e.g., force password reset).
body = ConfirmCompromisedPostRequestBody(user_ids=["<user-id>"])
await graph_client.identity_protection.risky_users.confirm_compromised.post(body)
```

### Dismiss User Risk

```python
from msgraph.generated.identity_protection.risky_users.dismiss.dismiss_post_request_body import (
    DismissPostRequestBody,
)

# Only dismiss after verifying the detection is a false positive.
# Dismissing without investigation creates security gaps.
body = DismissPostRequestBody(user_ids=["<user-id>"])
await graph_client.identity_protection.risky_users.dismiss.post(body)
```

## Risky Service Principals

Requires **Workload Identity Premium** license.

### List Risky Service Principals

```python
from msgraph.generated.identity_protection.risky_service_principals.risky_service_principals_request_builder import (
    RiskyServicePrincipalsRequestBuilder,
)

query = RiskyServicePrincipalsRequestBuilder.RiskyServicePrincipalsRequestBuilderGetQueryParameters(
    filter="riskLevel eq 'high' or riskLevel eq 'medium'",
    select=["id", "appId", "displayName", "riskLevel", "riskState",
            "riskDetail", "riskLastUpdatedDateTime"],
)
config = RiskyServicePrincipalsRequestBuilder.RiskyServicePrincipalsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
risky_sps = await graph_client.identity_protection.risky_service_principals.get(
    request_configuration=config,
)
for sp in risky_sps.value:
    print(f"{sp.display_name} (appId: {sp.app_id}) | "
          f"Risk: {sp.risk_level} | State: {sp.risk_state}")
```

### Confirm Service Principal Compromised

```python
from msgraph.generated.identity_protection.risky_service_principals.confirm_compromised.confirm_compromised_post_request_body import (
    ConfirmCompromisedPostRequestBody as SPConfirmCompromisedPostRequestBody,
)

body = SPConfirmCompromisedPostRequestBody(service_principal_ids=["<sp-id>"])
await graph_client.identity_protection.risky_service_principals.confirm_compromised.post(body)
# After confirming: rotate all credentials for this SP immediately
```

## Risk Policies (Deprecated)

> **NOTE:** The legacy risk policy APIs (`identityProtection/signInRiskPolicies` and `identityProtection/userRiskPolicies`) are deprecated. Microsoft recommends using **Conditional Access policies** with risk conditions instead. See `entra-conditional-access` for risk-based CA policy templates.

Risk-based controls via CA (recommended approach):
- **Sign-in risk** → CA condition `signInRiskLevels: ["medium", "high"]` → require MFA
- **User risk** → CA condition `userRiskLevels: ["high"]` → require password change

## Investigation Workflows

### Correlate Risk Detection with Sign-In Logs

```python
# Step 1: Get the risk detection
detection = await graph_client.identity_protection.risk_detections.by_risk_detection_id(
    "<detection-id>"
).get()

# Step 2: Find the corresponding sign-in using correlationId
from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import SignInsRequestBuilder

if detection.correlation_id:
    sign_in_query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
        filter=f"correlationId eq '{detection.correlation_id}'",
        select=["userDisplayName", "appDisplayName", "ipAddress", "location",
                "status", "conditionalAccessStatus", "deviceDetail",
                "riskLevelDuringSignIn", "riskState"],
    )
    sign_ins = await graph_client.audit_logs.sign_ins.get(
        request_configuration=SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
            query_parameters=sign_in_query,
        )
    )
    for si in sign_ins.value:
        print(f"App: {si.app_display_name} | IP: {si.ip_address} | "
              f"Location: {si.location} | CA: {si.conditional_access_status} | "
              f"Device: {si.device_detail}")
```

### Build Incident Timeline for a User

```python
from datetime import datetime, timedelta, timezone

user_id = "<user-id>"
since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

# 1. Risk detections for this user
det_query = RiskDetectionsRequestBuilder.RiskDetectionsRequestBuilderGetQueryParameters(
    filter=f"userId eq '{user_id}' and detectedDateTime ge {since}",
    orderby=["detectedDateTime asc"],
)
detections = await graph_client.identity_protection.risk_detections.get(
    request_configuration=RiskDetectionsRequestBuilder.RiskDetectionsRequestBuilderGetRequestConfiguration(
        query_parameters=det_query,
    )
)

# 2. Sign-in history for this user
si_query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
    filter=f"userId eq '{user_id}' and createdDateTime ge {since}",
    orderby=["createdDateTime asc"],
    select=["createdDateTime", "appDisplayName", "ipAddress", "location",
            "status", "riskLevelDuringSignIn", "conditionalAccessStatus"],
)
sign_ins = await graph_client.audit_logs.sign_ins.get(
    request_configuration=SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
        query_parameters=si_query,
    )
)

# 3. Merge into timeline
timeline = []
for d in detections.value:
    timeline.append({"time": d.detected_date_time, "type": "risk",
                     "detail": f"{d.risk_event_type} ({d.risk_level})"})
for s in sign_ins.value:
    timeline.append({"time": s.created_date_time, "type": "sign-in",
                     "detail": f"{s.app_display_name} from {s.ip_address}"})
timeline.sort(key=lambda x: x["time"])

for event in timeline:
    print(f"[{event['time']}] {event['type'].upper()}: {event['detail']}")
```

## Remediation Actions

### Force Password Reset (via Conditional Access)

The recommended approach is a CA policy with the `passwordChange` grant control targeting users with high user risk. This forces a self-service password reset at next sign-in:

```python
# See entra-conditional-access for full CA policy creation.
# Key fragment: user risk condition + password change control
from msgraph.generated.models.conditional_access_policy import ConditionalAccessPolicy
from msgraph.generated.models.conditional_access_conditions import ConditionalAccessConditions
from msgraph.generated.models.conditional_access_users import ConditionalAccessUsers
from msgraph.generated.models.conditional_access_applications import ConditionalAccessApplications
from msgraph.generated.models.conditional_access_grant_controls import ConditionalAccessGrantControls

policy = ConditionalAccessPolicy(
    display_name="CA-RISK: Force password reset for high-risk users",
    state="reportOnly",  # ALWAYS start in reportOnly
    conditions=ConditionalAccessConditions(
        users=ConditionalAccessUsers(include_users=["All"]),
        applications=ConditionalAccessApplications(include_applications=["All"]),
        user_risk_levels=["high"],
    ),
    grant_controls=ConditionalAccessGrantControls(
        operator="AND",
        built_in_controls=["mfa", "passwordChange"],
    ),
)
await graph_client.identity.conditional_access.policies.post(policy)
```

### Revoke Refresh Tokens

```python
# Immediately invalidate all refresh tokens for a compromised user.
# User must re-authenticate on next access attempt.
await graph_client.users.by_user_id("<user-id>").revoke_sign_in_sessions.post()
```

### Block Sign-In for Compromised Account

```python
from msgraph.generated.models.user import User

# Disable the account pending investigation
await graph_client.users.by_user_id("<user-id>").patch(
    User(account_enabled=False)
)
# Re-enable after remediation is complete and risk is dismissed
```

## Risky Users (.NET)

```csharp
using Azure.Identity;
using Microsoft.Graph;

var credential = new DefaultAzureCredential();
var graphClient = new GraphServiceClient(credential);

var riskyUsers = await graphClient.IdentityProtection.RiskyUsers.GetAsync(config =>
{
    config.QueryParameters.Filter = "riskLevel eq 'high'";
    config.QueryParameters.Orderby = new[] { "riskLastUpdatedDateTime desc" };
    config.QueryParameters.Top = 50;
});
foreach (var user in riskyUsers.Value)
{
    Console.WriteLine($"{user.UserDisplayName} | Risk: {user.RiskLevel} | State: {user.RiskState}");
}
```

## Security Considerations

- **Never auto-dismiss risk** without thorough investigation — dismissing wipes the risk state permanently
- **Never auto-confirm compromised** without evidence — this elevates risk to high and may trigger account lockout via CA
- **Audit all remediation actions** — log who confirmed/dismissed which user and why; use audit logs to track `Confirm compromised user` and `Dismiss user risk` activities
- **Least-privilege permissions** — use `IdentityRiskyUser.Read.All` for read-only dashboards; only grant `ReadWrite.All` to incident response tooling
- **Risk detections require Entra ID P2** — queries return empty results without the license
- **Risky SPs require Workload Identity Premium** — plan licensing before building SP risk workflows
- **Correlate before acting** — always cross-reference risk detections with sign-in logs before taking remediation action
- **Never hardcode credentials** — use `DefaultAzureCredential` for all SDK clients
- **Token revocation is immediate but not instant** — cached tokens may remain valid for up to 1 hour; combine with account disable for critical incidents

## Cross-References

- **→ `entra-conditional-access`** — Risk-based CA policies (sign-in risk + user risk conditions, `passwordChange` grant control)
- **→ `entra-audit-signin-logs`** — Sign-in logs for investigation; basic risk detection queries
- **→ `entra-users-groups`** — User operations for remediation (disable account, revoke sessions)
- **→ `entra-workload-identity-federation`** — Risky service principal management and credential-free alternatives
- **→ `entra-secret-certificate-lifecycle`** — Rotate credentials for compromised service principals
- **→ `entra-msal-deep-dive`** — Claims challenge handling when risk-based CA triggers step-up auth
