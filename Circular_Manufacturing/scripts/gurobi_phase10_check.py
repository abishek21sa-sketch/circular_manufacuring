from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.optimization.gurobi_advanced import solve_gurobi_multiobjective

_, scenarios, _ = ai_to_uncertainty_scenarios(raw_n=30, reduced_k=5, seed=20260817)
# Use the highest-probability representative future for licensed hierarchical multi-objective verification.
scenario=max(scenarios,key=lambda s:s.probability)
r=solve_gurobi_multiobjective(scenario)
print('GUROBI_PHASE10_OK')
for key in ('status','solver','is_multiobjective','runtime_seconds','mip_gap','shortage_kg',
            'service_acceptance_tolerance_kg','feasibility_tolerance',
            'service_objective_abs_tolerance_kg','cost','carbon_kgco2e','virgin_kg',
            'max_constraint_violation','max_integrality_violation','open_facilities','expansion_units'):
    print(f'{key.upper()}={r[key]}')
print(f"OBJECTIVE_PASSES={r['objective_passes']}")
bad_pass = any(row['status'] != 2 or row['mip_gap'] > 1e-6 for row in r['objective_passes'])
if (r['status']!='OPTIMAL' or not r['is_multiobjective'] or not r['objective_passes']
        or bad_pass
        or r['shortage_kg'] > r['service_acceptance_tolerance_kg']
        or r['max_constraint_violation']>1e-6
        or r['max_integrality_violation']>1e-6):
    raise SystemExit(1)
