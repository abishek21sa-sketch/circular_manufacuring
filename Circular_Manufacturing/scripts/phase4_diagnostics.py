from pathlib import Path
import json, threading, urllib.request
from http.server import ThreadingHTTPServer
from circular_battery.web.server import Handler, DIST
from circular_battery.web.service import reference_payload, optimize_payload, frontier_payload, stress_payload

checks={}
checks["frontend_artifacts"]=all((DIST/n).is_file() for n in ("index.html","styles.css","app.js"))
ref=reference_payload()
checks["locked_phase_artifacts"]=all(ref.get(k) for k in ("phase1","phase2","phase3"))
checks["evidence_boundary"]=ref["evidence"]["real_world_validation"]=="PENDING" and ref["evidence"]["data_status"]=="SYNTHETIC VALIDATION"
sol=optimize_payload({"scenario":{"collection_rate":.90,"recycle_yield":.92},"carbon_price_per_kg":.2})["solution"]
checks["scenario_optimal"]=bool(sol["status"]=="OPTIMAL")
checks["constraint_audit"]=bool(sol["max_constraint_violation"]<1e-6)
front=frontier_payload({})["frontier"]
checks["frontier_available"]=bool(len(front)>=2)
a=stress_payload({"n":20,"seed":20260816})["stress"]; b=stress_payload({"n":20,"seed":20260816})["stress"]
checks["stress_reproducible"]=bool(a==b)

server=ThreadingHTTPServer(("127.0.0.1",0),Handler); port=server.server_address[1]
t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
try:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health",timeout=5) as r:
        checks["live_http_health"]=bool(r.status==200 and json.loads(r.read())["status"]=="ok")
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/",timeout=5) as r:
        checks["live_workbench"]=bool(r.status==200 and b"Material Circularity Studio" in r.read())
finally:
    server.shutdown(); server.server_close(); t.join(timeout=2)

result={"phase":"PHASE-4","passed":all(checks.values()),"checks":checks,
        "reference":{"frontier_points":len(front),"scenario_cost":sol["total_cost"],"scenario_recycled_content":sol["recycled_content_rate"]}}
out=Path("docs/validation/phase4_diagnostics.json"); out.write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["passed"] else 1)
