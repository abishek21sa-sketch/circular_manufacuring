import pytest
from circular_battery.optimization.network import NetworkScenario, solve_network, brute_force_facility_oracle, audit_solution
from circular_battery.optimization.frontier import circular_strategy_frontier
from circular_battery.simulation.stochastic import stress_test_policy

def test_reference_milp_is_feasible_and_audited():
    s=NetworkScenario()
    sol=solve_network(s)
    assert sol.status=="OPTIMAL"
    assert sol.max_constraint_violation < 1e-5
    assert sol.recycled_content_rate > 0
    assert sol.virgin_kg < sum(s.demand_kg)

def test_binary_facility_decision_matches_independent_oracle():
    s=NetworkScenario(periods=2,demand_kg=(200000.,220000.),returns_kg=(100000.,120000.),
        recycle_capacity_kg=90000.,reman_capacity_kg=50000.,max_inventory_kg=50000.)
    sol=solve_network(s)
    oracle=brute_force_facility_oracle(s)
    assert sol.total_cost == pytest.approx(oracle["objective"], rel=1e-7, abs=1e-4)
    assert sol.recycle_open==oracle["recycle_open"]
    assert sol.reman_open==oracle["reman_open"]

def test_carbon_price_does_not_increase_carbon():
    s=NetworkScenario()
    cost=solve_network(s,carbon_price_per_kg=0)
    carbon=solve_network(s,carbon_price_per_kg=1.5)
    assert carbon.total_carbon_kgco2e <= cost.total_carbon_kgco2e + 1e-6

def test_frontier_is_non_dominated():
    pts=circular_strategy_frontier(NetworkScenario())
    assert len(pts)>=2
    assert pts[0]["total_cost"] <= pts[-1]["total_cost"]
    assert pts[-1]["total_carbon_kgco2e"] <= pts[0]["total_carbon_kgco2e"]
    assert (pts[-1]["total_cost"] > pts[0]["total_cost"] or pts[-1]["total_carbon_kgco2e"] < pts[0]["total_carbon_kgco2e"])
    for i,a in enumerate(pts):
        for j,b in enumerate(pts):
            if i==j: continue
            assert not (b["total_cost"]<=a["total_cost"] and b["total_carbon_kgco2e"]<=a["total_carbon_kgco2e"] and b["virgin_kg"]<=a["virgin_kg"]
                        and (b["total_cost"]<a["total_cost"] or b["total_carbon_kgco2e"]<a["total_carbon_kgco2e"] or b["virgin_kg"]<a["virgin_kg"]))

def test_stochastic_reproducibility():
    a=stress_test_policy(NetworkScenario(),n=25,seed=77)
    b=stress_test_policy(NetworkScenario(),n=25,seed=77)
    assert a==b
