# Decision Trace and Human Approval

A Phase-10 recommendation is not a language-model opinion. It is assembled from deterministic model and optimization outputs.

1. Demand model predicts material demand.
2. Return hazard predicts EOL return volume.
3. Scrap model predicts internal recovered feed.
4. Recovery classifier estimates second-life/reman/recycle/dispose pathway shares.
5. Scenario bridge converts predictions and uncertainty into stochastic futures.
6. Two-stage stochastic MILP selects shared recovery capacity under uncertainty.
7. Critical-material planner audits Li/Ni/Co/graphite sourcing and concentration.
8. CVRP constructs capacity-feasible collection tours.
9. Sensitivity lab tests structural assumption changes.
10. Policy replay evaluates candidate first-stage strategies across unreduced futures.
11. Decision engine ranks feasible non-dominated strategies and emits action, impact, assumptions, trade-offs, and confidence.

The final recommendation has `human_approval_required=true` by design.
