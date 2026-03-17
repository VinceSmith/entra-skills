---
name: entra-audit-signin-logs
description: "Entra ID audit and sign-in log analysis — directory audit queries, sign-in log queries (interactive, non-interactive, service principal), KQL patterns, risk events, identity protection."
---

# Entra Audit & Sign-In Logs

Query and analyze Entra ID directory audit logs, sign-in logs (interactive, non-interactive, service principal, managed identity), risk events, and identity protection detections via Microsoft Graph and KQL.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| Directory audits | `GET /auditLogs/directoryAudits` | `AuditLog.Read.All` |
| Sign-in logs (interactive) | `GET /auditLogs/signIns` | `AuditLog.Read.All` |
| Risk detections | `GET /identityProtection/riskDetections` | `IdentityRiskEvent.Read.All` |
| Risky users | `GET /identityProtection/riskyUsers` | `IdentityRiskyUser.Read.All` |
| Risky service principals | `GET /identityProtection/riskyServicePrincipals` | `IdentityRiskyServicePrincipal.Read.All` |

> **Note:** Sign-in logs require Entra ID P1 or P2 license. Risk detections require P2.

## Audit Log Queries

### Recent Directory Changes (Python)

```python
from msgraph.generated.audit_logs.directory_audits.directory_audits_request_builder import (
    DirectoryAuditsRequestBuilder,
)

query = DirectoryAuditsRequestBuilder.DirectoryAuditsRequestBuilderGetQueryParameters(
    filter="activityDateTime ge 2025-01-01T00:00:00Z",
    top=50,
    orderby=["activityDateTime desc"],
)
config = DirectoryAuditsRequestBuilder.DirectoryAuditsRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
audits = await graph_client.audit_logs.directory_audits.get(request_configuration=config)
for audit in audits.value:
    print(f"{audit.activity_date_time} | {audit.activity_display_name} | {audit.initiated_by}")
```

### Filter by Activity Type

```python
# App registration changes
filter = "activityDisplayName eq 'Add application' or activityDisplayName eq 'Update application'"

# Group membership changes
filter = "activityDisplayName eq 'Add member to group' or activityDisplayName eq 'Remove member from group'"

# Role assignment changes
filter = "activityDisplayName eq 'Add member to role' or activityDisplayName eq 'Remove member from role'"

# Credential changes (secrets/certificates)
filter = "activityDisplayName eq 'Update application – Certificates and secrets management'"
```

### Audit Log (.NET)

```csharp
var audits = await graphClient.AuditLogs.DirectoryAudits.GetAsync(config =>
{
    config.QueryParameters.Filter = "activityDisplayName eq 'Add application'";
    config.QueryParameters.Top = 50;
    config.QueryParameters.Orderby = new[] { "activityDateTime desc" };
});
foreach (var audit in audits.Value)
{
    Console.WriteLine($"{audit.ActivityDateTime} | {audit.ActivityDisplayName}");
}
```

## Sign-In Log Queries

### Interactive Sign-Ins

```python
from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import SignInsRequestBuilder

query = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
    filter="createdDateTime ge 2025-01-01T00:00:00Z and status/errorCode ne 0",
    top=100,
    select=["userDisplayName", "appDisplayName", "ipAddress", "status", "location",
            "conditionalAccessStatus", "riskState", "riskLevelDuringSignIn"],
    orderby=["createdDateTime desc"],
)
sign_ins = await graph_client.audit_logs.sign_ins.get(
    request_configuration=SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
        query_parameters=query,
    )
)
```

### Failed Sign-In Analysis

```python
# Failed sign-ins in the last 24 hours
from datetime import datetime, timedelta, timezone

since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
filter = f"createdDateTime ge {since} and status/errorCode ne 0"
```

### Service Principal Sign-Ins

```python
# Service principal sign-ins (app-only flows)
sp_sign_ins = await graph_client.audit_logs.sign_ins.get(
    request_configuration=SignInsRequestBuilder.SignInsRequestBuilderGetRequestConfiguration(
        query_parameters=SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
            filter="signInEventTypes/any(t:t eq 'servicePrincipal')",
            top=50,
        ),
    )
)
```

### Agent Attribution in Logs

Agent Identity sign-ins appear as **service principal sign-ins** with the agent's own identity:

```python
# Find sign-ins from Agent Identities
filter = "appDisplayName eq 'MyAgent-Blueprint'"  # Blueprint app name
# Or filter by the specific service principal ID of the agent
filter = f"servicePrincipalId eq '{agent_sp_id}'"
```

The sign-in log entry includes:
- `servicePrincipalId` — the agent's identity (not the user's)
- `autonomousSystemNumber` — network attribution
- `appId` — the Blueprint app registration
- `resourceDisplayName` — what API was accessed (e.g., Microsoft Graph)

## Risk Events & Identity Protection

