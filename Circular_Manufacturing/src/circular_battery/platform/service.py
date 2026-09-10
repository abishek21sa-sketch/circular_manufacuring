from __future__ import annotations
import os, time
from pathlib import Path
from circular_battery.decision.orchestrator import build_phase10_decision
from circular_battery.platform.storage import RunStore
from circular_battery.platform.postgres_storage import PostgresRunStore
from circular_battery.platform.validation import validate_decision_run_config
from circular_battery.platform.provenance import code_fingerprint, environment_snapshot
from circular_battery.platform.observability import JsonlEventLogger
from circular_battery.platform.errors import ExecutionError
from circular_battery.paths import find_repo_root

ROOT=find_repo_root()

class EnterpriseDecisionService:
    def __init__(self, store:RunStore, *, root:Path|str=ROOT, logger:JsonlEventLogger|None=None):
        self.root=Path(root)
        self.store=store
        self.logger=logger or JsonlEventLogger(self.root/"artifacts"/"logs"/"platform.jsonl")

    def create_scenario(self,payload):
        cfg=validate_decision_run_config(payload)
        return self.store.create_scenario(cfg)

    def execute(
        self,
        payload:dict|None=None,
        scenario_id:str|None=None,
        *,
        request_id:str|None=None,
        actor_role:str|None=None,
    ):
        if scenario_id:
            scenario=self.store.get_scenario(scenario_id)
            cfg=validate_decision_run_config(scenario["config"])
        else:
            cfg=validate_decision_run_config(payload)
            scenario=self.store.create_scenario(cfg)
            scenario_id=scenario["scenario_id"]

        fp=code_fingerprint(self.root)
        run_id=self.store.start_run(
            scenario_id,
            fp,
            request_id=request_id,
            actor_role=actor_role or "unknown",
        )
        self.logger.emit(
            "decision_run.started",
            run_id=run_id,
            scenario_id=scenario_id,
            config_hash=scenario["config_hash_sha256"],
            request_id=request_id,
            actor_role=actor_role or "unknown",
        )
        started=time.perf_counter()
        try:
            report=build_phase10_decision(
                seed=cfg["seed"],raw_n=cfg["raw_n"],reduced_k=cfg["reduced_k"],
                include_sensitivity=cfg["include_sensitivity"],
            )
            report["release"]="V1.2"
            report["version"]="1.2.1"
            report["platform_run"]={
                "run_id":run_id,"scenario_id":scenario_id,
                "scenario_config_hash_sha256":scenario["config_hash_sha256"],
                "code_fingerprint_sha256":fp,
                "request_id":request_id,
                "actor_role":actor_role or "unknown",
                "runtime_environment":environment_snapshot(self.root),
            }
            runtime=time.perf_counter()-started
            self.store.complete_run(run_id,report,runtime)
            self.logger.emit(
                "decision_run.completed",
                run_id=run_id,
                scenario_id=scenario_id,
                runtime_seconds=runtime,
                decision_hash=report.get("decision_hash_sha256"),
                request_id=request_id,
                actor_role=actor_role or "unknown",
            )
            return self.store.get_run(run_id)
        except Exception as exc:
            self.store.fail_run(run_id,exc)
            self.logger.emit("decision_run.failed",run_id=run_id,scenario_id=scenario_id,error_type=type(exc).__name__)
            raise ExecutionError("Decision run failed.",details={"run_id":run_id}) from exc

def default_store():
    backend=os.getenv("CIRCULAR_PLATFORM_DB_BACKEND","sqlite").strip().lower()
    if backend=="postgres":
        dsn=os.getenv("CIRCULAR_DATABASE_URL","").strip()
        if not dsn:
            raise RuntimeError("CIRCULAR_DATABASE_URL is required for the PostgreSQL backend.")
        return PostgresRunStore(dsn)
    if backend not in {"sqlite", ""}:
        raise RuntimeError("CIRCULAR_PLATFORM_DB_BACKEND must be sqlite or postgres.")
    db=os.getenv("CIRCULAR_PLATFORM_DB")
    path=Path(db) if db else ROOT/"artifacts"/"platform"/"circular_v1.sqlite3"
    return RunStore(path)

_SERVICE=None
def get_enterprise_service():
    global _SERVICE
    if _SERVICE is None:
        _SERVICE=EnterpriseDecisionService(default_store())
    return _SERVICE
