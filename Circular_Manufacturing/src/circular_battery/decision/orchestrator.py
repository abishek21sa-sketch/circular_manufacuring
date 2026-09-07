from __future__ import annotations
from dataclasses import replace
import json, math
from pathlib import Path

from circular_battery.ai.explainability import explain_all
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.ai.runtime import runtime_models, runtime_phase2_payload
from circular_battery.optimization.advanced_frontier import advanced_strategy_frontier
from circular_battery.optimization.stochastic_network import demo_stochastic_config
from circular_battery.optimization.critical_materials import solve_critical_material_plan
from circular_battery.analytics.sensitivity import strategic_sensitivity
from circular_battery.routing.demo import demo_cvrp_scenario
from circular_battery.routing.cvrp import solve_cvrp
from circular_battery.simulation.uncertainty import scenario_summary
from circular_battery.simulation.policy_experiments import FixedStrategicPolicy, compare_policies
from circular_battery.evidence.registry import stable_hash

ROOT=Path(__file__).resolve().parents[3]

def _load_models():
    # Portable execution path: fit deterministic models in the current sklearn runtime.
    # Persisted estimator binaries are never required by Phase-10 decision execution.
    return runtime_models()

def _normalize(vals):
    lo=min(vals);hi=max(vals)
    if hi-lo<1e-9: return [0.0 for _ in vals]
    return [(v-lo)/(hi-lo) for v in vals]

def _select_policy(frontier):
    nd=frontier['nondominated']
    feasible=[x for x in nd if x['expected_service_level']>=.995]
    if not feasible: feasible=nd
    costs=_normalize([x['expected_total_cost'] for x in feasible])
    carb=_normalize([x['expected_carbon_kgco2e'] for x in feasible])
    virgin=_normalize([x['expected_virgin_kg'] for x in feasible])
    tail=_normalize([x['cvar_operating_cost'] for x in feasible])
    rows=[]
    for i,x in enumerate(feasible):
        score=.30*costs[i]+.25*carb[i]+.20*virgin[i]+.25*tail[i]
        # small resilience credit only when N-1 capacity is explicitly purchased
        if x['settings'].get('n_minus_one_min_capacity_kg',0)>0: score-=.04
        rows.append((score,x))
    rows.sort(key=lambda z:(z[0],z[1]['expected_total_cost']))
    return rows[0][1], [{'policy':x['policy'],'decision_score':float(score)} for score,x in rows]

def _confidence(p2, explanations, replay_recommended):
    ev=p2['model_evidence']
    improvements=[]
    improvements.append(max(0.,1-ev['demand']['metrics']['mae']/ev['demand']['baseline_metrics']['mae']))
    improvements.append(max(0.,1-ev['returns']['metrics']['brier']/ev['returns']['baseline_metrics']['brier']))
    improvements.append(max(0.,(ev['recovery']['metrics']['macro_f1']-ev['recovery']['baseline_metrics']['macro_f1'])/(1-ev['recovery']['baseline_metrics']['macro_f1'])))
    improvements.append(max(0.,1-ev['scrap']['metrics']['mae']/ev['scrap']['baseline_metrics']['mae']))
    model_strength=sum(improvements)/len(improvements)
    calibration=1-min(1.,explanations['returns']['expected_calibration_error']*5)
    replay_strength=1-min(1.,replay_recommended['emergency_recovery_probability'])
    score=.55*model_strength+.20*calibration+.25*replay_strength
    return float(max(.05,min(.95,score)))

