"""Validate deployment configuration before the workbench binds a socket."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from circular_battery.web.auth import DeploymentConfigurationError, is_loopback_host, load_auth_config


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "production_preflight.json"


def _check(status: str, detail: str) -> dict[str, str]:
    return {"status": status, "detail": detail}


def build_preflight(env: Mapping[str, str] | None = None, *, host: str | None = None, mode: str | None = None) -> dict[str, object]:
    values = dict(os.environ if env is None else env)
    if mode is not None:
        values["CIRCULAR_DEPLOYMENT_MODE"] = mode
    effective_mode = values.get("CIRCULAR_DEPLOYMENT_MODE", "local").strip().lower()
    effective_host = host or values.get("HOST", "127.0.0.1")
    checks: dict[str, dict[str, str]] = {}

    if effective_mode not in {"local", "staging", "production"}:
        checks["deployment_mode"] = _check("FAIL", "CIRCULAR_DEPLOYMENT_MODE is invalid")
    else:
        checks["deployment_mode"] = _check("PASS", f"deployment mode is {effective_mode}")

    try:
        config = load_auth_config(values, bind_host=effective_host)
        checks["bind_and_authentication"] = _check("PASS", f"{effective_host} is protected by {config.auth_mode} authentication in {config.deployment_mode} mode")
    except DeploymentConfigurationError:
        checks["bind_and_authentication"] = _check("FAIL", "bind/authentication configuration is unsafe or incomplete; no credential details are recorded")

    if effective_mode == "production":
        backend = values.get("CIRCULAR_PLATFORM_DB_BACKEND", "sqlite").strip().lower()
        database_url_present = bool(values.get("CIRCULAR_DATABASE_URL", "").strip())
        migration_ok = values.get("CIRCULAR_DATABASE_MIGRATION_STATUS", "").strip().lower() == "approved"
        backup_ok = values.get("CIRCULAR_DATABASE_BACKUP_STATUS", "").strip().lower() == "approved"
        concurrency_ok = values.get("CIRCULAR_DATABASE_CONCURRENCY_STATUS", "").strip().lower() == "approved"
        database_ok = backend == "postgres" and database_url_present and migration_ok and backup_ok and concurrency_ok
        checks["production_database"] = _check(
            "PASS" if database_ok else "PENDING",
            "PostgreSQL adapter is configured and migration, backup/restore, and concurrency evidence is attested"
            if database_ok else
            f"production requires a supported PostgreSQL backend plus approved migration, backup/restore, and concurrency evidence; current backend={backend or 'sqlite'}",
        )
        declarations = {
            "CIRCULAR_PRODUCTION_ATTESTATION": values.get("CIRCULAR_PRODUCTION_ATTESTATION", "").strip().lower(),
            "CIRCULAR_GUROBI_LICENSE_CLASS": values.get("CIRCULAR_GUROBI_LICENSE_CLASS", "").strip().lower(),
            "CIRCULAR_DATA_VALIDATION_STATUS": values.get("CIRCULAR_DATA_VALIDATION_STATUS", "").strip().lower(),
        }
        attestation_ok = (
            declarations["CIRCULAR_PRODUCTION_ATTESTATION"] == "approved"
            and declarations["CIRCULAR_GUROBI_LICENSE_CLASS"] == "commercial"
            and declarations["CIRCULAR_DATA_VALIDATION_STATUS"] == "approved"
        )
        checks["external_production_attestations"] = _check("PASS", "required external attestations are present; independent evidence remains mandatory") if attestation_ok else _check("PENDING", "commercial solver authorization, data validation, and production approval must be attested externally")
    else:
        checks["production_database"] = _check("PASS", "not applicable to loopback local/staging preflight")
        checks["external_production_attestations"] = _check("PASS", "not applicable to local/staging preflight")

    blocking = [name for name, result in checks.items() if result["status"] != "PASS"]
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": effective_mode,
        "host": effective_host,
        "loopback": is_loopback_host(effective_host),
        "passed": not blocking,
        "checks": checks,
        "blocking_checks": blocking,
        "claim_boundary": "Preflight validates configuration declarations and safe binding behavior only. It does not prove commercial licensing, identity-provider assurance, data quality, or realized operational benefits.",
    }


def run_preflight(*, host: str | None = None, mode: str | None = None, write: bool = True) -> dict[str, object]:
    report = build_preflight(host=host, mode=mode)
    if write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("local", "staging", "production"))
    parser.add_argument("--host")
    args = parser.parse_args()
    report = run_preflight(host=args.host, mode=args.mode)
    print(f"PRODUCTION_PREFLIGHT mode={report['mode']} host={report['host']} status={'PASS' if report['passed'] else 'BLOCKED'}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
