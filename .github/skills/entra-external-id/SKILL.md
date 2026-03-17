---
name: entra-external-id
description: "Entra External ID (CIAM) — customer identity and access management for consumer/partner-facing apps. Covers external tenant configuration, self-service signup user flows, social identity providers, API connectors, custom authentication extensions, B2B guest invitations, and native authentication. USE FOR: CIAM, external identity, customer-facing auth, self-service signup, social login, Google/Facebook/Apple sign-in, user flow creation, API connector, custom authentication extension, B2B invitation, native auth, external tenant. DO NOT USE FOR: workforce tenant user management (use entra-users-groups), managed identity (use entra-managed-identity), internal app registration (use entra-app-registration)."
---

# Entra External ID (CIAM)

Customer identity and access management (CIAM) for consumer-facing and partner-facing applications using Microsoft Entra External ID. This is the **modern replacement for Azure AD B2C** — built natively on the Microsoft Entra platform with first-class Graph API support, unified admin experience, and no separate tenant topology.

> **External ID vs legacy Azure AD B2C:** External ID uses standard Entra tenants (configured as "external" tenants) with native Graph API endpoints. Azure AD B2C uses separate B2C tenants with custom policies (XML) and different API surfaces. For **new projects**, always use External ID. B2C remains supported but is in maintenance mode.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List user flows | `GET /identity/authenticationEventsFlows` | `EventListener.Read.All` |
| Create user flow | `POST /identity/authenticationEventsFlows` | `EventListener.ReadWrite.All` |
| List identity providers | `GET /identity/identityProviders` | `IdentityProvider.Read.All` |
| Create identity provider | `POST /identity/identityProviders` | `IdentityProvider.ReadWrite.All` |
| List API connectors | `GET /identity/apiConnectors` | `APIConnectors.Read.All` |
| Create API connector | `POST /identity/apiConnectors` | `APIConnectors.ReadWrite.All` |
| List custom auth extensions | `GET /identity/customAuthenticationExtensions` | `CustomAuthenticationExtension.Read.All` |
| Create custom auth extension | `POST /identity/customAuthenticationExtensions` | `CustomAuthenticationExtension.ReadWrite.All` |
| Invite guest user | `POST /invitations` | `User.Invite.All` |
| Cross-tenant access settings | `GET /policies/crossTenantAccessPolicy` | `Policy.Read.All` |
| Update cross-tenant access | `PATCH /policies/crossTenantAccessPolicy/partners/{id}` | `Policy.ReadWrite.CrossTenantAccess` |
| List custom user attributes | `GET /identity/userFlowAttributes` | `IdentityUserFlow.Read.All` |
| Create custom user attribute | `POST /identity/userFlowAttributes` | `IdentityUserFlow.ReadWrite.All` |

## External Tenant Configuration

### External vs Workforce Tenant

| Aspect | Workforce Tenant | External Tenant |
|--------|-----------------|-----------------|
| **Audience** | Employees, internal apps | Customers, partners, consumers |
| **User types** | Members (Entra ID users) | Self-service signups, social, local |
| **Branding** | Company portal | Fully customizable (logo, CSS, colors) |
| **User flows** | N/A | Self-service signup + sign-in |
| **Social IdPs** | Limited (B2B) | Google, Facebook, Apple, custom OIDC |
| **Native auth** | No | Email + password, email + OTP (mobile) |
| **Custom domain** | `*.onmicrosoft.com` or verified | Custom domain recommended for CIAM |

### Tenant Branding

Configure company branding for sign-in pages in the external tenant:

```python
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.organizational_branding_properties import (
    OrganizationalBrandingProperties,
)

credential = DefaultAzureCredential()
graph = GraphServiceClient(credential)

branding = OrganizationalBrandingProperties(
    sign_in_page_text="Welcome to Contoso Customer Portal",
    background_color="#f0f0f0",
    custom_css_relative_url=None,  # Upload CSS via PUT /branding/localizations/{locale}/customCSS
)
await graph.organization.by_organization_id(tenant_id).branding.patch(branding)
```

## User Flows (Self-Service Signup)

User flows define the self-service sign-up and sign-in experience. External ID uses the new `authenticationEventsFlows` API (not the legacy `b2xIdentityUserFlows`).

### Create a Self-Service Signup User Flow

