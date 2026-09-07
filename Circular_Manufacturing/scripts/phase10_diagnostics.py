from pathlib import Path
import json
from circular_battery.decision.orchestrator import build_phase10_decision

r=build_phase10_decision(seed=1010,raw_n=48,reduced_k=6)
trace=[x['component'] for x in r['decision_trace']]
checks={
 'all_ai_models_explained':bool(set(r['ai_uncertainty_and_explainability'])=={'demand','returns','recovery','scrap'}),
 'demand_interval_calibrated':bool(r['ai_uncertainty_and_explainability']['demand']['empirical_holdout_coverage']>=.80),
 'return_calibration_reasonable':bool(r['ai_uncertainty_and_explainability']['returns']['expected_calibration_error']<.05),
 'decision_trace_complete':bool(trace[0]=='DemandForecaster' and trace[-1]=='DecisionEngine' and len(trace)>=11),
 'frontier_available':bool(len(r['advanced_strategy_frontier']['nondominated'])>=2),
 'critical_material_resilience':bool(r['critical_material_resilience']['max_constraint_violation']<1e-7),
 'routing_audited':bool(r['routing']['max_constraint_violation']<1e-7),
 'digital_experiments':bool(len(r['policy_digital_experiments'])>=2),
 'recommendation_human_gate':bool(r['decision']['human_approval_required'] is True),
 'decision_hash':bool(len(r['decision_hash_sha256'])==64),
 'evidence_boundary':bool(r['data_status']=='SYNTHETIC VALIDATION' and r['real_world_validation']=='PENDING'),
}
out={'phase':'PHASE-10-CUMULATIVE','passed':all(checks.values()),'checks':checks,
     'recommended_policy':r['decision']['recommended_policy'],'confidence':r['decision']['confidence'],
     'trace_components':trace,'decision_hash_sha256':r['decision_hash_sha256']}
Path('docs/validation/phase10_diagnostics.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2));raise SystemExit(0 if out['passed'] else 1)
