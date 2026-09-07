from scripts.validate_engineering_readiness import build_report


def test_engineering_gate_passes_without_production_claim():
    report = build_report()
    assert report["status"] == "PASS", report["checks"]
    assert report["passed_checks"] == report["total_checks"]
    assert "not production certification" in report["claim_boundary"]
