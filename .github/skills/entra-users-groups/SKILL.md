---
name: entra-users-groups
description: "Entra ID user and group management — CRUD operations, group memberships, dynamic groups, nested groups, B2B guest users, bulk operations via Microsoft Graph."
---

# Entra Users & Groups

User and group lifecycle management via Microsoft Graph. Covers member users, B2B guests, security groups, Microsoft 365 groups, dynamic membership, nested groups, and bulk/batch operations.

## Key APIs

| Operation | Endpoint | Permission |
|-----------|----------|------------|
| List users | `GET /users` | `User.Read.All` |
| Get user | `GET /users/{id}` | `User.Read.All` |
| Create user | `POST /users` | `User.ReadWrite.All` |
| Update user | `PATCH /users/{id}` | `User.ReadWrite.All` |
| Delete user | `DELETE /users/{id}` | `User.ReadWrite.All` |
| List groups | `GET /groups` | `Group.Read.All` |
| Create group | `POST /groups` | `Group.ReadWrite.All` |
| Get group members | `GET /groups/{id}/members` | `GroupMember.Read.All` |
| Add member | `POST /groups/{id}/members/$ref` | `GroupMember.ReadWrite.All` |
| Remove member | `DELETE /groups/{id}/members/{id}/$ref` | `GroupMember.ReadWrite.All` |
| Check membership | `POST /users/{id}/checkMemberGroups` | `GroupMember.Read.All` |
| Invite guest | `POST /invitations` | `User.Invite.All` |
| List transitive members | `GET /groups/{id}/transitiveMembers` | `GroupMember.Read.All` |

## User Management

### Create a Member User (Python)

```python
from msgraph import GraphServiceClient
from msgraph.generated.models.user import User
from msgraph.generated.models.password_profile import PasswordProfile

user = User(
    account_enabled=True,
    display_name="Alex Johnson",
    mail_nickname="alexj",
    user_principal_name="alexj@contoso.onmicrosoft.com",
    password_profile=PasswordProfile(
        force_change_password_next_sign_in=True,
        password="xWwvJ]6NMw+bWH-d",  # Meets complexity requirements
    ),
)
result = await graph_client.users.post(user)
```

### Create a Member User (.NET)

```csharp
var user = new User
{
    AccountEnabled = true,
    DisplayName = "Alex Johnson",
    MailNickname = "alexj",
    UserPrincipalName = "alexj@contoso.onmicrosoft.com",
    PasswordProfile = new PasswordProfile
    {
        ForceChangePasswordNextSignIn = true,
        Password = "xWwvJ]6NMw+bWH-d",
    },
};
var result = await graphClient.Users.PostAsync(user);
```

### Query Users with Filters

```python
# Users in a specific department
from msgraph.generated.users.users_request_builder import UsersRequestBuilder

query = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
    filter="department eq 'Engineering'",
    select=["displayName", "mail", "jobTitle"],
    top=50,
    orderby=["displayName"],
)
config = UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
    query_parameters=query,
)
users = await graph_client.users.get(request_configuration=config)
```

### Disable / Enable User

```python
from msgraph.generated.models.user import User

# Disable
await graph_client.users.by_user_id(user_id).patch(
    User(account_enabled=False)
)
# Enable
await graph_client.users.by_user_id(user_id).patch(
    User(account_enabled=True)
)
```

## Group Management

### Group Types

| Type | `groupTypes` | `securityEnabled` | `mailEnabled` | Use Case |
|------|-------------|-------------------|---------------|----------|
| Security group | `[]` | `true` | `false` | RBAC, resource access |
| Microsoft 365 group | `["Unified"]` | `false` | `true` | Collaboration (Teams, SharePoint) |
| Mail-enabled security | `[]` | `true` | `true` | Distribution + access control |
| Dynamic security | `["DynamicMembership"]` | `true` | `false` | Auto-membership by rules |
| Dynamic M365 | `["Unified","DynamicMembership"]` | `false` | `true` | Auto-membership + collaboration |

### Create Security Group

```python
from msgraph.generated.models.group import Group

group = Group(
    display_name="SG-Engineering-ReadOnly",
    description="Read-only access for engineering team",
    mail_enabled=False,
    mail_nickname="sg-eng-readonly",
    security_enabled=True,
)
result = await graph_client.groups.post(group)
```

### Create Dynamic Group

```python
group = Group(
    display_name="DG-All-Engineers",
    description="Auto-populated: all users with Engineering department",
    group_types=["DynamicMembership"],
    mail_enabled=False,
    mail_nickname="dg-all-engineers",
    security_enabled=True,
    membership_rule="(user.department -eq \"Engineering\")",
    membership_rule_processing_state="On",
)
result = await graph_client.groups.post(group)
```

