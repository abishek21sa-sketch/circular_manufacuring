import json
from pathlib import Path
import pytest

from circular_battery.platform.storage import RunStore
from circular_battery.platform.service import EnterpriseDecisionService
from circular_battery.platform.observability import JsonlEventLogger
from circular_battery.platform.errors import ConflictError, ValidationError
from circular_battery.platform.validation import validate_decision_run_config

def test_v1_decision_config_validation_rejects_unknown_and_bad_sizes():
    with pytest.raises(ValidationError):
        validate_decision_run_config({"unknown":1})
    with pytest.raises(ValidationError):
        validate_decision_run_config({"raw_n":10})
    with pytest.raises(ValidationError):
        validate_decision_run_config({"raw_n":30,"reduced_k":31})
    cfg=validate_decision_run_config({"name":"x","seed":7,"raw_n":30,"reduced_k":5,"include_sensitivity":False})
    assert cfg["seed"]==7 and cfg["raw_n"]==30 and cfg["reduced_k"]==5

def test_v1_sqlite_registry_scenario_run_and_audit(tmp_path):
    store=RunStore(tmp_path/"registry.sqlite3")
    scenario=store.create_scenario({"name":"S","seed":1,"raw_n":30,"reduced_k":5,"include_sensitivity":False,"notes":""})
    assert scenario["scenario_id"].startswith("scn_")
    run_id=store.start_run(scenario["scenario_id"],"abc123")
    report={"decision_hash_sha256":"deadbeef","decision":{"recommended_policy":"resilience"}}
    store.complete_run(run_id,report,.25)
    rec=store.get_run(run_id)
    assert rec["status"]=="COMPLETED"
    assert rec["decision_hash_sha256"]=="deadbeef"
    assert rec["report"]["decision"]["recommended_policy"]=="resilience"
    assert store.list_runs()[0]["run_id"]==run_id
    assert any(e["event_type"]=="run.completed" for e in store.audit_events())
    with pytest.raises(ConflictError):
        store.delete_scenario(scenario["scenario_id"])

def test_v1_failed_run_is_persisted(tmp_path):
    store=RunStore(tmp_path/"registry.sqlite3")
    s=store.create_scenario({"name":"S","seed":1,"raw_n":30,"reduced_k":5,"include_sensitivity":False,"notes":""})
    run=store.start_run(s["scenario_id"],"code")
    store.fail_run(run,RuntimeError("boom"))
    rec=store.get_run(run)
    assert rec["status"]=="FAILED"
    assert rec["error"]["type"]=="RuntimeError"
    assert "message" not in rec["error"]

def test_v1_event_logger_redacts_credentials(tmp_path):
    logger=JsonlEventLogger(tmp_path/"events.jsonl")
    logger.emit(
        "security.test",
        authorization="Bearer super-secret-token",
        database_url="postgresql://user:password@example.invalid/db",
        message="provider=postgresql://user:password@example.invalid/db",
    )
    event=json.loads((tmp_path/"events.jsonl").read_text(encoding="utf-8"))
    assert event["authorization"]=="[REDACTED]"
    assert event["database_url"]=="[REDACTED]"
    assert "password" not in event["message"]

def test_v1_enterprise_service_persists_provenance(monkeypatch,tmp_path):
    import circular_battery.platform.service as service_module
    def fake_build(**kwargs):
        return {
            "release":"PHASE-10-CUMULATIVE","version":"0.x",
            "decision_hash_sha256":"hash-123",
            "decision":{"recommended_policy":"resilience","confidence":.8},
        }
    monkeypatch.setattr(service_module,"build_phase10_decision",fake_build)
    store=RunStore(tmp_path/"registry.sqlite3")
    svc=EnterpriseDecisionService(store,root=Path(__file__).resolve().parents[1],logger=JsonlEventLogger(tmp_path/"events.jsonl"))
    rec=svc.execute(payload={"name":"test","seed":9,"raw_n":30,"reduced_k":5,"include_sensitivity":False})
    assert rec["status"]=="COMPLETED"
    assert rec["report"]["release"]=="V1.2"
    assert rec["report"]["version"]=="1.2.1"
    assert rec["report"]["platform_run"]["code_fingerprint_sha256"]
    assert rec["report"]["platform_run"]["runtime_environment"]["python"]
    lines=(tmp_path/"events.jsonl").read_text(encoding="utf-8").splitlines()
    assert any(json.loads(x)["event_type"]=="decision_run.completed" for x in lines)


def test_v1_runstore_explicitly_closes_every_sqlite_connection(monkeypatch, tmp_path):
    import sqlite3
    import circular_battery.platform.storage as storage_module

    original_connect = sqlite3.connect
    created = []
    closed = []

    class TrackingConnection(sqlite3.Connection):
        def close(self):
            closed.append(id(self))
            return super().close()

    def tracking_connect(*args, **kwargs):
        kwargs["factory"] = TrackingConnection
        con = original_connect(*args, **kwargs)
        created.append(id(con))
        return con

    monkeypatch.setattr(storage_module.sqlite3, "connect", tracking_connect)

    store = storage_module.RunStore(tmp_path / "closure.sqlite3")
    scenario = store.create_scenario({
        "name": "closure-test",
        "seed": 1,
        "raw_n": 30,
        "reduced_k": 5,
        "include_sensitivity": False,
        "notes": "",
    })
    run_id = store.start_run(scenario["scenario_id"], "fingerprint")
    store.complete_run(
        run_id,
        {"decision_hash_sha256": "abc", "decision": {"recommended_policy": "resilience"}},
        0.01,
    )
    store.get_run(run_id)
    store.list_runs()
    store.audit_events()
    store.health()

    assert created
    assert sorted(created) == sorted(closed)
