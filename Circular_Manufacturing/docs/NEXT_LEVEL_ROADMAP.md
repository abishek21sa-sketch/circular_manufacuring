# Next-level engineering roadmap

This roadmap states exactly what is implemented, what remains, and what evidence is required to move the Circular Manufacturing Studio into a controlled enterprise pilot. It is intentionally cross-functional: industrial engineering, operations research, mathematics, AI/ML, data, product, security, platform, and business impact all have to progress together.

## Definition of the next stage

The next stage is an authorized pilot with one real operating context, governed data, a measured baseline, a named accountable owner, and a repeatable deployment runbook. “Done” means the system can make a bounded recommendation, explain it, reproduce it, obtain human approval, and measure whether the recommendation helped.

## Current state versus exit evidence

| Layer | Current evidence | Next-level requirement | Exit evidence |
|---|---|---|---|
| Industrial engineering and OR | Material balances, reverse-network planning, capacity constraints, routing checks, multiobjective policies | Validate process times, labor standards, queue assumptions, service rules, and facility operating limits with an operating partner | Signed process map, calibrated standards, and a shadow-mode plan compared with the current policy |
| Mathematical optimization | Mixed-integer planning, scenario recourse, CVaR-style tail control, conservation checks, objective decomposition | Add independently verified instances, infeasibility explanations, warm-start and time-limit policy, and stability tests across parameter changes | Solver report, reference-instance certificate, feasibility report, and documented acceptance tolerances |
| AI and ML | Modular demand, return, scrap, and pathway model roles with metrics and calibration scaffolding | Train on governed historical data, use time/group-aware holdouts, monitor drift, calibrate probabilities, and document approval thresholds | Model cards, holdout results, slice metrics, calibration report, and rollback procedure |
| Data and provenance | Source registry, public-reference validation, deterministic 120,000-row synthetic workload, checksums and manifests | Establish ownership, retention, consent, quality SLAs, lineage, data contracts, and data refresh jobs | Data contract, lineage diagram, access review, refresh log, and signed data-quality report |
| Public-reference evidence | EPA-derived reference extract used for schema and distribution anchoring | Add domain-specific public benchmarks and cite each factor, standard, and conversion used by the pilot | Source register with licenses, retrieval dates, transformation code, and review sign-off |
| Product and UX | Multi-view Material Circularity Studio with materials, network, plan, strategy, routes, AI, risk, trace, runs, and evidence views | Add role-based workflows, saved views, approval queues, comparison to baseline, and exportable decision packets | Usability review, role test script, approved recommendation packet, and accessibility check |
| API and security | Health/readiness endpoints, validation, structured errors, local audit/evidence patterns | Add SSO/OIDC, RBAC, tenant isolation, secret management, rate limits, threat modeling, and security testing | Threat model, access matrix, penetration findings resolved, and audit-log review |
| Platform and persistence | Local SQLite option, PostgreSQL configuration path, deterministic local launcher | Deploy managed PostgreSQL and object storage, migrations, backups, restore drills, environment separation, and infrastructure-as-code | Deployment runbook, migration test, restore evidence, and environment parity report |
| Reliability and observability | Smoke tests, acceptance tests, solver metadata, packaging checks | Add metrics, traces, structured logs, alerts, SLOs, queue controls, and graceful degradation when a model or solver is unavailable | Operational dashboard, alert test, SLO report, and incident playbook |
| Operations and impact | Baseline comparison fields and evidence bundle structure | Measure labor, cost, service, emissions, waste, and recovery outcomes against a pre-registered baseline | Controlled pilot readout with confidence intervals, realized-impact calculation, and owner sign-off |
| Release and CI | Local full test suite, frontend build, security scan, release manifest, and deterministic packaging | Add hosted CI, dependency scanning, coverage thresholds, signed artifacts, release approvals, and rollback automation | Green CI run, signed release, SBOM, release approval, and rollback rehearsal |
| Licensing and governance | Academic solver path documented; commercial authorization remains a gate | Confirm solver terms, data licenses, model-use rights, indemnity, and retention policy for the target deployment | Written approvals in the deployment record and a license-aware configuration |

## Priority sequence

### P0: prove the decision loop

1. Choose one bounded pilot use case, such as a single material family and a single planning horizon.
2. Define the current-policy baseline before looking at recommendations.
3. Obtain governed historical inputs and map them to the canonical schema.
4. Independently validate material, capacity, routing, and service constraints.
5. Run the system in shadow mode with human review and no automatic execution.
6. Capture recommendation quality, runtime, overrides, and operational impact.

### P1: make it safe to operate

1. Add identity, roles, tenant boundaries, and secret management.
2. Deploy managed persistence, backups, restores, migrations, and environment separation.
3. Add model and data drift monitoring, alerting, and rollback.
4. Add solver time-limit behavior, infeasibility diagnostics, and a documented fallback plan.
5. Produce signed evidence packets with source, model, scenario, solver, and reviewer metadata.
6. Establish incident response, change control, and a release approval workflow.

### P2: scale the operating model

1. Expand from one pilot context to multiple sites and material families.
2. Add asynchronous jobs, queue limits, caching, and cost controls.
3. Introduce continuous recalibration and champion/challenger model evaluation.
4. Add supplier, carrier, and downstream-recycler integrations where contracts permit.
5. Quantify realized impact over multiple planning cycles.
6. Harden capacity, disaster recovery, accessibility, and regional compliance controls.

## What can be claimed now

The repository can credibly claim:

- a reproducible engineering prototype;
- a large deterministic synthetic workload covering varied operating cases;
- public-reference schema and distribution checks;
- explicit mathematical constraints and post-solve validation;
- a Gurobi-backed research/engineering path when the local Academic license is available;
- modular AI/ML evaluation scaffolding;
- evidence, provenance, policy replay, and human-approval patterns;
- a runnable multi-view analyst experience with automated tests.

## What cannot be claimed yet

The repository should not claim:

- measured production savings or emissions reduction;
- field accuracy of forecasts or recovery predictions;
- regulatory or safety certification;
- unattended execution of material or disposal decisions;
- multi-tenant security accreditation;
- commercial solver authorization;
- resilience or service levels that have not been load-tested in the target environment.

## Suggested pilot scorecard

Use a pre-registered scorecard so success is not redefined after the result:

- service level and late-demand rate;
- recovered mass and recycled-content share;
- virgin-material displacement;
- disposal mass;
- total cost and cost per recovered unit;
- energy, water, and emissions indicators;
- planner override rate and reason;
- solver runtime, gap, and infeasibility rate;
- model calibration and slice performance;
- data freshness and quality SLA;
- realized impact against the current-policy baseline.

Report point estimates, uncertainty intervals, assumptions, and exclusions. A strong result is one that remains understandable and defensible when a reviewer challenges the data, model, objective, or operational constraint.
