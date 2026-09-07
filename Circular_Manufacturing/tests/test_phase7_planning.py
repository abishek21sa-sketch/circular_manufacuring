import pytest
from circular_battery.planning.demo import demo_planning_scenario
from circular_battery.planning.optimizer import solve_production_plan
from circular_battery.planning.ie_metrics import planning_ie_metrics
from circular_battery.planning.models import PlanningScenario
from circular_battery.reporting.phase567 import build_phase567_report

def test_phase7_reference_plan_is_feasible():
    s=demo_planning_scenario();sol=solve_production_plan(s)
    assert sol.status=="OPTIMAL"
    assert sol.max_constraint_violation < 1e-6
    assert 0 <= sol.recycled_content_rate <= s.max_recycled_content+1e-7
    assert sol.recycled_content_rate >= s.min_recycled_content-1e-7
    assert 0 <= sol.service_level <= 1

def test_phase7_all_inventory_and_material_balances_close():
    sol=solve_production_plan(demo_planning_scenario())
    for r in sol.period_rows:
        assert r["material_balance_error_kg"] < 1e-6
        assert r["recovered_inventory_balance_error_kg"] < 1e-6
        assert r["finished_goods_balance_error_packs"] < 1e-6

def test_phase7_ie_metrics_have_units_and_bounds():
    s=demo_planning_scenario();sol=solve_production_plan(s);m=planning_ie_metrics(sol,s)
    assert 0 <= m["service_level"] <= 1
    assert 0 <= m["aggregate_capacity_utilization"] <= 1
    assert 0 <= m["overtime_share"] <= 1
    assert m["material_productivity_packs_per_tonne"] > 0
    assert m["average_recovered_inventory_kg"] >= 0

def test_phase7_tiny_all_virgin_oracle():
    s=PlanningScenario(
        demand_packs=(100.,),recovered_supply_kg=(0.,),
        regular_capacity_packs=(100.,),overtime_capacity_packs=(0.,),
        pack_mass_kg=400.,initial_finished_goods_packs=0.,
        initial_recovered_inventory_kg=0.,min_recycled_content=0.,max_recycled_content=.5,
        safety_stock_fraction_next_period=0.,
    )
    sol=solve_production_plan(s)
    assert sol.total_regular_packs==pytest.approx(100)
    assert sol.total_overtime_packs==pytest.approx(0)
    assert sol.total_virgin_kg==pytest.approx(40_000)
    assert sol.total_recovered_use_kg==pytest.approx(0)
    assert sol.total_shortage_packs==pytest.approx(0)

def test_phase7_abundant_recovered_supply_hits_recycled_content_cap():
    s=PlanningScenario(
        demand_packs=(100.,),recovered_supply_kg=(50_000.,),
        regular_capacity_packs=(100.,),overtime_capacity_packs=(0.,),
        pack_mass_kg=400.,initial_finished_goods_packs=0.,
        initial_recovered_inventory_kg=0.,min_recycled_content=.2,max_recycled_content=.5,
        safety_stock_fraction_next_period=0.,
    )
    sol=solve_production_plan(s)
    assert sol.total_recovered_use_kg==pytest.approx(20_000,abs=1e-5)
    assert sol.total_virgin_kg==pytest.approx(20_000,abs=1e-5)
    assert sol.recycled_content_rate==pytest.approx(.5)

def test_phase567_pipeline_is_computationally_connected():
    r=build_phase567_report()
    assert r["phase5"]["max_material_balance_error_kg"] < 1e-6
    assert r["phase6"]["reverse_logistics"]["max_constraint_violation"] < 1e-6
    supplies=[x["available_recovered_supply_kg"] for x in r["integration"]["recovered_supply_to_planning"]]
    assert all(x>0 for x in supplies)
    plan=r["phase7"]["production_plan"]
    assert plan["total_recovered_use_kg"] > 0
    assert plan["max_constraint_violation"] < 1e-6
