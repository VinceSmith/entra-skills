---
name: entra-workload-identity-federation
description: "Workload Identity Federation — cross-cloud federation (AWS/GCP→Azure), GitHub Actions OIDC, Kubernetes WIF, trust policy configuration, claim mapping, security boundaries."
---

# Entra Workload Identity Federation

Workload Identity Federation (WIF) enables external workloads to authenticate to Azure without secrets. An external identity provider (GitHub, AWS, GCP, Kubernetes) issues a token, and Entra ID trusts that token via a configured federated credential. Auth hierarchy: MI → **WIF** → cert → secret.

## How It Works

1. External IdP issues a token (OIDC JWT) to the workload
2. Workload presents this token to Entra ID's token endpoint
3. Entra validates the token against the configured trust (issuer, subject, audience)
4. Entra issues an Azure AD token in exchange
5. Workload uses the Azure AD token to access Azure resources

No secrets stored, no rotation needed, no credential leakage risk.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| Create federated credential | `POST /applications/{id}/federatedIdentityCredentials` | `Application.ReadWrite.All` |
| List federated credentials | `GET /applications/{id}/federatedIdentityCredentials` | `Application.Read.All` |
| Get federated credential | `GET /applications/{id}/federatedIdentityCredentials/{id}` | `Application.Read.All` |
| Update federated credential | `PATCH /applications/{id}/federatedIdentityCredentials/{id}` | `Application.ReadWrite.All` |
| Delete federated credential | `DELETE /applications/{id}/federatedIdentityCredentials/{id}` | `Application.ReadWrite.All` |

**Limit:** 20 federated credentials per application registration.

## GitHub Actions OIDC Federation

The most common WIF scenario. Eliminates storing Azure credentials in GitHub secrets.

### Step 1: Create App Registration + Service Principal

```bash
az ad app create --display-name "github-deploy-myapp"
APP_ID=$(az ad app list --display-name "github-deploy-myapp" --query "[0].appId" -o tsv)
az ad sp create --id $APP_ID
```

### Step 2: Add Federated Credential

```bash
az ad app federated-credential create --id $APP_ID --parameters '{
  "name": "github-main-branch",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:myorg/myrepo:ref:refs/heads/main",
  "description": "Deploy from main branch",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

### Step 3: Assign RBAC Role

```bash
SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)
az role assignment create \
  --assignee-object-id $SP_ID \
  --assignee-principal-type ServicePrincipal \
  --role "Contributor" \
  --scope "/subscriptions/{sub-id}/resourceGroups/{rg-name}"
```

### Step 4: GitHub Actions Workflow

```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]

