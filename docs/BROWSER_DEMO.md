# Browser presentation demo

Visitors do not need Python, Ollama, an account or a tenant.

## Open without installing anything

Download `demo/index.html` from GitHub using **Download raw file**, then double-click
it. It is one self-contained HTML file with styles, JavaScript and synthetic
Ankkalinna reports embedded. Merely viewing the file on github.com displays code;
download it to open the interactive version. Do not save GitHub's surrounding page.

Choose a case from the selector. For a two-minute presentation:

1. Hansu: seasonal account expiry and the Service Desk verification draft.
2. Hannu: old finance access after a role change.
3. Taavi: a suggested research group and a human-selected request draft.

The prepared review date is fixed. The example identities must match the selected
case. This is a simulation, not an authentication boundary. All embedded reports
are public synthetic data. It does not connect to directories, send tickets or
call an AI model. The summary is explicitly rule-based. Nothing is saved remotely.
If clipboard access is unavailable, select the draft and copy it manually.

## GitHub Pages link

The `Browser demo` workflow builds and tests the standalone file before deployment.
Pages must use **Settings → Pages → Build and deployment → Source: GitHub Actions**.
If Pages is not enabled, an administrator must select that setting once, then rerun
the workflow. After a successful deployment, the demo is available at
<https://shelovestechy.github.io/manager-access-review-assistant/>.

The Pages version is the static presentation layer. The local Python application is
the separate learning prototype: it runs the deterministic analysis and manager
checks against synthetic JSON at request time. Pages uses precomputed versions of
those synthetic results and has no Python backend or live integrations.

## Maintenance

`python scripts/build_static.py` rebuilds the committed HTML from the same analyzer,
scenario data and UI assets used by the Python demo. Python is needed by the
maintainer/build workflow only. The Pages build regenerates it on each main push.
The static browser smoke test opens a `file://` URL and verifies that no HTTP
requests occur during selection, briefing or draft creation.
