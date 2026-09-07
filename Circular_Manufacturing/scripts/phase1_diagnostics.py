from pathlib import Path
import json, sys, math
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from circular_battery.reporting.report import build_phase1_report

report = build_phase1_report()
checks = {}
max_err = 0.0
for p in report["periods"]:
    mf = p["material_flow"]
    errs = [
        abs(mf["manufacturing_balance_error_kg"]),
        abs(mf["return_balance_error_kg"]),
        abs(mf["recycling_balance_error_kg"]),
        abs(mf["inventory_balance_error_kg"]),
    ]
    max_err = max(max_err, *errs)
checks["mass_balance_max_abs_error_kg"] = max_err
checks["mass_balance_pass"] = max_err < 1e-6
checks["rates_bounded"] = all(
    0 <= p["material_flow"][k] <= 1
    for p in report["periods"]
    for k in ["recycled_content_rate","collection_efficiency","recovery_efficiency","landfill_diversion_rate"]
)
checks["lca_positive"] = all(p["lca"]["total_kgco2e"] > 0 for p in report["periods"])
checks["vsm_pce_bounded"] = 0 <= report["recovery_value_stream"]["process_cycle_efficiency"] <= 1
checks["synthetic_label_present"] = report["data_status"] == "SYNTHETIC VALIDATION"
passed = all(v for k,v in checks.items() if k != "mass_balance_max_abs_error_kg")
result = {"phase":"PHASE-1","passed":passed,"checks":checks}
out = Path(__file__).resolve().parents[1] / "docs" / "validation" / "phase1_diagnostics.json"
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if passed else 1)
