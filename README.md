# Manager Access Review Assistant

An explainable, human-in-the-loop **learning and portfolio prototype** for exploring IAM, security, automation and bounded AI-assisted decision support.

> **Project status:** Design-and-testing stage. This repository is a learning project, not a production IAM system or a deployed enterprise service. The current demo uses only synthetic Ankkalinna JSON data and a deterministic rule engine. An optional local Ollama model can order existing evidence. It does not connect to a real tenant, authenticate real users, open tickets or change access.

## What I am learning with this project

This project is a practical study of how IAM, security and automation could meet in one bounded workflow. I am using it to learn and document:

- identity governance and access-review thinking;
- safe authorization boundaries and fail-closed design;
- separation of read-only evidence from access decisions;
- Service Desk and IAM workflow automation;
- testable Python application structure and browser/API behavior;
- responsible use of AI where deterministic evidence remains authoritative.

The architecture documents include ideas for possible future lab integrations. Those sections are **design exercises**, not claims of production implementation or professional IAM engineering experience.



## Demo organization

All employees and resources belong to the fictional **Ankkalinna Identity Lab Oy**.
The employee is **Aku Ankka** (`aku.ankka`) and the manager is **Roope Ankka**
(`roope.ankka`). Office: **Ankkalinna**. Email addresses use the reserved
`ankkalinna.example.invalid` domain. No real employee or tenant data is included.

## Why this project exists

Managers often need to review access without having one clear view of what an employee already has. Relevant permissions may be spread across Entra ID, Active Directory, Microsoft 365 groups, distribution groups, shared mailboxes, Teams and SharePoint.

This project brings those signals into one report. It highlights items that deserve human review, warns about an approaching AD account expiry, proposes possible missing access from documented role and location profiles and creates a Service Desk request draft when the manager explicitly selects a change.

## Non-negotiable boundary

The assistant cannot grant, remove, approve or deny access. It cannot submit a ticket. The verified manager chooses what to request, and ICT or Service Desk validates and implements the change through the organization's normal process.

## Why the prototype baseline is deterministic

Identity decisions are high-impact. The current prototype therefore keeps authorization, expiry calculation, anomaly flags and access-profile matching deterministic and testable. This is the evidence layer an AI summary can safely sit on top of later.

The optional language-model layer orders existing findings for a manager briefing. It returns evidence IDs only; the server validates that every ID appears exactly once and renders the original facts. It cannot generate new access facts, omit findings or call tools. Without a model, or if its output is invalid, a deterministic briefing remains available. This is AI-assisted evidence ordering, not free-form generative summarization.

## Manager authorization

A requester receives the report only when the requester is recorded as the employee's direct manager in **both** AD and Entra ID. Missing or conflicting manager data fails closed.

The MVP demonstrates this check with synthetic attributes. A live version must perform the same check server-side using freshly collected identity data; a manager ID supplied by the browser must never be trusted on its own.

## Example capabilities

- Classify current access as role-aligned, organization-wide or requiring review.
- Distinguish direct and transitive membership.
- Show the AD account expiry date and warn when it is 90 days or less away.
- Compare account expiry with the recorded contract end date.
- Create an informational Service Desk draft when dates should be verified.
- Suggest possible missing groups based on job title, department or office location.
- Explain the exact attributes behind each suggestion.
- Create an addition/removal request draft only from changes explicitly chosen by the manager.

Suggestions are candidates for review, not entitlements the employee automatically deserves.

## Design notes for a possible future deployment

Read the **[Finnish future-deployment design notes](docs/DEPLOYMENT_FI.md)** for a study of how a real implementation might separate user authorization, connector permissions, Graph/AD/Exchange read-only access and an optional Copilot Studio interface. This is architecture planning for learning purposes; live integrations, authenticated login and production deployment are not implemented in the current demo.

## Run the browser demo

> **Safe demo boundary:** Run this only with the synthetic data included in this repository. No Microsoft 365 tenant, Entra ID, Active Directory, employee data, API credentials or production access is required or expected.

Requirements: Python 3.11 or newer. No third-party packages are required.

