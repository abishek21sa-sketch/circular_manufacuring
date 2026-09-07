from pathlib import Path

from scripts.validate_synthetic_enterprise_dataset import validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "synthetic" / "enterprise_120k"


def test_synthetic_enterprise_dataset_is_large_covered_and_valid():
    report = validate_dataset(DATASET)
    assert report["status"] == "PASS"
    assert report["row_count"] >= 120000
    assert len(report["case_counts"]) == 12
    assert all(count >= 50 for count in report["case_counts"].values())
    assert report["checks"]["public_context_profile_declared"] is True
    assert report["checks"]["trend_profiles_declared"] is True
