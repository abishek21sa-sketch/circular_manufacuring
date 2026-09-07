import json
from pathlib import Path

from scripts.validate_data_source_registry import validate_registry
from circular4x.signature_algorithm import reference_problem


ROOT = Path(__file__).resolve().parents[1]


def test_data_source_registry_is_complete_and_explicit_about_fallback():
    report = validate_registry(ROOT / "data/public/data_source_registry.json")
    assert report["status"] == "PASS", report["errors"]
    assert report["source_count"] >= 10
    assert report["integrated_reference_count"] >= 1


def test_data_source_registry_rejects_missing_limitations(tmp_path):
    registry = {
        "sources": [{"source_id": "bad", "status": "integrated_reference", "data_role": ["x"], "usable_for_current_benchmark": True}],
        "fallback_policy": {"canonical_dataset": "data/synthetic/enterprise_120k/", "row_count": 120000, "evidence_class": "SYNTHETIC VALIDATION"},
        "github_disclosure": "disclosed",
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    report = validate_registry(path)
    assert report["status"] == "FAIL"
    assert any("limitation" in error for error in report["errors"])


def test_academic_solver_profile_selects_explicit_gurobi(monkeypatch):
    monkeypatch.setenv("CIRCULAR_SOLVER_BACKEND", "gurobi")
    _, config = reference_problem()
    assert config.solver_backend == "gurobi"
