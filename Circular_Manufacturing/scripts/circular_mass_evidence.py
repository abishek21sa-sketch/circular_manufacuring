from pathlib import Path
import csv,json,sys,time
from dataclasses import replace
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from circular4x.signature_algorithm import reference_problem, solve_circular_mass

scenarios,cfg=reference_problem()
_started=time.perf_counter()
base=solve_circular_mass(scenarios,cfg)
_runtime=time.perf_counter()-_started
zero_fac=tuple(replace(f,capacity_kg=0.0) for f in cfg.facilities)
virgin=solve_circular_mass(scenarios,replace(cfg,facilities=zero_fac,min_recycled_content=0.0,risk_aversion=0.0,max_virgin_share=1.0))
avg_yield=tuple(sum(s.probability*s.yields[f] for s in scenarios) for f in range(len(cfg.facilities)))
mean_demand=sum(s.probability*s.demand_kg for s in scenarios)
from circular4x.signature_algorithm import CircularMassScenario
avg=solve_circular_mass([CircularMassScenario('expected-value',1.0,mean_demand,avg_yield)],replace(cfg,risk_aversion=0.0))
stress_cfg=replace(cfg,max_virgin_share=.25,risk_aversion=.75)
stress=solve_circular_mass(scenarios,stress_cfg)
tail_scenarios=[scenarios[0],scenarios[1],replace(scenarios[2],probability=.15),CircularMassScenario('rare-severe',.05,1_300_000,(.45,.52,.40))]
tail_stress=solve_circular_mass(tail_scenarios,stress_cfg)
rows=[]
for floor in (.10,.20,.35,.50,.65):
  for risk in (0.0,.15,.35,.60):
    sol=solve_circular_mass(scenarios,replace(cfg,min_recycled_content=floor,risk_aversion=risk))
    rows.append({'recycled_content_floor':floor,'risk_aversion':risk,'objective':sol.objective,'expected_recovered_kg':sol.expected_recovered_kg,'recycled_content_share':sol.recycled_content_share,'expected_shortage_kg':sol.expected_shortage_kg,'cvar_shortage_kg':sol.cvar_shortage_kg,'open_facilities':';'.join(k for k,v in sol.open_facilities.items() if v)})
checks={
 'optimal':base.status=='OPTIMAL',
 'feasible':base.max_constraint_violation<1e-5,
 'recycled_content_met':base.recycled_content_share>=cfg.min_recycled_content-1e-8,
 'cvar_consistent':base.cvar_shortage_kg>=base.expected_shortage_kg-1e-8,
 'virgin_only_ablation_uses_less_recovery':virgin.expected_recovered_kg < base.expected_recovered_kg-1,
 'sensitivity_grid_complete':len(rows)==20,
 'stress_shortage_positive':stress.expected_shortage_kg>0,
 'stress_cvar_active':stress.cvar_shortage_kg>stress.expected_shortage_kg+1e-8 and stress.eta>0,
 'fine_tail_excess_active':tail_stress.cvar_shortage_kg>tail_stress.expected_shortage_kg+1e-8 and any(x['cvar_excess_kg']>0 for x in tail_stress.scenario_details),
 'objective_reconciles':base.diagnostics['objective_reconciliation_error']<1e-5 and stress.diagnostics['objective_reconciliation_error']<1e-5 and tail_stress.diagnostics['objective_reconciliation_error']<1e-5,
}
out=ROOT/'artifacts'/'circular_mass'; out.mkdir(parents=True,exist_ok=True)
payload={'algorithm':'CIRCULAR-MASS','null_hypothesis':'Under common demand/recovery-yield scenarios, stochastic CIRCULAR-MASS does not improve the virgin-material/shortage/tail-risk trade-off relative to deterministic average-yield or virgin-only planning.','falsification_question':'Does the explicit shortage-CVaR formulation activate and remain numerically consistent when virgin fallback is restricted enough to produce shortage?','runtime_seconds':_runtime,'evidence_class':'DETERMINISTIC SYNTHETIC VALIDATION','seed':None,'reference':base.to_dict(),'baselines':{'virgin_only':virgin.to_dict(),'deterministic_average_yield':avg.to_dict()},'stress_case':{'configuration':{'max_virgin_share':stress_cfg.max_virgin_share,'risk_aversion':stress_cfg.risk_aversion},'solution':stress.to_dict(),'fine_tail_solution':tail_stress.to_dict()},'comparison':{'reference_vs_average_yield_objective_delta':float(base.objective-avg.objective),'reference_vs_virgin_only_recovered_mass_delta_kg':float(base.expected_recovered_kg-virgin.expected_recovered_kg),'stress_cvar_minus_expected_shortage_kg':float(stress.cvar_shortage_kg-stress.expected_shortage_kg)},'checks':checks,'claim_boundary':'Results are deterministic synthetic formulation evidence. No realized industrial or environmental benefit is claimed.'}
(out/'evidence.json').write_text(json.dumps(payload,indent=2),encoding='utf-8')
with (out/'sensitivity.csv').open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
(out/'EVIDENCE_REPORT.md').write_text(f'''# CIRCULAR-MASS Validation Evidence\n\nEvidence class: deterministic synthetic formulation validation. This is not field-validated recovery performance.\n\n- Solver status: {base.status}\n- Expected recovered mass: {base.expected_recovered_kg:,.2f} kg\n- Recycled-content share: {base.recycled_content_share:.4f}\n- Expected shortage: {base.expected_shortage_kg:,.2f} kg\n- CVaR shortage: {base.cvar_shortage_kg:,.2f} kg\n- Virgin-only recovered mass: {virgin.expected_recovered_kg:,.2f} kg\n- Sensitivity cases: {len(rows)}\n- Checks: {sum(checks.values())}/{len(checks)}\n''',encoding='utf-8')
with (out/'EVIDENCE_REPORT.md').open('a',encoding='utf-8') as report:
 report.write(f"\n- Stress expected shortage: {stress.expected_shortage_kg:,.2f} kg\n- Stress shortage CVaR: {stress.cvar_shortage_kg:,.2f} kg\n- Fine-tail positive excess observed: {any(x['cvar_excess_kg'] > 0 for x in tail_stress.scenario_details)}\n")
print(f"CIRCULAR_MASS_EVIDENCE={sum(checks.values())}/{len(checks)}")
print(f"CIRCULAR_MASS_SENSITIVITY={len(rows)}")
print(f"RECYCLED_CONTENT={base.recycled_content_share:.6f}")
print(f"EXPECTED_RECOVERED_KG={base.expected_recovered_kg:.2f}")
