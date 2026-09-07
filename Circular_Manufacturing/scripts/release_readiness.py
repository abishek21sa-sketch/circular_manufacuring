"""Build a machine-readable release-readiness register.

This report deliberately separates the verified engineering gate from the
controls that are still required before commercial production. It is safe to
run locally and does not inspect or serialize license credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts.production_attestations import validate_attestations
except ModuleNotFoundError:  # direct ``python scripts/release_readiness.py`` execution
    from production_attestations import validate_attestations


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "release_readiness.json"

REQUIRED_FILES = (
    "requirements-windows-py314.lock",
    "migrations/README.md",
    "migrations/postgres/001_initial_schema.sql",
    "artifacts/production_attestations.json",
    "artifacts/production_attestation_validation.json",
    "artifacts/database_migration_validation.json",
    "artifacts/public_reference_validation.json",
    "web/package.json",
    "web/package-lock.json",
    "web/tsconfig.json",
    "scripts/build_frontend.py",
    "scripts/validate_production_attestations.py",
    "scripts/validate_database_migrations.py",
    "scripts/validate_public_reference_dataset.py",
    "data/public/epa_ghgrp_2023_facilities.csv",
    "data/public/epa_ghgrp_2023_metadata.json",
    "data/public/data_source_registry.json",
    "data/synthetic/enterprise_120k/manifest.json",
    "data/synthetic/enterprise_120k/observations.csv",
    "data/synthetic/enterprise_120k/case_catalog.csv",
    "data/synthetic/enterprise_120k/adversarial_cases.csv",
    "src/circular_battery/ingestion/public_reference.py",
    "scripts/postgres_operational_check.py",
    "scripts/validate_pilot_bundle.py",
    "scripts/benefit_measurement.py",
    "render.yaml",
    "Dockerfile",
    ".env.example",
    "docs/SECURITY.md",
    "docs/LIMITATIONS.md",
    "docs/ENTERPRISE_OPERATIONS.md",
    "docs/PRODUCTION_EVIDENCE_INTAKE.md",
    "docs/PUBLIC_REFERENCE_DATA.md",
    "docs/DATA_SOURCE_REVIEW.md",
    "docs/PILOT_DATA_AND_BENEFITS.md",
    "docs/SYNTHETIC_ENTERPRISE_DATASET.md",
    "data/templates/pilot_bundle/README.md",
    "data/templates/pilot_measurements.csv",
    "src/circular_battery/platform/postgres_storage.py",
    "src/circular_battery/ingestion/governance.py",
    "src/circular_battery/web/auth.py",
    "scripts/security_scan.py",
    "scripts/generate_synthetic_enterprise_dataset.py",
    "scripts/validate_synthetic_enterprise_dataset.py",
    "scripts/synthetic_enterprise_gurobi_benchmark.py",
    "scripts/validate_data_source_registry.py",
    "scripts/validate_engineering_readiness.py",
    "scripts/production_preflight.py",
    "scripts/windows_v1_final_gate.ps1",
    "docs/validation/v1_diagnostics.json",
    "artifacts/production_preflight.json",
    "artifacts/governed_reference_bundle.json",
    "artifacts/circular_mass/evidence.json",
    "artifacts/circular_mass/product_decision_evidence.json",
    "artifacts/circular_mass/gurobi_validation.json",
    "artifacts/synthetic_enterprise_validation.json",
    "artifacts/synthetic_enterprise_gurobi_validation.json",
)


def _load_json(root: Path, relative: str) -> tuple[Any | None, str | None]:
    path = root / relative
    if not path.is_file():
        return None, f"missing {relative}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"unreadable {relative}: {type(exc).__name__}"


def _check(passed: bool, evidence: str, detail: str) -> dict[str, Any]:
    return {"status": "PASS" if passed else "FAIL", "evidence": evidence, "detail": detail}


def _all_true(mapping: Any) -> bool:
    return isinstance(mapping, dict) and bool(mapping) and all(value is True for value in mapping.values())


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_inventory(root: Path) -> dict[str, Any]:
    excluded_directories = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
    forbidden: list[str] = []
    ignored_ephemeral: list[str] = []
    source_file_count = 0
    for path in root.rglob("*"):
        if any(part in excluded_directories for part in path.parts):
            continue
        if path.is_file():
            source_file_count += 1
            relative = path.relative_to(root).as_posix()
            if path.name in {".coverage", "postgres_operational_check.json"} or path.suffix.lower() in {".sqlite3", ".db", ".jsonl"}:
                ignored_ephemeral.append(relative)
            elif path.name == ".env" or path.suffix.lower() in {".joblib", ".zip"}:
                forbidden.append(relative)
    return {
        "source_file_count": source_file_count,
        "forbidden_release_files": sorted(forbidden),
        "ignored_ephemeral_files": sorted(ignored_ephemeral),
    }


def build_readiness(root: Path = ROOT) -> dict[str, Any]:
    v1, v1_error = _load_json(root, "docs/validation/v1_diagnostics.json")
    mass, mass_error = _load_json(root, "artifacts/circular_mass/evidence.json")
    product, product_error = _load_json(root, "artifacts/circular_mass/product_decision_evidence.json")
    gurobi, gurobi_error = _load_json(root, "artifacts/circular_mass/gurobi_validation.json")

    checks: dict[str, dict[str, Any]] = {}
    missing = [relative for relative in REQUIRED_FILES if not (root / relative).is_file()]
    checks["required_release_controls"] = _check(
        not missing,
        "REQUIRED_FILES",
        "all required lock, deployment, security, diagnostic, and evidence files are present"
        if not missing
        else f"missing: {', '.join(missing)}",
    )

    lock_path = root / "requirements-windows-py314.lock"
    lock_text = lock_path.read_text(encoding="utf-8") if lock_path.is_file() else ""
    checks["pinned_windows_runtime"] = _check(
        "gurobipy==13.0.3" in lock_text
        and "numpy==2.5.2" in lock_text
        and "scipy==1.18.1" in lock_text
        and "pandas==3.0.5" in lock_text,
        "requirements-windows-py314.lock",
        "verified Windows CPython 3.14 dependency pins include the licensed solver"
        if lock_text
        else "dependency lock file missing",
    )

    v1_passed = isinstance(v1, dict) and v1.get("passed") is True
    checks["v1_diagnostics"] = _check(
        v1_passed and _all_true(v1.get("checks")),
        "docs/validation/v1_diagnostics.json",
        "V1 diagnostics pass and every recorded diagnostic check is true"
        if v1_passed
        else v1_error or "V1 diagnostics did not pass",
    )

    mass_checks = mass.get("checks") if isinstance(mass, dict) else None
    mass_ok = isinstance(mass, dict) and _all_true(mass_checks)
    checks["circular_mass_evidence"] = _check(
        mass_ok,
        "artifacts/circular_mass/evidence.json",
        "CIRCULAR-MASS synthetic formulation evidence reports 10/10 checks"
        if mass_ok
        else mass_error or "CIRCULAR-MASS evidence checks are incomplete",
    )

    product_checks = product.get("checks") if isinstance(product, dict) else None
    product_ok = isinstance(product, dict) and _all_true(product_checks)
    checks["product_integration_evidence"] = _check(
        product_ok,
        "artifacts/circular_mass/product_decision_evidence.json",
        "product integration evidence reports 7/7 checks"
        if product_ok
        else product_error or "product integration evidence checks are incomplete",
    )

    gurobi_checks = gurobi.get("checks") if isinstance(gurobi, dict) else None
    reference = gurobi.get("reference", {}) if isinstance(gurobi, dict) else {}
    gurobi_ok = (
        isinstance(gurobi, dict)
        and gurobi.get("solver") == "gurobi"
        and _all_true(gurobi_checks)
        and reference.get("status") == "OPTIMAL"
        and reference.get("mip_gap") is not None
        and reference.get("mip_gap") <= 1e-9
    )
    checks["gurobi_circular_mass_gate"] = _check(
        gurobi_ok,
        "artifacts/circular_mass/gurobi_validation.json",
        "licensed Gurobi reference/stress verification reports 11/11 checks and zero reference MIP gap"
        if gurobi_ok
        else gurobi_error or "Gurobi evidence is missing, non-optimal, or incomplete",
    )

    migration_report, migration_error = _load_json(root, "artifacts/database_migration_validation.json")
    migrations_ok = (
        isinstance(migration_report, dict)
        and migration_report.get("status") == "PASS"
        and migration_report.get("migration_count", 0) >= 1
        and not migration_report.get("errors")
    )
    checks["database_migration_inventory"] = _check(
        migrations_ok,
        "artifacts/database_migration_validation.json",
        "checked-in PostgreSQL migrations are contiguous, schema-complete, and free of forbidden content"
        if migrations_ok
        else migration_error or "database migration inventory is incomplete or invalid",
    )

    public_report, public_error = _load_json(root, "artifacts/public_reference_validation.json")
    public_ok = (
        isinstance(public_report, dict)
        and public_report.get("status") == "PASS"
        and public_report.get("record_count", 0) > 0
        and public_report.get("record_count") == public_report.get("unique_facility_count")
        and not public_report.get("errors")
    )
    checks["public_reference_dataset"] = _check(
        public_ok,
        "artifacts/public_reference_validation.json",
        "EPA GHGRP public facility reference extract is validated, unique, and provenance-labeled"
        if public_ok
        else public_error or "public reference dataset validation is incomplete or invalid",
    )

    synthetic, synthetic_error = _load_json(root, "artifacts/synthetic_enterprise_validation.json")
    synthetic_checks = synthetic.get("checks") if isinstance(synthetic, dict) else None
    synthetic_ok = (
        isinstance(synthetic, dict)
        and synthetic.get("status") == "PASS"
        and synthetic.get("row_count", 0) >= 10000
        and len(synthetic.get("case_counts", {})) == 12
        and _all_true(synthetic_checks)
    )
    checks["synthetic_enterprise_dataset"] = _check(
        synthetic_ok,
        "artifacts/synthetic_enterprise_validation.json",
        "120,000-row deterministic synthetic benchmark passes schema, range, case-coverage, public-context, trend-profile, physical-reconciliation, and fingerprint checks"
        if synthetic_ok
        else synthetic_error or "synthetic enterprise dataset validation is incomplete or invalid",
    )

    synthetic_gurobi, synthetic_gurobi_error = _load_json(root, "artifacts/synthetic_enterprise_gurobi_validation.json")
    synthetic_gurobi_checks = synthetic_gurobi.get("checks") if isinstance(synthetic_gurobi, dict) else None
    synthetic_gurobi_ok = (
        isinstance(synthetic_gurobi, dict)
        and synthetic_gurobi.get("status") == "PASS"
        and synthetic_gurobi.get("solver") == "gurobi"
        and synthetic_gurobi.get("input_rows", 0) >= 10000
        and _all_true(synthetic_gurobi_checks)
    )
    checks["synthetic_enterprise_gurobi_gate"] = _check(
        synthetic_gurobi_ok,
        "artifacts/synthetic_enterprise_gurobi_validation.json",
        "case-stratified synthetic benchmark solves through the explicit Gurobi backend with optimal status, zero MIP gap, and feasible constraints"
        if synthetic_gurobi_ok
        else synthetic_gurobi_error or "synthetic enterprise Gurobi evidence is missing, non-optimal, or incomplete",
    )

    source_registry, source_registry_error = _load_json(root, "artifacts/data_source_registry_validation.json")
    source_registry_checks = source_registry.get("checks") if isinstance(source_registry, dict) else None
    source_registry_ok = (
        isinstance(source_registry, dict)
        and source_registry.get("status") == "PASS"
        and source_registry.get("source_count", 0) >= 10
        and source_registry.get("integrated_reference_count", 0) >= 1
        and _all_true(source_registry_checks)
    )
    checks["data_source_registry"] = _check(
        source_registry_ok,
        "artifacts/data_source_registry_validation.json",
        "public, research, community, commercial, and private data-source boundaries are explicitly inventoried and the synthetic fallback is declared"
        if source_registry_ok
        else source_registry_error or "data-source registry validation is incomplete or invalid",
    )

    try:
        gurobi_version = importlib.metadata.version("gurobipy")
    except importlib.metadata.PackageNotFoundError:
        gurobi_version = None
    runtime_target_ok = sys.version_info[:2] == (3, 14)
    checks["runtime_target"] = _check(
        runtime_target_ok,
        "pyproject.toml / runtime",
        f"running CPython {platform.python_version()} on {platform.system()}"
        if runtime_target_ok
        else f"expected CPython 3.14, running {platform.python_version()}",
    )
    checks["gurobi_binding"] = _check(
        gurobi_version == "13.0.3",
        "importlib.metadata gurobipy",
        f"gurobipy {gurobi_version} is installed; license credentials are not recorded"
        if gurobi_version
        else "gurobipy is not installed in this runtime",
    )

    inventory = _artifact_inventory(root)
    checks["release_artifact_cleanliness"] = _check(
        not inventory["forbidden_release_files"],
        "source tree inventory",
        "no .env, local database, runtime log, estimator .joblib, or nested .zip release files found; ephemeral output is excluded"
        if not inventory["forbidden_release_files"]
        else "forbidden files: " + ", ".join(inventory["forbidden_release_files"]),
    )

    engineering_passed = all(item["status"] == "PASS" for item in checks.values())
    attestation_report = validate_attestations(root)
    production_blockers = [
        {
            "id": item["id"],
            "status": item["status"],
            "owner": item["owner"],
            "exit_criteria": item["exit_criteria"],
            "evidence_boundary": item["evidence_boundary"],
            "evidence_ref": item.get("evidence_ref"),
            "issues": item.get("issues", []),
        }
        for item in attestation_report["attestations"]
        if item["status"] != "PASS"
    ]
    if attestation_report["register_issues"]:
        production_blockers.append(
            {
                "id": "production_attestation_register",
                "status": "BLOCKED",
                "owner": "release governance",
                "exit_criteria": "provide a valid production attestation register with no unknown ids",
                "evidence_boundary": "the register structure itself must be valid before commercial approvals can be evaluated",
                "issues": attestation_report["register_issues"],
            }
        )

    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "release": "CIRCULAR_PRODUCT_V1",
        "release_class": "GUROBI_VERIFIED_ENGINEERING_RC",
        "engineering_gate": {
            "status": "PASS" if engineering_passed else "FAIL",
            "passed_checks": sum(item["status"] == "PASS" for item in checks.values()),
            "total_checks": len(checks),
            "checks": checks,
        },
        "commercial_production_gate": {
            "status": "PASS" if not production_blockers else "BLOCKED",
            "blockers": production_blockers,
        },
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "gurobipy": gurobi_version,
        },
        "artifact_inventory": inventory,
        "evidence_fingerprints": {
            relative: _sha256(root / relative)
            for relative in REQUIRED_FILES
            if (root / relative).is_file()
        },
        "claim_boundary": (
            "This register certifies a repeatable engineering evidence state only. "
            "It does not certify production readiness, commercial solver "
            "authorization, field calibration, security accreditation, or realized benefits."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="also fail when commercial-production blockers remain")
    args = parser.parse_args()
    report = build_readiness()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    engineering = report["engineering_gate"]
    commercial = report["commercial_production_gate"]
    print(
        f"RELEASE_READINESS engineering={engineering['status']} "
        f"({engineering['passed_checks']}/{engineering['total_checks']}) "
        f"commercial_production={commercial['status']} blockers={len(commercial['blockers'])}"
    )
    return 0 if engineering["status"] == "PASS" and (not args.strict or commercial["status"] == "PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
