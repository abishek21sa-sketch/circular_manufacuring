from __future__ import annotations
from dataclasses import asdict
import json
import math
from pathlib import Path

from circular_battery.optimization.network import NetworkScenario, solve_network
from circular_battery.optimization.frontier import circular_strategy_frontier
from circular_battery.simulation.stochastic import stress_test_policy
from circular_battery.reporting.phase567 import build_phase567_report
from circular_battery.decision.orchestrator import build_phase10_decision
from circular_battery.platform.service import get_enterprise_service
from circular_battery.platform.validation import validate_decision_run_config
from circular_battery.platform.provenance import environment_snapshot
from circular_battery.ingestion.bundle import validate_bundle
from circular_battery.ingestion.governance import inspect_bundle
from circular_battery.ingestion.public_reference import public_reference_summary, public_reference_facilities
from circular_battery.decision.circular_mass_bridge import build_circular_mass_decision, circular_mass_reference_payload
from circular_battery.paths import find_repo_root

ROOT = find_repo_root()
VERSION="1.2.1"

def _load(name):
    p=ROOT/"artifacts"/name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def reference_payload():
    phase10=_load("v1_reference_decision_report.json") or _load("phase10_decision_report.json")
    return {
        "phase1":_load("phase1_engineering_report.json"),
        "phase2":{**(_load("phase2_ai_decision.json") or {}),"model_evidence":_load("models/model_evidence.json")},
        "phase3":_load("phase3_strategy_report.json"),
        "phase567":_load("phase567_integrated_report.json"),
        "phase10":phase10,
        "evidence":{
            "data_status":"SYNTHETIC VALIDATION",
            "real_world_validation":"PENDING",
            "release":"V1.2",
            "version":VERSION,
            "external_data_ingestion":"IMPLEMENTED; SOURCE TRUTH VALIDATION REMAINS USER/EXTERNAL RESPONSIBILITY",
        },
    }

def scenario_from_payload(payload:dict)->NetworkScenario:
    base=NetworkScenario()
    allowed=set(base.__dict__)
    values=dict(base.__dict__)
    unknown=sorted(set(payload)-allowed)
    if unknown:
        raise ValueError(f"Unknown scenario fields: {unknown}")
    for key,value in payload.items():
        if key in {"demand_kg","returns_kg"}:
            value=tuple(float(x) for x in value)
        elif key=="periods":
            value=int(value)
        else:
            value=float(value)
        values[key]=value
    for key,value in values.items():
        if key in {"demand_kg","returns_kg"}:
            if any(not math.isfinite(float(x)) for x in value):
                raise ValueError(f"{key} values must be finite.")
        elif key != "periods" and not math.isfinite(float(value)):
            raise ValueError(f"{key} must be finite.")
    s=NetworkScenario(**values)
    if s.periods<=0 or len(s.demand_kg)!=s.periods or len(s.returns_kg)!=s.periods:
        raise ValueError("periods must match demand_kg and returns_kg lengths.")
    if any(x<0 for x in s.demand_kg+s.returns_kg):
        raise ValueError("demand_kg and returns_kg must be nonnegative.")
    if not 0<=s.collection_rate<=1:
        raise ValueError("collection_rate must be in [0,1].")
    for key in ("recycle_yield","reman_yield"):
        if not 0<=getattr(s,key)<=1:
            raise ValueError(f"{key} must be in [0,1].")
    for key in ("recycle_capacity_kg","reman_capacity_kg","fixed_recycle_cost","fixed_reman_cost",
                "virgin_cost_per_kg","recycle_cost_per_kg","reman_cost_per_kg","disposal_cost_per_kg",
                "inventory_cost_per_kg","virgin_carbon_per_kg","recycle_carbon_per_kg","reman_carbon_per_kg",
                "disposal_carbon_per_kg","initial_inventory_kg","max_inventory_kg"):
        if getattr(s,key)<0:
            raise ValueError(f"{key} must be nonnegative.")
    if s.initial_inventory_kg>s.max_inventory_kg:
        raise ValueError("initial_inventory_kg must be <= max_inventory_kg.")
    return s

def optimize_payload(payload:dict):
    scenario_payload=payload.get("scenario")
    if scenario_payload is None:
        scenario_payload={k:v for k,v in payload.items() if k not in {"carbon_price_per_kg","virgin_penalty_per_kg"}}
    s=scenario_from_payload(scenario_payload)
    carbon_price=float(payload.get("carbon_price_per_kg",0.0))
    virgin_penalty=float(payload.get("virgin_penalty_per_kg",0.0))
    if not math.isfinite(carbon_price) or carbon_price < 0:
        raise ValueError("carbon_price_per_kg must be finite and nonnegative.")
    if not math.isfinite(virgin_penalty) or virgin_penalty < 0:
        raise ValueError("virgin_penalty_per_kg must be finite and nonnegative.")
    sol=solve_network(s,carbon_price_per_kg=carbon_price,virgin_penalty_per_kg=virgin_penalty)
    return {"scenario":asdict(s),"solution":sol.to_dict(),"evidence_class":"CALCULATED FROM USER/SYNTHETIC SCENARIO"}

