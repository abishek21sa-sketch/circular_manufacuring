# PostgreSQL migration control

The files in `migrations/postgres` are the change-controlled database schema
for hosted deployments. Apply them through the approved deployment pipeline,
review the provider output, and attach the resulting migration record to the
production evidence register.

The first migration can be applied with a managed PostgreSQL client from the
repository root, for example:

```powershell
psql $env:CIRCULAR_DATABASE_URL -v ON_ERROR_STOP=1 -f migrations/postgres/001_initial_schema.sql
```

The application’s PostgreSQL adapter performs an idempotent compatibility
bootstrap only in explicitly local mode. Staging and production require the
change-controlled migration to be applied before the process can report
readiness; the runtime gate also checks the recorded migration row. The
migration validator checks file naming, sequence continuity, required schema
objects, and the absence of destructive or credential-bearing content.

Migration application does not prove backup durability. A provider-approved
backup/restore exercise, concurrency test, and rollback record are still
required before commercial production approval.
