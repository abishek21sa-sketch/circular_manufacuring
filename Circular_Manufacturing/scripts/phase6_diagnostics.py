from pathlib import Path
import json
from circular_battery.logistics.demo import demo_reverse_logistics_scenario
from circular_battery.logistics.optimizer import solve_reverse_logistics

s=demo_reverse_logistics_scenario();sol=solve_reverse_logistics(s)
cap={f.name:f.capacity_kg for f in s.facilities}
used={name:0.0 for name in cap}
for row in sol.flows: used[row["facility"]]+=row["kg"]
checks={
 "optimal":sol.status=="OPTIMAL",
 "network_mass_balance":abs(sol.collected_kg-sol.processed_kg-sol.disposed_kg)<1e-6,
 "facility_capacities":all(used[k]<=cap[k]*sol.opened_facilities[k]+1e-5 for k in cap),
 "disposal_policy":sol.disposed_kg<=sol.collected_kg*s.max_disposal_share+1e-6,
 "constraint_audit":sol.max_constraint_violation<1e-6,
 "transport_cost_positive":sol.transport_cost>0,
 "transport_emissions_positive":sol.transport_kgco2e>0,
 "reman_pathway_exercised":any(sol.opened_facilities[f.name] for f in s.facilities if f.kind=="reman"),
}
out={"phase":"PHASE-6","passed":all(checks.values()),"checks":checks,
     "solver":sol.solver,"mip_gap":sol.mip_gap,"opened_facilities":sol.opened_facilities,
     "collected_kg":sol.collected_kg,"processed_kg":sol.processed_kg,"disposed_kg":sol.disposed_kg,
     "max_constraint_violation":sol.max_constraint_violation}
Path("docs/validation/phase6_diagnostics.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
raise SystemExit(0 if out["passed"] else 1)
