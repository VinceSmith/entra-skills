---
name: entra-authentication-methods
description: "Entra ID authentication methods management — per-user method lifecycle, tenant-wide method policies, authentication strengths, Temporary Access Pass, FIDO2/passkeys, registration campaigns, SSPR, and combined security info via Microsoft Graph."
---

# Entra Authentication Methods

Manage the full lifecycle of authentication methods in Microsoft Entra ID — enumerate and register per-user methods, configure tenant-wide method policies, define authentication strengths for Conditional Access, issue Temporary Access Passes for onboarding/recovery, and drive registration campaigns. All operations use Microsoft Graph.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List user methods | `GET /users/{id}/authentication/methods` | `UserAuthenticationMethod.Read.All` |
| List phone methods | `GET /users/{id}/authentication/phoneMethods` | `UserAuthenticationMethod.Read.All` |
| Add phone method | `POST /users/{id}/authentication/phoneMethods` | `UserAuthenticationMethod.ReadWrite.All` |
| Delete phone method | `DELETE /users/{id}/authentication/phoneMethods/{id}` | `UserAuthenticationMethod.ReadWrite.All` |
| List FIDO2 keys | `GET /users/{id}/authentication/fido2Methods` | `UserAuthenticationMethod.Read.All` |
| Delete FIDO2 key | `DELETE /users/{id}/authentication/fido2Methods/{id}` | `UserAuthenticationMethod.ReadWrite.All` |
| List Authenticator app | `GET /users/{id}/authentication/microsoftAuthenticatorMethods` | `UserAuthenticationMethod.Read.All` |
| List software OATH | `GET /users/{id}/authentication/softwareOathMethods` | `UserAuthenticationMethod.Read.All` |
| List email methods | `GET /users/{id}/authentication/emailMethods` | `UserAuthenticationMethod.Read.All` |
| Windows Hello keys | `GET /users/{id}/authentication/windowsHelloForBusinessMethods` | `UserAuthenticationMethod.Read.All` |
| Create TAP | `POST /users/{id}/authentication/temporaryAccessPassMethods` | `UserAuthenticationMethod.ReadWrite.All` |
| Get methods policy | `GET /policies/authenticationMethodsPolicy` | `Policy.Read.All` |
| Update methods policy | `PATCH /policies/authenticationMethodsPolicy` | `Policy.ReadWrite.AuthenticationMethod` |
| Update method config | `PATCH /policies/authenticationMethodsPolicy/authenticationMethodConfigurations/{id}` | `Policy.ReadWrite.AuthenticationMethod` |
| List auth strengths | `GET /identity/conditionalAccess/authenticationStrength/policies` | `Policy.Read.All` |
| Create auth strength | `POST /identity/conditionalAccess/authenticationStrength/policies` | `Policy.ReadWrite.AuthenticationMethod` |
| Registration campaign | `PATCH /policies/authenticationMethodsPolicy` (registrationEnforcement) | `Policy.ReadWrite.AuthenticationMethod` |

## Per-User Authentication Methods

### List All Methods for a User

```python
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient

credential = DefaultAzureCredential()
graph_client = GraphServiceClient(credential)

methods = await graph_client.users.by_user_id(
    "user@contoso.com"
).authentication.methods.get()

for method in methods.value:
    print(f"{method.odata_type} — {method.id}")
```

### List Specific Method Types

```python
# Phone methods
phones = await graph_client.users.by_user_id(
    user_id
).authentication.phone_methods.get()

# FIDO2 security keys
fido2 = await graph_client.users.by_user_id(
    user_id
).authentication.fido2_methods.get()

# Microsoft Authenticator
authenticator = await graph_client.users.by_user_id(
    user_id
).authentication.microsoft_authenticator_methods.get()

# Windows Hello for Business
whfb = await graph_client.users.by_user_id(
    user_id
).authentication.windows_hello_for_business_methods.get()

# Software OATH tokens
oath = await graph_client.users.by_user_id(
    user_id
).authentication.software_oath_methods.get()
```

## Temporary Access Pass (TAP)

TAP is a time-limited passcode for onboarding (passwordless bootstrapping), account recovery, or when a user loses their primary method. Can be one-time or multi-use.

### Create a TAP

```python
from msgraph.generated.models.temporary_access_pass_authentication_method import (
    TemporaryAccessPassAuthenticationMethod,
)

tap = TemporaryAccessPassAuthenticationMethod(
    lifetime_in_minutes=60,       # Default 60, range 10–43200
    is_usable_once=True,          # One-time use (recommended)
)

result = await graph_client.users.by_user_id(
    "new-employee@contoso.com"
).authentication.temporary_access_pass_methods.post(tap)

# The TAP value is ONLY available in the creation response
print(f"TAP: {result.temporary_access_pass}")
print(f"Expires: {result.created_date_time}")
```

> **CRITICAL:** The `temporary_access_pass` value is returned **only once** in the creation response. Store or deliver it securely immediately.

## Authentication Methods Policy

The tenant-wide policy controls which methods are available and to whom.

### Read Current Policy

```python
policy = await graph_client.policies.authentication_methods_policy.get()

for config in policy.authentication_method_configurations:
    print(f"{config.odata_type}: state={config.state}")
```

### Configure FIDO2 Policy

