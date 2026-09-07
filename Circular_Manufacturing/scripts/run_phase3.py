from pathlib import Path
import json
from circular_battery.optimization.network import NetworkScenario, solve_network, brute_force_facility_oracle
from circular_battery.optimization.frontier import circular_strategy_frontier
from circular_battery.simulation.stochastic import stress_test_policy

s=NetworkScenario()
sol=solve_network(s)
frontier=circular_strategy_frontier(s)
stress=stress_test_policy(s,n=100,seed=20260816)
report={"phase":"PHASE-3","evidence_class":"SYNTHETIC VALIDATION","reference_solution":sol.to_dict(),
        "facility_oracle":brute_force_facility_oracle(s),"frontier":frontier,"stochastic":stress}
out=Path("artifacts/phase3_strategy_report.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report,indent=2),encoding="utf-8")
print(f"PHASE3_REPORT={out.resolve()}")
print(f"STATUS={sol.status}")
print(f"SOLVER={sol.solver}")
print(f"COST={sol.total_cost:.2f}")
print(f"CARBON_KGCO2E={sol.total_carbon_kgco2e:.2f}")
print(f"VIRGIN_KG={sol.virgin_kg:.2f}")
print(f"RECYCLED_CONTENT={sol.recycled_content_rate:.4f}")
print(f"MAX_CONSTRAINT_VIOLATION={sol.max_constraint_violation:.8f}")
print(f"FRONTIER_POINTS={len(frontier)}")
