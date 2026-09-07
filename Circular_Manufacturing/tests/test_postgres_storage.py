import sys
import types

import pytest

from circular_battery.platform.postgres_storage import PostgresRunStore


class _Cursor:
    def __init__(self, row=None):
        self.row = row

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self):
        self.statements = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = 0

    def execute(self, statement, params=()):
        self.statements.append((statement, tuple(params)))
        if "SELECT value FROM metadata" in statement:
            return _Cursor({"value": "1"})
        if "SELECT version, filename FROM schema_migrations" in statement:
            return _Cursor({"version": 1, "filename": "001_initial_schema.sql"})
        return _Cursor()

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed += 1


def test_postgres_store_uses_optional_psycopg_and_never_reports_dsn(monkeypatch):
    connection = _Connection()
    psycopg = types.ModuleType("psycopg")
    psycopg.connect = lambda *args, **kwargs: connection
    rows = types.ModuleType("psycopg.rows")
    rows.dict_row = object()
    psycopg.rows = rows
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", rows)

    store = PostgresRunStore("postgresql://user:secret@example.invalid/circular")

    health = store.health()
    assert health == {
        "database": "ok",
        "backend": "postgres",
        "schema_version": 1,
        "migration_status": "PASS",
        "migration_version": 1,
        "migration_filename": "001_initial_schema.sql",
    }
    assert "secret" not in repr(store)
    assert connection.commits >= 2
    assert connection.closed >= 2
    assert all("?" not in statement for statement, _ in connection.statements)
    assert any("%s" in statement for statement, _ in connection.statements)


def test_postgres_store_missing_driver_is_actionable(monkeypatch):
    monkeypatch.setitem(sys.modules, "psycopg", None)
    with pytest.raises(RuntimeError, match="psycopg is not installed"):
        PostgresRunStore("postgresql://example.invalid/circular")


def test_default_store_selects_postgres_only_when_explicit(monkeypatch):
    import circular_battery.platform.service as service_module

    class FakeStore:
        def __init__(self, dsn):
            self.dsn = dsn

    monkeypatch.setattr(service_module, "PostgresRunStore", FakeStore)
    monkeypatch.setenv("CIRCULAR_PLATFORM_DB_BACKEND", "postgres")
    monkeypatch.setenv("CIRCULAR_DATABASE_URL", "postgresql://example.invalid/circular")
    store = service_module.default_store()
    assert isinstance(store, FakeStore)
    assert store.dsn.endswith("/circular")

    monkeypatch.setenv("CIRCULAR_PLATFORM_DB_BACKEND", "unsupported")
    with pytest.raises(RuntimeError, match="must be sqlite or postgres"):
        service_module.default_store()


def test_production_postgres_store_does_not_bootstrap_schema(monkeypatch):
    connection = _Connection()
    psycopg = types.ModuleType("psycopg")
    psycopg.connect = lambda *args, **kwargs: connection
    rows = types.ModuleType("psycopg.rows")
    rows.dict_row = object()
    psycopg.rows = rows
    monkeypatch.setitem(sys.modules, "psycopg", psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", rows)
    monkeypatch.setenv("CIRCULAR_DEPLOYMENT_MODE", "production")

    PostgresRunStore("postgresql://user:secret@example.invalid/circular")

    assert connection.statements == []
