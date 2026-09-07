import json
import shutil

from scripts.validate_pilot_bundle import validate_pilot_bundle


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "templates" / "reference_bundle"


def test_reference_bundle_is_not_eligible_as_a_plant_pilot():
    report = validate_pilot_bundle(REFERENCE)

    assert report["pilot_status"] == "BLOCKED"
    assert report["pilot_eligible"] is False
    assert report["checks"]["non_synthetic_pilot_evidence"]["status"] == "BLOCKED"


def test_operational_lineage_can_pass_pilot_label_gate(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(REFERENCE, bundle)
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["evidence_class"] = "PILOT VALIDATION"
    manifest["lineage"] = {
        "source_system": "plant-data-platform",
        "source_owner": "plant-operations",
        "facility_id": "plant-001",
        "as_of_utc": "2026-09-05T00:00:00+00:00",
        "data_classification": "operational-controlled",
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_pilot_bundle(bundle)

    assert report["pilot_status"] == "PASS"
    assert report["pilot_eligible"] is True
