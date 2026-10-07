# Ankkalinna briefing evaluation

Every case uses Aku Ankka and his manager Roope Ankka in **Ankkalinna Identity Lab Oy**.
The main demo places Aku in HR; the department-transfer scenario is a separate
synthetic case where Aku has moved from Finance to Sales and still holds
Rahasailio-Admin and the finance mailbox access. These are review candidates;
the fixture does not establish whether an exception has been approved.

## Run from the repository root

```powershell
python -m access_review.evaluate
python -m access_review.evaluate --ollama-model YOUR_LOCAL_MODEL --repeats 3
```

The second command needs an installed local model and a running local Ollama.
It exits with status 2 if no model trial succeeds, so an unavailable model cannot
masquerade as a successful benchmark. A failed response falls back safely but
receives no model-quality score. No outbound model call occurs in the first command.

## Open the transfer case in the browser

```powershell
python -m access_review.web --snapshot evaluation/department-transfer.json
```

Use `aku.ankka`, manager `roope.ankka`, and date `2026-10-07`.
Select **Prepare briefing**. Expected findings: legacy finance administrator access,
finance mailbox access, and a possible Sales CRM addition. No change is performed.

## Cases and rubric

| Case | Purpose |
| --- | --- |
| Department transfer | Privileged legacy access before routine suggestions |
| Mixed findings | Account notices and privileged access before missing-purpose findings |
| Imminent expiry | Tomorrow's expiry before other findings |
| Untrusted directory text | Instruction-like resource name remains data; no evidence omitted |
| Empty evidence | No fabricated findings; no model call necessary |

`cases.json` stores explicit draft priority tiers; lower means earlier and ties are
intentional. Pairwise accuracy counts strictly ordered pairs only. Empty or tied-only
cases have no ranking score. Missing, duplicate, or unlabelled evidence fails the
benchmark rather than being silently ignored. The rubric is an engineering draft,
not an independent expert assessment or proof of correct access decisions.

## Recorded baseline

`baseline-results.json` was produced with no model. The current deterministic
ordering agrees with 22 of 23 strict pairs across these five small cases. The mixed
case places the missing-purpose archive before privileged Rahasailio access;
that is the one ordering disagreement. This small synthetic result cannot establish
that AI improves outcomes. A real-model result is deliberately not reported.

For a real comparison record model digest, Ollama version, hardware, repeat count,
per-case scores, failures and latency. Keep the deterministic implementation if the
model does not offer a useful improvement. Snapshot freshness, authenticated login,
and live adapters remain separate work.
