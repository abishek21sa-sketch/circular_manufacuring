"""PostgreSQL-backed run registry for hosted deployments.

The local ``RunStore`` remains SQLite-backed for offline engineering work.  This
module provides the same service contract for a managed PostgreSQL database.
Connections are short-lived and created per transaction so the store is safe to
use from the threaded HTTP server without sharing a connection across threads.
The optional psycopg dependency is imported only when this backend is selected.
"""

from __future__ import annotations

from contextlib import contextmanager
import os
import threading
from typing import Iterator

from circular_battery.platform.storage import RunStore, SCHEMA_VERSION


class _PostgresConnectionProxy:
    """Adapt the qmark SQL used by the shared store methods to psycopg."""

    def __init__(self, connection):
        self._connection = connection

    def execute(self, statement: str, params=()):
        return self._connection.execute(statement.replace("?", "%s"), params)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()


class PostgresRunStore(RunStore):
    """Run registry using PostgreSQL and the same public contract as ``RunStore``.

    ``dsn`` is retained only in memory and is never returned by ``health`` or
    included in exception details.  Install the optional ``postgres`` extra
    before selecting ``CIRCULAR_PLATFORM_DB_BACKEND=postgres``.
    """

    backend = "postgres"

    def __init__(
        self,
        dsn: str,
        *,
        connect_timeout: int = 10,
        bootstrap: bool | None = None,
    ):
        dsn = str(dsn or "").strip()
        if not dsn:
            raise ValueError("A PostgreSQL connection URL is required.")
        if len(dsn) > 4096:
            raise ValueError("The PostgreSQL connection URL is too long.")
        self._dsn = dsn
        self.connect_timeout = max(1, min(int(connect_timeout), 60))
        self._lock = threading.RLock()
        if bootstrap is None:
            # Compatibility bootstrap is useful for local smoke tests, but a
            # production process must consume the change-controlled migration
            # rather than silently creating or altering its schema.
            deployment_mode = os.getenv("CIRCULAR_DEPLOYMENT_MODE", "local").strip().lower()
            bootstrap = deployment_mode == "local"
        self.bootstrap = bool(bootstrap)
        if self.bootstrap:
            self.initialize()

    def _connect(self):
        try:
            import psycopg
            from psycopg.rows import dict_row
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL backend selected but psycopg is not installed; "
                "install the project postgres extra."
            ) from exc
        connection = psycopg.connect(
            self._dsn,
            row_factory=dict_row,
            connect_timeout=self.connect_timeout,
        )
        return _PostgresConnectionProxy(connection)

    @contextmanager
    def _connection(self) -> Iterator[_PostgresConnectionProxy]:
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self):
        with self._lock, self._connection() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    config_hash_sha256 TEXT NOT NULL,
                    notes TEXT NOT NULL DEFAULT ''
                )
                """
            )
            con.execute(
                """
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
                    FOREIGN KEY(scenario_id) REFERENCES scenarios(scenario_id)
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id BIGSERIAL PRIMARY KEY,
                    created_at_utc TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    details_json TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at_utc DESC)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at_utc DESC)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    applied_at_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            con.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",
                ("schema_version", str(SCHEMA_VERSION)),
            )

    def health(self):
        with self._connection() as con:
            metadata_row = con.execute(
                "SELECT value FROM metadata WHERE key=?",
                ("schema_version",),
            ).fetchone()
            migration_row = con.execute(
                "SELECT version, filename FROM schema_migrations "
                "ORDER BY version DESC LIMIT 1",
            ).fetchone()
        migration_version = migration_row["version"] if migration_row else None
        migration_filename = migration_row["filename"] if migration_row else None
        return {
            "database": "ok" if metadata_row else "degraded",
            "backend": self.backend,
            "schema_version": int(metadata_row["value"]) if metadata_row else None,
            "migration_status": "PASS" if migration_version == SCHEMA_VERSION else "BLOCKED",
            "migration_version": migration_version,
            "migration_filename": migration_filename,
        }
