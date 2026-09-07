import pytest
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.optimization.stochastic_value import (
    expected_value_scenario,
    stochastic_value_metrics,
)


def _reduced():
    _, reduced, _ = ai_to_uncertainty_scenarios(
        raw_n=80, reduced_k=10, seed=20260817
    )
    return reduced


def test_expected_value_scenario_probability_and_dimensions():
    reduced = _reduced()
    ev = expected_value_scenario(reduced)
    assert ev.probability == pytest.approx(1.0)
    assert len(ev.demand_kg) == len(reduced[0].demand_kg)
    assert len(ev.returns_kg) == len(reduced[0].returns_kg)
    assert len(ev.facility_availability) == len(reduced[0].facility_availability)


def test_vss_evpi_ordering_and_nonnegativity():
    v = stochastic_value_metrics(_reduced())
    eev = v["expected_result_of_expected_value_cost"]
    rp = v["risk_neutral_stochastic_program_cost"]
    ws = v["wait_and_see_expected_cost"]
    assert eev + 1e-7 >= rp
    assert rp + 1e-7 >= ws
    assert v["value_of_stochastic_solution"] == pytest.approx(eev-rp)
    assert v["expected_value_of_perfect_information"] == pytest.approx(rp-ws)
    assert v["value_of_stochastic_solution"] >= -1e-7
    assert v["expected_value_of_perfect_information"] >= -1e-7


def test_reference_information_value_has_no_emergency_recourse_dependency():
    v = stochastic_value_metrics(_reduced())
    assert v["value_of_stochastic_solution"] > 0
    assert v["expected_value_of_perfect_information"] > 0
    assert "facility availability held at planned state" in v["scope"]
