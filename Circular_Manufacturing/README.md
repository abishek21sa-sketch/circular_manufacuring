> **RC3 Windows acceptance:** from the outer extracted RC3 folder, run `.\RUN_ACCEPTANCE.cmd`. Do not run the PowerShell acceptance scripts directly. The RC3 launcher creates/verifies a Python 3.14 project venv, installs the acceptance dependencies, and runs the correct repository gate without depending on PowerShell execution policy.

# Circular Manufacturing Intelligence Platform

**V1.2.1 — Integrated Circular Battery Manufacturing & Recovery Decision Workbench**

A computational decision platform for closed-loop lithium-ion battery manufacturing and recovery.

The system connects predictive AI, Industrial Engineering, Operations Research, circular manufacturing, lifecycle accounting, reverse logistics, vehicle routing, stochastic optimization and explainable decision intelligence into one auditable chain.

> Reference numerical results are **SYNTHETIC VALIDATION**. V1 does not claim observed factory/recycler performance or realized savings.

**Release posture:** this is a Gurobi-verified engineering release candidate,
not production certification. The validation machine reports an Academic Gurobi
license, and commercial licensing, enterprise identity/access controls,
operational SLOs, disaster recovery, field calibration, and realized-benefit
validation remain deployment gates.

---

## The operating decision

Given uncertain future battery demand, manufacturing scrap, end-of-life returns, recovery quality, process yield, transportation economics, carbon burden, material prices and recovery capacity:

**What mix of virgin material, recovered feed, remanufacturing, recycling, inventories, collection routes, facility capacity and resilience should be selected?**

V1.2.1 does not stop at forecasting or dashboarding. Predictions alter the engineering state; the engineering state constrains optimization; optimized policies are replayed across uncertain futures; the final recommendation preserves its full computational ancestry.

---

## Computational chain

```text
Demand / Return / Scrap / Recovery AI
                  ↓
          uncertainty bridge
                  ↓
 material + lifecycle accounting
                  ↓
      reverse recovery network
                  ↓
       IE production planning
                  ↓
 two-stage stochastic MILP + CVaR
                  ↓
  critical-material sourcing plan
                  ↓
              CVRP
                  ↓
       policy digital replay
                  ↓
 explainable human-gated decision
                  ↓
       SQLite-local/PostgreSQL-hosted registry + provenance + Studio
```

---


## V1.2.1 integration upgrade

V1.2.1 addresses the largest product-level weakness of the accepted V1.0.1 build: strong mathematical modules that were not all connected in the visible decision chain.

The reference workbench now couples:

- AI-derived demand -> stochastic network demand;
- stochastic expected recovery output -> IE production/inventory recovered supply;
- coupled pack demand + BOM -> lithium/nickel/cobalt/graphite sourcing demand;
- coupled recovered-use plan -> critical-material recovered supply;
- AI-derived return volume -> exact CVRP pickup demand.

The Studio also exposes a seven-model mathematical inventory with variable/constraint counts, solver class and verification route. The V1 API additionally exposes a bounded, read-only EPA facility benchmark summary/search surface with source provenance. See `docs/V12_MATH_AND_INTEGRATION_AUDIT.md` and `docs/API.md`.

The accepted Phase-10 computational files remain hash-locked and unchanged.

---

## What is actually implemented

### Predictive AI

Four real models with held-out validation and baselines:

- battery demand forecasting;
- discrete-time end-of-life return hazard;
- recovery-pathway classification;
- manufacturing scrap-rate prediction.

V1 additionally reports forecast uncertainty, return calibration and model explanations. Release execution reconstructs deterministic models in the installed scikit-learn runtime rather than depending on cross-version pickle internals.

### Industrial Engineering

Implemented IE state includes:

- material-flow analysis;
- value-stream / process-cycle efficiency;
- production planning;
- regular/overtime capacity;
- recovered-material inventory;
- finished-goods inventory;
- safety stock;
- service level;
- capacity utilization;
- material productivity;
- recycled-content and virgin-dependency metrics.

### Circular manufacturing

The physical lifecycle represents:

- virgin material;
- battery manufacturing;
- manufacturing scrap;
- use cohorts;
- end-of-life returns;
- collection;
- recovery grading;
- second life;
- remanufacturing;
- recycling;
- losses/disposal;
- recovered critical-material feed.

Lithium, nickel, cobalt and graphite are explicitly represented in the critical-material planning layer.

### Operations Research

V1 contains multiple genuine mathematical programs:

- closed-loop material MILP;
- reverse-logistics facility/flow MILP;
- production/inventory LP;
- two-stage stochastic closed-loop MILP;
- CVaR tail-risk objective;
- N−1 recovery-capacity resilience;
- hierarchical Gurobi multi-objective optimization;
- critical-material supplier optimization;
- literal capacitated vehicle routing;
- cost/carbon/virgin strategy frontier.

Small cases and post-solve conservation/constraint audits provide independent verification where practical.

### Simulation and digital experiments

