# Manager Access Review Assistant

An explainable, human-in-the-loop prototype that helps managers review an employee's accumulated access across Microsoft identity and collaboration services.

> **Project status:** Phase 1 MVP. The current version uses synthetic JSON data and a deterministic rule engine. It does not connect to a tenant, call a language model, or change access.

## Why this project exists

Managers often need to approve access without having one clear view of what an employee already has. Relevant permissions may be spread across Entra ID, Active Directory, Microsoft 365 groups, distribution groups, shared mailboxes, Teams, and SharePoint.

This project collects those signals into a single review report. It separates expected access, organization-wide access, and items that deserve human review. Every finding includes evidence; the assistant never removes access or makes the approval decision.

## Example

```text
Access review: Matti Meikäläinen
Role: HR Specialist | Department: Human Resources

6 access items found
- 3 appear role-aligned
- 1 is organization-wide
- 2 require review

Review findings
- Finance-Admin: department mismatch, privileged access
- Legacy-HR-Archive: access purpose is missing
```

## Security principles

- Read-only by design
- Least-privilege permissions for every data source
- Human approval remains mandatory
- Evidence is shown for every flag
- No automatic access removal
- No production or personal data in the repository
- Synthetic test data only in the MVP

See [SECURITY.md](SECURITY.md) for the threat model and the planned Microsoft Graph permission approach.

## Run the MVP

Requirements: Python 3.11 or newer. No third-party packages are required.

```powershell
python -m access_review data/sample_access_snapshot.json --user matti.meikalainen
```

For machine-readable output:

```powershell
python -m access_review data/sample_access_snapshot.json --user matti.meikalainen --json
```

Run the tests:

```powershell
python -m unittest discover -s tests -v
```

## Architecture

```text
Synthetic JSON snapshot
        |
        v
Validated data loader
        |
        v
Explainable rule engine
        |
        v
Manager-friendly report (text or JSON)
```

The code keeps collection, analysis, and presentation separate so that synthetic data can later be replaced by Microsoft Graph and lab Active Directory adapters without changing the review logic.

## Current review rules

An access item is flagged when one or more of these conditions apply:

- the employee's department is not in the entitlement's expected departments;
- the entitlement is tagged as privileged;
- the entitlement has no documented business purpose;
- the entitlement is marked dormant.

Organization-wide access is reported separately to reduce noise. The rules are intentionally conservative: a flag means **review**, never **remove**.

## Roadmap

- [x] Phase 1: synthetic data model, explainable analysis, CLI, and tests
- [ ] Phase 2: read-only Entra ID lab adapter using Microsoft Graph
- [ ] Phase 3: distinguish direct and transitive group membership in collected data
- [ ] Phase 4: AD DS, shared mailbox, and distribution-group adapters
- [ ] Phase 5: manager-facing web UI or Copilot Studio tool
- [ ] Phase 6: optional LLM summary grounded only in collected evidence
- [ ] Phase 7: audit logging, role-based access, and review export

## Planned Microsoft Graph scope

The first live integration will use a dedicated lab tenant and read-only access. Permission selection will be documented and tested against least privilege before any tenant connection is added. Secrets and tenant identifiers must be provided through environment variables and must never be committed.

## Portfolio talking points

- Identity governance and access-review thinking
- Microsoft Graph and hybrid identity integration
- Explainable decision support instead of autonomous authorization
- Least privilege, data minimization, and human oversight
- Testable architecture that can evolve from mock data to live sources

## Disclaimer

This is a portfolio and lab project, not a production authorization system. Findings are decision-support signals and may contain false positives. A qualified human reviewer is responsible for every access decision.