```python
import json
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient

credential = DefaultAzureCredential()
graph = GraphServiceClient(credential)

# The typed SDK models may lag behind beta API — use request_body dict
# when targeting beta features for authenticationEventsFlows.
flow_body = {
    "@odata.type": "#microsoft.graph.externalUsersSelfServiceSignUpEventsFlow",
    "displayName": "Customer Signup",
    "description": "Self-service signup for customer portal",
    "conditions": {
        "applications": {
            "includeApplications": [
                {"appId": "YOUR_CIAM_APP_CLIENT_ID"}  # App registered in external tenant
            ]
        }
    },
    "onInteractiveAuthFlowStart": {
        "@odata.type": "#microsoft.graph.onInteractiveAuthFlowStartExternalUsersSelfServiceSignUp",
        "isSignUpAllowed": True,
    },
    "onAuthenticationMethodLoadStart": {
        "@odata.type": "#microsoft.graph.onAuthenticationMethodLoadStartExternalUsersSelfServiceSignUp",
        "identityProviders": [
            {"id": "EmailPassword-OAUTH"},
            {"id": "Google-OAUTH"},  # Must be pre-configured
        ],
    },
    "onAttributeCollection": {
        "@odata.type": "#microsoft.graph.onAttributeCollectionExternalUsersSelfServiceSignUp",
        "accessPackages": [],
        "attributeCollectionPage": {
            "customStringsFileId": None,
            "views": [
                {
                    "title": None,
                    "description": None,
                    "inputs": [
                        {"attribute": "email", "label": "Email", "inputType": "text", "required": True},
                        {"attribute": "displayName", "label": "Display Name", "inputType": "text", "required": True},
                        {"attribute": "city", "label": "City", "inputType": "text", "required": False},
                    ],
                }
            ],
        },
        "attributes": [
            {"id": "email", "displayName": "Email Address", "userFlowAttributeType": "builtIn"},
            {"id": "displayName", "displayName": "Display Name", "userFlowAttributeType": "builtIn"},
            {"id": "city", "displayName": "City", "userFlowAttributeType": "builtIn"},
        ],
    },
}

result = await graph.identity.authentication_events_flows.post(
    body=flow_body,  # type: ignore[arg-type]
)
print(f"Created user flow: {result.id}")  # noqa: T201
```

> **Permissions required:** `EventListener.ReadWrite.All` (application)

### Custom User Attributes

```python
from msgraph.generated.models.identity_user_flow_attribute import (
    IdentityUserFlowAttribute,
    IdentityUserFlowAttributeDataType,
    IdentityUserFlowAttributeType,
)

custom_attr = IdentityUserFlowAttribute(
    display_name="Loyalty Tier",
    description="Customer loyalty program tier",
    data_type=IdentityUserFlowAttributeDataType.String,
    user_flow_attribute_type=IdentityUserFlowAttributeType.Custom,
)
result = await graph.identity.user_flow_attributes.post(custom_attr)
```

## Social Identity Providers

### Configure Google as Social IdP

```python
from msgraph.generated.models.social_identity_provider import SocialIdentityProvider

google_idp = SocialIdentityProvider(
    display_name="Google",
    identity_provider_type="Google",
    client_id=os.environ["GOOGLE_CLIENT_ID"],  # From Google Cloud Console
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],  # Never hardcode
)
result = await graph.identity.identity_providers.post(google_idp)
print(f"Configured Google IdP: {result.id}")  # noqa: T201
```

### Configure Facebook

```python
facebook_idp = SocialIdentityProvider(
    display_name="Facebook",
    identity_provider_type="Facebook",
    client_id=os.environ["FACEBOOK_APP_ID"],
    client_secret=os.environ["FACEBOOK_APP_SECRET"],
)
result = await graph.identity.identity_providers.post(facebook_idp)
```

### Configure Apple ID

```python
from msgraph.generated.models.apple_managed_identity_provider import (
    AppleManagedIdentityProvider,
)

apple_idp = AppleManagedIdentityProvider(
    display_name="Sign in with Apple",
    development_team_id=os.environ["APPLE_TEAM_ID"],
    service_id=os.environ["APPLE_SERVICE_ID"],
    key_id=os.environ["APPLE_KEY_ID"],
    certificate_data=os.environ["APPLE_CERTIFICATE_DATA"],  # Base64-encoded .p8 key
)
result = await graph.identity.identity_providers.post(apple_idp)
```

### Supported Identity Providers