V1 varies correlated future demand, returns, collection, yield, scrap, transport, material price, carbon and facility availability.

Representative scenarios are used for stochastic optimization. Chosen fixed policies are then replayed on the larger unreduced scenario population, producing expected, P90 and CVaR outcomes plus emergency-recovery probability.

### Explainable decision intelligence

The final recommendation includes:

- selected policy;
- facility/capacity actions;
- model-derived confidence;
- cost/carbon/virgin/tail-risk impact;
- trade-offs and assumptions;
- human-approval gate;
- stable decision hash;
- eleven-stage AI → IE → OR → simulation trace.

---

## External data input

V1 is no longer locked to the synthetic demo architecture.

A validated scenario bundle can supply:

```text
manifest.json
materials.csv
periods.csv
collections.csv
facilities.csv
planning.csv
```

A working template is included at:

```text
data/templates/reference_bundle
```

Before a controlled pilot, require governed ingestion:

```powershell
& .venv\Scripts\python.exe scripts\run_data_bundle.py `
  data\templates\reference_bundle --validate-only --require-lineage
```

The report records a stable ingestion ID, source lineage, row counts and
per-file fingerprints. Synthetic evidence remains synthetic even when all
schema and lineage checks pass.

Validate:

```powershell
python scripts\run_data_bundle.py data\templates\reference_bundle --validate-only
```

Run the ingested core lifecycle → reverse logistics → planning chain:

```powershell
python scripts\run_data_bundle.py data\templates\reference_bundle --out artifacts\bundle_report.json
```

Schema validation does not certify external source truth.

The source acquisition decision record is in
`docs/DATA_SOURCE_REVIEW.md`, with a machine-readable registry at
`data/public/data_source_registry.json`. It records the public EPA reference
extract, public/research candidates, Kaggle discovery limits, commercial
subscriptions, and private/company data that requires authorization. The
canonical end-to-end benchmark remains synthetic until those permissions and
source contracts exist.

The IE/math/AI/ML evidence rubric is validated by
`scripts/validate_engineering_readiness.py` and documented in
`docs/ENGINEERING_READINESS.md`. The detailed implementation is in
`docs/TECHNICAL_FOUNDATIONS.md`, and the cross-layer promotion requirements are
in `docs/NEXT_LEVEL_ROADMAP.md`.

### Large synthetic benchmark

For reproducible research and robustness testing, V1 includes the governed
120,000-row synthetic enterprise benchmark at
`data/synthetic/enterprise_120k/`. It covers twelve demand, quality, recovery,
logistics, capacity, outage, carbon, and data-quality case families. Run the
generator, validator, and explicit Academic-Gurobi benchmark from the outer
folder with `RUN_SYNTHETIC_ENTERPRISE.cmd`. The dataset is synthetic
validation only and cannot replace plant telemetry or realized-benefit
evidence; see `docs/SYNTHETIC_ENTERPRISE_DATASET.md`.

---


## V1.2.1 stochastic value diagnostics

The integrated workbench now reports classical stochastic-program value metrics:

- `RP`: risk-neutral stochastic-program expected cost;
- `EEV`: expected cost of the deterministic expected-value first-stage policy;
- `WS`: wait-and-see expected cost with perfect scenario information;
- `VSS = EEV - RP`;
- `EVPI = RP - WS`.

For the shipped seeded reference experiment, the comparable-recourse analysis reports a positive VSS and EVPI. Discrete facility-outage economics remain separated into the N-1 resilience and emergency-recovery experiments.

## Material Circularity Studio

The Studio ships two frontends during the rewrite:

- **`frontend/`** — the current UI: a real SvelteKit + TypeScript single-page
  app (file-based routing, one Svelte component per tab, `npm run build`
  produces a static Vercel deployment). This is what should be developed and
  deployed going forward.
- **`web/`** — the pre-rewrite legacy frontend: a hand-written TypeScript
  bundle compiled by plain `tsc` into `web/dist/app.js` and served directly by
  `circular_battery.web.server`. Kept for reference only; it is not part of
  the deploy path described below and can be removed once `frontend/` has
  been validated against a real deployment.

All eleven tabs (`MATERIALS · NETWORK · PLAN · STRATEGY · ROUTES · AI · RISK ·
CIRCULAR-MASS · TRACE · RUNS · EVIDENCE`) are ported to `frontend/` with full
feature parity against `web/`, including the interactive quick-resolve
(`/api/optimize`), the CIRCULAR-MASS solve-and-gate workflow, and the RUNS
registry composer/inspector. See `frontend/README` (this section) and
`frontend/src/routes/` for the route-per-tab layout.

### Running the backend only (legacy UI at the same origin)

```powershell
python scripts\run_workbench.py
```

Open `http://127.0.0.1:8765` — this serves `web/dist` unchanged, exactly as
before.

### Running the new SvelteKit frontend against it

```powershell
python scripts\run_workbench.py          # backend on :8765, in one terminal
cd frontend
npm install
npm run dev                              # SvelteKit dev server on :5173
```

