from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.analytics.sensitivity import strategic_sensitivity


def test_strategic_sensitivity_is_multi_dimensional_and_feasible():
    _,red,_=ai_to_uncertainty_scenarios(raw_n=36,reduced_k=5,seed=920)
    r=strategic_sensitivity(red)
    assert len(r['experiments']) >= 6
    assert all(x['max_constraint_violation'] < 1e-5 for x in r['experiments'])
    assert len({round(x['expected_total_cost'],2) for x in r['experiments']}) >= 3
    assert len({round(x['expected_virgin_kg'],2) for x in r['experiments']}) >= 2
