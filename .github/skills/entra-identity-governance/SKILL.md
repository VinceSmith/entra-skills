---
name: entra-identity-governance
description: "Entra ID Identity Governance — access reviews, entitlement management, lifecycle workflows, Privileged Identity Management (PIM), terms of use via Microsoft Graph."
---

# Entra Identity Governance

Identity Governance enforces the identity lifecycle — ensuring the right people have the right access at the right time, and that access is reviewed and revoked when no longer needed. It spans access reviews, entitlement management (access packages), lifecycle workflows (joiner/mover/leaver), Privileged Identity Management (PIM), and terms of use.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List access review definitions | `GET /identityGovernance/accessReviews/definitions` | `AccessReview.Read.All` |
| Create access review | `POST /identityGovernance/accessReviews/definitions` | `AccessReview.ReadWrite.All` |
| List review decisions | `GET /identityGovernance/accessReviews/definitions/{id}/instances/{id}/decisions` | `AccessReview.Read.All` |
| Record decision | `PATCH /identityGovernance/accessReviews/definitions/{id}/instances/{id}/decisions/{id}` | `AccessReview.ReadWrite.All` |
| List catalogs | `GET /identityGovernance/entitlementManagement/catalogs` | `EntitlementManagement.Read.All` |
| Create access package | `POST /identityGovernance/entitlementManagement/accessPackages` | `EntitlementManagement.ReadWrite.All` |
| List assignments | `GET /identityGovernance/entitlementManagement/assignments` | `EntitlementManagement.Read.All` |
| List lifecycle workflows | `GET /identityGovernance/lifecycleWorkflows/workflows` | `LifecycleWorkflows.Read.All` |
| Create lifecycle workflow | `POST /identityGovernance/lifecycleWorkflows/workflows` | `LifecycleWorkflows.ReadWrite.All` |
| PIM — list eligible roles | `GET /roleManagement/directory/roleEligibilityScheduleInstances` | `RoleEligibilitySchedule.Read.Directory` |
| PIM — activate role | `POST /roleManagement/directory/roleAssignmentScheduleRequests` | `RoleAssignmentSchedule.ReadWrite.Directory` |
| PIM — list role policies | `GET /policies/roleManagementPolicies` | `RoleManagementPolicy.Read.Directory` |
| PIM for Groups — list eligibility | `GET /identityGovernance/privilegedAccess/group/eligibilityScheduleInstances` | `PrivilegedEligibilitySchedule.Read.AzureADGroup` |
| List agreements (ToU) | `GET /identityGovernance/termsOfUse/agreements` | `Agreement.Read.All` |
| Create agreement | `POST /identityGovernance/termsOfUse/agreements` | `Agreement.ReadWrite.All` |

## Access Reviews

Create recurring reviews to verify group memberships, app role assignments, access packages, or Entra role assignments.

### Create a Quarterly Group Membership Review

```python
from azure.identity.aio import DefaultAzureCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.access_review_schedule_definition import AccessReviewScheduleDefinition
from msgraph.generated.models.access_review_scope import AccessReviewScope
from msgraph.generated.models.access_review_reviewer_scope import AccessReviewReviewerScope
from msgraph.generated.models.access_review_schedule_settings import AccessReviewScheduleSettings
from msgraph.generated.models.patterned_recurrence import PatternedRecurrence
from msgraph.generated.models.recurrence_pattern import RecurrencePattern
from msgraph.generated.models.recurrence_range import RecurrenceRange
import datetime

credential = DefaultAzureCredential()
scopes = ["https://graph.microsoft.com/.default"]
graph_client = GraphServiceClient(credential, scopes)

review = AccessReviewScheduleDefinition(
    display_name="Quarterly review — Finance team membership",
    scope=AccessReviewScope(
        odata_type="#microsoft.graph.accessReviewQueryScope",
        query=f"/groups/<group-id>/members",
        query_type="MicrosoftGraph",
    ),
    reviewers=[
        AccessReviewReviewerScope(
            query="/groups/<group-id>/owners",
            query_type="MicrosoftGraph",
        ),
    ],
    settings=AccessReviewScheduleSettings(
        mail_notifications_enabled=True,
        reminder_notifications_enabled=True,
        default_decision="Deny",  # Auto-deny if reviewer doesn't act
        auto_apply_decisions_enabled=True,
        instance_duration_in_days=14,
        recurrence=PatternedRecurrence(
            pattern=RecurrencePattern(type="absoluteMonthly", interval=3),
            range=RecurrenceRange(
                type="noEnd",
                start_date=datetime.date(2026, 4, 1),
            ),
        ),
    ),
)
result = await graph_client.identity_governance.access_reviews.definitions.post(review)
```

