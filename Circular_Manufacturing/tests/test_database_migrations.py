from pathlib import Path

from scripts.validate_database_migrations import validate_migrations


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_postgres_migrations_are_contiguous_and_safe():
    report = validate_migrations(ROOT)

    assert report["status"] == "PASS"
    assert report["migration_count"] == 1
    assert report["migrations"][0]["version"] == 1


def test_migration_validator_rejects_gaps_and_destructive_sql(tmp_path):
    directory = tmp_path / "postgres"
    directory.mkdir()
    (directory / "002_bad.sql").write_text("DROP DATABASE circular;", encoding="utf-8")

    report = validate_migrations(ROOT, directory)

    assert report["status"] == "BLOCKED"
    assert any("forbidden markers" in error for error in report["errors"])
    assert any("contiguous" in error for error in report["errors"])