| Provider | `identityProviderType` | Notes |
|----------|----------------------|-------|
| Google | `Google` | Requires Google Cloud OAuth consent screen |
| Facebook | `Facebook` | Requires Facebook for Developers app |
| Apple | `AppleManaged` | Requires Apple Developer account + service ID |
| Generic OIDC | `OpenIdConnect` | Any OIDC-compliant provider |
| Generic SAML | `Saml` | Enterprise federation |

## API Connectors

Inject custom logic during the sign-up flow — validate data, enrich user attributes, or block sign-up.

### Create an API Connector

```python
from msgraph.generated.models.identity_api_connector import IdentityApiConnector
from msgraph.generated.models.api_authentication_configuration_base import (
    ApiAuthenticationConfigurationBase,
)
from msgraph.generated.models.basic_authentication import BasicAuthentication

connector = IdentityApiConnector(
    display_name="Validate Domain Connector",
    target_url="https://my-api.azurewebsites.net/api/validate-signup",
    authentication_configuration=BasicAuthentication(
        odata_type="#microsoft.graph.basicAuthentication",
        username=os.environ["CONNECTOR_USERNAME"],
        password=os.environ["CONNECTOR_PASSWORD"],  # Store in Key Vault
    ),
)
result = await graph.identity.api_connectors.post(connector)
print(f"Created connector: {result.id}")  # noqa: T201
```

> **Security:** Use HTTPS endpoints only. Prefer certificate-based auth or managed identity for production. Store connector credentials in Azure Key Vault.

## Custom Authentication Extensions

Extend sign-up/sign-in flows with Azure Functions-backed logic for token enrichment, attribute validation, and custom blocking rules.

### Events

| Event | Trigger | Use Case |
|-------|---------|----------|
| `onTokenIssuanceStart` | Before token is issued | Add custom claims to tokens |
| `onAttributeCollectionStart` | Before attribute page shown | Pre-fill or hide attributes |
| `onAttributeCollectionSubmit` | After user submits attributes | Validate, enrich, or block |

### Create a Custom Authentication Extension (.NET)

```csharp
// Azure Function: token issuance start event handler
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.AuthenticationEvents.TokenIssuanceStart;
using Microsoft.Extensions.Logging;

public class CustomClaimsProvider
{
    private readonly ILogger<CustomClaimsProvider> _logger;

    public CustomClaimsProvider(ILogger<CustomClaimsProvider> logger) => _logger = logger;

    [Function("onTokenIssuanceStart")]
    public async Task<TokenIssuanceStartResponse> Run(
        [HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequestData req,
        [TokenIssuanceStartInput] TokenIssuanceStartRequest tokenRequest)
    {
        _logger.LogInformation("Token issuance event for {User}", tokenRequest.Payload.UserId);

        var response = new TokenIssuanceStartResponse();
        response.Actions.Add(new ProvideClaimsForToken
        {
            Claims = new Dictionary<string, string>
            {
                { "loyaltyTier", "Gold" },
                { "apiAccess", "premium" },
            }
        });
        return response;
    }
}
```

### Register the Extension in Graph (Python)

```python
extension_body = {
    "@odata.type": "#microsoft.graph.onTokenIssuanceStartCustomExtension",
    "displayName": "Add loyalty claims",
    "description": "Enriches tokens with customer loyalty data",
    "endpointConfiguration": {
        "@odata.type": "#microsoft.graph.httpRequestEndpoint",
        "targetUrl": "https://my-functions.azurewebsites.net/api/onTokenIssuanceStart",
    },
    "authenticationConfiguration": {
        "@odata.type": "#microsoft.graph.azureAdTokenAuthentication",
        "resourceId": "api://my-functions.azurewebsites.net",
    },
    "claimsForTokenConfiguration": [
        {"claimIdInApiResponse": "loyaltyTier"},
        {"claimIdInApiResponse": "apiAccess"},
    ],
}

result = await graph.identity.custom_authentication_extensions.post(
    body=extension_body,  # type: ignore[arg-type]
)
```

> **Permissions required:** `CustomAuthenticationExtension.ReadWrite.All` (application)

## B2B Guest Users

B2B invitation remains the model for inviting external business partners. For detailed user/group CRUD, see **→ `entra-users-groups`**.

### Invite a B2B Guest User

