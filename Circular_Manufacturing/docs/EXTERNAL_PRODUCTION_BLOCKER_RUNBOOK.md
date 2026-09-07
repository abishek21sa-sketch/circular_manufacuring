# External Production Blocker Runbook

Status: engineering gate passed; commercial/production gate remains blocked until the four external attestations are independently evidenced.

This runbook separates work the repository can verify from approvals, credentials, infrastructure, and plant measurements that must come from the responsible owner. It is intentionally compatible with the fail-closed validator in `scripts/validate_production_attestations.py`.

## Current state

The Windows final gate verifies the computational core, frontend build, dependency set, security scan, governed reference bundle, database migration asset, public reference dataset, live API smoke test, and licensed Gurobi engineering checks. It does not certify a commercial deployment.

The production register is expected to remain `BLOCKED` while any item below is pending. Do not change an attestation to `APPROVED` without an evidence file, SHA-256, named approver, and approval timestamp.

## 1. Commercial Gurobi entitlement

Owner: product owner and Gurobi account owner.

The installed Academic license is sufficient for research, coursework, and local engineering verification. Gurobi states that academic access is for non-commercial use and that commercial use is forbidden. A free commercial evaluation can be requested, but an evaluation is for evaluation/test purposes; it is not a production authorization.

Closure evidence must be a redacted, reviewable record that identifies:

- the commercial entitlement or contract type;
- the production deployment scope and authorized users/services;
- the applicable expiration/renewal terms; and
- the approver who authorizes this application to use the entitlement.

Do not place `gurobi.lic`, WLS API keys, passwords, or tokens in the repository or evidence bundle.

Official references:

- https://www.gurobi.com/academics
- https://www.gurobi.com/utility/free-trial/eval-license
- https://www.gurobi.com/EULA

## 2. Enterprise identity and transport

Owner: customer IT/security team.

Closure evidence must come from the actual deployment environment and cover:

- SSO/OIDC or SAML integration and MFA policy;
- viewer/operator/admin role mapping and least-privilege review;
- TLS certificate and protocol/cipher configuration;
- secret-manager references and rotation procedure;
- audit-log destination, retention, access review, and time synchronization; and
- network ingress/egress controls and incident escalation ownership.

The local bearer-token boundary and loopback checks in this repository are engineering controls, not proof that a customer enterprise identity system is deployed. Use the current NIST identity and TLS guidance when producing the customer verification record.

Official references:

- https://pages.nist.gov/800-63-4/sp800-63.html
- https://csrc.nist.gov/Pubs/sp/800/52/r2/Final

## 3. Managed PostgreSQL operations

Owner: DBA/SRE or managed-database provider.

Closure evidence must identify the live managed PostgreSQL service and include:

- the approved migration version and applied timestamp;
- backup schedule, retention, encryption, and monitoring;
- a witnessed restore or point-in-time-recovery test;
- measured RPO/RTO results and the approved targets;
- connection-pool/concurrency and failover test results; and
- the owner and runbook used for recovery.

The repository migration validator and local compatibility checks cannot substitute for a live managed-service backup/restore test. PostgreSQL documents SQL dumps, file-system backups, and continuous archiving/PITR as distinct recovery approaches; the selected production approach must be tested in the target environment.

Official references:

- https://www.postgresql.org/docs/current/backup.html
- https://www.postgresql.org/docs/current/continuous-archiving.html

## 4. Field calibration, lineage, and realized benefits

Owner: pilot customer, plant engineering, data owner, and finance/operations approver.

Closure evidence must use governed, permissioned plant data and show:

- source-system ownership, timestamps, units, and transformation lineage;
- calibration/validation results against measured plant outcomes;
- a frozen backtest window and an untouched validation window;
- baseline definitions for service, cost, recovery, emissions, and virgin-material use;
- measured results with uncertainty/tolerance and sign-off; and
- the approved data-use and retention boundary.

The EPA GHGRP extract in `data/public/` is a public reference benchmark. It is not customer plant telemetry and cannot be used to claim realized savings or field calibration. EPA describes its data as facility-level reported emissions from large sources, which makes it useful for external context and benchmarking only.

Official references:

- https://www.epa.gov/ghgreporting/data-sets
- https://www.epa.gov/ghgreporting/ghgrp-reported-data

## Evidence intake and re-run

After each owner supplies a redacted evidence file, place it at a safe repository-relative path outside generated reports, compute its SHA-256, and update only the matching register entry. Then run:

```powershell
$projectRoot = Join-Path $env:USERPROFILE 'OneDrive\Desktop\CIRCULAR_PRODUCT_V1\Circular_Manufacturing'
Set-Location $projectRoot
$py = '.\.venv\Scripts\python.exe'
& $py scripts\validate_production_attestations.py --strict --out artifacts\production_attestation_validation.json
& $py scripts\release_readiness.py
```

The strict validator must report `PRODUCTION_ATTESTATIONS status=PASS passed=4/4`. The release-readiness report and the Windows final gate must then be rerun. A green engineering gate by itself must not be used as a commercial production claim.

## What can and cannot be completed from this workstation

Can be completed here: code hardening, fail-closed gates, repeatable local/Gurobi engineering tests, public reference-data ingestion, evidence-schema validation, and integration of redacted evidence supplied by authorized owners.

Cannot be legitimately completed here without external authorization or facts: purchasing/activating a commercial Gurobi entitlement, approving a customer IAM/TLS deployment, proving a managed service's backup/restore controls, or inventing plant calibration and realized-benefit results.
