import hashlib, json, threading, urllib.request, urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
import pytest

from circular_battery.web.server import Handler
from circular_battery.platform.storage import RunStore
from circular_battery.platform.service import EnterpriseDecisionService
from circular_battery.platform.observability import JsonlEventLogger

def _request(url,method="GET",payload=None,extra_headers=None):
    data=None if payload is None else json.dumps(payload).encode()
    headers={"Content-Type":"application/json","X-Request-ID":"test-request"}
    headers.update(extra_headers or {})
    req=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return r.status,dict(r.headers),json.loads(r.read()) if "json" in r.headers.get("Content-Type","") else None
    except urllib.error.HTTPError as e:
        return e.code,dict(e.headers),json.loads(e.read())

@pytest.fixture()
def live_v1(monkeypatch,tmp_path):
    monkeypatch.setenv("CIRCULAR_DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("CIRCULAR_AUTH_MODE", "disabled")
    monkeypatch.delenv("CIRCULAR_API_TOKEN_SHA256", raising=False)
    import circular_battery.platform.service as ps
    import circular_battery.web.service as ws
    def fake_build(**kwargs):
        return {
            "release":"PHASE-10-CUMULATIVE","version":"0.x","data_status":"SYNTHETIC VALIDATION",
            "decision_hash_sha256":"api-hash",
            "decision":{"recommended_policy":"resilience","confidence":.75},
        }
    monkeypatch.setattr(ps,"build_phase10_decision",fake_build)
    svc=EnterpriseDecisionService(RunStore(tmp_path/"api.sqlite3"),root=Path(__file__).resolve().parents[1],logger=JsonlEventLogger(tmp_path/"events.jsonl"))
    monkeypatch.setattr(ps,"_SERVICE",svc)
    server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown();server.server_close();t.join(timeout=2)

def test_v1_health_envelope_and_security_headers(live_v1):
    status,headers,p=_request(live_v1+"/api/v1/health")
    assert status==200 and p["ok"] is True
    assert p["data"]["version"]=="1.2.1"
    assert p["request_id"]=="test-request"
    assert headers["X-Content-Type-Options"]=="nosniff"
    assert headers["X-Frame-Options"]=="DENY"
    assert "default-src 'self'" in headers["Content-Security-Policy"]

def test_v1_scenario_crud_contract(live_v1):
    payload={"name":"API case","seed":77,"raw_n":30,"reduced_k":5,"include_sensitivity":False}
    status,_,p=_request(live_v1+"/api/v1/scenarios","POST",payload)
    assert status==201
    sid=p["data"]["scenario_id"]
    status,_,p=_request(live_v1+f"/api/v1/scenarios/{sid}")
    assert status==200 and p["data"]["config"]["seed"]==77
    status,_,p=_request(live_v1+"/api/v1/scenarios")
    assert any(x["scenario_id"]==sid for x in p["data"])

def test_v1_invalid_contract_returns_structured_422(live_v1):
    status,_,p=_request(live_v1+"/api/v1/scenarios","POST",{"name":"x","raw_n":2})
    assert status==422
    assert p["ok"] is False
    assert p["error"]["code"]=="VALIDATION_ERROR"
    assert p["request_id"]=="test-request"


def test_v1_request_boundaries_sanitize_ids_and_limit_query_fields(live_v1):
    status,headers,p=_request(live_v1+"/api/v1/health",extra_headers={"X-Request-ID":"invalid request id"})
    assert status==200
    assert headers["X-Request-ID"] != "invalid request id"
    assert len(headers["X-Request-ID"]) == 16
    query="&".join(f"q{i}=1" for i in range(33))
    status,_,p=_request(live_v1+"/api/v1/health?"+query)
    assert status==422
    assert p["error"]["code"]=="VALIDATION_ERROR"


def test_v1_optimizer_rejects_nonfinite_and_negative_inputs(live_v1):
    status,_,p=_request(live_v1+"/api/optimize","POST",{
        "scenario":{"demand_kg":[float("nan"),960000,1020000]}
    })
    assert status==422
    assert p["error"]["code"]=="VALIDATION_ERROR"
    status,_,p=_request(live_v1+"/api/optimize","POST",{"carbon_price_per_kg":-1})
    assert status==422
    assert p["error"]["code"]=="VALIDATION_ERROR"


def test_v1_internal_solver_failure_is_generic_500(monkeypatch,live_v1):
    import circular_battery.web.server as server_module
    def explode(_payload):
        raise RuntimeError("secret solver internals")
    monkeypatch.setattr(server_module,"optimize_payload",explode)
    status,_,p=_request(live_v1+"/api/optimize","POST",{})
    assert status==500
    assert p["error"]["code"]=="INTERNAL_ERROR"
    assert "secret solver internals" not in json.dumps(p)

def test_v1_run_creation_persists_report(live_v1):
    status,_,p=_request(live_v1+"/api/v1/runs","POST",{"name":"API run","seed":5,"raw_n":30,"reduced_k":5,"include_sensitivity":False})
    assert status==201
    rec=p["data"]
    assert rec["status"]=="COMPLETED"
    assert rec["report"]["release"]=="V1.2"
    assert rec["report"]["platform_run"]["request_id"]=="test-request"
    assert rec["report"]["platform_run"]["actor_role"]=="local"
    assert any(
        event["event_type"]=="run.started"
        and event["details"]["request_id"]=="test-request"
        for event in _request(live_v1+"/api/v1/audit")[2]["data"]
    )
    run_id=rec["run_id"]
    status,_,p=_request(live_v1+f"/api/v1/runs/{run_id}")
    assert p["data"]["decision_hash_sha256"]=="api-hash"

def test_v1_readiness_and_bundle_validation(live_v1):
    status,_,p=_request(live_v1+"/api/v1/ready")
    assert status==200
    assert p["data"]["checks"]["database"]["database"]=="ok"
    status,_,p=_request(live_v1+"/api/v1/bundles/reference/validate")
    assert status==200
    assert len(p["data"]["bundle_hash_sha256"])==64
    status,_,p=_request(live_v1+"/api/v1/bundles/reference/governance")
    assert status==200
    assert p["data"]["validation_status"]=="PASS"
    assert p["data"]["governance_status"]=="PASS"


def test_public_reference_benchmark_api_is_bounded_and_provenance_labeled(live_v1):
    status,_,p=_request(live_v1+"/api/v1/public-reference/summary")
    assert status==200
    assert p["data"]["record_count"]==6470
    assert p["data"]["evidence"]["evidence_class"]=="PUBLIC_GOVERNMENT_FACILITY_REFERENCE"

    status,_,p=_request(live_v1+"/api/v1/public-reference/facilities?state=IL&limit=2")
    assert status==200
    assert p["data"]["returned_count"]<=2
    assert all(row["state"]=="IL" for row in p["data"]["facilities"])
    assert p["data"]["evidence"]["source_workbook_sha256"]

    status,_,p=_request(live_v1+"/api/v1/public-reference/facilities?state=ILL")
    assert status==422
    assert p["error"]["code"]=="VALIDATION_ERROR"


def test_v1_bearer_authentication_and_role_gate(monkeypatch,live_v1):
    token="T"*48
    monkeypatch.setenv("CIRCULAR_DEPLOYMENT_MODE","staging")
    monkeypatch.setenv("CIRCULAR_AUTH_MODE","bearer")
    monkeypatch.setenv("CIRCULAR_API_TOKEN_SHA256",hashlib.sha256(token.encode()).hexdigest())
    monkeypatch.setenv("CIRCULAR_API_ROLE","viewer")

    status,headers,p=_request(live_v1+"/api/v1/about")
    assert status==401
    assert p["error"]["code"]=="AUTHENTICATION_REQUIRED"
    assert headers["WWW-Authenticate"]=="Bearer"

    status,_,p=_request(live_v1+"/api/v1/about",extra_headers={"Authorization":"Bearer wrong"})
    assert status==401
    assert p["error"]["code"]=="AUTHENTICATION_FAILED"

    status,_,p=_request(live_v1+"/api/v1/about",extra_headers={"Authorization":f"Bearer {token}"})
    assert status==200
    status,_,p=_request(live_v1+"/api/v1/scenarios","POST",{"name":"blocked","seed":1,"raw_n":30,"reduced_k":5},extra_headers={"Authorization":f"Bearer {token}"})
    assert status==403
    assert p["error"]["code"]=="FORBIDDEN"


def test_v12_workbench_endpoint(live_v1):
    status,_,p=_request(live_v1+"/api/v1/workbench")
    assert status==200
    assert p["data"]["version"]=="1.2.1"
    assert p["data"]["coupled_planning"]["status"]=="OPTIMAL"
    assert p["data"]["coupled_routing"]["status"]=="OPTIMAL"

def test_circular_mass_reference_and_governed_decision_api(live_v1):
    status,_,p=_request(live_v1+"/api/v1/circular-mass/reference")
    assert status==200
    assert p["data"]["algorithm"]=="CIRCULAR-MASS"
    assert len(p["data"]["scenarios"])==3

    status,_,p=_request(live_v1+"/api/v1/circular-mass/decision","POST",{
        "min_recycled_content":0.65,
        "risk_aversion":0.35,
        "max_virgin_share":0.72,
    })
    assert status==200
    d=p["data"]
    assert d["algorithm"]=="CIRCULAR-MASS"
    assert d["decision_gate"]=="AUTHORIZED"
    assert d["human_review_required"] is True
    assert d["solution"]["recycled_content_share"]>=0.65
    assert d["decision_id"].startswith("CMASS-")


def test_circular_mass_api_rejects_unknown_fields(live_v1):
    status,_,p=_request(live_v1+"/api/v1/circular-mass/decision","POST",{"magic_score":1})
    assert status==422
    assert p["error"]["code"]=="VALIDATION_ERROR"


def test_production_server_refuses_unrecorded_postgres_migration(monkeypatch):
    import circular_battery.web.server as server_module

    class FakeStore:
        def health(self):
            return {"backend":"postgres", "database":"ok", "migration_status":"BLOCKED"}

    class FakeService:
        store=FakeStore()

    monkeypatch.setenv("CIRCULAR_DEPLOYMENT_MODE", "production")
    monkeypatch.setattr(server_module, "validate_server_configuration", lambda host: None)
    monkeypatch.setattr(server_module, "get_enterprise_service", lambda: FakeService())

    with pytest.raises(RuntimeError, match="migration is not recorded"):
        server_module.run(host="127.0.0.1", port=0)