### List Pending Decisions for a Review Instance

```python
decisions = await (
    graph_client.identity_governance
    .access_reviews.definitions.by_access_review_schedule_definition_id("<definition-id>")
    .instances.by_access_review_instance_id("<instance-id>")
    .decisions.get()
)
for d in decisions.value:
    print(f"{d.principal.display_name}: {d.decision} (reviewed by: {d.reviewed_by.display_name})")
```

### Record a Decision (Approve/Deny)

```python
from msgraph.generated.models.access_review_instance_decision_item import AccessReviewInstanceDecisionItem

decision_update = AccessReviewInstanceDecisionItem(
    decision="Approve",  # or "Deny"
    justification="Verified: user still requires access for Q2 project.",
)
await (
    graph_client.identity_governance
    .access_reviews.definitions.by_access_review_schedule_definition_id("<definition-id>")
    .instances.by_access_review_instance_id("<instance-id>")
    .decisions.by_access_review_instance_decision_item_id("<decision-id>")
    .patch(decision_update)
)
```

## Entitlement Management

Package resources (groups, apps, SharePoint sites) into access packages with approval policies and automatic expiry.

### Create a Catalog and Access Package

```python
from msgraph.generated.models.access_package_catalog import AccessPackageCatalog
from msgraph.generated.models.access_package import AccessPackage

# 1. Create catalog
catalog = AccessPackageCatalog(
    display_name="Engineering Resources",
    description="Access packages for engineering team resources",
    is_externally_visible=False,
)
catalog_result = await graph_client.identity_governance.entitlement_management.catalogs.post(catalog)

# 2. Create access package in catalog
package = AccessPackage(
    display_name="Engineering — DevOps Tools",
    description="Grants access to DevOps tool suite and related groups",
    catalog=AccessPackageCatalog(id=catalog_result.id),
)
package_result = await graph_client.identity_governance.entitlement_management.access_packages.post(package)
```

### Create an Assignment Policy with Approval

```python
from msgraph.generated.models.access_package_assignment_policy import AccessPackageAssignmentPolicy
from msgraph.generated.models.approval_settings import ApprovalSettings
from msgraph.generated.models.approval_stage import ApprovalStage
from msgraph.generated.models.subject_set import SubjectSet

policy = AccessPackageAssignmentPolicy(
    display_name="Manager approval — 90 day expiry",
    access_package_id=package_result.id,
    expiration=ExpirationPattern(duration="P90D", type="afterDuration"),
    request_approval_settings=ApprovalSettings(
        is_approval_required=True,
        stages=[
            ApprovalStage(
                approval_stage_time_out_in_days=7,
                is_escalation_enabled=False,
                primary_approvers=[
                    SubjectSet(
                        odata_type="#microsoft.graph.requestorManager",
                        manager_level=1,
                    ),
                ],
            ),
        ],
    ),
)
await graph_client.identity_governance.entitlement_management.assignment_policies.post(policy)
```

## Lifecycle Workflows

Automate identity lifecycle tasks — joiner, mover, and leaver events triggered by user attributes (e.g., `employeeHireDate`, `employeeLeaveDateTime`).

