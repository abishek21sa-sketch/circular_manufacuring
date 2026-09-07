from __future__ import annotations
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import uuid
from pathlib import Path
import sys
import threading
from urllib.parse import parse_qs, urlparse
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from product_adapter import (  # noqa: E402
    PROJECT, ALGORITHM, SUBTITLE, PORT, THEME, CONTROLS, DEFAULTS, DEMO_STRESS, compute
)

ARTIFACT = ROOT / "artifacts" / "product_runtime" / "latest_product_evidence.json"
MAX_REQUEST_TARGET_BYTES = 8_192
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def prepare_demo() -> dict:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    decision = compute(DEFAULTS)
    counterfactual = compute(DEMO_STRESS)
    payload = {
        "project": PROJECT,
        "algorithm": ALGORITHM,
        "mode": "DETERMINISTIC_PORTFOLIO_DEMO",
        "parameters": DEFAULTS,
        "decision": decision,
        "counterfactual": counterfactual,
        "evidence_boundary": decision["claim"],
        "runtime_contract": "interactive deterministic decision surface over repository-native signature algorithm",
        "volatile_fields_excluded_from_decision_id": ["runtime_seconds", "best_bound", "mip_gap", "diagnostics"],
    }
    ARTIFACT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(f"{ALGORITHM}_PRODUCT_DEMO_PREPARED=PASS")
    print(f"DECISION_ID={decision['decision_id']}")
    return payload


def _theme_css() -> str:
    return {
        "aurum": ":root{--bg:#080b12;--panel:#111827;--ink:#e5e7eb;--muted:#9ca3af;--accent:#e3b341;--line:#273246}",
        "circular": ":root{--bg:#f4f7f3;--panel:#ffffff;--ink:#162019;--muted:#66736a;--accent:#237a4b;--line:#d7e2d9}",
        "supply": ":root{--bg:#0c1217;--panel:#13202a;--ink:#e7f0f5;--muted:#94a7b3;--accent:#e37335;--line:#29404f}",
        "minco": ":root{--bg:#f5f7fb;--panel:#ffffff;--ink:#14213d;--muted:#65718a;--accent:#2c6e9b;--line:#d9e0ea}",
        "pdm": ":root{--bg:#0e1012;--panel:#181c20;--ink:#f1f3f5;--muted:#9da7af;--accent:#7fa3b8;--line:#30383f}",
    }[THEME]


def _html() -> str:
    controls = json.dumps(CONTROLS)
    return f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{PROJECT}</title>
