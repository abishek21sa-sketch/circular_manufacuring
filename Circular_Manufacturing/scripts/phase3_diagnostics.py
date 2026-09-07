import json
from pathlib import Path
from circular_battery.optimization.network import NetworkScenario, solve_network, brute_force_facility_oracle
from circular_battery.optimization.frontier import circular_strategy_frontier
from circular_battery.simulation.stochastic import stress_test_policy
s=NetworkScenario(); sol=solve_network(s); oracle=brute_force_facility_oracle(s); front=circular_strategy_frontier(s)
stress=stress_test_policy(s,n=40,seed=123)
checks={
 "optimal":bool(sol.status=="OPTIMAL"),
 "constraint_audit":bool(sol.max_constraint_violation<1e-5),
 "oracle_matches":bool(abs(sol.total_cost-oracle["objective"])<1e-3),
 "frontier_has_tradeoff":bool(len(front)>=2 and front[-1]["total_carbon_kgco2e"] < front[0]["total_carbon_kgco2e"]),
 "stochastic_reproducible":bool(stress==stress_test_policy(s,n=40,seed=123)),
 "synthetic_label":bool(stress["evidence_class"].startswith("SYNTHETIC")),
}
result={"phase":"PHASE-3","passed":all(checks.values()),"checks":checks,
        "solver":sol.solver,"mip_gap":sol.mip_gap,"max_constraint_violation":sol.max_constraint_violation}
Path("docs/validation/phase3_diagnostics.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["passed"] else 1)