permissions:
  id-token: write   # Required for OIDC
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      - run: az group list
```

### GitHub Actions Subject Claim Patterns

| Scenario | Subject Format |
|----------|---------------|
| Specific branch | `repo:org/repo:ref:refs/heads/main` |
| Any branch | `repo:org/repo:ref:refs/heads/*` — **NOT SUPPORTED** (no wildcards in subject) |
| Pull request | `repo:org/repo:pull_request` |
| Specific tag | `repo:org/repo:ref:refs/tags/v1.0.0` |
| Environment | `repo:org/repo:environment:production` |
| Reusable workflow | `repo:org/repo:ref:refs/heads/main` (caller's claim) |

> **Use `environment` subjects for production deployments** — they require environment protection rules in GitHub.

## Kubernetes Workload Identity (AKS)

### Step 1: Enable OIDC Issuer on AKS

```bash
az aks update \
  --name aks-myapp \
  --resource-group rg-myapp \
  --enable-oidc-issuer \
  --enable-workload-identity

OIDC_ISSUER=$(az aks show --name aks-myapp --resource-group rg-myapp \
  --query "oidcIssuerProfile.issuerUrl" -o tsv)
```

### Step 2: Create User-Assigned MI + Federated Credential

```bash
az identity create --name mi-myapp-k8s --resource-group rg-myapp
MI_CLIENT_ID=$(az identity show --name mi-myapp-k8s --resource-group rg-myapp --query clientId -o tsv)

az identity federated-credential create \
  --name k8s-myapp-sa \
  --identity-name mi-myapp-k8s \
  --resource-group rg-myapp \
  --issuer "$OIDC_ISSUER" \
  --subject "system:serviceaccount:myapp-ns:myapp-sa" \
  --audiences "api://AzureADTokenExchange"
```

### Step 3: Annotate Kubernetes Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: myapp-ns
  annotations:
    azure.workload.identity/client-id: "<mi-client-id>"
  labels:
    azure.workload.identity/use: "true"
```

### Step 4: Use in Pod (SDK Auto-Detects)

```python
from azure.identity import DefaultAzureCredential

# WorkloadIdentityCredential is tried automatically by DefaultAzureCredential
# when AZURE_FEDERATED_TOKEN_FILE, AZURE_CLIENT_ID, AZURE_TENANT_ID are set
credential = DefaultAzureCredential()
```

## Cross-Cloud Federation

### AWS → Azure

```bash
# Federated credential for AWS STS
az ad app federated-credential create --id $APP_ID --parameters '{
  "name": "aws-account-123456",
  "issuer": "https://sts.amazonaws.com",
  "subject": "arn:aws:iam::123456789012:role/my-role",
  "description": "Trust AWS role in account 123456789012",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

AWS workload uses STS `AssumeRoleWithWebIdentity` → gets AWS token → exchanges for Azure AD token.

### GCP → Azure

```bash
az ad app federated-credential create --id $APP_ID --parameters '{
  "name": "gcp-project-myproject",
  "issuer": "https://accounts.google.com",
  "subject": "123456789012345678901",
  "description": "Trust GCP service account",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

## Bicep: Federated Credential on App Registration

```bicep
resource app 'Microsoft.Graph/applications@v1.0' = {
  displayName: 'github-deploy-myapp'
  uniqueName: 'github-deploy-myapp'

  resource federatedCredential 'federatedIdentityCredentials' = {
    name: 'github-main-branch'
    audiences: ['api://AzureADTokenExchange']
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:myorg/myrepo:environment:production'
    description: 'GitHub Actions production environment'
  }
}
```

## Bicep: Federated Credential on User-Assigned MI

```bicep
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'mi-myapp-k8s'
  location: resourceGroup().location
}

resource federatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: managedIdentity
  name: 'k8s-myapp-sa'
  properties: {
    issuer: aksCluster.properties.oidcIssuerProfile.issuerUrl
    subject: 'system:serviceaccount:myapp-ns:myapp-sa'
    audiences: ['api://AzureADTokenExchange']
  }
}
```

## Security Boundaries

| Rule | Rationale |
|------|-----------|
| **No wildcards in `subject`** | Prevent unauthorized workloads from impersonating trusted identities |
| **One subject per federated credential** | Audit trail clarity — know exactly which workload authenticated |
| **Use `environment` subjects for production** | GitHub environment protection rules add approval gates |
| **Validate `audiences`** | Always `api://AzureADTokenExchange` for Azure — reject other audiences |
| **20 credential limit per app** | Design around this — use separate app registrations per team/service if needed |
| **Monitor sign-in logs** | Federated auth appears in service principal sign-in logs — monitor for anomalies |

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `AADSTS70021: No matching federated identity record found` | Subject claim doesn't match | Verify the exact subject format (case-sensitive) |
| `AADSTS700016: Application not found in tenant` | Wrong tenant or app ID | Verify `AZURE_TENANT_ID` and `AZURE_CLIENT_ID` |
| `AADSTS700024: Client assertion is not within its valid time range` | Token expired or clock skew | Check token lifetime; ensure NTP sync |
| `AADSTS50027: Invalid JWT token` | Issuer mismatch | Verify the `issuer` URL matches the IdP exactly |

## Cross-References

- **→ `entra-app-registration`** — App must exist before adding federated credentials
- **→ `entra-managed-identity`** — User-assigned MI supports federated credentials
- **→ `azure-identity-py`** — `WorkloadIdentityCredential` for Python
- **→ `azure-identity-dotnet`** — `WorkloadIdentityCredential` for .NET
- **→ `entra-secret-certificate-lifecycle`** — WIF eliminates secrets entirely
- **→ `azure-rbac`** — Federated identity needs RBAC role assignments