### Common Dynamic Membership Rules

| Scenario | Rule |
|----------|------|
| By department | `(user.department -eq "Engineering")` |
| By job title contains | `(user.jobTitle -contains "Manager")` |
| By company name | `(user.companyName -eq "Contoso")` |
| Members only (no guests) | `(user.userType -eq "Member")` |
| Guests only | `(user.userType -eq "Guest")` |
| By extension attribute | `(user.extensionAttribute1 -eq "ProjectX")` |
| Multiple conditions | `(user.department -eq "Engineering") -and (user.country -eq "US")` |

### Add / Remove Group Members

```python
from msgraph.generated.models.reference_create import ReferenceCreate

# Add member
ref = ReferenceCreate(
    odata_id=f"https://graph.microsoft.com/v1.0/directoryObjects/{user_id}",
)
await graph_client.groups.by_group_id(group_id).members.ref.post(ref)

# Remove member
await graph_client.groups.by_group_id(group_id).members.by_directory_object_id(user_id).ref.delete()
```

### Check Transitive Group Membership

```python
from msgraph.generated.users.item.check_member_groups.check_member_groups_post_request_body import (
    CheckMemberGroupsPostRequestBody,
)

body = CheckMemberGroupsPostRequestBody(
    group_ids=["group-id-1", "group-id-2", "group-id-3"],
)
result = await graph_client.users.by_user_id(user_id).check_member_groups.post(body)
# result.value contains IDs of groups the user belongs to (including nested)
```

## B2B Guest Users

### Invite External User

```python
from msgraph.generated.models.invitation import Invitation
from msgraph.generated.models.invited_user_message_info import InvitedUserMessageInfo

invitation = Invitation(
    invited_user_email_address="partner@fabrikam.com",
    invited_user_display_name="Partner User",
    invite_redirect_url="https://myapp.contoso.com",
    send_invitation_message=True,
    invited_user_message_info=InvitedUserMessageInfo(
        customized_message_body="Welcome to our collaboration portal.",
    ),
)
result = await graph_client.invitations.post(invitation)
guest_user_id = result.invited_user.id
```

### Filter Guest vs Member Users

```python
# List all guests
query = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
    filter="userType eq 'Guest'",
    select=["displayName", "mail", "createdDateTime"],
)
guests = await graph_client.users.get(
    request_configuration=UsersRequestBuilder.UsersRequestBuilderGetRequestConfiguration(
        query_parameters=query,
    )
)
```

## Bulk Operations (Batch API)

Use JSON batching for operations on many users/groups (up to 20 requests per batch):

```python
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
import httpx

# Build batch request (msgraph-sdk doesn't have native batch yet)
batch_body = {
    "requests": [
        {
            "id": "1",
            "method": "PATCH",
            "url": f"/users/{user_id_1}",
            "headers": {"Content-Type": "application/json"},
            "body": {"department": "Engineering"},
        },
        {
            "id": "2",
            "method": "PATCH",
            "url": f"/users/{user_id_2}",
            "headers": {"Content-Type": "application/json"},
            "body": {"department": "Engineering"},
        },
    ]
}
# POST to https://graph.microsoft.com/v1.0/$batch
```

## Pagination

Graph API returns pages of results. Always handle `@odata.nextLink`:

```python
users_response = await graph_client.users.get()
all_users = []

while users_response:
    if users_response.value:
        all_users.extend(users_response.value)
    if users_response.odata_next_link:
        users_response = await graph_client.users.with_url(
            users_response.odata_next_link
        ).get()
    else:
        break
```

## PII Handling

- **Never log** `userPrincipalName`, `mail`, `mobilePhone`, or `streetAddress` to shared logs
- **Use `$select`** to request only the properties you need — avoid fetching PII when not required
- **Mask in output**: When displaying user info to agents, redact email addresses and phone numbers unless the user explicitly requests them
- **Retention**: Do not cache user profile data beyond the current session

## Security Considerations

- Use `User.Read.All` (read) rather than `User.ReadWrite.All` unless writes are needed
- `GroupMember.ReadWrite.All` is a high-privilege permission — prefer per-group delegation if possible
- B2B guest invitations should be governed by external collaboration settings
- Dynamic group rules execute with directory-level access — validate rules before enabling

## Cross-References

- **→ `entra-app-registration`** — App needs User/Group permissions configured
- **→ `azure-rbac`** — Groups are common RBAC role assignment targets
- **→ `entra-admin-consent-permissions`** — Permission grants for user/group access
- **→ `entra-conditional-access`** — Target users/groups in CA policies
- **→ `entra-audit-signin-logs`** — User and group changes appear in audit logs
