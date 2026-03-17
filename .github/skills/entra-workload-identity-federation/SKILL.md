---
name: entra-workload-identity-federation
description: "Workload Identity Federation — cross-cloud federation (AWS/GCP→Azure), GitHub Actions OIDC, Kubernetes WIF, trust policy configuration, claim mapping, security boundaries."
---

# Entra Workload Identity Federation

> **Status:** Phase 2 — New skill

## Scope

- Federated identity credential concept (trust external IdP instead of secrets)
- GitHub Actions OIDC federation (most common scenario)
- Kubernetes workload identity (AKS + non-AKS)
- Cross-cloud federation: AWS IAM → Azure, GCP → Azure
- Trust policy configuration: issuer, subject, audience
- Claim mapping and validation
- Security boundaries and threat model
- Migration path: secrets → federated credentials

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| Create federated credential | `POST /applications/{id}/federatedIdentityCredentials` | `Application.ReadWrite.All` |
| List federated credentials | `GET /applications/{id}/federatedIdentityCredentials` | `Application.Read.All` |
| Delete federated credential | `DELETE /applications/{id}/federatedIdentityCredentials/{id}` | `Application.ReadWrite.All` |

## TODO

- [ ] Full SKILL.md content
- [ ] GitHub Actions OIDC: complete workflow YAML + federated cred setup
- [ ] AKS workload identity: pod identity → workload identity migration
- [ ] AWS → Azure federation step-by-step
- [ ] GCP → Azure federation step-by-step
- [ ] Security: claim validation rules, allowed subject patterns
- [ ] Acceptance criteria + test scenarios

## Cross-References

- **Depends on:** `entra-app-registration` (app must exist before adding federated cred)
- **Related:** `entra-managed-identity` (user-assigned MI can use federated creds)
- **See also:** `entra-secret-certificate-lifecycle` (WIF as alternative to secrets)