```python
from msgraph.generated.models.invitation import Invitation
from msgraph.generated.models.invited_user_message_info import InvitedUserMessageInfo

invitation = Invitation(
    invited_user_email_address="partner@fabrikam.com",
    invite_redirect_url="https://myapp.contoso.com",
    invited_user_display_name="Dana Fabrikam",
    send_invitation_message=True,
    invited_user_message_info=InvitedUserMessageInfo(
        customized_message_body="Welcome to the Contoso partner portal!",
    ),
)
result = await graph.invitations.post(invitation)
print(f"Invited user: {result.invited_user.id}")  # noqa: T201
```

### Cross-Tenant Access Settings

```python
# Read current cross-tenant access policy
policy = await graph.policies.cross_tenant_access_policy.get()

# Configure partner-specific settings
from msgraph.generated.models.cross_tenant_access_policy_configuration_partner import (
    CrossTenantAccessPolicyConfigurationPartner,
)

partner = CrossTenantAccessPolicyConfigurationPartner(
    tenant_id="fabrikam-tenant-id",
    b2b_collaboration_inbound=None,  # Configure as needed
)
await graph.policies.cross_tenant_access_policy.partners.post(partner)
```

### B2B Direct Connect

B2B direct connect enables users from partner tenants to access shared resources (e.g., Teams shared channels) without guest account creation. Configure via cross-tenant access settings with `b2bDirectConnectInbound` / `b2bDirectConnectOutbound` policies.

## Native Authentication (Mobile/Desktop CIAM Apps)

Native authentication enables password and OTP flows directly in your mobile app's UI — no browser redirect required. Available **only in External ID tenants**.

### Supported Methods

| Method | Flow | Platform Support |
|--------|------|-----------------|
| Email + password | Sign-up & sign-in | Android (MSAL), iOS (MSAL) |
| Email + OTP | Sign-up & sign-in | Android (MSAL), iOS (MSAL) |

### Enable Native Auth on App Registration

1. Register app in the **external tenant** (→ `entra-app-registration`)
2. Under **Authentication** → **Advanced settings**, enable **Allow public client flows**
3. Add platform: **Mobile and desktop applications**
4. Enable native authentication under the app's authentication settings

### MSAL Native Auth (Android — Kotlin)

```kotlin
// build.gradle: implementation 'com.microsoft.identity.client:msal:5.+'
val nativeAuthConfig = NativeAuthPublicClientApplicationConfiguration(
    clientId = "YOUR_CLIENT_ID",
    authorities = listOf("https://YOUR_TENANT.ciamlogin.com/YOUR_TENANT.onmicrosoft.com"),
    challengeTypes = listOf(ChallengeType.OOB, ChallengeType.PASSWORD),
)

// Sign up with email + password
val signUpResult = nativeAuthClient.signUp(
    username = "user@example.com",
    password = "securePassword123!".toCharArray(),
)
```

### Authority Format

External ID tenants use a **CIAM-specific authority**:
```
https://{tenant-name}.ciamlogin.com/{tenant-name}.onmicrosoft.com
```

This differs from workforce (`login.microsoftonline.com`) and legacy B2C (`{tenant}.b2clogin.com`).

## Security Considerations

- **Rate limiting:** External-facing sign-up flows are targets for abuse. Enable Azure WAF or API Management in front of API connectors.
- **Bot protection:** Enable CAPTCHA integration via custom authentication extensions on the attribute collection submit event.
- **Input validation:** Always validate and sanitize attribute values in API connectors before writing to the directory.
- **Credential storage:** Social IdP client secrets and API connector credentials must be stored in Azure Key Vault — never in source code or app settings.
- **Conditional Access:** Apply CA policies to external users to enforce MFA, block risky sign-ins, or restrict by location (→ `entra-conditional-access`).
- **Token claims:** Validate custom claims added by authentication extensions — consumers of tokens must not blindly trust enriched claims.

## Cross-References

- **→ `entra-app-registration`** — Register CIAM apps in the external tenant
- **→ `entra-msal-deep-dive`** — MSAL native auth libraries, CIAM authority format, B2C migration
- **→ `entra-conditional-access`** — CA policies targeting external / guest users
- **→ `entra-users-groups`** — B2B guest user CRUD, group membership for external users
- **→ `entra-admin-consent-permissions`** — Permission grants for CIAM app registrations
- **→ `entra-audit-signin-logs`** — Sign-in logs for external users, risk detection
