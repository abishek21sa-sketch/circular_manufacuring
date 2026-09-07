import argparse, json
from pathlib import Path
from circular_battery.ingestion.bundle import validate_bundle, run_bundle
from circular_battery.ingestion.governance import inspect_bundle

parser=argparse.ArgumentParser(description="Validate and run a Circular Manufacturing V1 scenario bundle.")
parser.add_argument("directory",type=Path)
parser.add_argument("--validate-only",action="store_true")
parser.add_argument("--require-lineage",action="store_true",help="reject bundles without complete source lineage")
parser.add_argument("--out",type=Path,default=Path("artifacts/external_bundle_report.json"))
args=parser.parse_args()

governance=inspect_bundle(args.directory,require_lineage=args.require_lineage)
if not governance["accepted_for_optimization"]:
    print(json.dumps(governance,indent=2))
    raise SystemExit("Bundle failed the governed-ingestion gate.")

if args.validate_only:
    result=validate_bundle(args.directory)
    result["governance"]=governance
    print(json.dumps(result,indent=2))
else:
    result=run_bundle(args.directory)
    result["governance"]=governance
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(f"BUNDLE_REPORT={args.out.resolve()}")
    print(f"BUNDLE_HASH={result['bundle']['bundle_hash_sha256']}")
    print(f"MASS_ERROR_KG={result['lifecycle']['max_material_balance_error_kg']:.10f}")
    print(f"REVERSE_STATUS={result['reverse_logistics']['status']}")
    print(f"PLANNING_STATUS={result['planning']['solution']['status']}")
