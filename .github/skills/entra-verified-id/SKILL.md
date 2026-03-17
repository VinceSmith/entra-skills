---
name: entra-verified-id
description: "Entra Verified ID (decentralized identity / verifiable credentials) — authority setup, credential contracts, issuance via Request Service REST API, presentation/verification, revocation, face check. USE FOR: verifiable credentials, decentralized identity, DID, issue credential, verify credential, VerifiedEmployee, credential contract, presentation request, Verified ID authority. DO NOT USE FOR: app registrations (use entra-app-registration), managed identity (use entra-managed-identity), RBAC (use azure-rbac)."
---

# Entra Verified ID

Issue and verify decentralized identity credentials using Microsoft Entra Verified ID. Covers authority configuration, credential contracts, issuance flows, presentation/verification, and revocation via the Request Service REST API and Microsoft Graph.

> **Important:** Issuance and presentation use the **Verified ID Request Service REST API** (`https://verifiedid.did.msidentity.com/v1.0/`), not the Graph SDK. Authority and contract management use **Microsoft Graph beta** (`/beta/verifiableCredentials/`).

## Key APIs

| Operation | Endpoint | Permission / Auth |
|-----------|----------|-------------------|
| Create authority | `POST /beta/verifiableCredentials/authorities` | `VerifiableCredentials.Create.All` (Graph) |
| Get authority | `GET /beta/verifiableCredentials/authorities/{id}` | `VerifiableCredentials.Create.All` (Graph) |
| Linked domain verification | `POST /beta/verifiableCredentials/authorities/{id}/didInfo/generateWellknownDidConfiguration` | `VerifiableCredentials.Create.All` (Graph) |
| Create contract | `POST /beta/verifiableCredentials/authorities/{id}/contracts` | `VerifiableCredentials.Create.All` (Graph) |
| List contracts | `GET /beta/verifiableCredentials/authorities/{id}/contracts` | `VerifiableCredentials.Create.All` (Graph) |
| Issue credential | `POST /verifiedid/v1.0/verifiableCredentials/createIssuanceRequest` | Access token (app credential) |
| Verify credential | `POST /verifiedid/v1.0/verifiableCredentials/createPresentationRequest` | Access token (app credential) |
| Revoke credential | `POST /beta/verifiableCredentials/authorities/{id}/contracts/{id}/revoke` | `VerifiableCredentials.Create.All` (Graph) |

## Prerequisites

1. **Entra ID P2 tenant** with Verified ID service enabled
2. **App registration** with `VerifiableCredentials.Create.All` permission (→ `entra-app-registration`)
3. **Azure Key Vault** for DID key storage (Verified ID authority keys)
4. **Linked domain** — public domain with DID configuration hosted at `/.well-known/did-configuration.json`

## Authority Setup

### Create a Verified ID Authority (Graph)

```python
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient

credential = DefaultAzureCredential()
scopes = ["https://graph.microsoft.com/.default"]
graph_client = GraphServiceClient(credential, scopes)

# Create authority with web DID method
authority_body = {
    "name": "Contoso",
    "linkedDomainUrl": "https://contoso.com",
    "didMethod": "web",
    "keyVaultMetadata": {
        "subscriptionId": os.environ["AZURE_SUBSCRIPTION_ID"],
        "resourceGroup": os.environ["KEY_VAULT_RG"],
        "resourceName": os.environ["KEY_VAULT_NAME"],
        "resourceUrl": f"https://{os.environ['KEY_VAULT_NAME']}.vault.azure.net/",
    },
}
authority = await graph_client.post(
    "/beta/verifiableCredentials/authorities",
    content=authority_body,
)
authority_id = authority["id"]
did = authority["didModel"]["did"]  # e.g., did:web:contoso.com
```

### Linked Domain Verification

```python
# Generate .well-known/did-configuration.json content
config_response = await graph_client.post(
    f"/beta/verifiableCredentials/authorities/{authority_id}"
    "/didInfo/generateWellknownDidConfiguration",
)
# Host the returned JSON at https://contoso.com/.well-known/did-configuration.json
did_configuration = config_response["value"]
```

## Credential Contracts

### Define a VerifiedEmployee Contract

