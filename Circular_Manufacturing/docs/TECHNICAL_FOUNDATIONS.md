# Technical foundations

This document explains the mathematical, industrial-engineering, optimization, machine-learning, and platform foundations of the Circular Manufacturing Studio. It is written as an engineering handoff: a reviewer should be able to understand what the system computes, what evidence supports each result, and what must be added before a controlled operational pilot.

## 1. Scope and claim boundary

The product is a decision-support system for circular manufacturing planning. It combines:

- material-flow accounting and bill-of-materials logic;
- reverse-network and facility-capacity planning;
- vehicle-routing feasibility;
- multi-scenario mixed-integer optimization;
- critical-material sourcing and lifecycle indicators;
- demand, return, scrap, and pathway models;
- provenance, evidence, policy replay, and human approval gates.

The current validation package is an engineering prototype. It uses a large deterministic synthetic enterprise dataset shaped by public environmental reporting patterns, plus a public EPA reference extract for schema and distribution checks. Synthetic observations are not measurements of a named company or facility. The local validation machine uses an Academic Gurobi license; commercial deployment requires the appropriate solver authorization and an operational license-management design.

The system can demonstrate reproducible computation, constraint handling, auditability, and interface behavior. It cannot currently claim field accuracy, realized savings, regulatory compliance, or production authorization without governed real data and a controlled pilot.

## 2. End-to-end computation

The main decision path is:

~~~
AI and statistical signals
        |
        v
scenario bridge and uncertainty calibration
        |
        v
material balance + LCA + critical-material ledger
        |
        v
reverse network + industrial engineering capacity plan
        |
        v
two-stage stochastic MILP with tail-risk control
        |
        v
route feasibility and CVRP checks
        |
        v
policy replay, evidence bundle, and human approval gate
~~~

Every material recommendation should be traceable to: input dataset and version, feature configuration, model version, scenario seed, solver backend and parameters, constraint report, objective components, and reviewer decision.

## 3. Mathematical model

### 3.1 Sets and parameters

The core planning model uses the following notation:

- f ∈ F: facilities, collection points, processors, and demand sites;
- m ∈ M: materials or material grades;
- t ∈ T: planning periods;
- s ∈ S: uncertainty scenarios;
- a ∈ A: directed transport arcs;
- p_s: probability of scenario s, with Σ_s p_s = 1;
- demand_{m,t,s}: material demand;
- yield_{f,m,t,s}: recoverable output per unit of activity;
- cap_{f,t}: processing or collection capacity;
- cost terms for opening, processing, transport, virgin supply, disposal, shortage, and emissions;
- policy bounds for service, recycled content, safety stock, emissions, and risk.

The implementation keeps quantities nonnegative and uses explicit binary variables for decisions that are genuinely discrete. This prevents a fractional solution from being interpreted as a physically executable plan.

### 3.2 Material balance and conservation

Let x_{f,t} be recovered activity at facility f in period t and q_{m,t,s} be recovered material output:

~~~
q_{m,t,s} = Σ_f yield_{f,m,t,s} × x_{f,t}
~~~

For each material, period, and scenario, the balance is:

~~~
q_{m,t,s} + virgin_{m,t,s} + inventory_in_{m,t,s}
    = demand_{m,t,s} + inventory_out_{m,t,s}
      + shortage_{m,t,s} + surplus_{m,t,s}
~~~

This balance is the primary conservation invariant. A validation failure occurs if the residual exceeds the configured numerical tolerance.

Typical structural constraints include:

~~~
0 ≤ x_{f,t} ≤ cap_{f,t} × open_f
Σ_m process_{f,m,t,s} ≤ cap_{f,t} × open_f
inventory_{m,t,s} ≤ storage_cap_{m,t}
shortage_{m,t,s} ≤ service_limit_{m,t,s}
~~~

The model separates physical flow from accounting flow. For example, recycled content is tracked by material grade and cannot be credited merely because a facility is open.

### 3.3 Two-stage stochastic mixed-integer optimization

The first-stage variables select structural actions that must be chosen before uncertainty is observed: facility activation, network design, contracted capacity, and baseline recovery commitments. The second-stage variables adapt material allocation, virgin purchases, inventory, disposal, and shortage to each scenario.

The canonical form is:

~~~
minimize  cᵀy + dᵀx + Σ_s p_s Q(x, y, ξ_s)
subject to
    A y + B x ≤ b
    y ∈ {0, 1}^k
    x ≥ 0
~~~

Here y represents binary structure, x represents first-stage continuous activity, ξ_s contains scenario data, and Q is the recourse problem for scenario s. The implementation records the objective components separately so an operator can distinguish operating cost, virgin-material cost, shortage penalty, disposal cost, emissions cost, and risk penalty.

### 3.4 Tail-risk and service protection

