# Security and Operational Boundary

V1 is a portfolio/offline decision-support system, not an authenticated multi-tenant SaaS.

Implemented safeguards include:
- no committed secrets;
- `.env` ignored and `.env.example` provided;
- request-body size cap;
- request-target size cap and bounded query-parameter parsing;
- sanitized request IDs before they are returned as response headers;
- JSON object validation;
- unknown-field rejection on V1 decision-run contracts;
- static path traversal protection;
- structured error responses that do not expose internal tracebacks;
- request IDs;
- CSP, `nosniff`, frame-deny, referrer and permissions-policy headers;
- SQLite foreign keys;
- audit events and code fingerprinting.
- governed ingestion reports with source/file fingerprints and explicit lineage
  completeness status;
- PostgreSQL adapter selection is explicit and local SQLite remains the only
  default offline backend.

Deployment boundary controls now include:
- loopback-only default when authentication is disabled;
- fail-closed non-loopback and production startup;
- constant-time comparison of a SHA-256 bearer-token digest held in the
  environment/secret manager;
- explicit viewer/operator/admin route authorization;
- a production preflight report at `artifacts/production_preflight.json`.

The Windows release also ships a pinned `requirements-windows-py314.lock` file;
the acceptance and product bootstrap paths install from that lock before
installing the repository editable package.

The bearer mode is a restricted-pilot bootstrap control, not a replacement for
enterprise identity. OIDC/SAML, MFA, centralized authorization, TLS
termination, secret-manager integration, and security accreditation remain
deployment responsibilities and are not claimed in the local V1.
