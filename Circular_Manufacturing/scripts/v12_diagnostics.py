from __future__ import annotations
import json
from pathlib import Path
from circular_battery import __version__
from circular_battery.decision.workbench_v12 import build_workbench_v12

ROOT=Path(__file__).resolve().parents[1]
r=build_workbench_v12()
html=(ROOT/'web/dist/index.html').read_text(encoding='utf-8')
css=(ROOT/'web/dist/styles.css').read_text(encoding='utf-8')
js=(ROOT/'web/dist/app.js').read_text(encoding='utf-8')
checks={
 'version_1_2_1':__version__=='1.2.1',
 'coupled_plan_optimal':r['coupled_planning']['status']=='OPTIMAL' and r['coupled_planning']['solution']['max_constraint_violation']<1e-7,
 'coupled_critical_materials_optimal':r['coupled_critical_materials']['status']=='OPTIMAL' and r['coupled_critical_materials']['max_constraint_violation']<1e-7,
 'coupled_routing_optimal':r['coupled_routing']['status']=='OPTIMAL' and r['coupled_routing']['max_constraint_violation']<1e-7,
 'routing_mass_contract':abs(sum(r['coupled_routing']['routing_input']['customer_pickups_kg'].values())-r['coupled_routing']['routing_input']['collected_batch_kg'])<1e-7,
 'math_inventory_seven_models':len(r['math_inventory'])==7,
 'integration_contract_complete':len(r['integration_contract'])==6 and sum(1 for x in r['integration_contract'] if x['status'].startswith('COUPLED'))==6,
 'known_boundaries_visible':len(r['known_model_boundaries'])>=4,
 'frontend_depth':all(x in html for x in ('MATHEMATICAL MODEL INVENTORY','COUPLING CONTRACT','SAME-SCENARIO POLICY COMPARISON','PERSISTED RUNS')),
 'risk_distribution_ui':'.hist-bar' in css and 'scenario_rows' in js,
 'trace_inspector_ui':'.trace-layout-v12' in css and 'trace-output' in css,
 'stochastic_value_nonnegative':r['stochastic_information_value']['value_of_stochastic_solution']>=-1e-7 and r['stochastic_information_value']['expected_value_of_perfect_information']>=-1e-7,
 'stochastic_value_ordering':r['stochastic_information_value']['expected_result_of_expected_value_cost']+1e-7>=r['stochastic_information_value']['risk_neutral_stochastic_program_cost']>=r['stochastic_information_value']['wait_and_see_expected_cost']-1e-7,
 'stochastic_value_ui':'.stochastic-value-grid' in css and 'value_of_stochastic_solution' in js,
 'run_report_ui':'.run-report-panel' in css and 'inspectRun' in js,
}
checks={k:bool(v) for k,v in checks.items()}
out={'release':'V1.2.1','version':__version__,'passed':all(checks.values()),'checks':checks,
     'recommended_policy':r['decision']['recommended_policy'],
     'coupled_plan_recycled_content':r['coupled_planning']['solution']['recycled_content_rate'],
     'critical_recovered_share':r['coupled_critical_materials']['recovered_share'],
     'routing_vehicles':r['coupled_routing']['vehicles_used']}
(ROOT/'docs/validation/v12_diagnostics.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
raise SystemExit(0 if out['passed'] else 1)
