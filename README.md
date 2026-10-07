# Manager Access Review Assistant

An explainable, human-in-the-loop prototype that helps a verified direct manager understand an employee's accumulated access and prepare a request for ICT or Service Desk.

> **Project status:** Portfolio demo v1.0. The current version uses synthetic JSON data and a deterministic rule engine. It does not connect to a tenant, call a language model, open tickets, or change access.



## Demo organization

All employees and resources belong to the fictional **Ankkalinna Identity Lab Oy**.
The employee is **Aku Ankka** (`aku.ankka`) and the manager is **Roope Ankka**
(`roope.ankka`). Office: **Ankkalinna**. Email addresses use the reserved
`ankkalinna.example.invalid` domain. No real employee or tenant data is included.

## Why this project exists

Managers often need to review access without having one clear view of what an employee already has. Relevant permissions may be spread across Entra ID, Active Directory, Microsoft 365 groups, distribution groups, shared mailboxes, Teams, and SharePoint.

This project brings those signals into one report. It highlights items that deserve human review, warns about an approaching AD account expiry, proposes possible missing access from documented role and location profiles, and creates a Service Desk request draft when the manager explicitly selects a change.

## Non-negotiable boundary

The assistant cannot grant, remove, approve, or deny access. It cannot submit a ticket. The verified manager chooses what to request, and ICT or Service Desk validates and implements the change through the organization's normal process.

## Why the v1.0 baseline is deterministic

Identity decisions are high-impact. Version 1.0 therefore keeps authorization, expiry calculation, anomaly flags, and access-profile matching deterministic and testable. This is the evidence layer an AI summary can safely sit on top of later.

An optional language-model phase is planned only for manager-friendly summarization. It must be grounded exclusively in the structured report, show supporting evidence, treat directory text as untrusted input, and remain unable to call write or ticket-submission tools. The project does not claim that deterministic rules are generative AI.

## Manager authorization

A requester receives the report only when the requester is recorded as the employee's direct manager in **both** AD and Entra ID. Missing or conflicting manager data fails closed.

The MVP demonstrates this check with synthetic attributes. A live version must perform the same check server-side using freshly collected identity data; a manager ID supplied by the browser must never be trusted on its own.

## Example capabilities

- Classify current access as role-aligned, organization-wide, or requiring review.
- Distinguish direct and transitive membership.
- Show the AD account expiry date and warn when it is 90 days or less away.
- Compare account expiry with the recorded contract end date.
- Create an informational Service Desk draft when dates should be verified.
- Suggest possible missing groups based on job title, department, or office location.
- Explain the exact attributes behind each suggestion.
- Create an addition/removal request draft only from changes explicitly chosen by the manager.

Suggestions are candidates for review, not entitlements the employee automatically deserves.

## Run the browser demo

Requirements: Python 3.11 or newer. No third-party packages are required.

```powershell
python -m access_review.web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and use the pre-filled synthetic identities:

- manager: `roope.ankka`
- employee: `aku.ankka`
- review date: `2026-10-07`

The browser application supports the complete demo flow: manager verification, access inventory, account-expiry warning, attribute-based suggestions, and a copyable Service Desk draft. It runs on localhost and includes no outbound application integrations.

## Run the CLI

The same analysis is available as a command-line report:

```powershell
python -m access_review access_review/demo_data/sample_access_snapshot.json `
  --user aku.ankka `
  --manager roope.ankka `
  --as-of 2026-10-07
```

Create an example Service Desk request draft:

```powershell
python -m access_review access_review/demo_data/sample_access_snapshot.json `
  --user aku.ankka `
  --manager roope.ankka `
  --as-of 2026-10-07 `
  --draft-add HR-Case-Management-Users `
  --draft-remove Rahasailio-Admin `
  --reason "Align access with current HR duties."
```

Add `--json` for machine-readable output.

## Quality checks

Run the full test suite:

```powershell
python -m unittest discover -s tests -v
```

The suite covers manager authorization, conflicting directory records, expiry and contract-date warnings, explainable suggestions, Service Desk draft boundaries, HTTP security headers, API denial behavior, and the browser demo backend. GitHub Actions runs the same suite for every push and pull request.

## Architecture

```text
Browser or CLI input (untrusted)
          |
          v
Server-side AD manager + Entra manager check ---- mismatch ---> deny
          |
          v
Read-only identity snapshot
          |
          +--> current access analysis
          +--> AD account expiry warning
          +--> attribute-based suggestions
          |
          v
Manager-friendly report
          |
          v
Optional Service Desk draft ----> human validation and implementation
```

Collection, authorization, analysis, and presentation are kept separate so synthetic data can later be replaced by Microsoft Graph and lab Active Directory adapters without making the analysis layer capable of changing access.

See [Architecture](docs/ARCHITECTURE.md) for trust boundaries, request flows, and the planned live-adapter design.

## Current deterministic rules

An existing access item is flagged when:

- the employee's department is outside the entitlement's expected departments;
- the entitlement is tagged as privileged;
- the entitlement has no documented business purpose; or
- the entitlement is marked dormant.

An account notice is produced when:

- the AD account has expired;
- the AD expiry date is at most 90 days away; or
- the recorded contract end date is later than the AD account expiry.

An access suggestion is shown only when all attributes defined by a documented access profile match and the employee does not already have the named access. Every suggestion still requires ICT or Service Desk validation.

## Security principles

- Read-only integrations only
- Direct-manager match required in AD and Entra ID
- Least-privilege permissions for every data source
- Evidence shown for every flag and suggestion
- No automatic remediation or ticket submission
- Human approval and ICT validation remain mandatory
- Synthetic data only in the repository

See [SECURITY.md](SECURITY.md) for the threat model.

## Completed v1.0 scope

- [x] Synthetic data model, explainable analysis, CLI, and tests
- [x] Dual-source direct-manager authorization check
- [x] AD account expiry warning and Service Desk notice draft
- [x] Attribute-based access suggestions with evidence
- [x] Explicit access-change request draft with a hard no-write boundary
- [x] Responsive local browser interface
- [x] Server-side API validation and security headers
- [x] Desktop and mobile browser QA
- [x] Continuous integration with GitHub Actions

## Future lab integrations

- [ ] Read-only Entra ID lab adapter using Microsoft Graph
- [ ] Read-only AD DS lab adapter for manager and account-expiry attributes
- [ ] Shared mailbox and distribution-group adapters
- [ ] Optional LLM summary grounded only in collected evidence
- [ ] Audit logging, role-based access, and review export

These integrations are deliberately outside the synthetic portfolio demo. They require a dedicated lab tenant, explicit permission review, and tenant-specific configuration; the demo is complete and usable without them.

## Portfolio talking points

- Identity governance and hybrid IAM thinking
- Microsoft Graph and AD integration planning
- Authorization based on verified organizational relationships
- Explainable decision support instead of autonomous authorization
- Contract/account lifecycle mismatch detection
- Least privilege, data minimization, and human oversight

## Disclaimer

This is a portfolio and lab project, not a production authorization system. Findings and suggestions may contain false positives. A qualified human reviewer is responsible for every request and access decision.
