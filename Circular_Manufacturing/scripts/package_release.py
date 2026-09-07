"""Create and verify a deterministic clean release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT.parent
DEFAULT_OUTPUT = SOURCE_ROOT.parent / f"{SOURCE_ROOT.name}_GUROBI_READINESS_RC_{datetime.now():%Y-%m-%d}.zip"
EXCLUDED_DIRECTORIES = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache"}
EXCLUDED_FILENAMES = {".env", ".coverage", "postgres_operational_check.json"}
EXCLUDED_SUFFIXES = {".sqlite3", ".db", ".jsonl"}
REQUIRED_ENTRIES = {
    f"{SOURCE_ROOT.name}/README_FIRST.txt",
    f"{SOURCE_ROOT.name}/RUN_ACCEPTANCE.cmd",
    f"{SOURCE_ROOT.name}/RUN_SYNTHETIC_ENTERPRISE.cmd",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/migrations/README.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/migrations/postgres/001_initial_schema.sql",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/public/epa_ghgrp_2023_facilities.csv",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/public/epa_ghgrp_2023_metadata.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/public/data_source_registry.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/synthetic/enterprise_120k/manifest.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/synthetic/enterprise_120k/observations.csv",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/synthetic/enterprise_120k/case_catalog.csv",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/synthetic/enterprise_120k/adversarial_cases.csv",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/src/circular_battery/ingestion/public_reference.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/release_readiness.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/build_frontend.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_production_attestations.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_database_migrations.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/ingest_epa_ghgrp.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_public_reference_dataset.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/postgres_operational_check.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_pilot_bundle.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/benefit_measurement.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/generate_synthetic_enterprise_dataset.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_synthetic_enterprise_dataset.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/synthetic_enterprise_gurobi_benchmark.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_data_source_registry.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_engineering_readiness.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/web/package.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/web/package-lock.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/web/tsconfig.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/production_attestations.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/production_attestation_validation.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/database_migration_validation.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/public_reference_validation.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/ENTERPRISE_OPERATIONS.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/PRODUCTION_EVIDENCE_INTAKE.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/PUBLIC_REFERENCE_DATA.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/DATA_SOURCE_REVIEW.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/ENGINEERING_READINESS.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/TECHNICAL_FOUNDATIONS.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/NEXT_LEVEL_ROADMAP.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/PILOT_DATA_AND_BENEFITS.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/SYNTHETIC_ENTERPRISE_DATASET.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/templates/pilot_bundle/README.md",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/data/templates/pilot_measurements.csv",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/production_preflight.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/scripts/validate_governed_bundle.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/src/circular_battery/platform/postgres_storage.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/src/circular_battery/ingestion/governance.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/src/circular_battery/web/auth.py",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/release_readiness.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/production_preflight.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/synthetic_enterprise_validation.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/synthetic_enterprise_gurobi_validation.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/engineering_readiness.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/artifacts/governed_reference_bundle.json",
    f"{SOURCE_ROOT.name}/Circular_Manufacturing/docs/PRODUCTION_READINESS.md",
}


def _excluded(path: Path) -> bool:
    relative_parts = path.relative_to(SOURCE_ROOT).parts
    if any(part in EXCLUDED_DIRECTORIES for part in relative_parts):
        return True
    return (
        path.name in EXCLUDED_FILENAMES
        or path.suffix.lower() in {".zip", ".pyc", ".pyo"} | EXCLUDED_SUFFIXES
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _members() -> list[tuple[Path, str]]:
    return [
        (path, f"{SOURCE_ROOT.name}/{path.relative_to(SOURCE_ROOT).as_posix()}")
        for path in sorted(SOURCE_ROOT.rglob("*"))
        if path.is_file() and not _excluded(path)
    ]


def package(output: Path = DEFAULT_OUTPUT) -> dict[str, object]:
    output = output.resolve()
    try:
        output.relative_to(SOURCE_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise ValueError("release output must be outside the source tree")

    readiness_path = ROOT / "artifacts" / "release_readiness.json"
    readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    if readiness.get("engineering_gate", {}).get("status") != "PASS":
        raise RuntimeError("engineering readiness gate is not PASS")

    members = _members()
    entry_names = {arcname for _, arcname in members}
    missing = sorted(REQUIRED_ENTRIES - entry_names)
    forbidden = sorted(
        arcname
        for arcname in entry_names
        if Path(arcname).name in EXCLUDED_FILENAMES
        or Path(arcname).suffix.lower() in {".zip", ".pyc", ".pyo", ".joblib"} | EXCLUDED_SUFFIXES
    )
    if missing or forbidden:
        raise RuntimeError(f"archive policy failed; missing={missing}, forbidden={forbidden}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, arcname in members:
            info = zipfile.ZipInfo(arcname, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 0
            info.external_attr = 0o100644 << 16
            archive.writestr(info, source.read_bytes())

    with zipfile.ZipFile(output) as archive:
        final_entries = set(archive.namelist())
    final_forbidden = sorted(
        name
        for name in final_entries
        if Path(name).name in EXCLUDED_FILENAMES
        or Path(name).suffix.lower() in {".zip", ".pyc", ".pyo", ".joblib"}
    )
    final_missing = sorted(REQUIRED_ENTRIES - final_entries)
    if final_missing or final_forbidden:
        raise RuntimeError(f"written archive failed verification; missing={final_missing}, forbidden={final_forbidden}")
    return {
        "archive": str(output),
        "sha256": _sha256(output),
        "entries": len(final_entries),
        "required_entries": len(REQUIRED_ENTRIES),
        "forbidden_entries": final_forbidden,
        "engineering_readiness": readiness["engineering_gate"],
        "commercial_production_status": readiness["commercial_production_gate"]["status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = package(args.output)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
