from pathlib import Path
import json
from circular_battery.lifecycle.demo import demo_design,demo_grades,demo_periods
from circular_battery.lifecycle.engine import evaluate_lifecycle_horizon
from circular_battery.lifecycle.metrics import circularity_metrics,pathway_economics
from circular_battery.lifecycle.impact import lifecycle_material_impact

d=demo_design();rs=evaluate_lifecycle_horizon(d,demo_grades(),demo_periods())
m=circularity_metrics(rs,d);e=pathway_economics(rs,d);impact=lifecycle_material_impact(rs,d)
checks={
 "pack_mass_400kg":abs(d.pack_mass_kg-400)<1e-9,
 "material_balances":max(abs(r.material_balance_error_kg) for r in rs)<1e-6,
 "collection_physical":0<=m["collection_efficiency"]<=1,
 "technical_recovery_physical":0<=m["technical_recovery_rate"]<=1,
 "critical_recovery_physical":0<=m["critical_material_recovery_rate"]<=1,
 "recovered_mass_positive":e["recovered_mass_kg"]>0,
 "comparative_impact_labeled":"EXTERNAL FACTOR VALIDATION PENDING" in impact["evidence_class"],
}
out={"phase":"PHASE-5","passed":all(checks.values()),"checks":checks,
     "metrics":m,"modeled_economics":e,
     "max_material_balance_error_kg":max(abs(r.material_balance_error_kg) for r in rs)}
Path("docs/validation/phase5_diagnostics.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["passed"] else 1)
