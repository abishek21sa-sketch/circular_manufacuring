# Enterprise operations control plan

This document defines the production operating contract. The local V1
environment does not claim that these controls are deployed or accredited.

## Target service levels

- Availability target: 99.9% for the decision API during an approved pilot.
- API latency target: p95 under 5 seconds for standard decision requests.
- Recovery point objective: 15 minutes or better once managed PostgreSQL
  backups are configured.
- Recovery time objective: 1 hour or better once the deployment is exercised.
- Every decision run must retain a request ID, scenario hash, code fingerprint,
  solver evidence, actor role, and approval state. The current bearer pilot
  records role-level identity; enterprise OIDC/SAML must supply user identity.

## Required controls before production

| Area | Required evidence | Current local state |
|---|---|---|
| Identity | OIDC/SAML, MFA, role mapping, access review | Restricted bearer pilot boundary |
| Transport | TLS at approved ingress, secure headers, network policy | Application headers and fail-closed bind checks |
| Secrets | Managed secret store, rotation, no repository credentials | Environment/secret-manager contract |
| Data plane | Managed PostgreSQL, applied migration, backup/restore, concurrency | Adapter, checked-in migration, runtime migration gate, and operational checker; live evidence pending |
| Observability | Metrics, structured logs, alerts, trace/request correlation | JSONL events and request IDs; alerting deployment pending |
| Resilience | Tested restore, failover, capacity, and rollback | Runbook defined; environment exercise pending |
| Change control | Reviewed release, dependency lock, rollback artifact | Locked release and acceptance gates |
| Model governance | Versioned inputs, validation, drift review, human approval | Provenance and governed ingestion; field calibration pending |
| Incident response | Severity matrix, on-call owner, evidence retention | This document; operational owner assignment pending |

## Incident and change procedure

1. Assign a severity and incident owner; preserve request IDs and run IDs.
2. Freeze autonomous decision execution and use the last approved release.
3. Record impact, affected facilities, data window, and decision hashes.
4. Restore or roll back only through an approved change record.
5. Re-run health, security, regression, and solver gates before reopening.
6. Close with a root-cause review and corrective-action owner.

## Database exercise

The repository includes `migrations/postgres/001_initial_schema.sql` and
`scripts/validate_database_migrations.py`. Validate the migration inventory,
apply the SQL through the approved deployment change record, and then run
`scripts/postgres_operational_check.py` with a managed PostgreSQL URL and
`--write-test` to exercise schema health, independent connections, and a
scenario/run persistence round trip. Backup and restore must additionally be
performed through provider-approved tooling and attached as external evidence;
the application cannot infer that a backup is restorable.

## Claim boundary

These are target controls and operating instructions. They do not constitute
SOC 2, ISO 27001, legal, privacy, or customer security certification.
