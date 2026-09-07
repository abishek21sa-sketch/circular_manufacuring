# Phase 8–10 Architecture

```text
Phase-2 AI models + held-out evidence
                 |
                 v
      AI uncertainty/explainability
                 |
                 v
       AI → planning state bridge
                 |
                 v
      raw correlated future generator
                 |
          scenario reduction
                 |
        +--------+--------+
        |                 |
        v                 v
Two-stage stochastic   Critical-material
closed-loop MILP       sourcing/resilience LP
(CVaR + N-1)           (Li/Ni/Co/graphite)
        |                 |
        +--------+--------+
                 |
                 v
         strategy frontier
                 |
        first-stage policies
                 |
       +---------+----------+
       |                    |
       v                    v
 exact collection CVRP   unreduced policy replay
                            + sensitivity lab
       |                    |
       +---------+----------+
                 |
                 v
      explainable decision engine
                 |
                 v
       decision trace + run hash
                 |
                 v
       Material Circularity Studio
```

## Architectural boundary
The system remains a lifecycle/material/network platform. It does not reconstruct machine/WIP state and does not use a factory-event digital-twin architecture.

## Solver architecture
- SciPy/HiGHS: portable LP/MILP reference and CI validation.
- Gurobi: licensed Windows hierarchical multi-objective verification.
- K-means: scenario reduction only; it does not replace stochastic optimization.

## Evidence architecture
`PREDICTED`, `CALCULATED`, `OPTIMIZED`, `SIMULATED`, `RECOMMENDED`, and `SYNTHETIC VALIDATION` remain distinct evidence classes throughout the report.
