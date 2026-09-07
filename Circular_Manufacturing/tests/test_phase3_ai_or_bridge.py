from circular_battery.optimization.network import NetworkScenario, solve_network
def test_more_predicted_returns_reduce_or_preserve_virgin_requirement():
    low=NetworkScenario(returns_kg=(200000.,220000.,240000.))
    high=NetworkScenario(returns_kg=(500000.,520000.,540000.))
    assert solve_network(high).virgin_kg <= solve_network(low).virgin_kg + 1e-6
