from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from circular4x.signature_algorithm import CircularMassScenario, reference_problem, solve_circular_mass

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    scenarios, cfg = reference_problem()
    gurobi_cfg = replace(cfg, solver_backend="gurobi")
    scipy_cfg = replace(cfg, solver_backend="scipy")
    gurobi = solve_circular_mass(scenarios, gurobi_cfg)
    scipy = solve_circular_mass(scenarios, scipy_cfg)

    tail_scenarios = [
        scenarios[0],
        scenarios[1],
        replace(scenarios[2], probability=0.15),
        CircularMassScenario("rare-severe", 0.05, 1_300_000, (0.45, 0.52, 0.40)),
    ]
    stress = solve_circular_mass(
        tail_scenarios,
        replace(gurobi_cfg, max_virgin_share=0.25, risk_aversion=0.75),
    )
    checks = {
        "backend_is_gurobi": gurobi.solver == "gurobi",
        "reference_optimal": gurobi.status == "OPTIMAL",
        "reference_zero_mip_gap": gurobi.mip_gap is not None and gurobi.mip_gap <= 1e-9,
        "reference_bound_matches": gurobi.best_bound is not None and abs(gurobi.best_bound - gurobi.objective) <= 1e-5,
        "reference_feasible": gurobi.max_constraint_violation <= 1e-6,
        "reference_integrality_verified": bool(gurobi.diagnostics and gurobi.diagnostics.get("integrality_verified")),
        "reference_objective_reconciles": bool(
            gurobi.diagnostics and gurobi.diagnostics.get("objective_reconciliation_error", 1.0) <= 1e-5
        ),
        "scipy_parity": abs(gurobi.objective - scipy.objective) <= 1e-5,
        "stress_tail_risk_active": stress.expected_shortage_kg > 0 and stress.cvar_shortage_kg > stress.expected_shortage_kg,
        "stress_backend_is_gurobi": stress.solver == "gurobi",
        "stress_objective_reconciles": bool(
            stress.diagnostics and stress.diagnostics.get("objective_reconciliation_error", 1.0) <= 1e-5
        ),
    }
    payload = {
        "algorithm": "CIRCULAR-MASS",
        "solver": "gurobi",
        "gurobi_version": gurobi.diagnostics.get("message") if gurobi.diagnostics else None,
        "reference": gurobi.to_dict(),
        "scipy_parity": {"objective": scipy.objective, "objective_delta": gurobi.objective - scipy.objective},
        "shortage_stress": stress.to_dict(),
        "checks": checks,
        "claim_boundary": "Licensed solver verification and synthetic formulation evidence only; no field or realized-benefit claim.",
    }
    out = ROOT / "artifacts" / "circular_mass" / "gurobi_validation.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"GUROBI_CIRCULAR_MASS={sum(checks.values())}/{len(checks)}")
    print(f"GUROBI_CIRCULAR_MASS_OBJECTIVE={gurobi.objective:.4f}")
    print(f"GUROBI_CIRCULAR_MASS_STRESS_CVAR={stress.cvar_shortage_kg:.4f}")
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