```python
from msgraph.generated.models.fido2_authentication_method_configuration import (
    Fido2AuthenticationMethodConfiguration,
)
from msgraph.generated.models.authentication_method_target import (
    AuthenticationMethodTarget,
)
from msgraph.generated.models.authentication_method_target_type import (
    AuthenticationMethodTargetType,
)

fido2_config = Fido2AuthenticationMethodConfiguration(
    odata_type="#microsoft.graph.fido2AuthenticationMethodConfiguration",
    state="enabled",
    is_attestation_enforced=False,
    key_restrictions=None,  # Or configure allowed AAGUIDs
    include_targets=[
        AuthenticationMethodTarget(
            id="<security-group-id>",          # Target a pilot group
            target_type=AuthenticationMethodTargetType.Group,
        ),
    ],
)

await graph_client.policies.authentication_methods_policy.authentication_method_configurations.by_authentication_method_configuration_id(
    "Fido2"
).patch(fido2_config)
```

### Enable Registration Campaign (Nudge)

Push users to register a specific method (e.g., Microsoft Authenticator):

```python
from msgraph.generated.models.authentication_methods_policy import (
    AuthenticationMethodsPolicy,
)
from msgraph.generated.models.registration_enforcement import RegistrationEnforcement
from msgraph.generated.models.authentication_methods_registration_campaign import (
    AuthenticationMethodsRegistrationCampaign,
)
from msgraph.generated.models.authentication_methods_registration_campaign_include_target import (
    AuthenticationMethodsRegistrationCampaignIncludeTarget,
)

campaign_policy = AuthenticationMethodsPolicy(
    registration_enforcement=RegistrationEnforcement(
        authentication_methods_registration_campaign=AuthenticationMethodsRegistrationCampaign(
            state="enabled",
            include_targets=[
                AuthenticationMethodsRegistrationCampaignIncludeTarget(
                    id="all_users",
                    target_type="group",
                    targeted_authentication_method="microsoftAuthenticator",
                ),
            ],
        ),
    ),
)

await graph_client.policies.authentication_methods_policy.patch(campaign_policy)
```

## Authentication Strengths

Authentication strengths define which method combinations satisfy a Conditional Access grant control. Built-in strengths: **MFA**, **Passwordless MFA**, **Phishing-resistant MFA**.

### List Authentication Strengths

```python
strengths = await (
    graph_client.identity.conditional_access
    .authentication_strength.policies.get()
)

for s in strengths.value:
    print(f"{s.display_name} (built-in={s.policy_type == 'builtIn'})")
    for combo in s.allowed_combinations:
        print(f"  - {combo}")
```

### Create Custom Authentication Strength

```python
from msgraph.generated.models.authentication_strength_policy import (
    AuthenticationStrengthPolicy,
)

custom_strength = AuthenticationStrengthPolicy(
    display_name="Hardware key or Authenticator push",
    description="Requires FIDO2 key or Authenticator push notification",
    allowed_combinations=[
        "fido2",
        "microsoftAuthenticatorPush,federatedMultiFactor",
        "microsoftAuthenticatorPush,federatedSingleFactor",
    ],
)

result = await (
    graph_client.identity.conditional_access
    .authentication_strength.policies.post(custom_strength)
)
print(f"Created strength: {result.id}")
```

## SSPR & Combined Registration

Self-Service Password Reset (SSPR) and MFA registration are unified through **combined security info registration** (`https://aka.ms/mysecurityinfo`). Users register once for both SSPR and MFA.

Key signals via Graph:
- `GET /reports/authenticationMethods/userRegistrationDetails` — per-user registration status
- `GET /reports/authenticationMethods/usersRegisteredByMethod` — aggregate counts by method

```python
# Per-user registration details (requires UserAuthenticationMethod.Read.All)
details = await graph_client.reports.authentication_methods.user_registration_details.get()

for user in details.value:
    print(
        f"{user.user_display_name}: "
        f"MFA={user.is_mfa_registered}, "
        f"SSPR={user.is_sspr_registered}, "
        f"methods={user.methods_registered}"
    )
```

## .NET Example — List User Methods

```csharp
using Azure.Identity;
using Microsoft.Graph;

var credential = new DefaultAzureCredential();
var graphClient = new GraphServiceClient(credential);

var methods = await graphClient.Users["user@contoso.com"]
    .Authentication.Methods
    .GetAsync();

foreach (var method in methods.Value)
{
    Console.WriteLine($"{method.ODataType} — {method.Id}");
}
```

## Security Considerations

- **Least privilege** — Use `UserAuthenticationMethod.Read.All` for reporting; only escalate to `ReadWrite.All` for provisioning workflows
- **TAP handling** — The TAP value is a credential; transmit via secure channel (e.g., encrypted email, in-person), never log it
- **Pilot with groups** — Enable new methods for a security group before tenant-wide rollout
- **Phishing-resistant preferred** — Prioritize FIDO2/passkeys and Windows Hello over SMS/phone
- **Disable weak methods** — Turn off SMS sign-in and voice call where possible; keep SMS only for SSPR fallback if required
- **Registration campaigns** — Use nudge to accelerate migration away from legacy methods
- **Never hardcode credentials** — Always use `DefaultAzureCredential` or managed identity
- **Audit method changes** — Monitor `Update user authentication method` events in audit logs

## Cross-References

- **→ `entra-conditional-access`** — Authentication strengths are used in CA grant controls to require specific method types
- **→ `entra-users-groups`** — Target groups for method policies and registration campaigns
- **→ `entra-msal-deep-dive`** — Claims challenge / step-up authentication when CA demands a stronger method
- **→ `entra-audit-signin-logs`** — Audit log events for method registration, deletion, and TAP usage
- **→ `entra-secret-certificate-lifecycle`** — TAP as an alternative to temporary passwords during onboarding