### Create a Joiner Workflow

```python
from msgraph.generated.models.identity_governance.workflow import Workflow
from msgraph.generated.models.identity_governance.trigger_and_scope_based_conditions import TriggerAndScopeBasedConditions
from msgraph.generated.models.identity_governance.rule_based_subject_set import RuleBasedSubjectSet
from msgraph.generated.models.identity_governance.time_based_attribute_trigger import TimeBasedAttributeTrigger
from msgraph.generated.models.identity_governance.task import Task

workflow = Workflow(
    display_name="Onboard new hire — Engineering",
    category="joiner",
    is_enabled=True,
    is_scheduling_enabled=True,
    execution_conditions=TriggerAndScopeBasedConditions(
        scope=RuleBasedSubjectSet(
            rule='(department eq "Engineering")',
        ),
        trigger=TimeBasedAttributeTrigger(
            time_based_attribute="employeeHireDate",
            offset_in_days=-1,  # 1 day before hire date
        ),
    ),
    tasks=[
        Task(
            is_enabled=True,
            display_name="Enable user account",
            task_definition_id="6fc52c9d-398b-4305-9763-15f42c1676fc",  # enableUserAccount
        ),
        Task(
            is_enabled=True,
            display_name="Add to Engineering group",
            task_definition_id="22085229-5809-45e8-97fd-270d28d66910",  # addUserToGroup
            arguments=[
                {"name": "groupID", "value": "<engineering-group-id>"},
            ],
        ),
        Task(
            is_enabled=True,
            display_name="Generate Temporary Access Pass",
            task_definition_id="e5c16509-1432-4a26-a6d4-e1a8cd5f1f64",  # generateTAP
            arguments=[
                {"name": "tapLifetimeMinutes", "value": "480"},
                {"name": "tapIsUsableOnce", "value": "true"},
            ],
        ),
        Task(
            is_enabled=True,
            display_name="Send welcome email",
            task_definition_id="aab41899-9972-422a-9d97-f626014578b7",  # sendEmail
        ),
    ],
)
result = await graph_client.identity_governance.lifecycle_workflows.workflows.post(workflow)
```

### Create a Leaver Workflow

```python
leaver = Workflow(
    display_name="Offboard departing employee",
    category="leaver",
    is_enabled=True,
    is_scheduling_enabled=True,
    execution_conditions=TriggerAndScopeBasedConditions(
        scope=RuleBasedSubjectSet(rule='(department ne null)'),
        trigger=TimeBasedAttributeTrigger(
            time_based_attribute="employeeLeaveDateTime",
            offset_in_days=0,  # On leave date
        ),
    ),
    tasks=[
        Task(
            is_enabled=True,
            display_name="Remove from all groups",
            task_definition_id="1953a66c-751c-45e5-8bfe-01462c70da3c",
        ),
        Task(
            is_enabled=True,
            display_name="Disable user account",
            task_definition_id="1dfdfcc7-52fa-4c2e-bf3a-e3919cc12950",
        ),
    ],
)
await graph_client.identity_governance.lifecycle_workflows.workflows.post(leaver)
```

## Privileged Identity Management (PIM)

PIM provides just-in-time (JIT) privileged access via eligible role assignments that require activation.

### List Eligible Role Assignments

```python
eligible = await graph_client.role_management.directory.role_eligibility_schedule_instances.get()
for e in eligible.value:
    print(f"Role: {e.role_definition.display_name}, Principal: {e.principal.display_name}")
```

### Activate an Eligible Role (Self-Activate)

