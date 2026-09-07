from __future__ import annotations

import json
from pathlib import Path

from scripts.release_readiness import build_readiness


ROOT = Path(__file__).resolve().parents[1]


def test_release_readiness_separates_engineering_and_commercial_gates():
    report = build_readiness(ROOT)

    assert report["schema_version"] == "1.0"
    assert report["engineering_gate"]["status"] == "PASS"
    assert report["engineering_gate"]["passed_checks"] == report["engineering_gate"]["total_checks"]
    assert report["commercial_production_gate"]["status"] == "BLOCKED"
    blocker_ids = {item["id"] for item in report["commercial_production_gate"]["blockers"]}
    assert "commercial_gurobi_entitlement" in blocker_ids
    assert "enterprise_identity_and_transport" in blocker_ids
    assert "field_calibration_and_data_lineage" in blocker_ids
    assert "realized_benefit_validation" in blocker_ids


def test_release_readiness_artifact_is_machine_readable():
    report = json.loads((ROOT / "artifacts/release_readiness.json").read_text(encoding="utf-8"))
    assert report["release_class"] == "GUROBI_VERIFIED_ENGINEERING_RC"
    assert report["engineering_gate"]["status"] == "PASS"
    assert report["commercial_production_gate"]["status"] == "BLOCKED"
    assert len(report["evidence_fingerprints"]) >= 10
