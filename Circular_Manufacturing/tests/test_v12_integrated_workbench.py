import json
from pathlib import Path
import pytest

from circular_battery.decision.workbench_v12 import build_workbench_v12

ROOT=Path(__file__).resolve().parents[1]


def test_v12_reference_workbench_artifact_is_integrated():
    p=ROOT/'artifacts'/'v12_workbench_report.json'
    assert p.is_file()
    r=json.loads(p.read_text(encoding='utf-8'))
    assert r['version']=='1.2.1'
    assert r['release']=='V1.2-INTEGRATED-WORKBENCH'
    assert r['coupled_planning']['status']=='OPTIMAL'
    assert r['coupled_critical_materials']['status']=='OPTIMAL'
    assert r['coupled_routing']['status']=='OPTIMAL'
    assert len(r['integration_contract'])==6
    assert len(r['math_inventory'])==7
    assert r['stochastic_information_value']['value_of_stochastic_solution'] > 0
    assert r['stochastic_information_value']['expected_value_of_perfect_information'] > 0


def test_v12_planning_demand_is_ai_bridge_demand():
    r=build_workbench_v12()
    expected=[x/400.0 for x in r['bridge']['derived_base_demand_kg']]
    assert r['coupled_planning']['scenario']['demand_packs']==pytest.approx(expected)
    assert r['coupled_planning']['solution']['service_level']==pytest.approx(1.0)
    assert r['coupled_planning']['solution']['total_recovered_use_kg']>0
    assert r['coupled_planning']['solution']['max_constraint_violation']<1e-7


def test_v12_critical_material_demand_is_coupled_to_pack_bom():
    r=build_workbench_v12()
    demand0=r['coupled_planning']['scenario']['demand_packs'][0]
    lithium=next(x for x in r['coupled_critical_materials']['material_rows'] if x['material']=='lithium' and x['period']==1)
    assert lithium['demand_kg']==pytest.approx(demand0*8.0)
    assert r['coupled_critical_materials']['total_shortage_kg']==pytest.approx(0,abs=1e-7)
    assert r['coupled_critical_materials']['max_constraint_violation']<1e-7


def test_v12_routing_pickups_come_from_return_state():
    r=build_workbench_v12()
    expected=r['bridge']['derived_base_returns_kg'][0]*.87*(1-r['bridge']['derived_second_life_share'])
    routing=r['coupled_routing']
    assert routing['routing_input']['collected_batch_kg']==pytest.approx(expected)
    assert sum(routing['routing_input']['customer_pickups_kg'].values())==pytest.approx(expected)
    assert routing['vehicles_used']<=6
    assert routing['max_constraint_violation']<1e-7


def test_v12_math_inventory_reports_real_model_dimensions():
    r=build_workbench_v12()
    by={x['model']:x for x in r['math_inventory']}
    assert by['Two-stage stochastic MILP + CVaR']['integer_variables']==6
    assert by['Exact capacitated vehicle routing MILP']['variables']==48
    assert by['Licensed hierarchical multi-objective MILP']['objectives']==4
    assert all(x['verification'] for x in r['math_inventory'])


def test_v12_frontend_exposes_decision_depth_not_raw_trace_columns():
    html=(ROOT/'web'/'dist'/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'web'/'dist'/'app.js').read_text(encoding='utf-8')
    css=(ROOT/'web'/'dist'/'styles.css').read_text(encoding='utf-8')
    for label in ('MATERIALS','NETWORK','PLAN','STRATEGY','ROUTES','AI','RISK','TRACE','RUNS','EVIDENCE'):
        assert label in html
    assert 'MATHEMATICAL MODEL INVENTORY' in html
    assert 'COUPLING CONTRACT' in html
    assert 'wall of circles' in html
    assert '/api/v1/workbench' in js
    assert '.trace-layout-v12' in css
    assert '.stochastic-value-grid' in css
    assert 'inspectRun' in js
