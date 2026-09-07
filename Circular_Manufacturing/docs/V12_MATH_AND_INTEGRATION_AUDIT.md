# V1.2 Math & Integration Audit

## Verdict

The accepted V1.0.1 backend already contains genuine IE/OR/AI computation. The main weakness was not absence of mathematics; it was that several strong modules were presented as parallel demonstrations rather than one visibly coupled decision workflow.

V1.2 keeps the accepted Phase-10 computational files unchanged and adds an integration layer around them.

## What was already strong

- deterministic closed-loop material MILP with binary recovery-facility decisions;
- reverse-logistics facility/flow MILP;
- multi-period circular production/inventory LP;
- two-stage stochastic recovery MILP with CVaR recourse;
- N-1 capacity resilience;
- lithium/nickel/cobalt/graphite sourcing optimization;
- exact CVRP with MTZ capacity/subtour constraints and a small exact oracle;
- licensed Gurobi hierarchical service -> cost -> carbon -> virgin optimization;
- scenario reduction and unreduced policy replay;
- independent balance/constraint audits and held-out AI baselines.

## Gaps found in V1.0.1

1. The Phase-7 IE production plan was displayed but did not receive the chosen Phase-10 stochastic recovery output.
2. The critical-material optimizer used a standalone synthetic demand/recovery configuration.
3. The CVRP used a standalone route-demand demo rather than AI-derived return volume.
4. The strategy frontier was a nondominated subset of six explicit scalarization policies. It was valid, but it was visually easy to mistake for a continuous Pareto surface.

## V1.2 coupling

### Stochastic recovery -> IE planning
Expected period recovery output from the chosen stochastic policy plus recovered internal manufacturing scrap becomes `recovered_supply_kg` in the production/inventory LP. AI-derived demand mass is converted back to pack demand.

### IE planning -> critical materials
Lithium, nickel, cobalt and graphite demand is computed from coupled pack demand times BOM kg/pack. Recovered supply is allocated from the coupled plan by BOM share. The synthetic supplier landscape is then scaled to the coupled demand level before solving.

### AI return state -> CVRP
Period-1 AI-derived return mass is filtered by collection and second-life allocation. That mass is split across the six representative pickup regions and solved as an exact CVRP. V1.2 explicitly labels this a representative collection batch, not a full multi-period fleet schedule.

## Model inventory

The Studio now exposes variable/constraint counts, solver class and verification route for seven mathematical programs. This is intended to make the computational depth auditable from the UI rather than only from source code.

## Boundaries intentionally retained

- Routing is not yet a full multi-period multi-depot split-delivery location-routing problem.
- Supplier disruption is represented through risk penalties and concentration limits rather than endogenous stochastic supplier failure.
- The policy set is six explicit scalarization designs, not a continuous epsilon-constraint frontier.
- Lifecycle factors remain synthetic/external-calibration-pending.

Those are model-scope boundaries, not hidden implementation claims.
