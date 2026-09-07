# CIRCULAR-MASS — Closed-Loop Mass-Balance CVaR Network Algorithm

CIRCULAR-MASS is the signature decision layer for Circular Manufacturing. It decides recovery routing/facility use and scenario-specific virgin fallback while enforcing a recycled-content floor under uncertain recovery yields.

## Mathematical center

For facility routing `x_f`, binary activation `y_f`, scenario virgin fallback `v_s`, shortage `short_s`, surplus/spill `w_s`, VaR threshold `eta ∈ R`, and CVaR excess `u_s ≥ 0`:

`min recovery + fixed facility + E[virgin + shortage] + lambda * CVaR_alpha(shortage)`

subject to:

- `x_f <= capacity_f y_f`, with `y_f` binary;
- `sum_f yield[s,f] x_f + v_s + short_s - w_s = demand_s` for every scenario;
- `sum_f yield[s,f] x_f - w_s >= min_recycled_content * demand_s` for every scenario;
- `v_s <= max_virgin_share * demand_s`;
- `u_s >= short_s - eta`, with `u_s` nonnegative.

`w_s` is an explicit destination for recovery output that is not consumed by scenario demand. It is penalized by the configured surplus-handling cost and excluded from the recycled-content numerator, so reported recycled content cannot exceed 100% merely because a shared first-stage plan overproduces in a favorable yield scenario.

The routed recovery quantities and facility activations are first-stage decisions shared across scenarios. Virgin fallback and shortage are scenario recourse. The loss passed to CVaR is explicitly scenario shortage in kg, not a generic score. The solution artifact reports `eta`, `alpha`, each scenario loss and excess, objective decomposition, best bound, MIP gap, runtime, variable/constraint counts, and reconciliation diagnostics.

The `CircularMassConfig.solver_backend` contract is `auto`, `scipy`, or `gurobi`. `auto` selects the optional licensed Gurobi backend when `gurobipy` is installed and otherwise falls back to portable SciPy/HiGHS; `gurobi` makes the licensed dependency mandatory; `scipy` is the explicit portability mode. The shipped Windows acceptance gate installs and verifies Gurobi, checks exact objective parity against SciPy on the reference case, and records the licensed-solver result in `artifacts/circular_mass/gurobi_validation.json`.

## Governed product workflow

The project-native bridge in `src/circular_battery/decision/circular_mass_bridge.py` converts a solved mathematical plan into an inspectable decision artifact. Promotion requires: a present/passing reference validation artifact, optimal solver status, numerical feasibility, satisfaction of the requested recycled-content policy, zero expected shortage in the canonical reference, explicit CVaR variable reporting, and objective reconciliation. Even when all checks pass, the artifact remains `human_review_required=true`; the system does not autonomously open a facility or alter sourcing.

API surface:

- `GET /api/v1/circular-mass/reference` exposes the formulation, facilities, uncertainty set, and validation artifact.
- `POST /api/v1/circular-mass/decision` accepts `min_recycled_content`, `risk_aversion`, and `max_virgin_share`, solves the reference stochastic MILP, and returns the governed decision artifact.

The browser includes a dedicated **CIRCULAR-MASS** workspace showing policy controls, facility/routing decisions, constraint/evidence gates, scenario assumptions, and the evidence boundary.

## Important CVaR interpretation

In the current canonical reference problem, optimized shortage is zero in all scenarios. Consequently the shortage-CVaR term is numerically inactive in that reference run. The implementation therefore does **not** use the zero-shortage reference as evidence that CVaR improves tail performance. Shortage-producing stress cases are required before promoting such a claim.

## Evidence

- `artifacts/circular_mass/evidence.json` — formulation/baseline/sensitivity evidence.
- `artifacts/circular_mass/product_decision_evidence.json` — governed service/product integration evidence.
- `artifacts/circular_mass/EVIDENCE_REPORT.md` — formulation report.
- `artifacts/circular_mass/PRODUCT_INTEGRATION_REPORT.md` — product gate report.

## Evidence boundary

The reference evidence is deterministic synthetic formulation validation. It demonstrates feasibility, mass-balance behavior, baseline differences, parameter sensitivity, API/service integration, governance behavior, and a shortage-producing stress case that activates the CVaR tail term. It does not establish realized industrial recovery yield, environmental benefit, financial benefit, or causal field performance.
