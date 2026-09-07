import json, threading, urllib.request, urllib.error
from http.server import ThreadingHTTPServer
from circular_battery.web.server import Handler, DIST
from circular_battery.web.service import reference_payload, optimize_payload, frontier_payload, stress_payload

def test_frontend_build_artifacts_present():
    assert (DIST/"index.html").is_file()
    assert (DIST/"app.js").is_file()
    assert (DIST/"styles.css").is_file()

def test_reference_payload_has_all_locked_phases():
    p=reference_payload()
    assert p["phase1"]["release"] == "PHASE-1"
    assert p["phase2"]["evidence_class"] == "SYNTHETIC VALIDATION"
    assert p["phase2"]["model_evidence"]["demand"]["metrics"]["mae"] < p["phase2"]["model_evidence"]["demand"]["baseline_metrics"]["mae"]
    assert p["phase3"]["reference_solution"]["status"] == "OPTIMAL"
    assert p["evidence"]["real_world_validation"] == "PENDING"

def test_scenario_api_service_changes_strategy():
    base=optimize_payload({"scenario":{"collection_rate":.70},"carbon_price_per_kg":.15})["solution"]
    improved=optimize_payload({"scenario":{"collection_rate":.95},"carbon_price_per_kg":.15})["solution"]
    assert improved["virgin_kg"] < base["virgin_kg"]
    assert improved["max_constraint_violation"] < 1e-6

def test_frontier_and_stress_service():
    f=frontier_payload({})
    assert len(f["frontier"]) >= 2
    s1=stress_payload({"n":20,"seed":44})["stress"]
    s2=stress_payload({"n":20,"seed":44})["stress"]
    assert s1 == s2

def test_live_http_contract():
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    port=server.server_address[1]
    t=threading.Thread(target=server.serve_forever,daemon=True); t.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health",timeout=5) as r:
            assert r.status == 200
            assert json.loads(r.read())["status"] == "ok"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/",timeout=5) as r:
            html=r.read().decode()
            assert "Material Circularity Studio" in html
        body=json.dumps({"scenario":{"collection_rate":.88},"carbon_price_per_kg":.2}).encode()
        req=urllib.request.Request(f"http://127.0.0.1:{port}/api/optimize",data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=10) as r:
            payload=json.loads(r.read())
            assert payload["solution"]["status"] == "OPTIMAL"
            assert payload["solution"]["max_constraint_violation"] < 1e-6
    finally:
        server.shutdown(); server.server_close(); t.join(timeout=2)


def test_frontend_has_distinct_material_studio_identity():
    html=(DIST/"index.html").read_text(encoding="utf-8")
    css=(DIST/"styles.css").read_text(encoding="utf-8")
    assert "Material Circularity Studio" in html
    assert all(label in html for label in ("MATERIALS","NETWORK","PLAN","STRATEGY","ROUTES","AI","RISK","TRACE","RUNS","EVIDENCE"))
    assert "Mission Control" not in html
    assert "sidebar" not in html.lower()
    assert ".risk-layout-v12" in css and ".hist-bar" in css


def test_render_blueprint_is_present_and_safe():
    text=(DIST.parents[1]/"render.yaml").read_text(encoding="utf-8")
    assert "runtime: python" in text
    assert "value: 3.14.7" in text
    assert 'buildCommand: pip install ".[gurobi,postgres]"' in text
    assert "healthCheckPath: /api/v1/health" in text
    assert "HOST=0.0.0.0" in text
    assert "CIRCULAR_DEPLOYMENT_MODE" in text
    assert "CIRCULAR_AUTH_MODE" in text
    assert "CIRCULAR_API_TOKEN_SHA256" in text
    assert "GEMINI_API_KEY" not in text
    assert "LicenseID" not in text


def test_reference_payload_surfaces_cumulative_phase7_artifact():
    p=reference_payload()
    assert p["evidence"]["release"] == "V1.2"
    from circular_battery import __version__
    assert p["evidence"]["version"] == __version__

def test_live_http_phase567_contract():
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    port=server.server_address[1]
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/phase567",timeout=10) as r:
            payload=json.loads(r.read())
            assert r.status==200
            assert payload["release"]=="PHASE-7-CUMULATIVE"
            assert payload["phase7"]["production_plan"]["status"]=="OPTIMAL"
            assert payload["phase6"]["reverse_logistics"]["max_constraint_violation"] < 1e-6
    finally:
        server.shutdown();server.server_close();t.join(timeout=2)
