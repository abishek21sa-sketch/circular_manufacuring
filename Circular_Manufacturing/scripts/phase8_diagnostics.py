from pathlib import Path
import json
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.optimization.stochastic_network import demo_stochastic_config,solve_stochastic_network
from circular_battery.optimization.advanced_frontier import advanced_strategy_frontier
from circular_battery.optimization.critical_materials import solve_critical_material_plan
from circular_battery.routing.demo import demo_cvrp_scenario
from circular_battery.routing.cvrp import solve_cvrp

_,red,bridge=ai_to_uncertainty_scenarios(raw_n=42,reduced_k=6,seed=808)
sto=solve_stochastic_network(red,demo_stochastic_config())
front=advanced_strategy_frontier(red)
route=solve_cvrp(demo_cvrp_scenario())
critical=solve_critical_material_plan()
checks={
 'ai_to_stochastic_contract':bool(bridge['demand_prediction_packs']>0 and bridge['return_prediction_packs']>0),
 'two_stage_optimal':bool(sto.status=='OPTIMAL'),
 'two_stage_constraint_audit':bool(sto.max_constraint_violation<1e-5),
 'cvar_tail_valid':bool(sto.cvar_operating_cost>=sto.expected_operating_cost),
 'nondominated_frontier':bool(len(front['nondominated'])>=2),
 'literal_cvrp_optimal':bool(route.status=='OPTIMAL' and route.max_constraint_violation<1e-7),
 'critical_material_plan':bool(critical.status=='OPTIMAL' and critical.max_constraint_violation<1e-7),
 'critical_material_no_shortage':bool(critical.total_shortage_kg<1e-7),
}
out={'phase':'PHASE-8','passed':all(checks.values()),'checks':checks,
     'stochastic':{'expected_cost':sto.expected_total_cost,'cvar_cost':sto.cvar_operating_cost,'expected_service':sto.expected_service_level},
     'routing':{'vehicles':route.vehicles_used,'distance_km':route.total_distance_km,'mip_gap':route.mip_gap},
     'critical_materials':{'recovered_share':critical.recovered_share,'supplier_hhi':critical.supplier_hhi_by_material}}
Path('docs/validation/phase8_diagnostics.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 1)
