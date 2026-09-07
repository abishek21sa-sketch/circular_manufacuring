# V1 Validation

V1 uses layered evidence rather than a single green test count.

## Mathematical/engineering gates
- material-flow closure;
- return/recovery conservation;
- inventory balances;
- capacity and policy constraints;
- reverse-logistics flow balance;
- CVRP route feasibility and exact-customer visitation;
- stochastic MILP feasibility;
- CVaR consistency;
- critical-material balance and shortage checks;
- independent small-instance/oracle checks.

## AI gates
- chronological/cohort holdouts;
- baseline comparisons;
- calibration where appropriate;
- uncertainty/explanation evidence;
- deterministic current-runtime reconstruction.

## Software gates
- full pytest regression suite;
- frontend build;
- structured V1 API/live smoke;
- SQLite persistence tests;
- external-bundle ingestion tests;
- path/security/contract checks;
- source package wheel build;
- exact ZIP clean-extraction rerun.

## Windows-only licensed gates
The portable build host does not possess the user's Gurobi academic license. Final Windows acceptance therefore re-runs:
- Phase-3 Gurobi equivalence;
- Phase-10 hierarchical multi-objective Gurobi;
- per-pass MIP gap/status;
- primal/integrality violation checks.

## Evidence boundary
Passing V1 validation certifies the computational/software implementation against the included tests and synthetic/reference data. It does not certify real-world causal benefit or external data truth.
