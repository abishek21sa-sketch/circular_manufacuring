# Phase 10 API Contracts

All endpoints are local/offline by default and return JSON except `/`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service/version readiness |
| GET | `/api/reference` | Locked reference artifacts and evidence boundary |
| GET | `/api/phase567` | Integrated lifecycle → reverse-logistics → IE planning report |
| GET | `/api/lifecycle` | Phase-5 lifecycle/material results |
| GET | `/api/reverse-logistics` | Phase-6 network solution |
| GET | `/api/production-plan` | Phase-7 production/inventory plan |
| GET | `/api/phase10` | Advanced AI/OR/simulation/decision report |
| POST | `/api/optimize` | Deterministic scenario re-solve |
| POST | `/api/frontier` | Deterministic strategy frontier |
| POST | `/api/stress` | Seeded stress-test request |

`/api/phase10` includes model evidence, uncertainty/explainability, AI-to-OR bridge, stochastic design, advanced frontier, critical-material plan, CVRP solution, sensitivity experiments, policy replay, final recommendation, and provenance trace.
