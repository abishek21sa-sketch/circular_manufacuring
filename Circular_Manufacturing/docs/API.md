# V1 API

All V1 responses use an envelope containing `ok`, API/schema versions, request ID and UTC timestamp.

## Deployment authentication

The loopback-only local Studio defaults to `CIRCULAR_AUTH_MODE=disabled`.
Non-loopback and production binds fail closed unless
`CIRCULAR_AUTH_MODE=bearer` and a 64-character
`CIRCULAR_API_TOKEN_SHA256` are configured through a secret manager. Send the
corresponding raw token as `Authorization: Bearer <token>`.

The configured token has one minimum role: `viewer` can read API evidence and
records, `operator` can create scenarios/runs and submit decisions, and `admin`
can read audit events and delete scenarios. This bootstrap is for a restricted
pilot; enterprise deployments should put OIDC/SAML, MFA, centralized RBAC,
TLS, and session policy at the approved identity-aware ingress.

Health liveness (`/api/v1/health`) remains unauthenticated for infrastructure
probes. Readiness and all other API routes are protected outside local mode.

Read:
- `GET /api/v1/health`
- `GET /api/v1/ready`
- `GET /api/v1/about`
- `GET /api/v1/reference`
- `GET /api/v1/phase10`
- `GET /api/v1/phase567`
- `GET /api/v1/bundles/reference/validate`
- `GET /api/v1/bundles/reference/governance`
- `GET /api/v1/public-reference/summary`
- `GET /api/v1/public-reference/facilities?state=IL&naics=327&limit=20`
- `GET /api/v1/scenarios`
- `GET /api/v1/scenarios/{scenario_id}`
- `GET /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/audit`

Write:
- `POST /api/v1/scenarios`
- `POST /api/v1/scenarios/import`
- `POST /api/v1/runs`
- `DELETE /api/v1/scenarios/{scenario_id}` when it has no persisted runs.

A decision-run configuration accepts `name`, `seed`, `raw_n`, `reduced_k`, `include_sensitivity`, and optional notes.

The governance endpoint returns the bundle ingestion ID, bundle/file SHA-256
fingerprints, row counts, required-column checks, finite-value checks, lineage
metadata, and evidence class. A production pilot must require complete lineage;
synthetic reference data remains synthetic even when its schema passes.

The public-reference endpoints expose bounded benchmark context from the
validated EPA GHGRP 2023 extract. They are read-only and provenance-labeled;
public facility records are not customer plant telemetry and do not provide
recovery, yield, cost, inventory, or realized-benefit measurements.

Legacy Phase endpoints remain available for the existing Studio integration.
