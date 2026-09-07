# Phases 8–10 Technical Methods

## Phase 8 — Advanced Integrated Operations Research

### AI-to-OR uncertainty contract
The locked Phase-2 predictors are converted into a planning state containing expected demand, end-of-life returns, manufacturing scrap supply, second-life withholding, and remanufacturing eligibility. These values parameterize seeded raw future scenarios rather than appearing only as UI outputs.

### Two-stage stochastic closed-loop network MILP
First-stage decisions are shared across all futures:
- binary recovery-facility activation;
- integer capacity-expansion units.

Scenario-dependent recourse includes:
- virgin material procurement;
- recycle/remanufacturing feed allocation;
- recovered inventory;
- disposal;
- shortage/emergency service slack.

Material balance for scenario `s`, period `t`:

`Virgin[s,t] + Σ_f Yield[s,f] Feed[s,t,f] + InternalScrap[s,t] + OpeningInventory[s,t] + Shortage[s,t] = Demand[s,t] + ClosingInventory[s,t]`

Return balance:

`Σ_f Feed[s,t,f] + Disposal[s,t] = Returns[s,t] × CollectionRate[s] × (1 - SecondLifeShare[s])`

Remanufacturing feed is bounded by the AI-derived remanufacturable share.

Facility capacity is scenario dependent:

`Feed[s,t,f] <= Availability[s,f] × (BaseCapacity[f] Open[f] + ExpansionUnit[f] Expansion[f])`

### CVaR tail-risk term
For operating cost `C_s`, VaR auxiliary `η`, and excess variable `ξ_s`:

`ξ_s >= C_s - η`

`CVaR_α = η + (1/(1-α)) Σ_s p_s ξ_s`

The objective can penalize expected operating cost and CVaR simultaneously.

### N−1 recovery resilience
When enabled, installed recovery capacity remaining after the loss of any single facility must exceed a specified strategic reserve threshold. This converts facility redundancy into an explicit mathematical requirement rather than a descriptive resilience score.

### Circular Strategy Frontier
Candidate policies vary carbon shadow price, virgin-material penalty, risk aversion, and N−1 reserve requirements. Dominated policies are removed using cost, lifecycle carbon, virgin-material dependency, and tail-risk comparisons.

### Literal vehicle routing
The collection layer implements a capacitated vehicle routing problem (CVRP), not inter-facility flow allocation mislabeled as routing.

Variables are directed route binaries `x[i,j]` with cumulative-load MTZ variables. Constraints enforce:
- exactly one customer arrival/departure;
- depot flow conservation;
- maximum fleet size;
- vehicle-capacity feasibility;
- subtour elimination.

The reference solver is SciPy/HiGHS MILP; a deterministic two-customer oracle validates distance and objective arithmetic.

### Critical-material resilience optimizer
Lithium, nickel, cobalt, and graphite are modeled individually across multiple periods. Decisions include supplier-specific virgin sourcing, recovered-material substitution, and strategic inventory.

The model constrains:
- material balance by material and period;
- supplier capacities;
- recovered-supply availability;
- minimum recovered-material share;
- maximum single-supplier share.

The output includes supplier HHI concentration by critical material, allowing circularity and supply resilience to be examined together.

### Licensed Gurobi multi-objective path
The Windows acceptance path additionally solves a hierarchical Gurobi model with objectives prioritized as:
1. service protection;
2. cost;
3. lifecycle carbon;
4. virgin-material dependence.

The portable SciPy models remain the reproducible CI/reference implementation; Gurobi provides the licensed high-performance verification path.

---

## Phase 9 — Circular Digital Experiments and Uncertainty

### Raw future generation
Seeded scenarios jointly vary:
- demand level/growth;
- return volume;
- collection rate;
- recycling/remanufacturing yield;
- virgin-material price;
- transportation cost;
- carbon multiplier;
- internal scrap recovery;
- second-life share;
- remanufacturing eligibility;
- recovery-facility outage state.

Temporal common factors create correlated multi-period futures instead of independent white-noise perturbations.

### Scenario reduction
Raw scenarios are standardized and clustered using K-means. A medoid representative is retained per cluster and assigned cluster probability. This reduces stochastic-MILP size while preserving heterogeneous risk states.

### Policy replay
Fixed first-stage policies are replayed against the unreduced raw scenario set using recourse optimization. The experiment engine measures:
- expected total cost;
- P90 cost;
- CVaR95 cost;
- lifecycle carbon;
- virgin-material demand;
- shortage/service level;
- emergency external-recovery use and probability.

All compared policies use the exact same scenario ensemble.

### Strategic sensitivity laboratory
Six policy experiments perturb carbon price, virgin dependence, risk aversion, N−1 reserve, and disposal restrictions. The report records decision changes and deltas against the base strategy.

---

## Phase 10 — AI Decision Intelligence and Explainability

### Demand uncertainty
A split holdout absolute-residual band supplies a conformal-style uncertainty interval and empirical holdout coverage.

### Return-model calibration
The discrete-time return hazard model is audited with probability bins and expected calibration error (ECE).

### Recovery-pathway explainability
Permutation importance under macro-F1 scoring ranks recovery-classifier features. Confidence and normalized predictive entropy are reported.

### Scrap-model uncertainty
Tree-ensemble prediction dispersion supplies a P10–P90 uncertainty-width diagnostic; feature importance remains available from the fitted forest.

### Decision engine
The decision engine scores non-dominated strategies using normalized cost, carbon, virgin dependency, and tail-risk dimensions. Service feasibility is a gate, and N−1 capacity receives only a small explicit resilience credit.

Every recommendation includes:
- action list;
- confidence;
- modeled impact versus the cost-focused policy;
- trade-offs;
- assumptions;
- human-approval requirement;
- evidence class.

### End-to-end provenance trace
The release emits an ordered machine-readable chain:

`DemandForecaster → ReturnHazardModel → ScrapPredictor → RecoveryPathwayClassifier → ScenarioBridge → TwoStageStochasticMILP → CriticalMaterialPlanner → CVRP → StrategicSensitivity → PolicyReplay → DecisionEngine`

A stable SHA-256 hash is generated from the decision trace and selected policy. Run records are written to `artifacts/run_registry/`.
