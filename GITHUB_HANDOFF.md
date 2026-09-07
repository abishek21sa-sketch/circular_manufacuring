# GitHub handoff

This product folder is now structured as a repository root. The inner
`Circular_Manufacturing` directory remains the Python package and release
acceptance target.

## CI boundaries

- `portable-engineering` runs on a standard Windows runner and covers the
  persistence contract, governed ingestion, API, readiness, and platform tests.
- `licensed-gurobi` is intentionally restricted to a manually dispatched,
  self-hosted Windows runner with an authorized Gurobi license. GitHub Actions
  must not receive or print academic or commercial license credentials.

## Required repository setup

1. Create a private GitHub repository with the intended organization owner.
2. Add the remote as `origin`.
3. Protect the default branch and require the portable CI check.
4. Keep the licensed Gurobi check on an approved self-hosted runner only.
5. Configure branch review, secret scanning, dependency alerts, and CODEOWNERS
   after ownership is assigned.

The product includes a provenance-labeled, read-only EPA facility
benchmark API, migration-enforced hosted readiness, and request/role
traceability for persisted decision runs. It also includes the deterministic
120,000-row synthetic enterprise benchmark with EPA-derived context strata and an explicit Academic-Gurobi
research runner. Commercial licensing, enterprise identity, managed-database
evidence, and production data approval remain separate release gates.

RUN_APP.cmd is the primary local entrypoint for the full multi-view Material
Circularity Studio at http://127.0.0.1:8765/. The smaller
RUN_PRODUCT_RUNTIME.cmd surface remains available at http://127.0.0.1:8812/
for a focused CIRCULAR-MASS decision-gate demonstration. The local studio
launcher uses an ignored SQLite runtime file under
Circular_Manufacturing/artifacts/platform; hosted deployments override this
with the governed PostgreSQL configuration.

The public, research, Kaggle, commercial, and private/company source review is
documented in `Circular_Manufacturing\docs\DATA_SOURCE_REVIEW.md`. The
repository includes a validated EPA reference extract, but does not claim
access to restricted plant, recycler, OEM, paid market, or licensed company
datasets. The deterministic 120,000-row benchmark is therefore synthetic
validation until authorized real data is supplied.

The technical readiness rubric is documented in
`Circular_Manufacturing\docs\ENGINEERING_READINESS.md` and its machine-readable
result is generated at
`Circular_Manufacturing\artifacts\engineering_readiness.json`.
The detailed mathematical and AI/ML foundations are in
`Circular_Manufacturing\docs\TECHNICAL_FOUNDATIONS.md`; the cross-layer
promotion requirements are in
`Circular_Manufacturing\docs\NEXT_LEVEL_ROADMAP.md`.
