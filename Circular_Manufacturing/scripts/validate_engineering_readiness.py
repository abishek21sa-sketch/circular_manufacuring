"""Validate the IE/math/AI/ML engineering evidence envelope."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "artifacts" / "engineering_readiness.json"


def _load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _exists(relative: str) -> bool:
    return (ROOT / relative).is_file()


def build_report() -> dict:
    readiness = _load_json(ROOT / "artifacts" / "release_readiness.json")
    source_registry = _load_json(ROOT / "artifacts" / "data_source_registry_validation.json")
    synthetic = _load_json(ROOT / "artifacts" / "synthetic_enterprise_validation.json")
    synthetic_gurobi = _load_json(ROOT / "artifacts" / "synthetic_enterprise_gurobi_validation.json")
    circular_mass = _load_json(ROOT / "artifacts" / "circular_mass" / "gurobi_validation.json")
    model_evidence_text = (ROOT / "artifacts" / "models" / "model_evidence.json").read_text(encoding="utf-8") if _exists("artifacts/models/model_evidence.json") else ""
    bridge_text = (ROOT / "src" / "circular_battery" / "decision" / "circular_mass_bridge.py").read_text(encoding="utf-8") if _exists("src/circular_battery/decision/circular_mass_bridge.py") else ""

    checks = {
        "engineering_release_gate": readiness.get("engineering_gate", {}).get("status") == "PASS",
        "explicit_gurobi_optimality": (
            circular_mass.get("solver") == "gurobi"
            and circular_mass.get("reference", {}).get("status") == "OPTIMAL"
            and circular_mass.get("reference", {}).get("mip_gap", 1.0) <= 1e-9
        ),
        "synthetic_scale_and_case_coverage": (
            synthetic.get("status") == "PASS"
            and synthetic.get("row_count", 0) >= 10000
            and len(synthetic.get("case_counts", {})) >= 12
        ),
        "synthetic_gurobi_benchmark": (
            synthetic_gurobi.get("status") == "PASS"
            and synthetic_gurobi.get("solver") == "gurobi"
            and synthetic_gurobi.get("input_rows", 0) >= 10000
        ),
        "industrial_engineering_and_or_docs": all(_exists(path) for path in (
            "docs/TECHNICAL_METHODS.md",
            "docs/V12_MATH_AND_INTEGRATION_AUDIT.md",
            "docs/AI_MODEL_CARDS_PHASE10.md",
        )),
        "ai_ml_evidence_is_labeled": "SYNTHETIC VALIDATION" in model_evidence_text,
        "data_governance_boundary": (
            source_registry.get("status") == "PASS"
            and source_registry.get("source_count", 0) >= 12
            and source_registry.get("integrated_reference_count", 0) >= 1
        ),
        "reproducibility_and_license_boundary": (
            _exists("requirements-windows-py314.lock")
            and "gurobipy==13.0.3" in (ROOT / "requirements-windows-py314.lock").read_text(encoding="utf-8")
            and _exists("docs/DATA_SOURCE_REVIEW.md")
        ),
        "human_review_and_claim_boundary": (
            '"human_review_required": True' in bridge_text
            and "no field-calibrated" in bridge_text
        ),
        "source_registry_and_engineering_rubric_present": (
            _exists("data/public/data_source_registry.json")
            and _exists("docs/ENGINEERING_READINESS.md")
        ),
    }
    passed = all(checks.values())
    return {
        "schema_version": "1.0",
        "status": "PASS" if passed else "FAIL",
        "gate": "ENGINEERING_IE_MATH_AI_ML",
        "checks": checks,
        "passed_checks": sum(checks.values()),
        "total_checks": len(checks),
        "license_policy": "Academic Gurobi for student/research engineering validation only; commercial authorization remains external.",
        "claim_boundary": "This is a portfolio engineering rubric, not production certification or evidence of field accuracy, realized savings, regulatory compliance, or commercial authorization.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = build_report()
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"ENGINEERING_READINESS status={report['status']} checks={report['passed_checks']}/{report['total_checks']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