### List Risk Detections

```python
risks = await graph_client.identity_protection.risk_detections.get()
for risk in risks.value:
    print(f"{risk.detected_date_time} | {risk.risk_event_type} | "
          f"User: {risk.user_display_name} | Level: {risk.risk_level}")
```

### List Risky Users

```python
risky_users = await graph_client.identity_protection.risky_users.get()
for user in risky_users.value:
    print(f"{user.user_display_name} | Risk: {user.risk_level} | State: {user.risk_state}")
```

### Common Risk Event Types

| Risk Type | Source | Description |
|-----------|--------|-------------|
| `unfamiliarFeatures` | Offline | Sign-in with unfamiliar properties |
| `anonymizedIPAddress` | Real-time | Sign-in from anonymous IP (Tor, VPN) |
| `maliciousIPAddress` | Offline | Sign-in from known malicious IP |
| `leakedCredentials` | Offline | Credentials found in breach database |
| `impossibleTravel` | Offline | Sign-ins from geographically distant locations |
| `anomalousToken` | Real-time | Unusual token characteristics |
| `tokenIssuerAnomaly` | Offline | Unusual token issuer pattern |

## KQL Patterns (Azure Monitor / Log Analytics)

When logs are streamed to Log Analytics workspace, use KQL:

### Failed Sign-Ins by Location

```kql
SigninLogs
| where TimeGenerated > ago(24h)
| where ResultType != "0"
| summarize FailedCount = count() by Location, AppDisplayName
| order by FailedCount desc
| take 20
```

### Service Principal Activity

```kql
AADServicePrincipalSignInLogs
| where TimeGenerated > ago(7d)
| summarize SignInCount = count(), 
    DistinctResources = dcount(ResourceDisplayName)
    by ServicePrincipalName, AppId
| order by SignInCount desc
```

### Agent Identity Activity

```kql
AADServicePrincipalSignInLogs
| where TimeGenerated > ago(24h)
| where AppDisplayName contains "Blueprint"  // Agent Identity blueprint apps
| project TimeGenerated, ServicePrincipalName, ResourceDisplayName, 
    IPAddress, Location, ConditionalAccessStatus
| order by TimeGenerated desc
```

### Credential Changes (Audit)

```kql
AuditLogs
| where TimeGenerated > ago(30d)
| where OperationName has_any ("Update application", "Certificates and secrets")
| project TimeGenerated, OperationName, 
    InitiatedBy = tostring(InitiatedBy.app.displayName),
    TargetApp = tostring(TargetResources[0].displayName)
| order by TimeGenerated desc
```

### CA Policy Impact (Report-Only)

```kql
SigninLogs
| where TimeGenerated > ago(7d)
| mv-expand ConditionalAccessPolicies
| where ConditionalAccessPolicies.result == "reportOnlyFailure"
| summarize BlockedCount = count() by 
    PolicyName = tostring(ConditionalAccessPolicies.displayName),
    AppDisplayName
| order by BlockedCount desc
```

## Pagination for Large Result Sets

```python
all_sign_ins = []
response = await graph_client.audit_logs.sign_ins.get(
    request_configuration=config
)
while response:
    if response.value:
        all_sign_ins.extend(response.value)
    if response.odata_next_link:
        response = await graph_client.audit_logs.sign_ins.with_url(
            response.odata_next_link
        ).get()
    else:
        break
```

## Common Investigation Scenarios

| Scenario | Approach |
|----------|----------|
| Who added a secret to an app? | Audit logs: `activityDisplayName eq 'Update application – Certificates and secrets management'` |
| Why was a user blocked? | Sign-in logs: filter by user, check `conditionalAccessStatus` and `status/errorCode` |
| Is an app over-privileged? | List `appRoleAssignments` + `oauth2PermissionGrants` on its service principal |
| Agent acting on graph? | Service principal sign-in logs filtered by agent's SP ID |
| Impossible travel detection | Risk detections: `riskEventType eq 'impossibleTravel'` |
| Stale service principals | SP sign-in logs: find SPs with no sign-ins in 90 days |

## Security Considerations

- **Audit logs retain 30 days** in Entra ID (stream to Log Analytics for longer retention)
- Sign-in logs require **P1 license**; risk events require **P2**
- **Don't log PII** unnecessarily — use `$select` to limit returned properties
- **Monitor emergency access accounts** — any sign-in is an alert condition
- **Stream logs to Log Analytics** for KQL analysis and longer retention

## Cross-References

- **→ `entra-conditional-access`** — CA policy evaluation results in sign-in logs
- **→ `entra-agent-id`** — Agent Identity sign-ins in service principal logs
- **→ `entra-secret-certificate-lifecycle`** — Credential changes in audit logs
- **→ `entra-app-registration`** — App registration changes in audit logs
- **→ `entra-users-groups`** — User and group changes in audit logs
