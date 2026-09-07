# V1.2.1 — Circular Operations Decision Studio

V1.2.1 completes the product/depth release built on the Windows-accepted
V1.0.1 baseline and the V1.2 integration workbench.

## Added OR depth

The stochastic recovery model now exposes classical information-value metrics
for comparable operational uncertainty:

- **RP** — risk-neutral stochastic-program expected cost;
- **EEV** — expected cost of the deterministic expected-value first-stage
  policy when replayed across the scenario distribution;
- **WS** — wait-and-see expected cost with perfect scenario information;
- **VSS = EEV - RP** — expected cost avoided by explicitly optimizing against
  uncertainty;
- **EVPI = RP - WS** — upper bound on the expected economic value of perfect
  advance information.

For the classical comparison, discrete facility outages are held at the
planned/available state so all three formulations share comparable recourse.
Outage economics remain represented separately by N-1 resilience and emergency
recovery policy replay.

## Product UX

- STRATEGY now explains and quantifies the value of stochastic optimization.
- RUNS rows are clickable and open a persisted run report with scenario,
  recommended policy, actions, runtime, decision hash, code fingerprint and
  runtime provenance.
- V1.2 risk distributions, trace inspector, coupled planning, coupled critical
  materials and AI-derived routing remain intact.

The accepted 49-file Phase-10 computational core remains unchanged.