<style>{_theme_css()}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,Segoe UI,Arial,sans-serif}} header{{padding:28px 34px 20px;border-bottom:1px solid var(--line)}}
.eyebrow{{font-size:11px;letter-spacing:.14em;color:var(--accent);font-weight:800}} h1{{margin:8px 0 6px;font-size:29px}} .sub{{max-width:1050px;color:var(--muted);line-height:1.5}}
main{{display:grid;grid-template-columns:290px minmax(0,1fr);gap:18px;padding:20px;max-width:1480px;margin:auto}} .panel{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px}} .panel h2{{font-size:15px;margin:2px 0 14px}}
label{{display:block;font-size:12px;margin:15px 0 6px;color:var(--muted)}} .hint{{font-size:11px;line-height:1.45;color:var(--muted)}} input{{width:100%;padding:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:7px}}
button{{width:100%;margin-top:18px;padding:11px;border:0;border-radius:7px;background:var(--accent);color:#111;font-weight:800;cursor:pointer}} button:disabled{{opacity:.55;cursor:wait}}
.status{{display:flex;justify-content:space-between;gap:12px;margin-bottom:14px;align-items:center}} .gate{{font-weight:800;color:var(--accent);letter-spacing:.08em}} .decision-id{{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:var(--muted)}}
.cards{{display:grid;grid-template-columns:repeat(6,minmax(110px,1fr));gap:8px}} .card{{border:1px solid var(--line);padding:12px;border-radius:9px;min-height:76px}} .card small{{color:var(--muted);font-size:10px}} .card strong{{display:block;margin-top:7px;font-size:18px}}
.grid-2{{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(280px,.8fr);gap:16px}} h2{{font-size:15px;margin:23px 0 11px}} table{{width:100%;border-collapse:collapse;font-size:12px}} th,td{{padding:9px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}} th{{color:var(--muted);font-weight:700;font-size:10px;letter-spacing:.05em}} td.num{{text-align:right;font-variant-numeric:tabular-nums}}
.section-label{{font-size:10px;color:var(--muted);letter-spacing:.1em;font-weight:800;margin:2px 0 10px}} .claim{{margin-top:16px;padding:12px;border-left:3px solid var(--accent);color:var(--muted);line-height:1.5;font-size:12px}} .ok{{color:#237a4b;font-weight:800}} .fail{{color:#b33b2e;font-weight:800}} .check-grid{{display:grid;grid-template-columns:1fr 1fr;gap:7px}} .check{{padding:9px;border:1px solid var(--line);border-radius:7px;font-size:11px}} .check b{{float:right}} .bar{{height:8px;background:var(--bg);border-radius:5px;overflow:hidden;margin-top:5px}} .bar i{{display:block;height:100%;background:var(--accent)}} details{{margin-top:16px;color:var(--muted)}} pre{{white-space:pre-wrap;word-break:break-word;font-size:10px;max-height:380px;overflow:auto}}
.error{{color:#b33b2e;min-height:18px;font-size:12px;margin-top:12px}} @media(max-width:1100px){{main{{grid-template-columns:1fr}}.cards{{grid-template-columns:repeat(3,1fr)}}}} @media(max-width:700px){{header{{padding:22px 18px 16px}}main{{padding:14px}}.cards,.grid-2,.check-grid{{grid-template-columns:1fr 1fr}}}}
/* domain-specific console treatment: material flow, not generic BI */
:root{{--bg:#06120d;--panel:#0b1d15;--panel-2:#10281d;--ink:#edf7ef;--muted:#8ca99a;--accent:#c8f169;--accent-2:#58d49b;--line:#214535;--warm:#ffb765;--danger:#ff857b}}
body{{background:radial-gradient(circle at 78% -10%,rgba(74,168,116,.20),transparent 34%),linear-gradient(135deg,#06120d 0%,#091a13 55%,#06100c 100%);letter-spacing:.01em}}
body::before{{content:"";position:fixed;inset:0;pointer-events:none;opacity:.16;background-image:linear-gradient(rgba(200,241,105,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(200,241,105,.08) 1px,transparent 1px);background-size:44px 44px;mask-image:linear-gradient(to bottom,black,transparent 80%)}}
header.masthead{{padding:26px 34px 18px;border-bottom:1px solid var(--line);background:rgba(5,16,11,.78);position:relative}}
.brand-row{{display:flex;gap:16px;align-items:flex-start;max-width:1480px;margin:0 auto}}
.brand-symbol{{width:42px;height:42px;border:1px solid var(--accent);color:var(--accent);display:grid;place-items:center;font-size:28px;line-height:1;border-radius:50%;box-shadow:0 0 22px rgba(200,241,105,.12);flex:0 0 auto}}
.brand-symbol span{{transform:translateY(-2px)}}
header.masthead h1{{font-size:clamp(26px,3.2vw,44px);font-weight:540;letter-spacing:-.045em;margin:6px 0 8px}}
header.masthead .sub{{max-width:900px;font-size:12px}}
.status-stack{{margin-left:auto;border:1px solid var(--line);padding:10px 13px;min-width:190px;text-align:right;color:var(--accent);font-size:10px;letter-spacing:.12em}}
.status-stack small{{display:block;color:var(--muted);font-size:8px;letter-spacing:.08em;margin-top:5px}}
.status-dot{{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 11px var(--accent);margin-right:7px}}
.loop-map{{max-width:1480px;margin:22px auto 0;display:grid;grid-template-columns:1fr 80px 1fr 80px 1fr;align-items:center}}
.loop-node{{border-left:2px solid var(--accent-2);padding:8px 13px;background:linear-gradient(90deg,rgba(88,212,155,.10),transparent);display:grid;gap:2px}}
.loop-node span{{font-size:9px;color:var(--accent);letter-spacing:.14em}} .loop-node b{{font-size:12px;letter-spacing:.14em}} .loop-node small{{font-size:9px;color:var(--muted)}}
.loop-connector{{height:1px;background:linear-gradient(90deg,var(--accent-2),var(--accent));position:relative}} .loop-connector::after{{content:"›";position:absolute;right:-2px;top:-10px;color:var(--accent);font-size:17px}}
main.console-grid{{grid-template-columns:300px minmax(0,1fr);padding:24px;gap:20px;max-width:1480px}}
.panel{{background:linear-gradient(145deg,rgba(16,40,29,.94),rgba(8,25,18,.98));border:1px solid var(--line);border-radius:3px;box-shadow:0 18px 50px rgba(0,0,0,.18)}}
.control-panel{{position:sticky;top:18px;height:max-content}}
.panel-kicker{{font-size:9px;color:var(--accent);font-weight:800;letter-spacing:.17em;margin-bottom:9px}}
.panel h2{{font-size:14px;letter-spacing:.02em;font-weight:650;margin-top:22px}}
label{{font-size:10px;letter-spacing:.04em;color:var(--muted);margin:17px 0 7px}} input{{padding:11px 10px;border-radius:2px;background:#07150e;border-color:#2d5942;font-family:ui-monospace,Consolas,monospace;font-size:14px}}
button{{border-radius:2px;background:var(--accent);color:#07120b;letter-spacing:.12em;box-shadow:0 0 24px rgba(200,241,105,.12)}} button:hover{{background:#e0ff91;transform:translateY(-1px)}}
.result-panel{{padding:20px 22px}} .status{{padding-bottom:13px;border-bottom:1px solid var(--line)}} .gate{{padding:5px 9px;border:1px solid var(--accent);background:rgba(200,241,105,.08)}} .decision-id{{color:var(--muted)}}
.decision-banner{{display:flex;justify-content:space-between;gap:20px;align-items:end;padding:16px 0 2px}} .decision-banner strong{{display:block;font-size:20px;font-weight:520;letter-spacing:-.02em}} .decision-banner small{{display:block;color:var(--muted);font-size:9px;letter-spacing:.13em;margin-top:5px}} .decision-banner .metric-note{{color:var(--muted);font-size:10px;text-align:right;max-width:240px;line-height:1.45}}
.cards{{grid-template-columns:repeat(7,minmax(92px,1fr));gap:7px;margin-top:14px}} .card{{background:rgba(6,18,13,.66);border-color:var(--line);border-radius:2px;min-height:82px}} .card small{{font-size:9px;letter-spacing:.05em}} .card strong{{font-size:17px;color:var(--ink)}}
.grid-2{{gap:22px}} table{{font-size:11px}} th{{font-size:9px;color:#668774;letter-spacing:.09em}} th,td{{border-bottom-color:rgba(72,128,92,.28);padding:10px 8px}} td{{color:#d7e7dc}} td.num{{color:var(--accent)}}
.section-label,.hint{{color:var(--muted)}} .claim{{border-left-color:var(--accent);background:rgba(200,241,105,.055);border-top:1px solid rgba(200,241,105,.16);border-bottom:1px solid rgba(200,241,105,.16)}} .check{{border-color:var(--line);border-radius:2px;background:rgba(6,18,13,.5)}} .ok{{color:var(--accent-2)}} .fail{{color:var(--danger)}}
.evidence-rail{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:18px}} .evidence-chip{{border:1px solid var(--line);padding:11px;background:#07150e}} .evidence-chip small{{display:block;color:var(--muted);font-size:8px;letter-spacing:.12em}} .evidence-chip b{{display:block;color:var(--accent);font-size:11px;margin-top:5px}}
details{{border-top:1px solid var(--line);padding-top:12px}} summary{{cursor:pointer;color:var(--accent);font-size:10px;letter-spacing:.08em}}
@media(max-width:1100px){{.control-panel{{position:static}}.status-stack{{min-width:150px}}.cards{{grid-template-columns:repeat(4,1fr)}}}}
@media(max-width:700px){{header.masthead{{padding:20px 18px 14px}}.brand-row{{gap:10px}}.status-stack{{display:none}}.loop-map{{grid-template-columns:1fr;gap:7px}}.loop-connector{{width:55px;margin-left:13px;transform:rotate(90deg);transform-origin:left center}}main.console-grid{{padding:14px}}.cards,.grid-2,.check-grid,.evidence-rail{{grid-template-columns:1fr 1fr}}.decision-banner{{display:block}}.decision-banner .metric-note{{text-align:left;margin-top:10px}}}}
</style></head>
<body><header class="masthead"><div class="brand-row"><div class="brand-symbol" aria-hidden="true"><span>↺</span></div><div><div class="eyebrow">{ALGORITHM} · HUMAN-GATED DECISION INTELLIGENCE</div><h1>{PROJECT}</h1><div class="sub">{SUBTITLE} The decision is a governed analytical recommendation: review is required before any facility, sourcing, or recovery action is released.</div></div><div class="status-stack"><span class="status-dot"></span>LOCAL MODEL GATE<small>REFERENCE RUN · HUMAN REVIEW</small></div></div><div class="loop-map" aria-label="Closed-loop decision chain"><div class="loop-node"><span>01</span><b>COLLECT</b><small>returns + scrap</small></div><div class="loop-connector"></div><div class="loop-node"><span>02</span><b>RECOVER</b><small>facility + route</small></div><div class="loop-connector"></div><div class="loop-node"><span>03</span><b>DECIDE</b><small>CVaR + virgin fallback</small></div></div></header>
<main class="console-grid"><section class="panel control-panel"><div class="panel-kicker">POLICY LEVERS / INPUT CONTRACT</div><h2>Policy controls</h2><div id="controls"></div><button id="solve" onclick="runDecision()">SOLVE + GATE</button><div id="error" class="error"></div><p class="hint">These controls change the mathematical policy contract. They do not trigger an operational write. Results are reproducible reference-scenario outputs.</p><h2>Decision contract</h2><div class="hint"><b>First-stage:</b> route recovery mass and activate facilities.<br><b>Recourse:</b> scenario virgin fallback and shortage.<br><b>Risk:</b> shortage CVaR at the reported alpha.<br><b>Evidence:</b> synthetic formulation validation only.</div><a href="/download/evidence.json" style="display:inline-block;margin-top:18px;color:var(--accent);font-size:12px">Download evidence JSON ↗</a></section>
<section class="panel result-panel"><div class="status"><span class="decision-id" id="decisionId">—</span><span class="gate" id="gate">—</span></div><div class="decision-banner"><div><small>OPTIMIZATION RESULT</small><strong>Closed-loop material allocation</strong></div><div class="metric-note">A first-stage recovery policy is tested against yield uncertainty and shortage tail risk.</div></div><div class="cards" id="metrics"></div><div class="grid-2"><div><h2>Facility and routing decisions</h2><div id="actions"></div><h2>Scenario outcomes and CVaR tail</h2><div id="scenarios"></div></div><div><h2>Objective decomposition</h2><div id="objective"></div><h2>Governance checks</h2><div id="checks" class="check-grid"></div><h2>Solver diagnostics</h2><div id="diagnostics"></div></div></div><h2>Baselines and claim boundary</h2><div id="baselines"></div><div class="claim" id="claim"></div><div class="evidence-rail"><div class="evidence-chip"><small>EVIDENCE CLASS</small><b>SYNTHETIC VALIDATION</b></div><div class="evidence-chip"><small>SOLVER POLICY</small><b>GUROBI ACADEMIC / LOCAL</b></div><div class="evidence-chip"><small>RELEASE ACTION</small><b>HUMAN REVIEW REQUIRED</b></div></div><details><summary>RAW AUDITABLE PAYLOAD</summary><pre id="raw"></pre></details></section></main>
<script>
const controls={controls};
function esc(x){{return String(x??'').replace(/[&<>"']/g,s=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[s]))}}
function fmt(x,d=2){{const n=Number(x);return Number.isFinite(n)?n.toLocaleString(undefined,{{maximumFractionDigits:d}}):'N/A'}}
function table(rows,keys){{if(!rows||!rows.length)return '<em>No evidence rows.</em>';return '<table><thead><tr>'+keys.map(k=>'<th>'+esc(k.replaceAll('_',' '))+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+keys.map(k=>'<td>'+esc(r[k])+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}}
document.getElementById('controls').innerHTML=controls.map(c=>`<label>${{esc(c.label)}}<input id="${{c.key}}" type="number" min="${{c.min}}" max="${{c.max}}" step="${{c.step}}" value="${{c.default}}"></label>`).join('');
async function runDecision(){{const button=document.getElementById('solve');const error=document.getElementById('error');button.disabled=true;button.textContent='SOLVING…';error.textContent='';try{{const q=new URLSearchParams();controls.forEach(c=>q.set(c.key,document.getElementById(c.key).value));const response=await fetch('/api/decision?'+q.toString());const d=await response.json();if(!response.ok)throw new Error(d.detail||'Decision request failed');render(d)}}catch(e){{error.textContent=e.message}}finally{{button.disabled=false;button.textContent='SOLVE + GATE'}}}}
function render(d){{const sol=d.raw?.solution||{{}};document.getElementById('decisionId').textContent=d.decision_id||'—';document.getElementById('gate').textContent=d.gate||'—';document.getElementById('metrics').innerHTML=(d.metrics||[]).map(x=>`<div class="card"><small>${{esc(x[0])}}</small><strong>${{esc(x[1])}}</strong></div>`).join('');document.getElementById('actions').innerHTML=table(d.actions,['Facility','Open','Recovery route']);document.getElementById('scenarios').innerHTML=table((d.scenario_details||[]).map(x=>({{scenario:x.name,probability:fmt(x.probability,2),demand_kg:fmt(x.demand_kg,0),recovered_kg:fmt(x.recovered_kg,0),virgin_kg:fmt(x.virgin_kg,0),shortage_kg:fmt(x.shortage_kg,2),cvar_excess_kg:fmt(x.cvar_excess_kg,2)}})),['scenario','probability','demand_kg','recovered_kg','virgin_kg','shortage_kg','cvar_excess_kg']);const comps=d.objective_components||{{}};document.getElementById('objective').innerHTML='<table><tbody>'+Object.entries(comps).map(([k,v])=>`<tr><th>${{esc(k.replaceAll('_',' '))}}</th><td class="num">${{fmt(v,2)}}</td></tr>`).join('')+`<tr><th><b>Total objective</b></th><td class="num"><b>${{fmt(sol.objective,2)}}</b></td></tr></tbody></table>`;document.getElementById('checks').innerHTML=Object.entries(d.checks||{{}}).map(([k,v])=>`<div class="check">${{esc(k.replaceAll('_',' '))}} <b class="${{v?'ok':'fail'}}">${{v?'PASS':'FAIL'}}</b></div>`).join('');const diag=d.diagnostics||{{}};document.getElementById('diagnostics').innerHTML='<table><tbody>'+[['eta',fmt(sol.eta,3)],['alpha',fmt(sol.alpha,3)],['variables',fmt(sol.variable_count,0)],['constraints',fmt(sol.constraint_count,0)],['MIP gap',fmt(sol.mip_gap,6)],['best bound',fmt(sol.best_bound,2)],['reconciliation error',fmt(diag.objective_reconciliation_error,8)]].map(x=>`<tr><th>${{esc(x[0])}}</th><td class="num">${{esc(x[1])}}</td></tr>`).join('')+'</tbody></table>';document.getElementById('baselines').innerHTML=table(d.baselines.map(x=>({{comparison:x[0],value:x[1]}})),['comparison','value']);document.getElementById('claim').textContent=d.claim||'';document.getElementById('raw').textContent=JSON.stringify(d.raw,null,2)}}
fetch('/api/evidence').then(r=>r.json()).then(x=>render(x.decision)).catch(e=>document.getElementById('error').textContent=e.message);
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def _request_id(self) -> str:
        candidate = self.headers.get("X-Request-ID", "")
        return candidate if REQUEST_ID_PATTERN.fullmatch(candidate) else uuid.uuid4().hex[:16]

    def _send(self, code: int, body: bytes, ctype: str = "application/json", request_id: str | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-ID", request_id or self._request_id())
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        request_id = self._request_id()
        if len(self.path.encode("utf-8")) > MAX_REQUEST_TARGET_BYTES:
            return self._send(414, b'{"error":"REQUEST_TARGET_TOO_LARGE","detail":"Request target is too large."}', request_id=request_id)
        p = urlparse(self.path)
        try:
            if p.path == "/health":
                return self._send(200, json.dumps({"status": "ok", "project": PROJECT, "algorithm": ALGORITHM}).encode(), request_id=request_id)
            if p.path == "/":
                return self._send(200, _html().encode("utf-8"), "text/html; charset=utf-8", request_id=request_id)
            if p.path == "/api/evidence":
                payload = json.loads(ARTIFACT.read_text(encoding="utf-8")) if ARTIFACT.exists() else prepare_demo()
                return self._send(200, json.dumps(payload, default=str).encode(), request_id=request_id)
            if p.path == "/api/decision":
                q = parse_qs(p.query, max_num_fields=16)
                params = {}
                for control in CONTROLS:
                    raw_value = q.get(control["key"], [control["default"]])[0]
                    try:
                        value = float(raw_value)
                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"{control['label']} must be numeric.") from exc
                    if not control["min"] <= value <= control["max"]:
                        raise ValueError(f"{control['label']} must be between {control['min']} and {control['max']}.")
                    params[control["key"]] = value
                d = compute(params)
                ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
                ARTIFACT.write_text(json.dumps({"project": PROJECT, "algorithm": ALGORITHM, "mode": "INTERACTIVE", "parameters": params, "decision": d}, indent=2, sort_keys=True, default=str), encoding="utf-8")
                return self._send(200, json.dumps(d, default=str).encode(), request_id=request_id)
            if p.path == "/download/evidence.json":
                payload = ARTIFACT.read_bytes() if ARTIFACT.exists() else json.dumps(prepare_demo(), indent=2).encode()
                return self._send(200, payload, "application/json", request_id=request_id)
            return self._send(404, b'{"detail":"not found"}', request_id=request_id)
        except ValueError as exc:
            return self._send(422, json.dumps({"error": "VALIDATION_ERROR", "detail": str(exc)}).encode(), request_id=request_id)
        except Exception as exc:
            print(f"[product] internal error request_id={request_id} type={type(exc).__name__}")
            return self._send(500, b'{"error":"INTERNAL_ERROR","detail":"Internal server error."}', request_id=request_id)

    def log_message(self, fmt: str, *args) -> None:
        print("[product]", fmt % args)


def serve(*, open_browser: bool = True) -> None:
    if not ARTIFACT.exists():
        prepare_demo()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/"
    print(f"PRODUCT_RUNTIME_READY={url}", flush=True)
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping product runtime...")
    finally:
        server.server_close()


def acceptance() -> None:
    payload = prepare_demo()
    if payload["decision"]["gate"] not in ("AUTHORIZED", "RESEARCH_ONLY"):
        raise SystemExit(f"PRODUCT_RUNTIME_ACCEPTANCE=FAIL gate={payload['decision']['gate']}")
    changed = compute(DEMO_STRESS)
    if changed["decision_id"] == payload["decision"]["decision_id"] and changed["raw"] == payload["decision"]["raw"]:
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL counterfactual did not change")
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        for path in ("/health", "/", "/api/evidence"):
            with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=20) as response:
                if response.status != 200:
                    raise SystemExit(f"PRODUCT_RUNTIME_ACCEPTANCE=FAIL http={path}:{response.status}")
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
    if not ARTIFACT.exists():
        raise SystemExit("PRODUCT_RUNTIME_ACCEPTANCE=FAIL evidence artifact missing")
    print(f"{ALGORITHM}_PRODUCT_RUNTIME_ACCEPTANCE=PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare-demo", action="store_true")
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--accept", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    if args.prepare_demo:
        prepare_demo()
    if args.accept:
        acceptance()
    if args.serve:
        serve(open_browser=not args.no_browser)
    if not (args.prepare_demo or args.accept or args.serve):
        ap.print_help()


if __name__ == "__main__":
    main()