```python
contract_body = {
    "name": "VerifiedEmployee",
    "displays": [
        {
            "locale": "en-US",
            "card": {
                "title": "Verified Employee",
                "issuedBy": "Contoso Ltd",
                "backgroundColor": "#2E4057",
                "textColor": "#FFFFFF",
                "logo": {"uri": "https://contoso.com/logo.png", "description": "Contoso logo"},
                "description": "Proof of employment at Contoso",
            },
            "claims": {
                "vc.credentialSubject.displayName": {"type": "String", "label": "Name"},
                "vc.credentialSubject.jobTitle": {"type": "String", "label": "Job Title"},
                "vc.credentialSubject.department": {"type": "String", "label": "Department"},
                "vc.credentialSubject.employeeId": {"type": "String", "label": "Employee ID"},
            },
        }
    ],
    "rules": {
        "attestations": {
            "idTokenHints": [
                {
                    "mapping": [
                        {"outputClaim": "displayName", "required": True, "inputClaim": "name", "indexed": False},
                        {"outputClaim": "jobTitle", "required": True, "inputClaim": "jobTitle", "indexed": False},
                        {"outputClaim": "department", "required": False, "inputClaim": "department", "indexed": False},
                        {"outputClaim": "employeeId", "required": True, "inputClaim": "employeeId", "indexed": True},
                    ],
                    "required": True,
                }
            ]
        },
        "validityInterval": 2592000,  # 30 days in seconds
        "vc": {"type": ["VerifiedEmployee"]},
    },
}
contract = await graph_client.post(
    f"/beta/verifiableCredentials/authorities/{authority_id}/contracts",
    content=contract_body,
)
contract_id = contract["id"]
manifest_url = contract["manifestUrl"]  # Used in issuance requests
```

## Issuance (Request Service REST API)

> Issuance uses the **Request Service REST API**, not the Graph SDK. Acquire an access token with scope `3db474b9-6a0c-4840-96ac-1fceb342124f/.default` (Verified ID Service resource).

### Issue a Credential

```python
import httpx
from azure.identity.aio import DefaultAzureCredential

credential = DefaultAzureCredential()
token = await credential.get_token("3db474b9-6a0c-4840-96ac-1fceb342124f/.default")

issuance_request = {
    "includeQRCode": True,
    "callback": {
        "url": os.environ["CALLBACK_URL"],  # Your publicly reachable endpoint
        "state": "unique-correlation-id",
        "headers": {"api-key": os.environ["CALLBACK_API_KEY"]},
    },
    "authority": did,  # did:web:contoso.com
    "registration": {"clientName": "Contoso Employee Portal"},
    "type": "VerifiedEmployee",
    "manifest": manifest_url,
    "claims": {
        "displayName": "Jane Smith",
        "jobTitle": "Software Engineer",
        "department": "Engineering",
        "employeeId": "EMP-12345",
    },
    "pin": {"length": 4, "value": "1234"},  # Optional: PIN protection
}

async with httpx.AsyncClient() as client:
    resp = await client.post(
        "https://verifiedid.did.msidentity.com/v1.0/verifiableCredentials/createIssuanceRequest",
        json=issuance_request,
        headers={"Authorization": f"Bearer {token.token}"},
    )
    resp.raise_for_status()
    result = resp.json()
    qr_code_url = result.get("qrCode")  # Display to user
    request_id = result["requestId"]     # Track issuance status
```

### Issuance Callback Handler

```python
# FastAPI example — receives issuance status updates
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/issuance-callback")
async def issuance_callback(request: Request):
    body = await request.json()
    state = body["state"]
    code = body["requestStatus"]

    if code == "issuance_successful":
        # Credential issued — update your records
        pass
    elif code == "issuance_error":
        error = body.get("error", {})
        # Handle error (user declined, timeout, etc.)
        pass
    return {"status": "ok"}
```

## Presentation / Verification (Request Service REST API)

### Verify a Credential

