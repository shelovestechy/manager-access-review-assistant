"""Build a self-contained synthetic demo: visitors need only a web browser."""
from pathlib import Path
from datetime import date
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from access_review.repository import load_snapshot
from access_review.analyzer import analyze_access
from access_review.summary import summarize_report


def build(destination):
    assets = ROOT / 'access_review/web_assets'
    manifest = json.loads((ROOT / 'scenarios/cases.json').read_text())
    cases = manifest['cases']
    catalogue = [{k: c[k] for k in ('id','title','employee','manager','review_date')} for c in cases]
    default = dict(id='',employee='aku.ankka',manager='roope.ankka',review_date='2026-10-07',snapshot='../access_review/demo_data/sample_access_snapshot.json')
    records = {}
    for case in [default] + cases:
        snapshot = load_snapshot(ROOT / 'scenarios' / case['snapshot'])
        record = {k: case[k] for k in ('employee','manager','review_date')}
        try:
            report = analyze_access(snapshot,case['employee'],case['manager'],as_of=date.fromisoformat(case['review_date']))
            record.update(report=report,briefing=summarize_report(report))
        except (ValueError,PermissionError) as error:
            record['error'] = str(error)
        records[case['id']] = record
    data = json.dumps(dict(scenarios=catalogue,records=records),ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    html = (assets / 'index.html').read_text()
    html = html.replace('<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">','<link rel="icon" href="data:,">')
    html = html.replace('<link rel="stylesheet" href="/assets/styles.css">','<style>'+(assets/'styles.css').read_text()+'</style>')
    html = html.replace('<script src="/assets/app.js" defer></script>','')
    html = html.replace('href="/"','href="#"')
    html = html.replace('Read-only demo','Browser demo')
    html = html.replace('<p class="eyebrow">Human-in-the-loop identity governance</p>', '<p class="eyebrow">Ankkalinna Identity Lab Oy · Browser demo</p>')
    html = html.replace('<p class="lede">','<p class="form-note">Synthetic presentation demo. No login, live directory connection or AI model call. All reports are prepared examples.</p><p class="lede">')
    html = html.replace('id="as-of" name="as_of"', 'id="as-of" readonly name="as_of"')
    script = (assets / 'app.js').read_text()
    script = script.replace('async function postJson(url, payload) {','async function postJson(url, payload) {\n  if (window.staticDemoPost) return window.staticDemoPost(url, payload);')
    script = script.replace('fetch("/api/demo-scenarios")', '(window.staticDemoData ? Promise.resolve({ok:true,json:async()=>window.staticDemoData}) : fetch("/api/demo-scenarios"))')
    script = script.replace('await navigator.clipboard.writeText(document.querySelector("#draft-text").textContent);','try { await navigator.clipboard.writeText(document.querySelector("#draft-text").textContent); } catch { showMessage("Select the draft text and copy it with Ctrl+C / Cmd+C."); return; }')
    transport = (ROOT/'scripts/static-transport.js').read_text()
    html=html.replace('</body>', '<script>window.staticDemoData='+data+';</script>\n<script>'+transport+'\n'+script+'</script>\n</body>')
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(html,encoding='utf-8')
    return html


if __name__ == '__main__':
    target=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'demo/index.html'
    build(target)
    print(target)
