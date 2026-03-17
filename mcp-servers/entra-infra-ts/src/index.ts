#!/usr/bin/env node
/**
 * Entra Infrastructure MCP Server
 *
 * Infrastructure-level Entra operations via Azure CLI wrappers.
 * Tools: managed identity, WIF, conditional access, secret lifecycle.
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const server = new McpServer({
  name: "Entra Infrastructure MCP Server",
  version: "0.1.0",
});

// --- Helpers ---

async function azCli(args: string[]): Promise<string> {
  const { stdout, stderr } = await execFileAsync("az", args, {
    timeout: 30_000,
  });
  if (stderr && !stdout) throw new Error(stderr);
  return stdout.trim();
}

async function azJson<T = unknown>(args: string[]): Promise<T> {
  const out = await azCli([...args, "-o", "json"]);
  return JSON.parse(out) as T;
}

// --- Managed Identity Tools ---

server.tool(
  "entra_create_user_assigned_mi",
  "Create a user-assigned managed identity",
  {
    name: z.string().describe("MI name (e.g. mi-myapp-prod)"),
    resourceGroup: z.string().describe("Resource group name"),
    location: z.string().default("eastus2").describe("Azure region"),
  },
  async ({ name, resourceGroup, location }) => {
    const result = await azJson<{ principalId: string; clientId: string; id: string }>([
      "identity", "create",
      "--name", name,
      "--resource-group", resourceGroup,
      "--location", location,
    ]);
    return {
      content: [{
        type: "text" as const,
        text: [
          `Created managed identity: ${name}`,
          `  Principal ID: ${result.principalId}`,
          `  Client ID: ${result.clientId}`,
          `  Resource ID: ${result.id}`,
        ].join("\n"),
      }],
    };
  }
);

server.tool(
  "entra_assign_mi_to_resource",
  "Assign a user-assigned managed identity to an Azure resource (App Service, Container App, VM)",
  {
    resourceType: z.enum(["webapp", "containerapp", "vm"]).describe("Type of Azure resource"),
    resourceName: z.string().describe("Resource name"),
    resourceGroup: z.string().describe("Resource group"),
    identityResourceId: z.string().describe("Full resource ID of the user-assigned MI"),
  },
  async ({ resourceType, resourceName, resourceGroup, identityResourceId }) => {
    const commands: Record<string, string[]> = {
      webapp: ["webapp", "identity", "assign", "--name", resourceName, "--resource-group", resourceGroup, "--identities", identityResourceId],
      containerapp: ["containerapp", "identity", "assign", "--name", resourceName, "--resource-group", resourceGroup, "--user-assigned", identityResourceId],
      vm: ["vm", "identity", "assign", "--name", resourceName, "--resource-group", resourceGroup, "--identities", identityResourceId],
    };
    await azCli(commands[resourceType]);
    return {
      content: [{
        type: "text" as const,
        text: `Assigned MI to ${resourceType} '${resourceName}' in ${resourceGroup}.`,
      }],
    };
  }
);

server.tool(
  "entra_configure_mi_rbac",
  "Assign an RBAC role to a managed identity",
  {
    principalId: z.string().describe("MI principal (object) ID"),
    role: z.string().describe("Role name or ID (e.g. 'Key Vault Secrets User')"),
    scope: z.string().describe("Azure scope (e.g. /subscriptions/{sub}/resourceGroups/{rg}/providers/...)"),
  },
  async ({ principalId, role, scope }) => {
    await azCli([
      "role", "assignment", "create",
      "--assignee-object-id", principalId,
      "--assignee-principal-type", "ServicePrincipal",
      "--role", role,
      "--scope", scope,
    ]);
    return {
      content: [{
        type: "text" as const,
        text: `Assigned role '${role}' to principal ${principalId} at scope ${scope}.`,
      }],
    };
  }
);

// --- WIF Tools ---

server.tool(
  "entra_create_federated_credential",
  "Create a federated identity credential on an app registration",
  {
    appObjectId: z.string().describe("Application object ID"),
    name: z.string().describe("Credential name (e.g. github-main-branch)"),
    issuer: z.string().describe("OIDC issuer URL (e.g. https://token.actions.githubusercontent.com)"),
    subject: z.string().describe("Subject claim (e.g. repo:org/repo:ref:refs/heads/main)"),
    description: z.string().default("").describe("Optional description"),
  },
  async ({ appObjectId, name, issuer, subject, description }) => {
    const params = JSON.stringify({
      name,
      issuer,
      subject,
      description: description || `Federated credential: ${name}`,
      audiences: ["api://AzureADTokenExchange"],
    });
    await azCli(["ad", "app", "federated-credential", "create", "--id", appObjectId, "--parameters", params]);
    return {
      content: [{
        type: "text" as const,
        text: [
          `Created federated credential '${name}' on app ${appObjectId}:`,
          `  Issuer: ${issuer}`,
          `  Subject: ${subject}`,
          `  Audience: api://AzureADTokenExchange`,
        ].join("\n"),
      }],
    };
  }
);

server.tool(
  "entra_list_federated_credentials",
  "List federated identity credentials for an app registration",
  {
    appObjectId: z.string().describe("Application object ID"),
  },
  async ({ appObjectId }) => {
    const creds = await azJson<Array<{ name: string; issuer: string; subject: string }>>(
      ["ad", "app", "federated-credential", "list", "--id", appObjectId]
    );
    if (!creds.length) {
      return { content: [{ type: "text" as const, text: "No federated credentials found." }] };
    }
    const lines = [`Found ${creds.length} federated credential(s):`];
    for (const c of creds) {
      lines.push(`- ${c.name}: issuer=${c.issuer}, subject=${c.subject}`);
    }
    return { content: [{ type: "text" as const, text: lines.join("\n") }] };
  }
);

server.tool(
  "entra_validate_wif_trust",
  "Validate an OIDC issuer by fetching its discovery document",
  {
    issuer: z.string().describe("OIDC issuer URL to validate"),
  },
  async ({ issuer }) => {
    const discoveryUrl = `${issuer.replace(/\/$/, "")}/.well-known/openid-configuration`;
    const resp = await fetch(discoveryUrl);
    if (!resp.ok) {
      return {
        content: [{
          type: "text" as const,
          text: `Failed to validate issuer: HTTP ${resp.status} from ${discoveryUrl}`,
        }],
      };
    }
    const doc = await resp.json() as { issuer: string; jwks_uri: string; subject_types_supported?: string[] };
    return {
      content: [{
        type: "text" as const,
        text: [
          `Issuer validated: ${doc.issuer}`,
          `JWKS URI: ${doc.jwks_uri}`,
          `Subject types: ${(doc.subject_types_supported || []).join(", ") || "N/A"}`,
        ].join("\n"),
      }],
    };
  }
);

// --- Conditional Access Tools ---

server.tool(
  "entra_list_ca_policies",
  "List Conditional Access policies (requires az ad signed-in user with Policy.Read.All)",
  {},
  async () => {
    const policies = await azJson<{ value: Array<{ displayName: string; state: string; id: string }> }>(
      ["rest", "--method", "GET", "--url", "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies"]
    );
    const value = policies.value;
    if (!value?.length) {
      return { content: [{ type: "text" as const, text: "No CA policies found." }] };
    }
    const lines = [`Found ${value.length} CA policy(ies):`];
    for (const p of value) {
      lines.push(`- ${p.displayName} [${p.state}] (id=${p.id})`);
    }
    return { content: [{ type: "text" as const, text: lines.join("\n") }] };
  }
);

server.tool(
  "entra_get_ca_policy",
  "Get details of a specific Conditional Access policy",
  {
    policyId: z.string().describe("CA policy ID"),
  },
  async ({ policyId }) => {
    const policy = await azJson<Record<string, unknown>>(
      ["rest", "--method", "GET", "--url", `https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies/${policyId}`]
    );
    return {
      content: [{
        type: "text" as const,
        text: JSON.stringify(policy, null, 2),
      }],
    };
  }
);

server.tool(
  "entra_create_ca_policy",
  "Create a Conditional Access policy in reportOnly state",
  {
    displayName: z.string().describe("Policy display name"),
    templateJson: z.string().describe("Policy JSON body (conditions + grantControls). State will be forced to reportOnly."),
  },
  async ({ displayName, templateJson }) => {
    const body = JSON.parse(templateJson);
    body.displayName = displayName;
    body.state = "reportOnly"; // Safety: always reportOnly

    const result = await azJson<{ id: string; displayName: string; state: string }>(
      ["rest", "--method", "POST",
       "--url", "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies",
       "--body", JSON.stringify(body)]
    );
    return {
      content: [{
        type: "text" as const,
        text: [
          `Created CA policy in reportOnly mode:`,
          `  Name: ${result.displayName}`,
          `  ID: ${result.id}`,
          `  State: ${result.state}`,
          `\nMonitor in sign-in logs for 1-2 weeks before enabling.`,
        ].join("\n"),
      }],
    };
  }
);

server.tool(
  "entra_what_if_ca",
  "Review CA what-if results from recent sign-in logs for a user",
  {
    userId: z.string().describe("User ID or UPN"),
  },
  async ({ userId }) => {
    const result = await azJson<{ value: Array<{ createdDateTime: string; conditionalAccessStatus: string; appliedConditionalAccessPolicies: Array<{ displayName: string; result: string }> }> }>(
      ["rest", "--method", "GET",
       "--url", `https://graph.microsoft.com/v1.0/auditLogs/signIns?$filter=userId eq '${userId}'&$top=5&$orderby=createdDateTime desc&$select=createdDateTime,conditionalAccessStatus,appliedConditionalAccessPolicies`]
    );
    if (!result.value?.length) {
      return { content: [{ type: "text" as const, text: "No recent sign-in data found." }] };
    }
    const lines = [`CA evaluation for ${userId} (last ${result.value.length} sign-ins):`];
    for (const s of result.value) {
      lines.push(`\n${s.createdDateTime} — CA: ${s.conditionalAccessStatus}`);
      for (const p of s.appliedConditionalAccessPolicies || []) {
        lines.push(`  Policy: ${p.displayName} → ${p.result}`);
      }
    }
    return { content: [{ type: "text" as const, text: lines.join("\n") }] };
  }
);

// --- Secret/Cert Lifecycle Tools ---

server.tool(
  "entra_scan_expiring_secrets",
  "Scan app registrations for secrets/certificates expiring within N days",
  {
    daysWarning: z.number().default(30).describe("Threshold in days (default 30)"),
  },
  async ({ daysWarning }) => {
    const apps = await azJson<Array<{
      displayName: string;
      appId: string;
      passwordCredentials: Array<{ displayName: string; endDateTime: string }>;
      keyCredentials: Array<{ displayName: string; endDateTime: string }>;
    }>>(["ad", "app", "list", "--all", "--query", "[].{displayName:displayName,appId:appId,passwordCredentials:passwordCredentials,keyCredentials:keyCredentials}"]);

    const now = Date.now();
    const threshold = now + daysWarning * 86400_000;
    const findings: string[] = [];

    for (const app of apps) {
      for (const c of app.passwordCredentials || []) {
        const exp = new Date(c.endDateTime).getTime();
        if (exp < threshold) {
          const status = exp < now ? "EXPIRED" : "EXPIRING SOON";
          findings.push(`[${status}] ${app.displayName} — secret '${c.displayName || "unnamed"}' expires ${c.endDateTime}`);
        }
      }
      for (const c of app.keyCredentials || []) {
        const exp = new Date(c.endDateTime).getTime();
        if (exp < threshold) {
          const status = exp < now ? "EXPIRED" : "EXPIRING SOON";
          findings.push(`[${status}] ${app.displayName} — cert '${c.displayName || "unnamed"}' expires ${c.endDateTime}`);
        }
      }
    }

    return {
      content: [{
        type: "text" as const,
        text: findings.length
          ? `Found ${findings.length} expiring credential(s):\n${findings.join("\n")}`
          : `No credentials expiring within ${daysWarning} days.`,
      }],
    };
  }
);

server.tool(
  "entra_rotate_secret",
  "Rotate a secret on an app registration (add new, return value, caller removes old)",
  {
    appObjectId: z.string().describe("Application object ID"),
    displayName: z.string().default("rotated").describe("Label for new secret"),
  },
  async ({ appObjectId, displayName }) => {
    const result = await azJson<{ secretText: string; keyId: string; endDateTime: string }>(
      ["ad", "app", "credential", "reset", "--id", appObjectId, "--display-name", displayName, "--append"]
    );
    return {
      content: [{
        type: "text" as const,
        text: [
          `New secret created for app ${appObjectId}:`,
          `  Key ID: ${result.keyId}`,
          `  Expires: ${result.endDateTime}`,
          `  Secret Value: ${result.secretText}`,
          ``,
          `WARNING: Store this secret in Key Vault immediately — it cannot be retrieved again.`,
          `After deploying the new secret, remove the old one.`,
        ].join("\n"),
      }],
    };
  }
);

server.tool(
  "entra_setup_keyvault_rotation",
  "Configure a Key Vault secret rotation notification policy",
  {
    vaultName: z.string().describe("Key Vault name"),
    secretName: z.string().describe("Secret name"),
    expiryDays: z.number().default(180).describe("Secret lifetime in days"),
    notifyBeforeDays: z.number().default(30).describe("Notify this many days before expiry"),
  },
  async ({ vaultName, secretName, expiryDays, notifyBeforeDays }) => {
    const policy = JSON.stringify({
      lifetimeActions: [{
        trigger: { timeBeforeExpiry: `P${notifyBeforeDays}D` },
        action: { type: "Notify" },
      }],
      attributes: { expiryTime: `P${expiryDays}D` },
    });

    await azCli([
      "keyvault", "secret", "rotation-policy", "update",
      "--vault-name", vaultName,
      "--name", secretName,
      "--value", policy,
    ]);
    return {
      content: [{
        type: "text" as const,
        text: `Rotation policy set for ${vaultName}/${secretName}: expires after ${expiryDays} days, notifies ${notifyBeforeDays} days before.`,
      }],
    };
  }
);

// --- Start server ---

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch(console.error);