```python
from msgraph.generated.models.unified_role_assignment_schedule_request import UnifiedRoleAssignmentScheduleRequest
from msgraph.generated.models.request_schedule import RequestSchedule
from msgraph.generated.models.expiration_pattern import ExpirationPattern

activation = UnifiedRoleAssignmentScheduleRequest(
    action="selfActivate",
    principal_id="<user-object-id>",
    role_definition_id="<role-definition-id>",
    directory_scope_id="/",
    justification="Incident #INC-4521: investigating permissions issue",
    schedule_info=RequestSchedule(
        expiration=ExpirationPattern(
            type="afterDuration",
            duration="PT4H",  # 4-hour activation window
        ),
    ),
)
await graph_client.role_management.directory.role_assignment_schedule_requests.post(activation)
```

### Create an Eligible Assignment (Admin)

```python
from msgraph.generated.models.unified_role_eligibility_schedule_request import UnifiedRoleEligibilityScheduleRequest

eligibility = UnifiedRoleEligibilityScheduleRequest(
    action="adminAssign",
    principal_id="<user-object-id>",
    role_definition_id="<role-definition-id>",  # e.g., User Administrator
    directory_scope_id="/",
    justification="Approved in access request ticket #REQ-1234",
    schedule_info=RequestSchedule(
        expiration=ExpirationPattern(
            type="afterDateTime",
            end_date_time=datetime.datetime(2026, 9, 30, tzinfo=datetime.timezone.utc),
        ),
    ),
)
await graph_client.role_management.directory.role_eligibility_schedule_requests.post(eligibility)
```

## .NET Example: List Access Review Definitions

```csharp
var reviews = await graphClient.IdentityGovernance.AccessReviews.Definitions.GetAsync();
foreach (var review in reviews.Value)
{
    Console.WriteLine($"{review.DisplayName} — Status: {review.Status}");
}
```

## .NET Example: Activate PIM Role

```csharp
var activation = new UnifiedRoleAssignmentScheduleRequest
{
    Action = UnifiedRoleScheduleRequestActions.SelfActivate,
    PrincipalId = "<user-object-id>",
    RoleDefinitionId = "<role-definition-id>",
    DirectoryScopeId = "/",
    Justification = "Incident triage — need elevated access",
    ScheduleInfo = new RequestSchedule
    {
        Expiration = new ExpirationPattern
        {
            Type = ExpirationPatternType.AfterDuration,
            Duration = TimeSpan.FromHours(4),
        },
    },
};
await graphClient.RoleManagement.Directory.RoleAssignmentScheduleRequests.PostAsync(activation);
```

## Terms of Use

Track acceptance of organizational agreements as a prerequisite for access.

```python
agreements = await graph_client.identity_governance.terms_of_use.agreements.get()
for a in agreements.value:
    print(f"{a.display_name} — Created: {a.created_date_time}")
```

## Security Considerations

- **Least-privilege reviewers** — Assign group owners or managers as reviewers, not Global Admins
- **Auto-apply deny** — Set `defaultDecision` to `Deny` so unreviewed access is revoked automatically
- **Time-bound assignments** — Use PIM eligible assignments with expiry; avoid permanent privileged roles
- **Justification required** — Enforce justification on PIM activations and access package requests
- **Separation of duties** — The person requesting access should not be the same person approving it
- **Audit all governance actions** — Access review decisions, PIM activations, and entitlement assignments are logged in Entra audit logs; review them regularly
- **Lifecycle workflow scoping** — Use precise ODATA filter rules to target only the intended user population
- **TAP security** — Temporary Access Passes generated by lifecycle workflows should be single-use and short-lived

## Cross-References

- **→ `entra-users-groups`** — Target groups for access reviews; group membership managed by entitlement management
- **→ `entra-app-registration`** — App role assignments reviewable via access reviews
- **→ `azure-rbac`** — PIM for Azure resource roles (separate from PIM for Entra roles)
- **→ `entra-conditional-access`** — Require access review completion as a CA grant control; require ToU acceptance
- **→ `entra-audit-signin-logs`** — Audit trail for governance decisions (review outcomes, PIM activations, workflow executions)
- **→ `entra-authentication-methods`** — Temporary Access Pass (TAP) generation in lifecycle joiner workflows