```powershell
python -m access_review.web
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and use the pre-filled synthetic identities:

- manager: `roope.ankka`
- employee: `aku.ankka`
- review date: `2026-10-07`

The browser application supports the complete demo flow: manager verification, access inventory, account-expiry warning, attribute-based suggestions and a copyable Service Desk draft. It runs on localhost. By default it makes no model calls. Select **Prepare briefing** after opening a review to see cited findings and timing.

## Optional local AI ordering

With Ollama running locally and a local model already installed, start:

```powershell
python -m access_review.web --ollama-model YOUR_LOCAL_MODEL
```

Use your installed model name. The application calls only `127.0.0.1:11434`, disables HTTP proxies and redirects and rejects model names containing `cloud`. Configure Ollama itself for local-only operation; a loopback address alone cannot prove that its service does not forward data. Keep using synthetic data.

The briefing displays its mode (rule-based, AI-ordered or fallback), report-path citations, elapsed time and attempted model calls. Source collection timestamps and completeness are currently unknown and are explicitly labelled. It makes no monetary savings claims.

See [AI briefing design and evaluation](docs/AI_BRIEFING.md) for boundaries, budgets, tests and remaining work.

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

The suite covers manager authorization, conflicting directory records, expiry and contract-date warnings, explainable suggestions, Service Desk draft boundaries, HTTP security headers, API denial behavior and the browser demo backend. GitHub Actions runs the same suite for every push and pull request.

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

Collection, authorization, analysis and presentation are kept separate so synthetic data can later be replaced by Microsoft Graph and lab Active Directory adapters without making the analysis layer capable of changing access.

See [Architecture](docs/ARCHITECTURE.md) for trust boundaries, request flows and the planned live-adapter design.

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

## Completed prototype scope

- [x] Synthetic data model, explainable analysis, CLI and tests
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
- [x] Optional local LLM ordering of cited evidence with deterministic fallback
- [ ] Evaluate ordering quality with a real local model
- [ ] Free-form grounded summaries, if justified by evaluation
- [ ] Audit logging, role-based access and review export

These integrations are deliberately outside the synthetic portfolio demo. They are future learning work and would require a dedicated lab tenant, explicit permission review, authentication design and tenant-specific configuration. The current repository demonstrates the concept without them.

## Portfolio talking points

- Identity governance and hybrid IAM thinking
- Microsoft Graph and AD integration planning
- Authorization based on verified organizational relationships
- Explainable decision support instead of autonomous authorization
- Contract/account lifecycle mismatch detection
- Least privilege, data minimization and human oversight

## Disclaimer

This is a self-directed learning, portfolio and lab project for studying IAM, security, automation and bounded AI assistance. It is not a production authorization system, a deployed access-review service or evidence of production IAM engineering experience. The included identities and access data are fictional. Findings and suggestions may contain false positives, and any real-world access decision would require approved organizational policy, authoritative data and qualified human review.


## Repeatable Ankkalinna evaluation

Five synthetic scenarios now exercise department transfer, imminent expiry, mixed
findings, untrusted directory text and empty evidence. Run
`python -m access_review.evaluate` from the repository root. See
[evaluation instructions and baseline](evaluation/README.md).

## Expanded Ankkalinna scenario foundation

The combined organization dataset contains **12 employees**, including Mikki Hiiri,
Taavi Ankka and Hansu Hanhi. Hansu reports to Mummo Ankka; the other demo employees
report to Roope Ankka. The standalone suite adds **22 acceptance cases** for joiners,
role changes, seasonal work, inherited access, mail resources, lifecycle boundaries,
manager conflicts, unauthorized requesters and duplicate identity data.

```powershell
python -m access_review.web --snapshot access_review/demo_data/ankkalinna_organization.json
```

See the [Finnish scenario catalogue and account list](scenarios/README.md) for every
case, expected outcome and runnable commands. Cases are synthetic alternatives,
not a historical audit trail. The original five model-ordering evaluation cases
remain separate from these functional acceptance tests.

## Choose a case in the browser

Run `python -m access_review.web` from the source checkout. The Ankkalinna case
selector loads all 22 standalone scenarios and opens the selected review with
its sample employee, manager and date. The empty option keeps the configured
snapshot and manual identity fields. Denial/error scenarios deliberately show an
error rather than a report. Navigation links connect current access, attention
items and the Service Desk request. Account-expiry notice drafts are now visible.

The catalogue is synthetic demo metadata, not a production employee directory.
Scenario IDs select server-loaded fixtures; HTTP callers cannot provide file paths.
Every review, briefing and draft reruns authorization against the selected fixture.
When `scenarios/cases.json` is absent (for example a wheel-only installation), the
manual snapshot workflow remains available and the catalogue is empty.

GitHub Actions now includes `scripts/browser-smoke.cjs` to exercise all cases,
mobile overflow, briefings, drafts and stale-response handling with Chromium.