Expected cost alone can select an apparently cheap plan that performs poorly in an adverse scenario. The risk module uses a CVaR-style tail term. Let loss_s be the scenario loss, η be a VaR threshold, and z_s be excess loss:

~~~
z_s ≥ loss_s - η
z_s ≥ 0
CVaR_α(loss) = η + (1 / (1 - α)) × Σ_s p_s z_s
~~~

The planning objective can then be written:

~~~
total objective = expected cost + λ × CVaR_α(loss)
~~~

The coefficient λ is a transparent policy parameter. The UI exposes the risk posture and shows how the frontier changes as the decision maker increases λ or changes α.

### 3.5 Network and routing feasibility

Reverse logistics is represented as a directed network. For route-level feasibility, the CVRP uses binary edge variables e_{i,j,k} for vehicle k traveling from node i to node j, load variables load_{i,k}, demand_i, vehicle capacity Q, and route cost c_{i,j}.

The basic objective is:

~~~
minimize Σ_k Σ_i Σ_j c_{i,j} × e_{i,j,k}
~~~

Representative constraints are:

~~~
Σ_k Σ_j e_{i,j,k} = 1       for each required customer i
Σ_j e_{depot,j,k} = 1       for each used vehicle k
Σ_i demand_i × visit_{i,k} ≤ Q
load_{j,k} ≥ load_{i,k} + demand_j - Q × (1 - e_{i,j,k})
~~~

The load propagation constraint removes subtours when paired with the depot and visit constraints. The implementation also checks route continuity, capacity, and complete customer coverage after optimization. A mathematically optimal route that fails those post-solve checks is rejected.

### 3.6 Critical-material and lifecycle accounting

The bill-of-materials ledger maps products to components, materials, grades, and recovery pathways. Critical-material exposure is calculated by material mass and an explicit criticality weight rather than by a single opaque score.

For a product p:

~~~
critical_mass_p = Σ_m mass_{p,m} × criticality_weight_m
recycled_share_p = recycled_mass_p / total_relevant_mass_p
~~~

Lifecycle indicators are additive over process steps:

~~~
impact_total = Σ_r quantity_r × emission_factor_r
water_total  = Σ_r quantity_r × water_factor_r
energy_total = Σ_r quantity_r × energy_factor_r
~~~

The factors are configuration data with source, version, unit, and uncertainty metadata. They are not treated as universal constants; a deployment must map them to the geography, process technology, and accounting standard in scope.

### 3.7 Multiobjective frontier and sensitivity

Cost, service, emissions, virgin-material dependence, and critical-material exposure can conflict. The frontier engine evaluates explicit policy weights and records the resulting efficient points. It also supports one-factor-at-a-time sensitivity and scenario comparisons.

For each run, the evidence bundle should include:

- objective vector and normalized values;
- binding constraints and slack;
- scenario-level losses;
- solver status, incumbent objective, bound, gap, and runtime;
- parameter set and random seed;
- a comparison against the baseline policy.

This makes a tradeoff inspectable instead of hiding it inside a composite score.

## 4. Machine-learning and AI foundations

### 4.1 Model roles

The AI layer is deliberately modular. Current model roles are:

1. Demand forecast: estimates future demand by product, material, site, and period.
2. End-of-life return model: estimates the probability and timing of recoverable returns.
3. Scrap-rate model: estimates process loss or recovery yield under operating conditions.
4. Recovery-pathway classifier: recommends a candidate pathway such as reuse, remanufacture, recycle, or controlled disposal.

Each model is used as a decision input, not as an autonomous execution authority.

### 4.2 Features and labels

Feature groups include product and material attributes, age and usage, seasonality, site or region, process conditions, historical quantities, lead-time proxies, and policy context. A feature dictionary records semantic meaning, unit, allowable range, missing-value behavior, and leakage risk.

Labels must be defined before training:

- demand: future quantity over a declared horizon;
- return: observed return event or quantity within a declared window;
- scrap: observed scrap quantity or rate after process completion;
- pathway: reviewed disposition label with an explicit “unknown” class.

The synthetic generator produces these fields from documented distributions and correlated latent drivers. It does not turn generated outcomes into evidence of real operational performance.

### 4.3 Evaluation and split design

Time-aware splits are preferred for forecasting and return prediction. Group-aware splits are required when multiple records belong to the same product family, site, supplier, or batch. A random row split is not sufficient when it can leak a repeated entity into both train and test.

The evaluation contract includes:

- MAE and RMSE for continuous forecasts;
- weighted absolute percentage error where denominators are valid;
- Brier score, calibration curve, and expected calibration error for probabilities;
- macro-F1, per-class recall, and confusion matrix for pathway classification;
- baseline comparisons against seasonal-naive, moving-average, and majority-class models;
- slice metrics by material family, period, site type, and missingness pattern.

