# Production evidence intake

The commercial gate is intentionally closed until independent evidence exists.
This runbook explains what the four evidence owners must supply; it is not
itself production evidence and must never be referenced as an approval record.

## Evidence packet rules

For each blocker, place a redacted, reviewable record in a controlled evidence
location under the repository, then update the matching entry in
`artifacts/production_attestations.json` with:

- `status`: `APPROVED` only after the control owner signs off;
- `evidence_ref`: a repository-relative path to the record;
- `evidence_sha256`: SHA-256 of the exact record;
- `approved_by`: a non-empty accountable approver identity; and
- `approved_at_utc`: a timezone-aware ISO-8601 approval timestamp.

Never commit solver license files, API keys, database URLs, customer data, or
unredacted security material. Repository templates and generated readiness
reports are explicitly ineligible as approved evidence.

## Required packet contents

### `commercial_gurobi_entitlement`

Provide a redacted commercial entitlement/contract reference, the licensed
deployment scope, expiration/renewal owner, and explicit authorization for the
production hosts. The local Academic license run is engineering evidence only.

### `enterprise_identity_and_transport`

Provide the approved architecture and verification record for identity/RBAC,
MFA, TLS termination, secret management and rotation, network policy, audit
retention, and access review. Include the deployment/environment identifier and
verification date without including credentials.

### `field_calibration_and_data_lineage`

Provide the governed plant-data source and facility identifiers, data owner,
as-of window, lineage/hash record, recovery/yield/cost calibration method,
backtest results, data-quality exceptions, and operations approval. The
reference bundle and synthetic data do not qualify.

### `realized_benefit_validation`

Provide the approved baseline ID, governed measurement sources, pilot window,
positive and negative outcomes, service/cost/recovery/emissions/circularity
results, causal-attribution limitations, finance/business-owner review, and
the hash of the measurement report produced by
`scripts/benefit_measurement.py`. Projections are not realized benefits.

## Validation

Run the validator after updating the register:

```powershell
& .venv\Scripts\python.exe scripts\validate_production_attestations.py `
  --out artifacts\production_attestation_validation.json `
  --strict
```

Only a `PASS 4/4` result closes this evidence gate. Database migration,
backup/restore, and concurrency evidence remain separate controls and must also
be attested before a production preflight can pass.