def build_phase10_decision(seed:int=20260817, raw_n:int=80, reduced_k:int=10, include_sensitivity:bool=True):
    p2=runtime_phase2_payload();models=_load_models();xai=explain_all(models)
    raw,reduced,bridge=ai_to_uncertainty_scenarios(raw_n=raw_n,reduced_k=reduced_k,seed=seed)
    uncertainty=scenario_summary(reduced)
    frontier=advanced_strategy_frontier(reduced)
    chosen,scores=_select_policy(frontier)
    by={x['policy']:x for x in frontier['candidates']}
    policy_names=['cost']
    if 'resilience' in by: policy_names.append('resilience')
    if 'low_carbon' in by: policy_names.append('low_carbon')
    if chosen['policy'] not in policy_names: policy_names.append(chosen['policy'])
    policies=[FixedStrategicPolicy(name,by[name]['open_facilities'],by[name]['expansion_units']) for name in policy_names]
    replay=compare_policies(raw,demo_stochastic_config(),policies)
    replay_by={r['policy']:r for r in replay}
    routing=solve_cvrp(demo_cvrp_scenario()).to_dict()
    critical_materials=solve_critical_material_plan().to_dict()
    sensitivity=strategic_sensitivity(reduced) if include_sensitivity else {'experiments':[],'evidence_class':'FAST VALIDATION PATH; FULL SENSITIVITY NOT EXECUTED'}
    base=by['cost'];rec=chosen
    delta={
        'expected_total_cost':rec['expected_total_cost']-base['expected_total_cost'],
        'expected_carbon_kgco2e':rec['expected_carbon_kgco2e']-base['expected_carbon_kgco2e'],
        'expected_virgin_kg':rec['expected_virgin_kg']-base['expected_virgin_kg'],
        'cvar_operating_cost':rec['cvar_operating_cost']-base['cvar_operating_cost'],
    }
    conf=_confidence(p2,xai,replay_by[chosen['policy']])
    action=[]
    for name,val in rec['open_facilities'].items():
        if val: action.append(f'activate {name}')
    for name,val in rec['expansion_units'].items():
        if val: action.append(f'add {val} expansion unit(s) at {name}')
    recommendation={
        'recommended_policy':rec['policy'],'action':action,
        'confidence':conf,
        'expected_impact_vs_cost_policy':delta,
        'tradeoffs':[
            'Modeled cost, carbon, virgin-material dependence and tail-risk are competing objectives.',
            'Second-life allocation withholds material from current-horizon recycling/remanufacturing feed.',
            'N-1 reserve capacity increases fixed cost when selected but protects recovery capacity against a single-site loss.',
        ],
        'assumptions':[
            'All numerical scenario results are synthetic/offline validation evidence.',
            'Phase-2 model evidence is based on synthetic held-out data, not field observations.',
            'Lifecycle impact factors remain externally uncalibrated.',
            'Emergency recovery in policy replay represents an expensive external processor used only when fixed installed capacity is insufficient.',
        ],
        'human_approval_required':True,
        'evidence_class':'EXPLAINABLE RECOMMENDATION FROM VALIDATED SYNTHETIC COMPUTATIONAL CHAIN',
    }
    trace=[
        {'step':1,'component':'DemandForecaster','output':bridge['demand_prediction_packs'],'unit':'packs','evidence':'PREDICTED'},
        {'step':2,'component':'ReturnHazardModel','output':bridge['return_prediction_packs'],'unit':'packs','evidence':'PREDICTED'},
        {'step':3,'component':'ScrapPredictor','output':bridge['scrap_prediction_rate'],'unit':'fraction','evidence':'PREDICTED'},
        {'step':4,'component':'RecoveryPathwayClassifier','output':bridge['recovery_pathway_shares'],'unit':'probability shares','evidence':'PREDICTED'},
        {'step':5,'component':'ScenarioBridge','output':uncertainty,'unit':'scenario distribution','evidence':'SIMULATED'},
        {'step':6,'component':'TwoStageStochasticMILP','output':{'policy':rec['policy'],'open':rec['open_facilities'],'expansion':rec['expansion_units']},'unit':'strategic decisions','evidence':'OPTIMIZED'},
        {'step':7,'component':'CriticalMaterialPlanner','output':{'recovered_share':critical_materials['recovered_share'],'supplier_hhi':critical_materials['supplier_hhi_by_material']},'unit':'critical-material sourcing plan','evidence':'OPTIMIZED'},
        {'step':8,'component':'CVRP','output':{'vehicles':routing['vehicles_used'],'distance_km':routing['total_distance_km']},'unit':'collection routing','evidence':'OPTIMIZED'},
        {'step':9,'component':'StrategicSensitivity','output':{'experiments':len(sensitivity['experiments'])},'unit':'policy sensitivity experiments','evidence':'SIMULATED'},
        {'step':10,'component':'PolicyReplay','output':{'scenarios':raw_n,'cvar95_cost':replay_by[rec['policy']]['cvar95_total_cost'],'emergency_probability':replay_by[rec['policy']]['emergency_recovery_probability']},'unit':'digital experiments','evidence':'SIMULATED'},
        {'step':11,'component':'DecisionEngine','output':recommendation,'unit':'recommendation','evidence':'RECOMMENDED'},
    ]
    report={
        'release':'PHASE-10-CUMULATIVE','version':'0.10.0','seed':seed,
        'data_status':'SYNTHETIC VALIDATION','real_world_validation':'PENDING',
        'ai_model_evidence':p2['model_evidence'],'ai_uncertainty_and_explainability':xai,
        'ai_to_or_bridge':bridge,'uncertainty_design':uncertainty,
        'advanced_strategy_frontier':frontier,'policy_scores':scores,
        'critical_material_resilience':critical_materials,'routing':routing,
        'strategic_sensitivity':sensitivity,'policy_digital_experiments':replay,
        'decision':recommendation,'decision_trace':trace,
        'decision_hash_sha256':None,
        'evidence_classes':['PREDICTED','CALCULATED','OPTIMIZED','SIMULATED','RECOMMENDED','SYNTHETIC VALIDATION'],
    }
    report['decision_hash_sha256']=stable_hash({'seed':seed,'trace':trace,'policy':rec['policy']})
    return report
