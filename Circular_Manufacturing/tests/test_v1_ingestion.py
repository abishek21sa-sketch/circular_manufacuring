from pathlib import Path
import shutil, csv, json
import pytest

from circular_battery.ingestion.bundle import validate_bundle, run_bundle
from circular_battery.platform.errors import ValidationError

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/"data"/"templates"/"reference_bundle"

def test_v1_reference_bundle_validates_and_hashes():
    r=validate_bundle(REF)
    assert r["manifest"]["evidence_class"]=="SYNTHETIC VALIDATION"
    assert len(r["bundle_hash_sha256"])==64
    assert len(r["files"])==6

def test_v1_reference_bundle_runs_full_ingested_core_chain():
    r=run_bundle(REF)
    assert r["lifecycle"]["max_material_balance_error_kg"] < 1e-6
    assert r["reverse_logistics"]["status"]=="OPTIMAL"
    assert r["reverse_logistics"]["max_constraint_violation"] < 1e-6
    assert r["planning"]["solution"]["status"]=="OPTIMAL"
    assert r["planning"]["solution"]["max_constraint_violation"] < 1e-6
    assert r["planning"]["solution"]["total_recovered_use_kg"] > 0
    assert r["integration"]["network_capture_rate"] > 0

def test_v1_bundle_missing_file_rejected(tmp_path):
    shutil.copytree(REF,tmp_path/"bundle")
    (tmp_path/"bundle"/"facilities.csv").unlink()
    with pytest.raises(ValidationError):
        validate_bundle(tmp_path/"bundle")

def test_v1_bundle_invalid_recycling_yield_rejected(tmp_path):
    dst=tmp_path/"bundle";shutil.copytree(REF,dst)
    rows=list(csv.DictReader((dst/"materials.csv").open(encoding="utf-8")))
    rows[0]["recycling_yield"]="1.4"
    with (dst/"materials.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    with pytest.raises(ValidationError):
        run_bundle(dst)

def test_v1_external_evidence_label_is_preserved(tmp_path):
    dst=tmp_path/"bundle";shutil.copytree(REF,dst)
    m=json.loads((dst/"manifest.json").read_text(encoding="utf-8"))
    m["evidence_class"]="USER-SUPPLIED / UNVALIDATED"
    (dst/"manifest.json").write_text(json.dumps(m),encoding="utf-8")
    r=run_bundle(dst)
    assert r["bundle"]["evidence_class"]=="USER-SUPPLIED / UNVALIDATED"
    assert "does not independently verify source truth" in r["claims_boundary"]
