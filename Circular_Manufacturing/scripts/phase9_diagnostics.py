from pathlib import Path
import json
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.optimization.advanced_frontier import advanced_strategy_frontier
from circular_battery.optimization.stochastic_network import demo_stochastic_config
from circular_battery.simulation.policy_experiments import FixedStrategicPolicy,compare_policies
from circular_battery.analytics.sensitivity import strategic_sensitivity

raw,red,_=ai_to_uncertainty_scenarios(raw_n=50,reduced_k=6,seed=909)
front=advanced_strategy_frontier(red);by={x['policy']:x for x in front['candidates']}
names=[n for n in ('cost','resilience','low_carbon') if n in by]
pol=[FixedStrategicPolicy(n,by[n]['open_facilities'],by[n]['expansion_units']) for n in names]
replay=compare_policies(raw,demo_stochastic_config(),pol)
sens=strategic_sensitivity(red)
checks={
 'multiple_policies':bool(len(replay)>=2),
 'same_scenario_replay':bool(len({r['scenarios'] for r in replay})==1 and replay[0]['scenarios']==50),
 'tail_metrics_valid':bool(all(r['cvar95_total_cost']>=r['expected_total_cost'] for r in replay)),
 'service_physical':bool(all(0<=r['expected_service_level']<=1 for r in replay)),
 'sensitivity_multidimensional':bool(len(sens['experiments'])>=6),
 'sensitivity_feasible':bool(all(x['max_constraint_violation']<1e-5 for x in sens['experiments'])),
 'uncertainty_changes_decisions_or_impacts':bool(len({round(x['expected_total_cost'],2) for x in sens['experiments']})>=3),
}
out={'phase':'PHASE-9','passed':all(checks.values()),'checks':checks,'policy_replay':replay,'strategic_sensitivity':sens}
Path('docs/validation/phase9_diagnostics.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'phase':out['phase'],'passed':out['passed'],'checks':checks,'policies':[{'policy':r['policy'],'expected_cost':r['expected_total_cost'],'cvar95':r['cvar95_total_cost'],'emergency_probability':r['emergency_recovery_probability']} for r in replay]},indent=2))
raise SystemExit(0 if out['passed'] else 1)
