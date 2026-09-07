"""Run non-secret operational checks against a configured PostgreSQL database."""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from circular_battery.platform.postgres_storage import PostgresRunStore


ROOT = Path(__file__).resolve().parents[1]


def _ping(dsn: str, timeout: int) -> bool:
    import psycopg

    with psycopg.connect(dsn, connect_timeout=timeout) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone()[0] == 1


def run_operational_check(
    dsn: str | None = None,
    *,
    workers: int = 4,
    timeout: int = 10,
    write_test: bool = False,
) -> dict[str, Any]:
    """Return an operational report without ever serializing the database URL."""

    dsn = (dsn or os.getenv("CIRCULAR_DATABASE_URL", "")).strip()
    workers = max(1, min(int(workers), 16))
    timeout = max(1, min(int(timeout), 60))
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED",
        "checks": {},
        "claim_boundary": (
            "This check validates connectivity and application-level database behavior only. "
            "It does not certify provider durability, backup restoration, failover, access "
            "reviews, or production authorization."
        ),
    }
    if not dsn:
        report["checks"] = {
            "database_url_configured": {"status": "PENDING", "detail": "CIRCULAR_DATABASE_URL is not configured"},
            "schema_health": {"status": "PENDING", "detail": "requires a managed PostgreSQL connection"},
            "concurrent_connections": {"status": "PENDING", "detail": "requires a managed PostgreSQL connection"},
            "write_path": {"status": "PENDING", "detail": "requires a managed PostgreSQL connection and --write-test"},
        }
        return report

    try:
        import psycopg  # noqa: F401
    except ImportError:
        report["checks"] = {
            "database_url_configured": {"status": "PASS", "detail": "database URL is configured"},
            "schema_health": {"status": "PENDING", "detail": "psycopg is not installed; install the project postgres extra"},
            "concurrent_connections": {"status": "PENDING", "detail": "psycopg is not installed"},
            "write_path": {"status": "PENDING", "detail": "psycopg is not installed"},
        }
        return report

    try:
        # A readiness probe must not silently create a production schema. The
        # migration must already have been applied through change control.
        store = PostgresRunStore(dsn, connect_timeout=timeout, bootstrap=False)
        health = store.health()
        schema_ok = (
            health.get("backend") == "postgres"
            and health.get("database") == "ok"
            and health.get("migration_status") == "PASS"
        )
        concurrent_results: list[bool]
        with ThreadPoolExecutor(max_workers=workers) as pool:
            concurrent_results = list(pool.map(lambda _: _ping(dsn, timeout), range(workers)))
        concurrency_ok = len(concurrent_results) == workers and all(concurrent_results)
        checks: dict[str, dict[str, Any]] = {
            "database_url_configured": {"status": "PASS", "detail": "database URL is configured"},
            "schema_health": {
                "status": "PASS" if schema_ok else "FAIL",
                "detail": "PostgreSQL schema and recorded migration are healthy" if schema_ok else "database connectivity succeeded but the expected applied migration was not recorded",
                "schema_version": health.get("schema_version"),
                "migration_status": health.get("migration_status"),
                "migration_version": health.get("migration_version"),
                "migration_filename": health.get("migration_filename"),
            },
            "concurrent_connections": {
                "status": "PASS" if concurrency_ok else "FAIL",
                "detail": f"{sum(concurrent_results)}/{workers} independent connections completed SELECT 1",
                "workers": workers,
            },
            "write_path": {
                "status": "SKIPPED" if not write_test else "PENDING",
                "detail": "pass --write-test to exercise scenario/run persistence without using a real decision payload",
            },
        }
        if write_test:
            scenario = store.create_scenario({"name": "operational-check", "notes": "controlled readiness probe"})
            run_id = store.start_run(scenario["scenario_id"], "operational-check")
            store.complete_run(run_id, {"decision_hash_sha256": "operational-check"}, 0.0)
            persisted = store.get_run(run_id, include_report=False)
            checks["write_path"] = {
                "status": "PASS" if persisted.get("status") == "COMPLETED" else "FAIL",
                "detail": "scenario and completed run round-trip succeeded",
            }
        report["checks"] = checks
        report["status"] = "PASS" if all(item["status"] in {"PASS", "SKIPPED"} for item in checks.values()) else "BLOCKED"
    except Exception as exc:  # deliberately generic to avoid leaking DSN/provider details
        report["checks"] = {
            "database_url_configured": {"status": "PASS", "detail": "database URL is configured"},
            "schema_health": {"status": "BLOCKED", "detail": f"database operational check failed: {type(exc).__name__}"},
            "concurrent_connections": {"status": "BLOCKED", "detail": "not executed after database check failure"},
            "write_path": {"status": "BLOCKED", "detail": "not executed after database check failure"},
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--write-test", action="store_true", help="write a controlled scenario/run probe")
    parser.add_argument("--out", type=Path, default=Path("artifacts/postgres_operational_check.json"))
    parser.add_argument("--strict", action="store_true", help="return non-zero unless all requested checks pass")
    args = parser.parse_args()
    report = run_operational_check(workers=args.workers, timeout=args.timeout, write_test=args.write_test)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"POSTGRES_OPERATIONAL_CHECK status={report['status']}")
    return 0 if report["status"] == "PASS" or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
