import pytest
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.simulation.uncertainty import generate_raw_scenarios,reduce_scenarios,scenario_summary
from circular_battery.optimization.advanced_frontier import advanced_strategy_frontier
from circular_battery.optimization.stochastic_network import demo_stochastic_config
from circular_battery.simulation.policy_experiments import FixedStrategicPolicy,evaluate_policy,compare_policies

def test_uncertainty_generation_is_seed_reproducible():
    a=generate_raw_scenarios(20,seed=123);b=generate_raw_scenarios(20,seed=123)
    assert [x.to_dict() for x in a]==[x.to_dict() for x in b]

def test_scenario_reduction_is_seed_reproducible():
    raw=generate_raw_scenarios(30,seed=124)
    a=reduce_scenarios(raw,5,seed=124);b=reduce_scenarios(raw,5,seed=124)
    assert [x.to_dict() for x in a]==[x.to_dict() for x in b]
    assert scenario_summary(a)['probability_sum']==pytest.approx(1)

def test_uncertainty_contains_multiple_risk_dimensions():
    raw=generate_raw_scenarios(60,seed=125)
    assert len({round(x.virgin_cost_multiplier,3) for x in raw})>10
    assert len({round(x.collection_rate,3) for x in raw})>10
    assert len({round(x.recycle_yield,3) for x in raw})>10
    assert any(0 in x.facility_availability for x in raw)

def test_policy_replay_metrics_are_physical():
    raw,red,_=ai_to_uncertainty_scenarios(raw_n=40,reduced_k=6,seed=126)
    f=advanced_strategy_frontier(red);x={p['policy']:p for p in f['candidates']}['cost']
    p=FixedStrategicPolicy('cost',x['open_facilities'],x['expansion_units'])
    r=evaluate_policy(raw,demo_stochastic_config(),p)
    assert r.cvar95_total_cost >= r.expected_total_cost
    assert r.p90_total_cost >= r.expected_total_cost*.8
    assert 0 <= r.expected_service_level <= 1
    assert 0 <= r.emergency_recovery_probability <= 1

def test_policy_comparison_uses_same_scenarios():
    raw,red,_=ai_to_uncertainty_scenarios(raw_n=40,reduced_k=6,seed=127)
    f=advanced_strategy_frontier(red);by={p['policy']:p for p in f['candidates']}
    pol=[FixedStrategicPolicy(k,by[k]['open_facilities'],by[k]['expansion_units']) for k in ('cost','resilience')]
    r=compare_policies(raw,demo_stochastic_config(),pol)
    assert len(r)==2
    assert r[0]['scenarios']==r[1]['scenarios']==40
    assert r[0]['delta_vs_first_policy']['expected_cost']==pytest.approx(0)
