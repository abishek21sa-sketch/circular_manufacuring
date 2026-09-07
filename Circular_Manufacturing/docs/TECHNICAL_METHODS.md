# Technical Methods — Circular Manufacturing Intelligence Platform V1.0

## System question

V1 answers a connected decision problem:

> Under uncertain battery demand, manufacturing scrap, end-of-life returns, recovery quality, processing yields, transport economics, carbon factors and facility availability, what combination of virgin sourcing, circular recovery, facility/capacity decisions, inventories, routing and operating policy should be used?

The reference benchmark is synthetic. External-data ingestion is implemented, but source truth and field calibration remain external validation responsibilities.

## 1. Physical circular manufacturing state

The product is represented by a material bill of materials. For material \(m\), period \(t\):

`ManufacturingInput[m,t] = EmbeddedProduct[m,t] / (1 - ScrapRate)`

`ManufacturingScrap[m,t] = ManufacturingInput[m,t] - EmbeddedProduct[m,t]`

End-of-life returned mass is conserved across:

`Uncollected + SecondLife + RemanRetained + RecycledOutput + RecyclingLoss + DirectDisposal`

Remanufacturing loss is explicitly routed into recycling feed. Material conservation is independently audited numerically.

Implemented circular indicators include collection efficiency, technical recovery, circular-pathway rate, manufacturing scrap rate, critical-material recovery, recycled content, material productivity and virgin-material dependency.

## 2. Lifecycle and sustainability accounting

Each material carries explicit virgin/secondary cost and kgCO2e factors plus recycling yield. V1 computes material-level virgin-equivalent versus circular-material comparative impacts.

These are modeled comparative impacts, not realized savings. Lifecycle factors in the shipped benchmark are synthetic and externally uncalibrated.

## 3. Predictive AI

Four deterministic, current-runtime models are trained from seeded synthetic benchmark generators.

### Demand
Ridge regression with exogenous drivers; chronological final-18-month holdout; seasonal-naive baseline. A residual conformal-style band provides empirical holdout interval coverage.

### End-of-life returns
Scaled logistic discrete-time hazard model; entire future cohorts held out; constant training event-rate baseline. Calibration bins and expected calibration error are reported.

### Recovery pathway
HistGradientBoostingClassifier; final synthetic return records held out; majority/empirical-frequency baseline. Permutation macro-F1 importance supports explanation.

### Manufacturing scrap
RandomForestRegressor; chronological final-24-month holdout; training-mean baseline. Ensemble dispersion and feature importance provide uncertainty/explanation signals.

Release execution does not rely on version-fragile serialized sklearn estimator binaries. Models are deterministically reconstructed in the installed runtime.

## 4. AI-to-OR contract

Predictions are transformed into:
- multi-period demand mass;
- expected return mass;
- internal scrap availability;
- second-life withholding;
- remanufacturing eligibility;
- stochastic scenario distributions.

The bridge retains an explicit evidence label: `PREDICTED SYNTHETIC STATE -> STOCHASTIC OR INPUT CONTRACT`.

## 5. Reverse logistics

Collected end-of-life material is allocated from collection regions to remanufacturing/recycling facilities or disposal.

Variables:
- continuous `x[c,f]` routed kg;
- continuous disposal `d[c]`;
- binary facility activation `y[f]`.

Constraints enforce node mass balance, reman eligibility, facility capacity, disposal policy and domains.

Transport economics and emissions are computed in kg-km.

## 6. IE production and circular inventory planning

Per period V1 optimizes:
- regular production;
- overtime production;
- virgin material;
- recovered material use;
- recovered-material inventory;
- finished-goods inventory;
- emergency shortage slack.

Core equations:

`Virgin + RecoveredUse = PackMass × Production`

`OpeningRecoveredInventory + RecoveredSupply = RecoveredUse + ClosingRecoveredInventory`

`OpeningFG + Production + Shortage = Demand + ClosingFG`

Capacity, safety stock and circular-content bounds are enforced.

## 7. Two-stage stochastic closed-loop optimization

