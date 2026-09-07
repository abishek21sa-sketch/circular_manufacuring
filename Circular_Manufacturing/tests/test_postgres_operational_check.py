from scripts.postgres_operational_check import run_operational_check


def test_postgres_operational_check_is_truthfully_pending_without_database_url(monkeypatch):
    monkeypatch.delenv("CIRCULAR_DATABASE_URL", raising=False)

    report = run_operational_check()

    assert report["status"] == "BLOCKED"
    assert report["checks"]["schema_health"]["status"] == "PENDING"

def test_postgres_operational_check_requires_recorded_migration(monkeypatch):
    import sys
    import scripts.postgres_operational_check as check_module

    class FakeStore:
        def __init__(self, dsn, **kwargs):
            assert kwargs["bootstrap"] is False

        def health(self):
            return {
                "database": "ok",
                "backend": "postgres",
                "schema_version": 1,
                "migration_status": "BLOCKED",
                "migration_version": None,
            }

    monkeypatch.setenv("CIRCULAR_DATABASE_URL", "postgresql://example.invalid/db")
    monkeypatch.setattr(check_module, "PostgresRunStore", FakeStore)
    monkeypatch.setitem(sys.modules, "psycopg", object())
    monkeypatch.setattr(check_module, "_ping", lambda dsn, timeout: True)

    report = check_module.run_operational_check(workers=2)

    assert report["status"] == "BLOCKED"
    assert report["checks"]["schema_health"]["status"] == "FAIL"
