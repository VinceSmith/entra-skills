# Entra Graph MCP Server (Python/FastMCP)

Live tools for coding agents to manage Entra identities via Microsoft Graph.

## Tools

### User & Group Tools (Step 3.2)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_users` | Search/filter Entra users | No |
| `entra_get_user` | Get user profile by ID or UPN | No |
| `entra_list_groups` | Search/filter Entra groups | No |
| `entra_get_group_members` | List group members | No |
| `entra_add_group_member` | Add user to group | Yes (confirmation) |
| `entra_remove_group_member` | Remove user from group | Yes (confirmation) |

### App Registration Tools (Step 3.3)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_apps` | Search/filter app registrations | No |
| `entra_get_app` | App details by ID or display name | No |
| `entra_list_app_permissions` | Configured API permissions | No |
| `entra_check_credential_expiry` | Secret/cert expiry check | No |
| `entra_create_app_registration` | Guided app creation | Yes (confirmation) |

### Identity Diagnostics Tools (Step 3.4)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_get_signin_logs` | Query sign-in logs | No |
| `entra_get_audit_logs` | Query audit logs | No |
| `entra_check_user_risk` | Identity protection risk status | No |
| `entra_evaluate_conditional_access` | What-if CA evaluation | No |

### RBAC Tools (Step 3.5)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_role_assignments` | Role assignments for a principal | No |
| `entra_find_role` | Least-privilege role for an action | No |
| `entra_assign_role` | Assign role to principal | Yes (confirmation) |

### Agent Identity Tools (Step 3.6)
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_create_agent_blueprint` | Create Agent Identity Blueprint | Yes (confirmation) |
| `entra_create_agent_identity` | Provision agent from blueprint | Yes (confirmation) |
| `entra_get_agent_token` | Token exchange (autonomous/OBO) | No |

### Identity Governance Tools
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_access_reviews` | List access review definitions | No |
| `entra_create_access_review` | Create access review | Yes (confirmation) |
| `entra_list_access_packages` | List entitlement access packages | No |
| `entra_list_lifecycle_workflows` | List lifecycle workflows | No |
| `entra_list_pim_role_assignments` | List eligible PIM roles | No |
| `entra_activate_pim_role` | Activate PIM role | Yes (confirmation) |

### ID Protection & Auth Methods Tools
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_risk_detections` | List risk detections | No |
| `entra_confirm_user_compromised` | Confirm user compromised | Yes (confirmation) |
| `entra_dismiss_user_risk` | Dismiss user risk | Yes (confirmation) |
| `entra_list_risky_service_principals` | List risky service principals | No |
| `entra_list_user_auth_methods` | List user auth methods | No |
| `entra_create_temporary_access_pass` | Create TAP for user | Yes (confirmation) |

### Workload Identity Tools
| Tool | Description | Write? |
|------|-------------|--------|
| `entra_list_service_principals` | Search/filter service principals | No |
| `entra_get_sp_permissions` | SP permissions inventory | No |
| `entra_find_stale_service_principals` | Find inactive SPs | No |
| `entra_workload_identity_posture` | Workload identity posture scan | No |

## Auth

- `azure-identity` `DefaultAzureCredential` (dev: Azure CLI, prod: managed identity)
- Configurable mode: `ENTRA_MCP_MODE=read-only` or `ENTRA_MCP_MODE=full`

## Setup

```bash
pip install -e .
```

## Usage

```bash
# Read-only mode (safe for exploration)
ENTRA_MCP_MODE=read-only python -m entra_graph_mcp

# Full mode (all tools including write operations)
ENTRA_MCP_MODE=full python -m entra_graph_mcp
```