First-stage strategic decisions include facility activation and capacity expansion. Second-stage recourse adapts virgin material, recovery feed, inventory, disposal and shortage to each representative uncertain future.

Expected operating cost is augmented by CVaR tail-risk:

`CVaR(alpha) = eta + (1/(1-alpha)) * sum_s p_s * xi_s`

An N-1 capacity-resilience requirement can force adequate remaining recovery capacity after loss of any single site.

## 8. Multi-objective licensed verification

The Gurobi path uses hierarchical objectives:
1. service;
2. economic cost;
3. lifecycle carbon;
4. virgin-material dependency.

V1 records each Gurobi objective pass independently using the documented multi-objective pass attributes. Windows acceptance checks pass status, pass MIP gap, primal constraint violation and integrality violation.

## 9. Critical-material resilience

Lithium, nickel, cobalt and graphite are planned separately across virgin suppliers and recovered supply. The formulation includes supplier capacities, cost, carbon, risk weighting, recovered content and concentration.

Supplier concentration is reported via HHI.

## 10. Capacitated vehicle routing

Collection routing is a literal CVRP:
- directed binary arcs;
- depot departure/return;
- exact customer visitation;
- vehicle-capacity load variables;
- MTZ capacity/subtour elimination;
- vehicle fixed cost;
- distance cost and route emissions.

Independent oracle cases verify small-instance arithmetic.

## 11. Scenario generation and digital experiments

Uncertainty dimensions include demand, returns, collection, recovery yield, material price, transportation, carbon, internal scrap, facility availability and pathway shares.

Raw correlated scenarios are reduced into representative medoids for optimization. Policies are then replayed on the unreduced scenario population for out-of-optimization performance evidence.

Reported policy metrics include expected cost, P90 cost, CVaR95 cost, expected carbon, expected virgin material, service and emergency recovery probability.

## 12. Explainable decision intelligence

The decision engine scores feasible nondominated strategies and produces:
- selected policy;
- concrete capacity/facility actions;
- model-derived confidence;
- impact versus cost-focused policy;
- trade-offs;
- assumptions;
- human-approval requirement.

An eleven-stage trace links prediction through uncertainty, stochastic optimization, critical-material planning, CVRP, sensitivity analysis and policy replay to the final recommendation.

## 13. Enterprise persistence and provenance

SQLite stores:
- decision scenarios;
- decision runs;
- full reports;
- stable decision hashes;
- code fingerprints;
- execution status;
- runtime;
- audit events.

Operational events are additionally written as JSON Lines. Run records capture Python/dependency versions and a deterministic source fingerprint.

## 14. External scenario-bundle ingestion

A V1 scenario bundle contains:

`manifest.json`
`materials.csv`
`periods.csv`
`collections.csv`
`facilities.csv`
`planning.csv`

The ingestion layer validates structure, numeric domains and physical model requirements before running the material lifecycle -> reverse-logistics -> IE-planning chain.

The software validates schema and model feasibility. It does not independently certify the truth or provenance of user-supplied source data.

## 15. Evidence language

V1 separates:
- **PREDICTED**
- **CALCULATED**
- **OPTIMIZED**
- **SIMULATED**
- **RECOMMENDED**
- **SYNTHETIC VALIDATION**
- **EXTERNAL VALIDATION PENDING**

No synthetic result is represented as observed factory or recycler performance.


## 16. Value of stochastic optimization

V1.2.1 adds a classical information-value analysis on a comparable-recourse
operational-uncertainty scenario set.

`RP` is the risk-neutral stochastic-program optimum.

`EV` is the deterministic problem formed from probability-weighted expected
uncertain parameters.

The EV first-stage decision is replayed across the scenario set to obtain
`EEV`.

`WS` is the probability-weighted wait-and-see cost obtained by solving each
scenario with perfect advance information.

The two standard metrics are:

`VSS = EEV - RP`

`EVPI = RP - WS`

Discrete facility outages are held at the planned/available state for this
specific classical comparison so that all formulations share comparable
recourse. Outage economics remain explicitly represented in the N-1 and
emergency-recovery policy replay layers.
