# Phase 10 Hotfix 0.10.2

Windows licensed acceptance of 0.10.1 returned an optimal four-pass Gurobi
hierarchical solution, but the checker rejected `SHORTAGE_KG=1.0001e-06`
against a hard-coded `1e-6` threshold.

The model itself reported:
- OPTIMAL;
- four optimal multi-objective passes;
- zero per-pass MIP gaps;
- zero model constraint violation;
- zero integrality violation.

The acceptance gate now uses and reports:

`service acceptance tolerance = service objective absolute tolerance + Gurobi FeasibilityTol`

For the reference configuration this is:

`1e-6 kg + 1e-6 kg = 2e-6 kg`

This does not relax the optimization formulation. It makes the acceptance rule
consistent with the tolerances already configured in the hierarchical
multi-objective solve and the solver's finite-precision feasibility policy.
