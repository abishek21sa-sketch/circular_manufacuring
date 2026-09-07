import pytest

from scripts.benefit_measurement import build_measurement_report


def test_benefit_measurement_calculates_directional_improvement():
    report = build_measurement_report(
        [
            {"period": "2026-Q1", "metric": "service_level", "baseline_value": "0.90", "observed_value": "0.95", "unit": "fraction", "aggregation": "mean", "source_ref": "plant-system://service"},
            {"period": "2026-Q1", "metric": "cost_usd", "baseline_value": "1000", "observed_value": "800", "unit": "USD", "aggregation": "sum", "source_ref": "finance-ledger://cost"},
        ],
        baseline_id="baseline-001",
    )

    assert report["status"] == "PASS"
    assert report["evidence_class"] == "REALIZED_PILOT_MEASUREMENT"
    summary = {item["metric"]: item for item in report["summary"]}
    assert summary["service_level"]["improvement"] == pytest.approx(0.05)
    assert summary["cost_usd"]["improvement"] == 200


def test_benefit_measurement_rejects_bad_units_and_rates():
    report = build_measurement_report(
        [
            {"period": "2026-Q1", "metric": "service_level", "baseline_value": "1.2", "observed_value": "0.8", "unit": "percent", "aggregation": "mean", "source_ref": "source"},
        ]
    )

    assert report["status"] == "BLOCKED"
    assert {error["reason"] for error in report["errors"]} >= {"unit_mismatch", "fraction_out_of_range"}
