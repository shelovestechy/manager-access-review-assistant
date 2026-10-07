# Architecture

## Design goal

Manager Access Review Assistant gives a verified direct manager a consolidated, explainable access view without granting the application any path to change access.

The portfolio demo uses synthetic data, but its boundaries mirror the intended live design: identity collection, authorization, analysis, presentation, and organizational change processes remain separate.

## Components

| Component | Responsibility | Explicitly does not do |
| --- | --- | --- |
| Browser UI | Collect review inputs, display evidence, and let a manager select requested changes | Trust the claimed manager, call directory APIs, or submit tickets |
| Local HTTP layer | Validate input, apply security headers, and re-run authorization for every report or draft | Store sessions, expose a public listener by default, or call external systems |
| Repository loader | Parse and validate the synthetic identity snapshot | Mutate source data |
| Authorization check | Require the requester to match the direct manager in both AD and Entra ID | Treat a browser claim as proof or allow a partial match |
| Deterministic analyzer | Classify access, calculate expiry status, and match approved access profiles | Make an access decision or infer undocumented policy |
| Draft builder | Produce copyable Service Desk request text from explicit manager selections | Open a ticket or grant/revoke access |

## Review request flow

```text
1. Manager enters requester and employee IDs
2. Server loads trusted identity data
3. Server compares requester with AD direct manager
4. Server compares requester with Entra ID direct manager
5. Any missing/conflicting result -> HTTP 403, no report
6. Dual match -> deterministic analysis
7. Browser renders evidence and suggestions
```

The authorization check is repeated when a Service Desk draft is requested. A previously rendered browser report is not treated as authorization.

## Access-change request flow

```text
Manager selects candidate changes
              |
              v
Server re-verifies manager relationship
              |
              v
Plain-text draft is generated
              |
              v
Manager reviews and contacts ICT / Service Desk
              |
              v
ICT validates policy and implements in source system
```

There is no connector after the draft-generation step. The application has no code path for Graph write scopes, AD modification, ticket submission, approval, or remediation.

## Attribute-based suggestions

Suggestions come from explicit access profiles in structured data. A profile may require one or more attributes such as job title, department, or office location. All configured attributes must match. The report shows the matched attributes and excludes access the employee already has.

Profiles should be reviewed by IAM and business owners. A production design should not build profiles automatically from unreviewed peer access because historical access can contain role creep or bias.

## Planned live adapters

A future lab version can replace the JSON repository with read-only adapters while preserving the analyzer interface:

- Microsoft Graph adapter for Entra manager and transitive membership
- AD DS adapter for direct manager, group membership, and account expiry
- Exchange Online adapter for shared mailbox and distribution-group access

Each adapter must return normalized data with source evidence and collection timestamps. The authorization layer must fail closed when sources are missing, stale, or contradictory.

## Deployment boundary

Version 1.0 is a local portfolio demonstration bound to `127.0.0.1`. It is not intended for public hosting or production identity data. A production service would additionally require enterprise authentication, tenant isolation, server-side sessions, audit logging, secure secret storage, data-retention controls, monitoring, and formal threat review.



## Evidence-backed briefing extension

`POST /api/summary` accepts identity and review-date input, reruns the manager check,
and builds its own report. Browser-supplied reports and authorization flags are not used.
`summary.py` extracts cited account notices, review findings, and suggestions.
An optional Ollama adapter proposes an ordering of those evidence IDs; validation
requires an exact permutation. The server always renders original evidence text.
No model result can change access, draft selections, authorization, or findings.
The default needs no model. Failures return all evidence in deterministic order.
See [AI_BRIEFING.md](AI_BRIEFING.md) for evaluation and limits.
