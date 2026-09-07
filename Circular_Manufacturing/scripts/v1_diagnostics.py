from __future__ import annotations
import json,tempfile
from pathlib import Path

from circular_battery import __version__
from circular_battery.ingestion.bundle import validate_bundle,run_bundle
from circular_battery.platform.storage import RunStore
from circular_battery.platform.provenance import environment_snapshot
from circular_battery.web.service import reference_payload

ROOT=Path(__file__).resolve().parents[1]
compliance=json.loads((ROOT/"docs/validation/v1_compliance.json").read_text(encoding="utf-8"))
ref=reference_payload()
bundle_meta=validate_bundle(ROOT/"data/templates/reference_bundle")
bundle=run_bundle(ROOT/"data/templates/reference_bundle")

with tempfile.TemporaryDirectory() as td:
    store=RunStore(Path(td)/"diag.sqlite3")
    health=store.health()
    scenario=store.create_scenario({"name":"diagnostic","seed":1,"raw_n":30,"reduced_k":5,"include_sensitivity":False,"notes":""})
    registry_ok=bool(scenario["scenario_id"]) and health["database"]=="ok"

required_docs=[
    "README.md","docs/TECHNICAL_METHODS.md","docs/ARCHITECTURE.md","docs/DATA_INGESTION.md",
    "docs/API.md","docs/SECURITY.md","docs/LIMITATIONS.md","docs/CONSTITUTION_COMPLIANCE_MATRIX_V1.md",
]
missing_docs=[x for x in required_docs if not (ROOT/x).is_file()]
bad_status=[r for r in compliance["requirements"] if "NOT_IMPLEMENTED" in r["status"] or r["status"]=="PARTIAL"]
missing_evidence=[r for r in compliance["requirements"] if not (ROOT/r["evidence"]).exists()]
html=(ROOT/"web/dist/index.html").read_text(encoding="utf-8")
checks={
    "version_1_2_1":__version__=="1.2.1",
    "reference_release_v1":ref["evidence"]["release"]=="V1.2" and ref["evidence"]["version"]=="1.2.1",
    "phase10_reference_present":bool(ref.get("phase10")),
    "frontend_v1_depth":all(x in html for x in ("MATERIALS","NETWORK","PLAN","STRATEGY","ROUTES","AI","RISK","TRACE","RUNS","EVIDENCE")),
    "external_bundle_valid":len(bundle_meta["bundle_hash_sha256"])==64,
    "external_bundle_mass_closes":bundle["lifecycle"]["max_material_balance_error_kg"]<1e-6,
    "external_bundle_reverse_optimal":bundle["reverse_logistics"]["status"]=="OPTIMAL",
    "external_bundle_plan_optimal":bundle["planning"]["solution"]["status"]=="OPTIMAL",
    "registry_operational":registry_ok,
    "compliance_no_unimplemented":not bad_status,
    "compliance_evidence_paths_exist":not missing_evidence,
    "required_docs_present":not missing_docs,
    "render_asset":(ROOT/"render.yaml").is_file(),
    "docker_asset":(ROOT/"Dockerfile").is_file(),
    "env_template":(ROOT/".env.example").is_file(),
    "no_release_joblib_estimators":not list((ROOT/"artifacts/models").glob("*_model.joblib")),
}
out={
    "release":"V1.2","version":__version__,"passed":all(checks.values()),
    "checks":checks,
    "missing_docs":missing_docs,"bad_compliance_statuses":bad_status,"missing_compliance_evidence":missing_evidence,
    "bundle_hash_sha256":bundle_meta["bundle_hash_sha256"],
    "runtime_environment":environment_snapshot(ROOT),
}
(ROOT/"docs/validation/v1_diagnostics.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["passed"] else 1)
