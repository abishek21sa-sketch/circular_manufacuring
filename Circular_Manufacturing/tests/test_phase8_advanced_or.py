import pytest
from dataclasses import replace
from circular_battery.routing.models import RouteNode,CVRPScenario
from circular_battery.routing.demo import demo_cvrp_scenario
from circular_battery.routing.cvrp import solve_cvrp
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.optimization.stochastic_network import demo_stochastic_config,solve_stochastic_network
from circular_battery.optimization.advanced_frontier import advanced_strategy_frontier

def test_cvrp_reference_is_optimal_and_capacity_feasible():
    s=demo_cvrp_scenario();sol=solve_cvrp(s)
    assert sol.status=='OPTIMAL'
    assert sol.max_constraint_violation < 1e-7
    assert sol.vehicles_used <= s.max_vehicles
    assert all(x <= s.vehicle_capacity_kg+1e-7 for x in sol.route_loads_kg)
    names=[n.name for n in s.customers]
    visited=[x for r in sol.routes for x in r[1:-1]]
    assert sorted(visited)==sorted(names)

def test_cvrp_two_customer_oracle():
    depot=RouteNode('D',0,0,0);a=RouteNode('A',3,0,10);b=RouteNode('B',6,0,10)
    s=CVRPScenario(depot,(a,b),vehicle_capacity_kg=30,max_vehicles=1,vehicle_fixed_cost=100,distance_cost_per_km=2,kgco2e_per_km=1)
    sol=solve_cvrp(s)
    # D-A-B-D or D-B-A-D = 12 km, plus one vehicle.
    assert sol.total_distance_km == pytest.approx(12)
    assert sol.objective_cost == pytest.approx(124)
    assert sol.vehicles_used == 1

def test_stochastic_scenario_bridge_probabilities_and_dimensions():
    raw,red,trace=ai_to_uncertainty_scenarios(raw_n=40,reduced_k=6,seed=77)
    assert len(raw)==40 and len(red)==6
    assert sum(s.probability for s in red)==pytest.approx(1)
    assert all(len(s.demand_kg)==3 and len(s.internal_scrap_supply_kg)==3 for s in red)
    assert trace['demand_prediction_packs']>0 and trace['scrap_prediction_rate']>0

def test_stochastic_network_feasibility_and_cvar():
    _,red,_=ai_to_uncertainty_scenarios(raw_n=40,reduced_k=6,seed=78)
    sol=solve_stochastic_network(red,demo_stochastic_config())
    assert sol.status=='OPTIMAL'
    assert sol.max_constraint_violation < 1e-5
    assert sol.expected_service_level >= .975
    assert sol.cvar_operating_cost >= sol.expected_operating_cost

def test_n_minus_one_reserve_changes_capacity_decision():
    _,red,_=ai_to_uncertainty_scenarios(raw_n=50,reduced_k=6,seed=79)
    cfg=demo_stochastic_config()
    nominal=solve_stochastic_network(red,replace(cfg,n_minus_one_min_capacity_kg=0,risk_aversion=.1))
    robust=solve_stochastic_network(red,replace(cfg,n_minus_one_min_capacity_kg=210_000,risk_aversion=.3))
    nominal_cap=sum(nominal.expansion_units.values())
    robust_cap=sum(robust.expansion_units.values())
    assert robust_cap >= nominal_cap
    assert robust.max_constraint_violation < 1e-5

def test_advanced_frontier_has_real_tradeoff():
    _,red,_=ai_to_uncertainty_scenarios(raw_n=50,reduced_k=6,seed=80)
    f=advanced_strategy_frontier(red)
    assert len(f['nondominated']) >= 2
    costs={round(x['expected_total_cost'],3) for x in f['candidates']}
    carb={round(x['expected_carbon_kgco2e'],3) for x in f['candidates']}
    assert len(costs)>=2 and len(carb)>=2
    assert any(x['open_facilities'].get('M-Detroit')==1 for x in f['candidates'])
