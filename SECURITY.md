# Security model

## Trust boundary

The assistant is a read-only decision-support component. It may collect entitlement metadata and employee context, but it is not authorized to grant, revoke, approve, deny, or submit access changes.

The only output that resembles an action is plain-text content for a Service Desk request. The manager must review it and use an approved organizational channel. ICT or Service Desk remains responsible for validation and implementation.

## Authorization rule

The requester must be the employee's direct manager in both AD and Entra ID. The comparison must be made server-side from trusted, freshly collected directory data.

- Match in both sources: continue.
- Missing manager in either source: deny.
- Conflicting managers: deny.
- Requester-supplied manager claim without directory verification: deny.

This relationship check is necessary but not sufficient for production. The application must also enforce authentication, tenant boundaries, approved manager roles, audit logging, and appropriate Graph/AD permissions.

## Main risks and controls

| Risk | Control |
| --- | --- |
| Excessive API permissions | Use a lab tenant, read-only access, and documented least-privilege scopes. |
| Unauthorized employee lookup | Require a server-side direct-manager match in both AD and Entra ID and fail closed on disagreement. |
| Sensitive identity data exposure | Minimize attributes, avoid production data in development, redact exports, and keep tokens out of logs. |
| Hallucinated recommendations | Ground every finding in structured evidence and retain deterministic rules as the baseline. |
| Biased or incorrect group suggestions | Use approved access profiles, show matching attributes, and require ICT validation. Do not learn profiles directly from unreviewed peer access. |
| Incorrect access change | Provide text drafts only. Do not add write permissions, remediation calls, or automatic ticket submission. |
| Prompt injection in metadata | Treat names and descriptions as untrusted data and never interpret them as instructions. |
| Stale manager or expiry data | Show collection time in live reports and re-check authorization for each request. |
| Credential leakage | Use environment variables or a secret store; never commit credentials or tenant-specific secrets. |

## Planned live integration

Before enabling a live connection:

1. Register a separate application in a lab tenant.
2. Identify the minimum delegated permissions for the signed-in manager workflow.
3. Read the target employee's manager relationship from Entra ID and AD through trusted backend adapters.
4. Deny access unless both sources identify the signed-in requester as the direct manager.
5. Keep all connectors read-only and omit access-change and ticket-submission APIs.
6. Record authorization result, source collection time, and report access without logging tokens or unnecessary personal data.
7. Test conflicting manager records, missing objects, guests, disabled accounts, nested membership, expired accounts, and throttling.

Exact permissions will be selected during the lab-integration phase because they depend on the final delegated workflow and resource types.

## Reporting a security issue

Do not open a public issue containing credentials, tenant identifiers, employee information, or access data. Use the repository owner's private contact channel instead.



## Optional local model boundary

The evidence-ordering adapter is opt-in, fixed to loopback, and does not use
HTTP proxies or follow redirects. It has no tool definitions, retry loop, or
write integration. Output must contain each server-issued evidence ID exactly
once. The UI uses textContent, not model-generated HTML. Directory text remains
untrusted: malicious text could influence ordering, but cannot become a new
finding or remove evidence through this output contract. The full report remains
visible. IDs are report-local references, not persistent identity IDs.

Ollama must independently be configured for local-only operation. Rejecting model
names containing `cloud` is only an extra guard, not a guarantee about a local
service's behavior. Use synthetic data. This demo still has no authenticated login;
typing a matching manager ID is a simulated relationship check, not authentication.
Do not expose it as a production service.
