# Pilot data and realized-benefit evidence

## Data admission

Use `data/templates/pilot_bundle/` as the submission contract. A pilot bundle
must pass schema, numeric-quality, complete-lineage, and non-synthetic-label
checks before it is eligible for controlled optimization. The `evidence_class`
must identify the operational source; the reference bundle remains synthetic
validation only.

## Benefit measurement

Populate `data/templates/pilot_measurements.csv` with one row per period and
metric, then run:

```powershell
& .venv\Scripts\python.exe scripts\benefit_measurement.py `
  .\data\pilot\PLANT_ID\benefit_measurements.csv `
  --baseline-id BASELINE_ID `
  --out artifacts\benefit_measurement.json `
  --strict
```

Supported metrics are service level, cost, recovery rate, emissions, virgin
material, and circularity rate. The tool checks units, aggregation method,
finite values, rate bounds, and source references, then calculates deltas and
directional improvement. It does not claim causality or realized value without
an approved baseline, source-owner sign-off, and an independent business
review.

## Pilot decision controls

- Keep a human approver for every operational decision.
- Record the bundle hash, baseline ID, run ID, code fingerprint, and approval.
- Define success thresholds before the pilot starts.
- Report both positive and negative outcomes, including service degradation,
  cost increases, and material-quality failures.
- Do not promote synthetic results into realized-benefit evidence.
