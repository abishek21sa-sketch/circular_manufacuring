# Phase 10 Hotfix 0.10.5

Fixes Windows path-separator variance in migration evidence by returning repository-relative POSIX-style paths with `Path.as_posix()`.

Adds a short final Windows gate that reruns only migration, licensed Gurobi validation, Phase-10 diagnostics, and the release-gate tests.
