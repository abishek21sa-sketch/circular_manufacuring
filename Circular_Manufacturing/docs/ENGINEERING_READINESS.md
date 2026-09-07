# Engineering readiness

This is an internal engineering rubric for the portfolio release. It evaluates
the evidence that can be demonstrated from the workstation and identifies the
external controls required before an operational deployment.

## Scope of this gate

The gate evaluates only the parts that can be demonstrated from this
workstation: IE/OR formulation quality, mathematical verification, AI/ML
validation design, reproducibility, data governance, safety boundaries, and
release evidence.

| Engineering area | Evidence required | Current status |
|---|---|---|
| Mathematical integrity | Feasibility audits, conservation checks, integrality checks, optimality/bound evidence, sensitivity and stochastic diagnostics | PASS |
| Licensed optimization | Explicit Gurobi backend, Academic-license engineering run, zero recorded MIP gap on acceptance cases | PASS |
| Industrial engineering | Material flow, production/inventory, capacity, service, safety stock, recovery, sourcing, resilience, and routing models | PASS |
| AI/ML discipline | Held-out evaluation, baselines, uncertainty/calibration evidence, explainability, deterministic reconstruction, and claim labels | PASS |
| Scenario robustness | 120,000-row case-stratified benchmark, twelve adverse/nominal case families, public-context strata, bounded trend profiles, and separate negative fixtures | PASS |
| Data governance | Source registry, lineage, hashes, public-reference separation, permission boundary, and synthetic fallback | PASS |
| Reproducibility | Locked Python runtime, fixed seed, deterministic artifacts, machine-readable reports, and rerunnable Windows gate | PASS |
| Human and security controls | Human approval boundary, no autonomous facility action, secret scan, sanitized package, and release claim boundaries | PASS |

## What the gate does not certify

It does not certify commercial Gurobi authorization, customer SSO/MFA/TLS,
managed-database operations, regulatory compliance, cybersecurity accreditation,
field-calibrated accuracy, realized savings, or causal environmental benefit.
Those require external owners, permissions, infrastructure, and measured plant
evidence. Academic Gurobi is used only for student/research engineering
validation.

## Promotion path

The next promotion is a permissioned pilot: obtain approved plant/recycler data,
map it through the governed bundle contract, freeze a backtest and untouched
validation window, calibrate the models and engineering parameters, and measure
benefits against an approved baseline. Only after that evidence exists should a
commercial license and enterprise deployment approval be evaluated.