```python
presentation_request = {
    "includeQRCode": True,
    "callback": {
        "url": os.environ["CALLBACK_URL"],
        "state": "verification-session-id",
        "headers": {"api-key": os.environ["CALLBACK_API_KEY"]},
    },
    "authority": did,
    "registration": {"clientName": "Contoso Verification Portal"},
    "requestedCredentials": [
        {
            "type": "VerifiedEmployee",
            "purpose": "Verify employment status",
            "acceptedIssuers": [did],  # Only accept credentials from your authority
            "configuration": {"validation": {"allowRevoked": False, "validateLinkedDomain": True}},
        }
    ],
    # Optional: face check for liveness verification
    # "includeReceipt": True,
    # "requestedCredentials[0].constraints": {"faceCheck": {"sourcePhotoClaimName": "photo"}}
}

async with httpx.AsyncClient() as client:
    resp = await client.post(
        "https://verifiedid.did.msidentity.com/v1.0/verifiableCredentials/createPresentationRequest",
        json=presentation_request,
        headers={"Authorization": f"Bearer {token.token}"},
    )
    resp.raise_for_status()
    result = resp.json()
    qr_code_url = result.get("qrCode")
    request_id = result["requestId"]
```

### Presentation Callback Handler

```python
@app.post("/api/presentation-callback")
async def presentation_callback(request: Request):
    body = await request.json()
    code = body["requestStatus"]

    if code == "presentation_verified":
        # Extract verified claims
        claims = body["verifiedCredentialsData"][0]["claims"]
        display_name = claims.get("displayName")
        employee_id = claims.get("employeeId")
        issuer = body["verifiedCredentialsData"][0]["issuer"]
        # Proceed with verified identity
    elif code == "presentation_error":
        pass  # User declined or credential invalid
    return {"status": "ok"}
```

### Face Check (Liveness Verification)

```python
# Add faceCheck constraint to requestedCredentials
face_check_request = {
    **presentation_request,
    "requestedCredentials": [
        {
            "type": "VerifiedEmployee",
            "acceptedIssuers": [did],
            "configuration": {"validation": {"allowRevoked": False, "validateLinkedDomain": True}},
            "constraints": {
                "faceCheck": {
                    "sourcePhotoClaimName": "photo",
                    "matchConfidenceThreshold": 70,
                }
            },
        }
    ],
}
```

## Credential Revocation

```python
# Revoke a credential by indexed claim value
revoke_body = {"indexedClaimValue": "EMP-12345"}  # Must match an indexed claim

await graph_client.post(
    f"/beta/verifiableCredentials/authorities/{authority_id}"
    f"/contracts/{contract_id}/revoke",
    content=revoke_body,
)
```

## Common Scenarios

| Scenario | Credential Type | Issuance Trigger | Verification Point |
|----------|----------------|------------------|--------------------|
| Employee onboarding | VerifiedEmployee | HR system after hire | Internal apps, partner portals |
| B2B partner verification | VerifiedPartner | Partner org issues | Your supply chain portal |
| Education credentials | VerifiedDegree | University issues | Employer career portal |
| Age verification | VerifiedAge | Government-issued | Age-gated services |
| Skills certification | VerifiedSkill | Training platform | Hiring workflows |

## Security Considerations

1. **DID key management** — Keys are stored in Azure Key Vault; use RBAC (`Key Vault Crypto Officer`) to restrict access. Never export private keys.
2. **Callback endpoint security** — Always validate the `api-key` header on callbacks. Use HTTPS only. Never expose callback URLs publicly without authentication.
3. **Claim validation** — Verify `acceptedIssuers` to prevent credentials from untrusted authorities. Always set `allowRevoked: False` in production.
4. **PIN protection** — Use PIN for high-value issuance (e.g., employee credentials). Do not log or store PINs.
5. **Linked domain** — Keep `did-configuration.json` up to date. Domain ownership proves issuer authenticity.
6. **Revocation** — Index claims you may need to revoke by (e.g., `employeeId`). Check revocation status on every presentation.
7. **Token handling** — Access tokens for Request Service API are short-lived. Use `DefaultAzureCredential` — never hardcode secrets.

## Cross-References

- **`entra-app-registration`** — Register the app with `VerifiableCredentials.Create.All` permission and configure redirect URIs for the issuance/verification portal.
- **`entra-users-groups`** — Query user profile claims (displayName, jobTitle, department) to populate credential issuance via id_token_hint.
- **`entra-external-id`** — Integrate Verified ID presentation into CIAM sign-up/sign-in user flows for self-service identity proofing.
- **`entra-app-registration`** — The Verified ID service app needs client credentials for the Request Service REST API token acquisition.
- **`entra-identity-governance`** — Use verifiable credentials as proof in entitlement management access packages.