`frontend/.env.example` documents `VITE_API_BASE` (defaults to
`http://127.0.0.1:8765`, matching the command above). Copy it to `.env` to
override for a different backend. The whole app is a client-rendered SPA
(`ssr = false` in the root layout) that fetches `/api/v1/workbench` and
`/api/reference` once on load and shares them across every tab; CIRCULAR-MASS
and RUNS each fetch their own data independently, matching the legacy
per-view boot behavior in `web/src/app.ts`.

The final Studio is organized as an engineering workspace rather than a conventional KPI dashboard:

`MATERIALS · NETWORK · PLAN · STRATEGY · ROUTES · AI · RISK · TRACE · RUNS · EVIDENCE`

The `RUNS` workspace executes and persists full decision experiments. Every persisted run carries scenario configuration, code fingerprint, runtime provenance, request ID, actor role, decision hash and complete report. The current bearer pilot records role-level identity; enterprise OIDC/SAML remains required for user identity.

---

## Enterprise V1 layer

The final platform adds:

- SQLite scenario/run registry;
- audit-event ledger;
- structured JSONL operational events;
- code fingerprinting;
- runtime dependency provenance;
- scenario import;
- structured V1 API envelopes;
- request IDs;
- health/readiness endpoints;
- structured errors;
- request-size validation;
- security headers;
- legacy endpoint compatibility;
- Render Blueprint;
- Dockerfile;
- clean Windows acceptance workflow.

See `docs/API.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, and
`docs/PRODUCTION_READINESS.md`.

---

## V1 API

Examples:

```text
GET  /api/v1/health
GET  /api/v1/ready
GET  /api/v1/reference
GET  /api/v1/scenarios
POST /api/v1/scenarios
GET  /api/v1/runs
POST /api/v1/runs
GET  /api/v1/runs/{run_id}
GET  /api/v1/audit
```

See `docs/API.md` for the complete contract.

---

## Windows setup

V1 is released and accepted with Windows as the required local target.

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-windows-py314.lock
python -m pip install -e ".[dev,gurobi]" --no-deps
```

Your Gurobi license is external to the repository. No license credentials are stored here.
The governed CIRCULAR-MASS solver uses Gurobi automatically when the binding and license are available; set `solver_backend="scipy"` only for an explicit portable fallback.

### Final acceptance

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows_v1_final_gate.ps1
```

The final success marker is:

```text
CIRCULAR MANUFACTURING V1.0 FINAL WINDOWS GATE PASSED
```

---

## Evidence and reproducibility

Important evidence files:

- `docs/TECHNICAL_METHODS.md`
- `docs/CONSTITUTION_COMPLIANCE_MATRIX_V1.md`
- `docs/validation/v1_compliance.json`
- `docs/validation/v1_diagnostics.json`
- `artifacts/release_readiness.json`
- `artifacts/v1_reference_decision_report.json`
- `artifacts/v1_reference_bundle_report.json`

Every public claim should retain the distinction between **PREDICTED**, **CALCULATED**, **OPTIMIZED**, **SIMULATED**, **RECOMMENDED**, and **SYNTHETIC VALIDATION**.

---

## Deployment

A Render Blueprint (`render.yaml`) deploys the Python backend; the SvelteKit
app in `frontend/` deploys separately to Vercel. Bring them up **in this
order** — each step depends on the last:

1. **Backend first, on Render.** Deploy `render.yaml` as-is (`CIRCULAR_CORS_ORIGINS`
   ships empty, so the backend still only serves `web/dist` same-origin at
   this point). Note the resulting URL, e.g.
   `https://circular-material-studio.onrender.com`.
2. **Frontend second, on Vercel, pointed at that URL.** Import `frontend/` as
   a Vercel project (root directory `frontend/`; it already targets
   `@sveltejs/adapter-vercel` and builds to fully static output — no
   serverless functions are required for this app). Set the project's
   `VITE_API_BASE` environment variable to the Render URL from step 1, then
   deploy. Note the resulting Vercel URL.
3. **CORS back on the backend, last.** Set `CIRCULAR_CORS_ORIGINS` on the
   Render service to the Vercel URL from step 2 (comma-separate a preview URL
   too, if used) and redeploy the backend. Until this step, the deployed
   frontend's API calls will fail the browser's CORS check even though the
   backend itself is reachable.

Local Windows execution remains the required acceptance target. Public deployment is intentionally a separate operational step and is not represented as completed simply because configuration files exist.

---

## Scope boundary

V1 is a portfolio-grade engineering decision platform, not a production multi-tenant SaaS. It does not claim authentication, enterprise IAM, externally calibrated lifecycle factors, real-world causal benefit, or independently verified user-supplied data.

Those limitations are explicit rather than hidden.

See `docs/LIMITATIONS.md`.


## Signature algorithm

See [`docs/SIGNATURE_ALGORITHM.md`](docs/SIGNATURE_ALGORITHM.md) for the governed CIRCULAR-MASS formulation and validation contract.
