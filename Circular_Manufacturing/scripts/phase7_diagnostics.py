from pathlib import Path
import json
from circular_battery.reporting.phase567 import build_phase567_report,write_phase567_report

r=build_phase567_report()
plan=r["phase7"]["production_plan"];ie=r["phase7"]["ie_metrics"];rl=r["phase6"]["reverse_logistics"]
sup=[x["available_recovered_supply_kg"] for x in r["integration"]["recovered_supply_to_planning"]]
checks={
 "phase5_material_closure":bool(r["phase5"]["max_material_balance_error_kg"]<1e-6),
 "phase6_network_closure":bool(rl["max_constraint_violation"]<1e-6 and abs(rl["collected_kg"]-rl["processed_kg"]-rl["disposed_kg"])<1e-6),
 "recovered_supply_connected":bool(all(x>0 for x in sup)),
 "planning_optimal":bool(plan["status"]=="OPTIMAL"),
 "planning_constraint_audit":bool(plan["max_constraint_violation"]<1e-6),
 "service_level_physical":bool(0<=plan["service_level"]<=1),
 "reference_service_target":bool(plan["service_level"]>=.99),
 "recycled_content_physical":bool(0<=plan["recycled_content_rate"]<=1),
 "ie_metrics_present":bool(ie["material_productivity_packs_per_tonne"]>0),
 "synthetic_label":bool(r["data_status"]=="SYNTHETIC VALIDATION"),
}
out={"phase":"PHASE-7-CUMULATIVE","passed":all(checks.values()),"checks":checks,
     "service_level":plan["service_level"],"recycled_content_rate":plan["recycled_content_rate"],
     "virgin_kg":plan["total_virgin_kg"],"recovered_use_kg":plan["total_recovered_use_kg"],
     "max_planning_violation":plan["max_constraint_violation"]}
Path("docs/validation/phase7_diagnostics.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
write_phase567_report("artifacts/phase567_integrated_report.json")
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["passed"] else 1)
