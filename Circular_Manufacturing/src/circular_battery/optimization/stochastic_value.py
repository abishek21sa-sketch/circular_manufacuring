from __future__ import annotations

from dataclasses import replace
from circular_battery.optimization.stochastic_network import (
    StochasticNetworkConfig,
    demo_stochastic_config,
    solve_stochastic_network,
)
from circular_battery.simulation.uncertainty import CircularUncertaintyScenario
from circular_battery.simulation.policy_experiments import FixedStrategicPolicy, evaluate_policy


def _risk_neutral_config(cfg: StochasticNetworkConfig | None = None):
    base = cfg or demo_stochastic_config()
    return replace(
        base,
        risk_aversion=0.0,
        carbon_price_per_kg=0.0,
        virgin_penalty_per_kg=0.0,
        n_minus_one_min_capacity_kg=0.0,
    )


def _operational_uncertainty_only(scenarios):
    """Hold discrete facility availability at planned/available state.

    This produces the classical comparable-recourse setting for VSS/EVPI.
    Facility-outage value is evaluated elsewhere through the N-1/resilience and
    emergency-recovery experiments; mixing discrete outage infeasibility into
    EEV would make the classical VSS comparison undefined.
    """
    return [
        replace(
            s,
            facility_availability=tuple(1.0 for _ in s.facility_availability),
        )
        for s in scenarios
    ]


def expected_value_scenario(scenarios):
    if not scenarios:
        raise ValueError("at least one scenario required")
    total = sum(s.probability for s in scenarios)
    if abs(total - 1.0) > 1e-8:
        raise ValueError("scenario probabilities must sum to 1")
    T = len(scenarios[0].demand_kg)
    F = len(scenarios[0].facility_availability)

    def w(fn):
        return float(sum(s.probability * fn(s) for s in scenarios))

    return CircularUncertaintyScenario(
        name="expected-value",
        probability=1.0,
        demand_kg=tuple(w(lambda s, t=t: s.demand_kg[t]) for t in range(T)),
        returns_kg=tuple(w(lambda s, t=t: s.returns_kg[t]) for t in range(T)),
        collection_rate=w(lambda s: s.collection_rate),
        recycle_yield=w(lambda s: s.recycle_yield),
        reman_yield=w(lambda s: s.reman_yield),
        virgin_cost_multiplier=w(lambda s: s.virgin_cost_multiplier),
        transport_cost_multiplier=w(lambda s: s.transport_cost_multiplier),
        carbon_multiplier=w(lambda s: s.carbon_multiplier),
        facility_availability=tuple(
            w(lambda s, f=f: s.facility_availability[f]) for f in range(F)
        ),
        internal_scrap_supply_kg=tuple(
            w(lambda s, t=t: s.internal_scrap_supply_kg[t]) for t in range(T)
        ),
        second_life_share=w(lambda s: s.second_life_share),
        reman_eligible_share=w(lambda s: s.reman_eligible_share),
    )


def stochastic_value_metrics(scenarios, cfg: StochasticNetworkConfig | None = None):
    """Compute RP, EEV, WS, VSS and EVPI for comparable operational uncertainty.

    Definitions:
      RP   = optimal risk-neutral stochastic-program expected cost.
      EV   = deterministic expected-value problem.
      EEV  = expected cost of the EV first-stage policy under all scenarios.
      WS   = expected wait-and-see cost with perfect scenario information.
      VSS  = EEV - RP.
      EVPI = RP - WS.

    Discrete facility outages are intentionally held at available state for
    this classical information-value calculation. Outage economics remain in
    the separate N-1 / policy-replay resilience experiments.
    """
    cfg = _risk_neutral_config(cfg)
    comparable = _operational_uncertainty_only(scenarios)

    rp = solve_stochastic_network(comparable, cfg)

    ev_sc = expected_value_scenario(comparable)
    ev = solve_stochastic_network([ev_sc], cfg)
    ev_policy = FixedStrategicPolicy(
        "expected_value_policy",
        ev.open_facilities,
        ev.expansion_units,
    )
    eev = evaluate_policy(comparable, cfg, ev_policy)
    if eev.emergency_recovery_probability > 1e-12:
        raise RuntimeError(
            "Expected-value policy required emergency recourse in comparable "
            "VSS/EVPI setting; classical VSS would not be comparable."
        )

    ws_cost = 0.0
    wait_and_see_rows = []
    for s in comparable:
        single = replace(s, probability=1.0)
        sol = solve_stochastic_network([single], cfg)
        weighted = s.probability * sol.expected_total_cost
        ws_cost += weighted
        wait_and_see_rows.append({
            "scenario": s.name,
            "probability": s.probability,
            "optimal_total_cost": sol.expected_total_cost,
            "weighted_cost": weighted,
            "open_facilities": sol.open_facilities,
            "expansion_units": sol.expansion_units,
        })

    vss = eev.expected_total_cost - rp.expected_total_cost
    evpi = rp.expected_total_cost - ws_cost

    return {
        "risk_neutral_stochastic_program_cost": rp.expected_total_cost,
        "expected_value_problem_cost": ev.expected_total_cost,
        "expected_result_of_expected_value_cost": eev.expected_total_cost,
        "wait_and_see_expected_cost": ws_cost,
        "value_of_stochastic_solution": vss,
        "expected_value_of_perfect_information": evpi,
        "vss_percent_of_rp": vss / rp.expected_total_cost if rp.expected_total_cost else 0.0,
        "evpi_percent_of_rp": evpi / rp.expected_total_cost if rp.expected_total_cost else 0.0,
        "stochastic_first_stage": {
            "open_facilities": rp.open_facilities,
            "expansion_units": rp.expansion_units,
        },
        "expected_value_first_stage": {
            "open_facilities": ev.open_facilities,
            "expansion_units": ev.expansion_units,
        },
        "wait_and_see_rows": wait_and_see_rows,
        "scope": (
            "Classical comparable-recourse information-value analysis with "
            "facility availability held at planned state. Discrete outage value "
            "is evaluated separately through N-1 resilience and emergency-recovery replay."
        ),
        "evidence_class": "SYNTHETIC STOCHASTIC OR INFORMATION-VALUE ANALYSIS",
    }
