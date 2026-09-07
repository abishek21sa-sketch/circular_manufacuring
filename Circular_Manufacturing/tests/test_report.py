from circular_battery.reporting.report import build_phase1_report
def test_report_labels_synthetic_evidence():
    r = build_phase1_report()
    assert r["data_status"] == "SYNTHETIC VALIDATION"
    assert r["release"] == "PHASE-1"
    assert len(r["periods"]) == 3
