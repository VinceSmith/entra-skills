# Entra Infrastructure MCP Server (TypeScript/MCP SDK)

Infrastructure-level Entra operations via Azure CLI wrappers, distributable via npx.

## Tools

### Managed Identity Tools (Step 4.2)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_create_user_assigned_mi` | Create user-assigned managed identity | Yes (confirmation) |
| `entra_assign_mi_to_resource` | Assign MI to Azure resource | Yes (confirmation) |
| `entra_configure_mi_rbac` | Assign RBAC roles to MI | Yes (confirmation) |

### WIF Tools (Step 4.3)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_create_federated_credential` | Create federated identity credential | Yes (confirmation) |
| `entra_list_federated_credentials` | List WIF configurations | No |
| `entra_validate_wif_trust` | Validate OIDC issuer trust chain | No |

### Conditional Access Tools (Step 4.4)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_ca_policies` | List CA policies | No |
| `entra_get_ca_policy` | Policy details | No |
| `entra_create_ca_policy` | Create from template | Yes (confirmation) |
| `entra_what_if_ca` | What-if evaluation | No |

### Secret/Cert Lifecycle Tools (Step 4.5)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_scan_expiring_secrets` | Scan apps for approaching expiry | No |
| `entra_rotate_secret` | Rotate a secret | Yes (confirmation) |
| `entra_setup_keyvault_rotation` | Configure Key Vault auto-rotation | Yes (confirmation) |

## Setup

```bash
npm install
npm run build
```

## Usage

```bash
# Run directly
npx entra-infra-mcp

# Or via MCP config
# Add to .copilot/mcp-config.json or .vscode/mcp.json
```
