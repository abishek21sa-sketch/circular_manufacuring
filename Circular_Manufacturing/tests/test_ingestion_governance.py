import json
import shutil
from pathlib import Path

import pytest

from circular_battery.ingestion.governance import inspect_bundle, validate_governed_bundle
from circular_battery.platform.errors import ValidationError


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "data" / "templates" / "reference_bundle"


def test_reference_bundle_has_lineage_quality_and_file_fingerprints():
    report = inspect_bundle(REF, require_lineage=True)
    assert report["validation_status"] == "PASS"
    assert report["governance_status"] == "PASS"
    assert report["accepted_for_optimization"] is True
    assert report["evidence_class"] == "SYNTHETIC VALIDATION"
    assert report["ingestion_id"].startswith("ing_")
    assert len(report["files"]) == 5
    assert all(len(item["sha256"]) == 64 for item in report["files"])
    assert validate_governed_bundle(REF)["ingestion_id"] == report["ingestion_id"]


def test_missing_lineage_is_pending_for_inspection_but_rejected_for_pilot(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(REF, bundle)
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    manifest.pop("lineage")
    (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = inspect_bundle(bundle)
    assert report["validation_status"] == "PASS"
    assert report["governance_status"] == "PENDING"
    assert report["accepted_for_optimization"] is True
    with pytest.raises(ValidationError, match="not eligible"):
        validate_governed_bundle(bundle)


def test_missing_required_csv_column_fails_quality_gate(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(REF, bundle)
    path = bundle / "materials.csv"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("kg_per_pack,", "removed_kg_per_pack,", 1), encoding="utf-8")
    report = inspect_bundle(bundle)
    assert report["validation_status"] == "FAIL"
    assert report["checks"]["schema_integrity"]["status"] == "FAIL"
    assert report["accepted_for_optimization"] is False
