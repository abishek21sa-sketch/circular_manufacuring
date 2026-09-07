-- CIRCULAR_PRODUCT_V1 PostgreSQL schema migration 001.
-- Apply through approved deployment change control with ON_ERROR_STOP=1.
BEGIN;

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenarios (
    scenario_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    config_json TEXT NOT NULL,
    config_hash_sha256 TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    scenario_id TEXT,
    created_at_utc TEXT NOT NULL,
    completed_at_utc TEXT,
    status TEXT NOT NULL,
    runtime_seconds DOUBLE PRECISION,
    decision_hash_sha256 TEXT,
    code_fingerprint_sha256 TEXT,
    report_json TEXT,
    error_json TEXT,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    event_id BIGSERIAL PRIMARY KEY,
    created_at_utc TEXT NOT NULL,
    event_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    details_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at_utc DESC);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at_utc DESC);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    applied_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO metadata(key, value)
VALUES ('schema_version', '1')
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

INSERT INTO schema_migrations(version, filename)
VALUES (1, '001_initial_schema.sql')
ON CONFLICT (version) DO NOTHING;

COMMIT;
