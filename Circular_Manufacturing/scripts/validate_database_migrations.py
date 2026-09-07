"""Validate the checked-in PostgreSQL migration inventory without connecting."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "migrations" / "postgres"
MIGRATION_NAME = re.compile(r"^(?P<version>[0-9]{3})_[a-z0-9_]+\.sql$")
REQUIRED_MARKERS = (
    "CREATE TABLE IF NOT EXISTS METADATA",
    "CREATE TABLE IF NOT EXISTS SCENARIOS",
    "CREATE TABLE IF NOT EXISTS RUNS",
    "CREATE TABLE IF NOT EXISTS AUDIT_EVENTS",
    "CREATE TABLE IF NOT EXISTS SCHEMA_MIGRATIONS",
    "CREATE INDEX IF NOT EXISTS IDX_RUNS_CREATED",
    "CREATE INDEX IF NOT EXISTS IDX_AUDIT_CREATED",
)
FORBIDDEN_MARKERS = (
    "DROP DATABASE",
    "DROP SCHEMA",
    "TRUNCATE ",
    "POSTGRESQL://",
    "POSTGRES://",
)


def validate_migrations(root: Path = ROOT, directory: Path | str | None = None) -> dict[str, Any]:
    """Return a deterministic file-level migration validation report."""

    migration_dir = Path(directory) if directory is not None else Path("migrations/postgres")
    if not migration_dir.is_absolute():
        migration_dir = root / migration_dir
    errors: list[str] = []
    migrations: list[dict[str, Any]] = []
    files = sorted(migration_dir.glob("*.sql")) if migration_dir.is_dir() else []
    if not migration_dir.is_dir():
        errors.append("migration directory is missing")
    versions: list[int] = []
    for path in files:
        match = MIGRATION_NAME.fullmatch(path.name)
        if match is None:
            errors.append(f"invalid migration filename: {path.name}")
            continue
        version = int(match.group("version"))
        versions.append(version)
        try:
            sql = path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"unreadable migration {path.name}: {type(exc).__name__}")
            continue
        normalized = re.sub(r"\s+", " ", sql.upper())
        missing_markers = [marker for marker in REQUIRED_MARKERS if marker not in normalized]
        forbidden_markers = [marker for marker in FORBIDDEN_MARKERS if marker in normalized]
        if missing_markers:
            errors.append(f"{path.name} is missing required schema markers: {', '.join(missing_markers)}")
        if forbidden_markers:
            errors.append(f"{path.name} contains forbidden markers: {', '.join(forbidden_markers)}")
        migrations.append(
            {
                "version": version,
                "filename": path.name,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "required_markers_present": not missing_markers,
                "forbidden_markers_absent": not forbidden_markers,
            }
        )
    if versions != list(range(1, len(versions) + 1)):
        errors.append("migration versions must be unique and contiguous starting at 001")
    passed = bool(files) and not errors
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "BLOCKED",
        "migration_directory": str(migration_dir.relative_to(root).as_posix()) if migration_dir.is_relative_to(root) else str(migration_dir),
        "migration_count": len(migrations),
        "migrations": migrations,
        "errors": errors,
        "claim_boundary": (
            "This report validates the checked-in migration inventory and file content only. "
            "It does not apply migrations, prove provider availability, certify backup/restore, "
            "or authorize a production deployment."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("migrations/postgres"))
    parser.add_argument("--out", type=Path, default=Path("artifacts/database_migration_validation.json"))
    args = parser.parse_args()
    report = validate_migrations(ROOT, args.directory)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DATABASE_MIGRATIONS status={report['status']} count={report['migration_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