def frontier_payload(payload:dict):
    scenario_payload=payload.get("scenario")
    if scenario_payload is None:
        scenario_payload={k:v for k,v in payload.items() if k not in {"carbon_price_per_kg","virgin_penalty_per_kg"}}
    s=scenario_from_payload(scenario_payload)
    return {"scenario":asdict(s),"frontier":circular_strategy_frontier(s),"evidence_class":"SCENARIO STRATEGY EXPERIMENT"}

def stress_payload(payload:dict):
    scenario_payload=payload.get("scenario",{})
    s=scenario_from_payload(scenario_payload)
    n=min(max(int(payload.get("n",100)),10),500)
    seed=int(payload.get("seed",20260816))
    return {"scenario":asdict(s),"stress":stress_test_policy(s,n=n,seed=seed)}

def phase567_payload():
    return _load("phase567_integrated_report.json") or build_phase567_report()

def lifecycle_payload(): return phase567_payload()["phase5"]
def reverse_logistics_payload(): return phase567_payload()["phase6"]
def production_plan_payload(): return phase567_payload()["phase7"]

def phase10_payload(seed=20260817,raw_n=60,reduced_k=8):
    artifact=_load("v1_reference_decision_report.json") or _load("phase10_decision_report.json")
    return artifact or build_phase10_decision(seed=seed,raw_n=raw_n,reduced_k=reduced_k)

def v1_health():
    return {"status":"ok","service":"material-circularity-studio","version":VERSION}

def v1_ready():
    service=get_enterprise_service()
    database=service.store.health()
    database_ready=(
        database.get("database")=="ok"
        and (database.get("backend")!="postgres" or database.get("migration_status")=="PASS")
    )
    checks={
        "database":database,
        "frontend":(ROOT/"web"/"dist"/"index.html").is_file(),
        "phase10_reference":(ROOT/"artifacts"/"v1_reference_decision_report.json").is_file() or (ROOT/"artifacts"/"phase10_decision_report.json").is_file(),
        "bundle_template":(ROOT/"data"/"templates"/"reference_bundle"/"manifest.json").is_file(),
    }
    boolean_checks=all(value for value in checks.values() if isinstance(value,bool))
    return {"status":"ready" if database_ready and boolean_checks else "degraded","checks":checks}

def v1_about():
    return {
        "name":"Circular Battery Manufacturing & Recovery Decision Intelligence Platform",
        "version":VERSION,
        "decision_chain":["AI prediction","uncertainty bridge","lifecycle/material accounting","reverse logistics","IE planning","stochastic MILP","critical-material sourcing","CVRP","digital experiments","recommendation"],
        "evidence_boundary":{
            "reference_data":"SYNTHETIC VALIDATION",
            "external_bundle_support":"IMPLEMENTED",
            "realized_operational_benefits":"NOT CLAIMED",
            "field_calibration":"PENDING",
        },
        "runtime":environment_snapshot(ROOT),
    }

def create_scenario_payload(payload):
    return get_enterprise_service().create_scenario(payload)

def list_scenarios_payload(limit=50):
    return get_enterprise_service().store.list_scenarios(limit)

def get_scenario_payload(scenario_id):
    return get_enterprise_service().store.get_scenario(scenario_id)

def delete_scenario_payload(scenario_id):
    get_enterprise_service().store.delete_scenario(scenario_id)
    return {"deleted":scenario_id}

def create_run_payload(payload, *, request_id=None, actor_role=None):
    payload=dict(payload or {})
    scenario_id=payload.pop("scenario_id",None)
    return get_enterprise_service().execute(
        payload=payload or None,
        scenario_id=scenario_id,
        request_id=request_id,
        actor_role=actor_role,
    )

def list_runs_payload(limit=50):
    return get_enterprise_service().store.list_runs(limit)

def get_run_payload(run_id):
    return get_enterprise_service().store.get_run(run_id)

def audit_payload(limit=100):
    return get_enterprise_service().store.audit_events(limit)

def import_scenario_payload(payload):
    cfg=validate_decision_run_config(payload.get("config",payload))
    return get_enterprise_service().store.import_scenario({"config":cfg})

def validate_reference_bundle_payload():
    return validate_bundle(ROOT/"data"/"templates"/"reference_bundle")

def governance_reference_bundle_payload():
    return inspect_bundle(ROOT/"data"/"templates"/"reference_bundle")

def public_reference_summary_payload():
    return public_reference_summary()

def public_reference_facilities_payload(*, state=None, naics=None, query=None, limit=50):
    return public_reference_facilities(state=state, naics=naics, query=query, limit=limit)


def circular_mass_reference_service_payload():
    return circular_mass_reference_payload()

def circular_mass_decision_payload(payload):
    payload=dict(payload or {})
    allowed={"min_recycled_content","risk_aversion","max_virgin_share"}
    unknown=sorted(set(payload)-allowed)
    if unknown:
        raise ValueError(f"Unknown CIRCULAR-MASS fields: {unknown}")
    return build_circular_mass_decision(
        min_recycled_content=float(payload.get("min_recycled_content",0.20)),
        risk_aversion=float(payload.get("risk_aversion",0.35)),
        max_virgin_share=float(payload.get("max_virgin_share",0.72)),
    )


def workbench_v12_payload():
    artifact=_load("v12_workbench_report.json")
    if artifact is not None:
        return artifact
    from circular_battery.decision.workbench_v12 import build_workbench_v12
    return build_workbench_v12()
