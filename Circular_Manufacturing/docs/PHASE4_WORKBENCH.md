# Phase 4 — Circular Strategy Workbench

## Product role
The workbench is the decision interface over the already-validated lifecycle, AI, OR, and stochastic engines. It is not a factory digital-twin timeline and does not model machine/WIP state.

## Decision workflow
1. Inspect the closed-loop material system.
2. Review the reference optimized strategy and solver evidence.
3. Explore non-dominated cost–carbon–virgin-material policies.
4. Review held-out AI evidence.
5. change collection, recovery yield, or carbon shadow-price assumptions.
6. Re-solve the closed-loop MILP.
7. Review seeded stochastic stress evidence.
8. Preserve the evidence boundary: synthetic/offline validation versus pending external validation.

## Technology decision
Phase 4 uses a Python standard-library HTTP service plus a TypeScript/SVG frontend. This avoids introducing a web framework dependency merely for portfolio uniformity and keeps clean-extraction acceptance small. The source-build toolchain is pinned in `web/package.json` and `web/package-lock.json`; acceptance compiles `web/src/app.ts` with the project-local TypeScript compiler. Windows users do not need Node to run the already-built workbench, but Node 24 is required to reproduce the frontend build from source.

## API surface
- `GET /api/health`
- `GET /api/reference`
- `POST /api/optimize`
- `POST /api/frontier`
- `POST /api/stress`

The API never invents sustainability results. Scenario outputs are computed by the locked Phase 3 optimization/simulation engines.