The release gate is based on a declared holdout and a reproducible seed. A model that improves average accuracy while failing a critical slice does not automatically pass.

### 4.4 Calibration and uncertainty propagation

Probabilities are calibrated before they influence optimization. Forecast intervals or residual distributions are converted into scenarios using a declared method and seed. Correlation matters: demand, return volume, scrap rate, and transport availability should not be sampled as independent if the same latent event can affect them.

The scenario bridge maps model outputs into optimization parameters:

~~~
scenario demand  = forecast_mean + demand_residual_s
scenario return  = return_probability_s × available_population_s
scenario yield   = predicted_yield_s × process_activity
scenario route   = base_route_cost × disruption_multiplier_s
~~~

The bridge validates units, bounds, and monotonicity. For example, a probability is clipped only with a logged reason, and a recovery yield cannot exceed the physically available input.

### 4.5 Explainability and guardrails

The product records feature importance or permutation sensitivity for each released model, plus representative explanations for a recommendation. Explanations are descriptive, not causal. Human reviewers can reject a model signal, override a pathway, or force a conservative scenario.

Required guardrails include:

- schema and range validation before inference;
- missingness and out-of-distribution checks;
- model/version hash in the run record;
- no hidden internet calls during scoring;
- a fallback baseline when a model is unavailable;
- a human approval gate for material, safety, compliance, or disposal decisions.

### 4.6 AI-assisted analyst experience

The AI surface summarizes evidence, highlights sensitivities, and explains why a plan changed. It must cite the run, source, scenario, and policy objects that support each statement. It should never invent a supplier, facility capability, regulatory interpretation, or realized benefit.

## 5. Data, provenance, and reproducibility

The source registry distinguishes public reference data, generated synthetic data, user-provided data, and derived artifacts. Every dataset has a source URI or generation recipe, retrieval/build date, schema version, license or usage note, row count, checksum, and quality checks.

The reproducibility contract requires:

- deterministic seeds for synthetic data, scenario generation, and benchmark sampling;
- canonical schemas and units;
- immutable run identifiers;
- configuration captured beside outputs;
- checksums for source and derived files;
- no credentials, private data, or local machine paths in committed artifacts.

The public-reference validation is a schema and distribution anchor. It is not silently treated as a factory production dataset.

## 6. Runtime and evidence architecture

The full local studio exposes views for materials, network, plan, strategy, routes, AI, risk, CIRCULAR-MASS, traceability, runs, and evidence. The lightweight runtime remains available for a focused decision-gate demonstration.

The API and persistence layers provide:

- health and readiness checks;
- data and scenario inspection;
- plan generation and route validation;
- run metadata and evidence retrieval;
- policy replay and audit records;
- bounded inputs and structured error responses.

For an enterprise deployment, PostgreSQL replaces the local SQLite runtime, object storage holds immutable evidence bundles, and an identity provider controls role-based access. The application should never expose solver credentials or raw database credentials to the browser.

## 7. Solver integration and verification

The optimization backend is selected by configuration. The Gurobi adapter is the preferred research and engineering backend when an authorized Academic license is available; the fallback backend supports portable tests and environments without Gurobi.

Solver verification is more than “the solver returned optimal.” The release checks:

- model construction succeeds for representative and edge-case inputs;
- status is interpreted correctly for optimal, feasible, infeasible, time-limited, and interrupted runs;
- integrality and feasibility tolerances are explicit;
- objective, bound, gap, and runtime are recorded;
- conservation and capacity invariants are independently recomputed;
- a small reference instance has a known answer;
- changing the solver backend does not silently change business semantics.

Numerical tolerances are part of the model contract. A plan is not accepted solely because a floating-point value is close to a bound; the post-solve validator applies domain tolerances and reports any violation.

## 8. Verification matrix

The current test strategy spans:

- unit tests for schemas, balances, classifiers, policy rules, and utilities;
- optimizer tests for feasibility, conservation, risk, and route constraints;
- data tests for row counts, ranges, missingness, and deterministic checksums;
- model tests for baselines, metrics, calibration, and feature contracts;
- API tests for status codes, validation errors, and audit behavior;
- frontend build and runtime smoke tests;
- security scans for secrets and unsafe committed paths;
- release packaging and manifest validation.

The next quality increment is a separate independent validation dataset and a small set of hand-checked optimization instances maintained outside the generator.

## 9. What this foundation supports today

Today the system supports a credible, reproducible engineering demonstration: a large synthetic enterprise-scale workload, public-reference schema anchoring, optimization with a Gurobi-backed path, route checks, model-evaluation scaffolding, evidence bundles, and a multi-view analyst workflow.

Promotion to an operational pilot requires real governed data, a measured baseline, calibrated models, security and identity controls, monitored service levels, disaster recovery, solver licensing, and a signed benefits-validation plan. Those are engineering requirements, not cosmetic polish.
