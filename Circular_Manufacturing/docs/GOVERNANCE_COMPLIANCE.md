# Governance Compliance Traceability — Circular Manufacturing

This file records the updated CIRCULAR-MASS engineering-release evidence against the supplied Portfolio Engineering Governance Pack and Signature Algorithms & Mathematical Foundations standard.

## Mandatory engineering-release controls

- **Project-specific signature algorithm:** `CIRCULAR-MASS` in the documented project-native decision/math package.
- **Fresh signature-module line coverage:** **99%** (required threshold: >=90%).
- **Regression evidence:** 130/130 tests.
- **Research/evidence gate:** 10/10 formulation; 7/7 product integration; 20-case sensitivity; shortage-CVaR stress and fine-tail ablation.
- **Explicit objective, variables, constraints, operational decision and claim boundary:** documented in [`docs/CIRCULAR_MASS.md`](CIRCULAR_MASS.md).
- **Baseline/counterfactual, ablation and sensitivity evidence:** present in machine-readable artifacts under `artifacts/`.
- **Evidence classes:** observational/ingested, predicted, simulated, optimized and realized evidence are not conflated.
- **AI/agent role:** explanatory, predictive or analytical support only; the mathematical optimizer/control model remains the decision engine.
- **Human/evidence gate:** optimization recommendations are governed and do not autonomously execute external operational actions.
- **API/service exposure:** signature decision is exposed through the project service boundary.
- **Dedicated operator UI:** signature inputs, constraints/trade-offs, evidence status and baseline/counterfactual context are visible in the project UI.
- **Windows acceptance commands:** `..\RUN_ACCEPTANCE.cmd` and `..\RUN_PRODUCT_ACCEPTANCE.cmd`. The Python 3.14 RC3, product-runtime, CIRCULAR-MASS Gurobi, Phase 3 Gurobi, and Phase 10 Gurobi gates passed on this Windows environment. The signature solver reports `solver=gurobi`, `OPTIMAL`, zero MIP gap, zero feasibility residual, exact objective parity with SciPy on the reference case, and active shortage-CVaR stress evidence. The local runtime reports an Academic Gurobi license; commercial production licensing/terms remain a separate release gate.
- **Runtime hardening evidence:** request-target limits, bounded query parsing, sanitized request IDs, generic unexpected-error responses, finite optimizer-input validation, and a pinned Windows/Python-3.14 dependency lock are covered by regression tests and the final gate.
- **README traceability:** README links the canonical `docs/SIGNATURE_ALGORITHM.md`.
- **Clean packaging:** RC3 packaging excludes `.env`, `.git`, virtual environments, caches/bytecode and stale nested archives.

## Explicit null hypotheses

- H0-C1: CIRCULAR-MASS does not reduce virgin-material dependence versus a virgin-only policy while satisfying the same modeled demand/service constraints.
- H0-C2: Stochastic recovery-yield modeling does not materially change shortage/tail-risk decisions versus deterministic average-yield planning.

These are falsification targets, not claims that current evidence establishes causal or field superiority.

## Research-upgrade path

The engineering-release gate is intentionally separate from publication-grade research. Literature-positioning, stronger theoretical guarantees, broad public-benchmark studies, solver-scaling/warm-start studies, and field/causal validation remain **research-upgrade work unless explicitly evidenced in this repository**. The release does not backfill or imply those claims.
