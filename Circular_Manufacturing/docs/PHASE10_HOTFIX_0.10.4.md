# Phase 10 Hotfix 0.10.4 — Dirty-folder migration safety

## Windows defect exposed by incremental upgrades
The 0.10.3 release itself contained no sklearn estimator joblib binaries.
However, users upgrading repeatedly into the same repository directory could
retain deprecated `artifacts/models/*_model.joblib` files from 0.10.0–0.10.2.
A release-gate test incorrectly treated the presence of those harmless stale
files as a runtime dependency and failed.

## Permanent fix
- Add an idempotent Phase-10 migration that removes only
  `artifacts/models/*_model.joblib`.
- Run that migration automatically before both full and hotfix Windows
  acceptance.
- Preserve JSON model evidence and unrelated artifacts.
- Replace the dirty-worktree-fragile test with migration correctness,
  idempotency and runtime-independence tests.
- Current-runtime deterministic model reconstruction remains the only Phase-10
  runtime AI path.

This fix is specifically designed for repeated upgrades into the same Windows
folder; a clean extraction is no longer required merely to remove legacy model
binaries.
