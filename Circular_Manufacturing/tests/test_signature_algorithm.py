import pytest
from dataclasses import replace
from circular4x.signature_algorithm import CircularMassScenario, reference_problem, solve_circular_mass

def test_circular_mass_is_feasible_and_closes_mass():
    scenarios,cfg=reference_problem()
    sol=solve_circular_mass(scenarios,cfg)
    assert sol.status=='OPTIMAL'
    assert sol.max_constraint_violation < 1e-5
    assert sol.recycled_content_share >= cfg.min_recycled_content-1e-8
    assert sol.cvar_shortage_kg >= sol.expected_shortage_kg-1e-8

def test_circularity_floor_displaces_virgin_material():
    scenarios,cfg=reference_problem()
    zero_fac=tuple(replace(f,capacity_kg=0.0) for f in cfg.facilities)
    virgin_only=solve_circular_mass(scenarios,replace(cfg,facilities=zero_fac,min_recycled_content=0.0,risk_aversion=0.0,max_virgin_share=1.0))
    circular=solve_circular_mass(scenarios,cfg)
    assert circular.expected_recovered_kg > virgin_only.expected_recovered_kg + 1.0
    assert sum(circular.virgin_kg) < sum(virgin_only.virgin_kg)

def test_higher_recycled_content_requires_more_recovery():
    scenarios,cfg=reference_problem()
    low=solve_circular_mass(scenarios,replace(cfg,min_recycled_content=.15))
    high=solve_circular_mass(scenarios,replace(cfg,min_recycled_content=.65))
    assert high.expected_recovered_kg > low.expected_recovered_kg
    assert high.recycled_content_share >= .65-1e-8

def test_probability_validation():
    scenarios,cfg=reference_problem()
    bad=[replace(scenarios[0],probability=.2),*scenarios[1:]]
    with pytest.raises(ValueError): solve_circular_mass(bad,cfg)


def test_solution_exposes_cvar_and_solver_evidence():
    scenarios,cfg=reference_problem()
    sol=solve_circular_mass(scenarios,cfg)
    assert sol.alpha == cfg.risk_alpha
    assert sol.diagnostics["eta_domain"] == "R"
    assert len(sol.scenario_details) == len(scenarios)
    assert all("loss_kg" in row and "cvar_excess_kg" in row for row in sol.scenario_details)
    assert sol.objective_components["cvar_risk_premium"] == pytest.approx(cfg.risk_aversion*sol.cvar_shortage_kg)
    assert sol.diagnostics["objective_reconciliation_error"] < 1e-5
    assert sol.variable_count > 0
    assert sol.constraint_count > 0
    assert sol.runtime_seconds >= 0


def test_solver_backend_contract_and_gurobi_parity():
    scenarios,cfg=reference_problem()
    scipy=solve_circular_mass(scenarios,replace(cfg,solver_backend="scipy"))
    assert scipy.solver == "scipy.optimize.milp"
    assert scipy.diagnostics["effective_solver_backend"] == "scipy"
    try:
        import gurobipy  # noqa: F401
    except ImportError:
        return
    gurobi=solve_circular_mass(scenarios,replace(cfg,solver_backend="gurobi"))
    assert gurobi.solver == "gurobi"
    assert gurobi.diagnostics["effective_solver_backend"] == "gurobi"
    assert gurobi.status == "OPTIMAL"
    assert gurobi.mip_gap <= 1e-9
    assert gurobi.best_bound == pytest.approx(gurobi.objective)
    assert gurobi.objective == pytest.approx(scipy.objective)


def test_shortage_stress_activates_tail_risk_without_changing_loss_definition():
    scenarios,cfg=reference_problem()
    tail_scenarios=[
        scenarios[0],
        scenarios[1],
        replace(scenarios[2],probability=.15),
        CircularMassScenario("rare-severe",.05,1_300_000,(.45,.52,.40)),
    ]
    stressed=replace(cfg,max_virgin_share=.25,risk_aversion=.75)
    sol=solve_circular_mass(tail_scenarios,stressed)
    assert sol.expected_shortage_kg > 0
    assert sol.cvar_shortage_kg >= sol.expected_shortage_kg
    assert sol.eta > 0
    assert any(row["cvar_excess_kg"] > 0 for row in sol.scenario_details)
    assert sol.diagnostics["loss_definition"].startswith("scenario shortage")


def test_invalid_inputs_are_rejected_before_solver_call():
    scenarios,cfg=reference_problem()
    with pytest.raises(ValueError,match="probabilities"):
        solve_circular_mass([replace(scenarios[0],probability=-.1),*scenarios[1:]],cfg)
    with pytest.raises(ValueError,match="yields"):
        solve_circular_mass([replace(scenarios[0],yields=(1.2,.9,.8)),*scenarios[1:]],cfg)
    with pytest.raises(ValueError,match="max_virgin_share"):
        solve_circular_mass(scenarios,replace(cfg,max_virgin_share=1.1))
    with pytest.raises(ValueError,match="positive"):
        solve_circular_mass([replace(scenarios[0],demand_kg=0),*scenarios[1:]],cfg)
    with pytest.raises(ValueError,match="capacity and costs"):
        solve_circular_mass(scenarios,replace(cfg,facilities=(replace(cfg.facilities[0],fixed_cost=-1),*cfg.facilities[1:])))
    with pytest.raises(ValueError,match="solver_backend"):
        solve_circular_mass(scenarios,replace(cfg,solver_backend="unknown"))
    with pytest.raises(ValueError,match="finite"):
        solve_circular_mass(scenarios,replace(cfg,risk_aversion=float("nan")))


def test_explicit_gurobi_reports_missing_binding(monkeypatch):
    import builtins
    scenarios,cfg=reference_problem()
    real_import=builtins.__import__
    def missing_gurobi(name,*args,**kwargs):
        if name == "gurobipy":
            raise ImportError("test-only missing binding")
        return real_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,"__import__",missing_gurobi)
    with pytest.raises(RuntimeError,match="gurobipy is not installed"):
        solve_circular_mass(scenarios,replace(cfg,solver_backend="gurobi"))
