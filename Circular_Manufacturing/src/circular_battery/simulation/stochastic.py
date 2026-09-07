from dataclasses import dataclass, asdict
import numpy as np
from circular_battery.optimization.network import NetworkScenario, solve_network

def stress_test_policy(base: NetworkScenario, n=250, seed=20260816):
    rng=np.random.default_rng(seed)
    costs=[]; carbons=[]; virgins=[]; shortages=[]
    for _ in range(n):
        demand=tuple(max(1.,x*rng.normal(1,0.07)) for x in base.demand_kg)
        returns=tuple(max(0.,x*rng.normal(1,0.12)) for x in base.returns_kg)
        y=float(np.clip(rng.normal(base.recycle_yield,0.025),.70,.98))
        scenario=NetworkScenario(**{**base.__dict__,"demand_kg":demand,"returns_kg":returns,"recycle_yield":y})
        sol=solve_network(scenario,carbon_price_per_kg=.15)
        costs.append(sol.total_cost); carbons.append(sol.total_carbon_kgco2e); virgins.append(sol.virgin_kg)
        shortages.append(any(r["virgin_kg"]>0.90*demand[i] for i,r in enumerate(sol.period_rows)))
    return {
        "n":n,"seed":seed,"evidence_class":"SYNTHETIC STOCHASTIC VALIDATION",
        "expected_cost":float(np.mean(costs)),"p90_cost":float(np.quantile(costs,.90)),
        "expected_carbon_kgco2e":float(np.mean(carbons)),
        "expected_virgin_kg":float(np.mean(virgins)),
        "high_virgin_dependency_probability":float(np.mean(shortages)),
    }
