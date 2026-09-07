# Phase 10 Hotfix 0.10.1

## Why this hotfix exists
Windows acceptance of 0.10.0 exposed two release-quality issues:

1. The licensed hierarchical Gurobi model queried the ordinary `MIPGap` model attribute. Gurobi multi-objective models do not expose that model-level attribute; each optimization pass has its own documented `ObjPassNMipGap` and related `ObjPassN*` metrics.
2. The PowerShell acceptance wrapper did not fail immediately when a native Python process returned a non-zero exit code, so the script could continue after a failed licensed check.
3. Loading persisted scikit-learn models through joblib 1.5.x on NumPy 2.5 emitted a large volume of one known upstream `DeprecationWarning`.

## Changes
- Query and retain Gurobi per-objective-pass status, MIP gap, runtime, objective value and bound.
- Treat any non-optimal pass or pass gap above tolerance as licensed acceptance failure.
- Use a checked PowerShell wrapper for every Python command.
- Add a short affected-path hotfix acceptance script.
- Suppress only the known joblib/NumPy 2.5 shape-assignment deprecation at the model-deserialization boundary; all other warnings remain visible.
- Add regression tests for all three defects.

The computational formulation and policy logic are unchanged.
