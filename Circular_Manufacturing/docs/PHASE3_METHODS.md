# Phase 3 — Closed-Loop Network Optimization & Stochastic Circular Strategy

## Decision model
The Phase-3 model is a multi-period mixed-integer closed-loop material planning problem. Binary variables activate recycling and remanufacturing capacity. Continuous variables represent virgin procurement, recycling feed, remanufacturing feed, recovered-material inventory, and disposal.

For each period `t`:

`Virgin[t] + recycle_yield*RecycleFeed[t] + reman_yield*RemanFeed[t] + Inventory[t-1] - Inventory[t] = Demand[t]`

`RecycleFeed[t] + RemanFeed[t] + Disposal[t] = collection_rate*Returns[t]`

Facility binaries gate recovery throughput.

The economic objective contains virgin procurement, recovery processing, disposal, inventory carrying, and fixed facility costs. A carbon shadow price creates alternative cost/carbon policies. Virgin-material use is retained as an explicit third decision metric.

## Verification
The optimizer is independently checked by:
1. post-solve material/capacity/inventory constraint auditing;
2. an independent enumeration of all facility binary configurations for a small/reference instance;
3. regression tests proving higher predicted returns cannot worsen virgin-material availability under otherwise identical assumptions;
4. non-dominance checks for the Circular Strategy Frontier.

## Stochastic experiments
Monte Carlo scenarios perturb demand, return volumes, and recycling yield. Each scenario re-solves the circular strategy model. Outputs include expected/P90 cost, expected lifecycle-carbon proxy, expected virgin-material dependence, and a high-virgin-dependency probability.

All bundled Phase-3 numerical evidence is synthetic validation evidence.
