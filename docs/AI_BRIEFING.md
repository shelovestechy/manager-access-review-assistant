# Evidence-backed manager briefing

## User problem and scope

Managers need a quick view of what needs attention without mistaking AI-written
claims for directory evidence. The briefing combines account notices, access
review findings, and possible additions from the existing analyzer. It cites
JSON Pointer-style report paths and source labels. Collection time and source
completeness are unknown in the current fixture; the UI says so.

## Why this design

This first AI increment uses **extractive evidence ordering**: the optional model
orders existing facts; it does not write new claims. All findings remain visible.
This makes invented IDs, omissions, duplicates, and extra response fields
rejectable in code. Citation validity alone would not prove a free-form sentence
true, so we do not claim free-form factual verification.

The standard-library implementation preserves the dependency-free demo. There is
no agent loop, RAG store, semantic cache, or autonomous action. Those components
are not required for this bounded task.

## Flow and trust boundaries

1. Browser submits the identities and date of the opened review.
2. Server checks the simulated AD and Entra manager relationship again.
3. Analyzer produces the report; no browser-provided report is trusted.
4. Briefing extracts notices, findings, and suggestions, with report-local IDs.
5. If enabled, Ollama returns a JSON object containing only `evidence_ids`.
6. Server requires an exact permutation of the issued IDs and renders original text.
7. Any supported transport/schema failure uses the deterministic ordering.

Model input excludes the full employee record and requester's ID, but finding text
can contain department, resource, and location data. Directory text is untrusted.
Prompt injection can still affect ranking quality; it cannot add or suppress
findings through the output contract. Real-world identity data is out of scope.

## Resource budgets and measurements

- At most one model attempt per briefing; no retries.
- At most 32 evidence items and 24,000 request bytes for the model path.
- 512 requested output tokens; at most 16,000 response bytes read.
- 15-second HTTP socket timeout (not a strict total wall-clock deadline).
- No cross-user or semantic cache.
- Display measured briefing duration and model-attempt count.
- No asserted API savings: local compute is not free and there is no measured baseline.

The configured model must already be installed. No model is downloaded by this
application. Set the Ollama service to local-only operation independently; an
endpoint on localhost does not attest to the service's own network behavior.

## Validation performed

`python -m unittest discover -s tests -v` — 64 tests passed in the development
workspace. Tests cover valid ordering, invented/missing/duplicate IDs, malformed
JSON, timeout fallback, evidence budgets, report citation resolution, API denial,
blank/null manager records, and source-aware suggestion matching. The Ollama HTTP
contract is mocked; a real model was not installed or benchmarked here.

`node --check access_review/web_assets/app.js` passed. Browser visual/smoke QA
could not run because the workspace has no Chromium executable; this remains
a pre-merge check.

These tests validate the integration and boundaries, not the quality of a model's
ranking. Before recommending a model, evaluate several synthetic scenarios
(role transfer, privileged legacy access, imminent expiry, clean report, injected
directory text) against a human-reviewed priority order. Record model/version,
hardware, latency, fallback rate, and ranking quality, including a comparison
with the deterministic baseline. Keep deterministic ordering if the model does
not provide a useful improvement.

## Next portfolio increment

Add collected-at timestamps and per-source collection status to snapshots, then
create a synthetic department-transfer evaluation set. Live read-only adapters
and authenticated login remain separate work. Free-form explanation or RAG can
follow when the evidence and evaluation justify them.

## API references

- https://docs.ollama.com/api/chat
- https://docs.ollama.com/capabilities/structured-outputs


A runnable five-case suite and recorded deterministic baseline are now available in
[evaluation/README.md](../evaluation/README.md). Model quality remains unmeasured.

Browser automation is now configured in GitHub Actions; consult the current run
for its result. Local Chromium remains unavailable.
