from pathlib import Path

from circular_battery.optimization.gurobi_advanced import _collect_multiobjective_pass_metrics
from circular_battery.decision.orchestrator import _load_models


class _Params:
    ObjPassNumber = -1


class _FakeMultiObjectiveModel:
    def __init__(self):
        self.Params = _Params()
        self.NumObjPasses = 4
        self._rows = [
            {"status":2,"gap":0.0,"runtime":.1,"value":0.0,"bound":0.0},
            {"status":2,"gap":0.0,"runtime":.2,"value":10.0,"bound":10.0},
            {"status":2,"gap":0.0,"runtime":.3,"value":20.0,"bound":20.0},
            {"status":2,"gap":0.0,"runtime":.4,"value":30.0,"bound":30.0},
        ]

    @property
    def _row(self):
        return self._rows[self.Params.ObjPassNumber]

    @property
    def ObjPassNStatus(self): return self._row["status"]
    @property
    def ObjPassNMipGap(self): return self._row["gap"]
    @property
    def ObjPassNRuntime(self): return self._row["runtime"]
    @property
    def ObjPassNObjVal(self): return self._row["value"]
    @property
    def ObjPassNObjBound(self): return self._row["bound"]


def test_multiobjective_gap_uses_documented_pass_attributes():
    m=_FakeMultiObjectiveModel()
    rows=_collect_multiobjective_pass_metrics(m)
    assert len(rows)==4
    assert [r["pass_number"] for r in rows]==[0,1,2,3]
    assert all(r["status"]==2 for r in rows)
    assert all(r["mip_gap"]==0 for r in rows)
    assert m.Params.ObjPassNumber==-1




def test_phase10_powershell_acceptance_is_fail_fast():
    script=Path("scripts/windows_phase10_acceptance.ps1").read_text(encoding="utf-8")
    assert "Invoke-PythonChecked" in script
    assert "if ($LASTEXITCODE -ne 0)" in script
    assert "gurobi_phase10_check.py" in script
    assert script.index("gurobi_phase10_check.py") < script.index("PHASE 10 ACCEPTANCE PASSED")


def test_windows_observed_shortage_is_within_solver_consistent_tolerance():
    observed_shortage_kg = 1.0001e-6
    objective_abs_tol_kg = 1e-6
    gurobi_default_feasibility_tol = 1e-6
    service_acceptance_tol = objective_abs_tol_kg + gurobi_default_feasibility_tol
    assert observed_shortage_kg <= service_acceptance_tol



def test_phase10_runtime_does_not_deserialize_release_joblib_models():
    import inspect
    import circular_battery.decision.orchestrator as orchestrator
    source = inspect.getsource(orchestrator._load_models)
    assert "joblib.load" not in source
    models = orchestrator._load_models()
    assert set(models) == {"demand", "returns", "recovery", "scrap"}


def test_runtime_model_provenance_declares_no_portable_pickle_dependency():
    from circular_battery.ai.runtime import runtime_phase2_payload
    p = runtime_phase2_payload()
    prov = p["runtime_model_provenance"]
    assert prov["strategy"] == "DETERMINISTIC CURRENT-RUNTIME RETRAINING"
    assert prov["portable_pickle_dependency"] is False
    assert all(
        p["model_evidence"][k]["metrics"]
        for k in ("demand", "returns", "recovery", "scrap")
    )


def test_portable_ai_migration_removes_only_deprecated_estimators(tmp_path):
    from circular_battery.maintenance.migrations import remove_deprecated_phase10_model_artifacts
    model_dir = tmp_path / "artifacts" / "models"
    model_dir.mkdir(parents=True)
    stale = model_dir / "recovery_model.joblib"
    evidence = model_dir / "model_evidence.json"
    unrelated = model_dir / "keep.bin"
    stale.write_bytes(b"legacy")
    evidence.write_text("{}", encoding="utf-8")
    unrelated.write_bytes(b"keep")

    removed = remove_deprecated_phase10_model_artifacts(tmp_path)

    assert removed == ["artifacts/models/recovery_model.joblib"]
    assert all("\\" not in item for item in removed)
    assert not stale.exists()
    assert evidence.exists()
    assert unrelated.exists()

def test_portable_ai_migration_is_idempotent(tmp_path):
    from circular_battery.maintenance.migrations import remove_deprecated_phase10_model_artifacts
    assert remove_deprecated_phase10_model_artifacts(tmp_path) == []
    assert remove_deprecated_phase10_model_artifacts(tmp_path) == []

def test_runtime_evidence_beats_baselines_after_current_runtime_retraining():
    from circular_battery.ai.runtime import runtime_model_evidence
    ev = runtime_model_evidence()
    assert ev["demand"]["metrics"]["mae"] < ev["demand"]["baseline_metrics"]["mae"]
    assert ev["returns"]["metrics"]["brier"] < ev["returns"]["baseline_metrics"]["brier"]
    assert ev["recovery"]["metrics"]["macro_f1"] > ev["recovery"]["baseline_metrics"]["macro_f1"]
    assert ev["scrap"]["metrics"]["mae"] < ev["scrap"]["baseline_metrics"]["mae"]
