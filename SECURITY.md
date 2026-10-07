# Security model

## Trust boundary

The assistant is a read-only decision-support component. It may collect entitlement metadata and employee context, but it is not authorized to grant, revoke, approve, or deny access.

## Main risks and controls

| Risk | Control |
| --- | --- |
| Excessive API permissions | Begin in a dedicated lab tenant, request read-only scopes, and document why each permission is needed. |
| Sensitive identity data exposure | Minimize collected attributes, avoid production data in development, redact exports, and keep logs free of tokens. |
| Hallucinated recommendations | Ground every finding in structured evidence and keep deterministic checks available as the baseline. |
| Incorrect access removal | Do not implement automatic remediation; require a human decision in the source system. |
| Prompt injection in metadata | Treat group names and descriptions as untrusted data; never interpret them as instructions. |
| Stale information | Show collection timestamps and source systems in future live reports. |
| Credential leakage | Use environment variables or a secret store; never commit credentials or tenant-specific secrets. |

## Planned Graph integration

Before enabling a live connection:

1. Register a separate application in a lab tenant.
2. Identify the minimum delegated or application permissions for the chosen workflow.
3. Prefer delegated access when a signed-in manager should only see data they are already authorized to view.
4. Add explicit authorization checks in the application; Graph permission alone is not the business authorization model.
5. Record consent, token audience, collection time, and data source in audit events without logging access tokens.
6. Test nested membership, missing objects, guest accounts, disabled accounts, and throttling behavior.

Exact permissions will be selected and documented during Phase 2 because they depend on whether the lab uses delegated or application access and which resource types are included.

## Reporting a security issue

Do not open a public issue containing credentials, tenant identifiers, or personal access data. Use the repository owner's private contact channel instead.
