# Production-readiness register

The repository produces `artifacts/release_readiness.json` through:

```powershell
& .venv\Scripts\python.exe scripts\release_readiness.py
```

The report has two deliberately separate gates:

- `engineering_gate`: the reproducible local state—pinned Windows runtime,
  security and deployment controls present, clean release tree, V1 diagnostics,
  product evidence, and Gurobi verification.
- `commercial_production_gate`: the external controls required before a real
  enterprise deployment. It is driven by the controlled
  `artifacts/production_attestations.json` register and is expected to remain
  `BLOCKED` until each attestation has independently reviewable evidence.

Current engineering evidence is deterministic and synthetic. The optimizer is
eligible for qualified engineer review, but it does not issue autonomous
facility or sourcing actions. A passing engineering gate must not be described
as production certification.

Commercial-production exit criteria remain:

1. Record a commercial Gurobi entitlement and deployment authorization. The
   local validation environment currently reports an Academic license.
2. Deploy with approved enterprise identity/RBAC, TLS, secret management,
   network controls, and audit retention.
3. Replace the current SQLite-only `RunStore` with a supported PostgreSQL data
   plane. The repository now includes explicit backend selection, a checked-in
   migration, migration inventory validation, and an operational checker, but
   production still requires applying the migration plus backup/restore and
   concurrency testing with a real managed database.
4. Approve governed plant-data lineage, calibrate the recovery/yield/cost
   assumptions, complete backtesting, and require the governed bundle
   validation path before pilot optimization.
5. Measure realized service, cost, recovery, emissions, and circularity
   outcomes against an approved baseline.

The repository validates the evidence handoff without storing credentials:

```powershell
& .venv\Scripts\python.exe scripts\validate_production_attestations.py `
  --out artifacts\production_attestation_validation.json
```

Use `docs/PRODUCTION_EVIDENCE_INTAKE.md` for the required contents and owner
responsibilities for each of the four production attestations.

An attestation can become `APPROVED` only when its register entry references a
repository-relative evidence artifact, includes the artifact's SHA-256,
records an approver and ISO-8601 approval time, and the validator confirms the
hash. The register cannot independently prove that an external approver or
business result is truthful; that remains a human governance responsibility.
Use `--strict` when a deployment pipeline must fail while any attestation is
pending.

The checked-in migration inventory is validated by the acceptance gate:

```powershell
& .venv\Scripts\python.exe scripts\validate_database_migrations.py `
  --out artifacts\database_migration_validation.json
```

This is a source-control and SQL-safety check. It is intentionally separate
from provider evidence: only a managed-database migration record, successful
restore exercise, and concurrency result can close the production database
control.

The report stores SHA-256 fingerprints of the evidence and control files so a
reviewer can detect when the recorded state has changed. It intentionally never
records license credentials or other secrets.

The application now fails closed when the workbench is configured for a
non-loopback or production bind without bearer authentication. The token
digest is accepted from environment/secret-manager configuration only; no raw
token is committed or written to readiness artifacts. This is a restricted
pilot bridge while enterprise OIDC/SAML is placed at the approved ingress.

For a clean release archive, run the repository-owned packager from the inner
repository and provide an output path outside the source tree:

```powershell
& .venv\Scripts\python.exe scripts\package_release.py `
  --output "C:\release-output\CIRCULAR_PRODUCT_V1_GUROBI_READINESS_RC.zip"
```

The packager requires an engineering `PASS`, excludes virtual environments,
caches, bytecode, local environment files, coverage output, and nested ZIPs,
then reopens the archive and verifies required entries and forbidden-entry
absence.
