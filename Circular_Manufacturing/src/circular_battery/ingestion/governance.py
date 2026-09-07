"""Lineage and data-quality controls for scenario bundles.

Bundle validation proves that the optimizer can consume a dataset.  Governance
validation adds the evidence needed to know where the dataset came from, when it
was valid, what files were received, and whether it is eligible for a controlled
pilot.  It does not independently prove that a plant or supplier reported the
truth.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from circular_battery.evidence.registry import stable_hash
from circular_battery.platform.errors import ValidationError
from circular_battery.ingestion.bundle import REQUIRED_FILES, validate_bundle


_EXPECTED_COLUMNS = {
    "materials.csv": {
        "name", "kg_per_pack", "virgin_cost_per_kg", "recycled_cost_per_kg",
        "virgin_kgco2e_per_kg", "recycled_kgco2e_per_kg", "recycling_yield", "critical",
    },
    "periods.csv": {"period", "production_packs", "eol_returns_packs", "collection_rate"},
    "collections.csv": {"name", "returns_kg", "reman_eligible_share", "x_km", "y_km"},
    "facilities.csv": {
        "name", "kind", "capacity_kg", "fixed_cost", "processing_cost_per_kg",
        "processing_kgco2e_per_kg", "x_km", "y_km",
    },
    "planning.csv": {"period", "demand_packs", "regular_capacity_packs", "overtime_capacity_packs"},
}

_NUMERIC_COLUMNS = {
    "kg_per_pack", "virgin_cost_per_kg", "recycled_cost_per_kg", "virgin_kgco2e_per_kg",
    "recycled_kgco2e_per_kg", "recycling_yield", "period", "production_packs",
    "eol_returns_packs", "collection_rate", "grade_A", "grade_B", "grade_C",
    "returns_kg", "reman_eligible_share", "x_km", "y_km", "capacity_kg", "fixed_cost",
    "processing_cost_per_kg", "processing_kgco2e_per_kg", "demand_packs",
    "regular_capacity_packs", "overtime_capacity_packs",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _lineage(manifest: dict[str, Any]) -> dict[str, str]:
    nested = manifest.get("lineage") if isinstance(manifest.get("lineage"), dict) else {}
    return {
        field: str(nested.get(field, manifest.get(field, ""))).strip()
        for field in ("source_system", "source_owner", "facility_id", "as_of_utc", "data_classification")
    }


def _valid_timestamp(value: str) -> bool:
    if not value:
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _file_quality(path: Path, expected: set[str]) -> dict[str, Any]:
    missing_columns: set[str] = set()
    invalid_cells: list[dict[str, Any]] = []
    row_count = 0
    columns: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        missing_columns = expected - set(columns)
        for row_number, row in enumerate(reader, start=2):
            row_count += 1
            for column, raw in row.items():
                if column is None or raw is None or not str(raw).strip():
                    invalid_cells.append({"row": row_number, "column": column or "<extra>"})
                    continue
                if column in _NUMERIC_COLUMNS:
                    try:
                        value = float(raw)
                    except (TypeError, ValueError):
                        invalid_cells.append({"row": row_number, "column": column, "reason": "not_numeric"})
                        continue
                    if not math.isfinite(value):
                        invalid_cells.append({"row": row_number, "column": column, "reason": "not_finite"})
    return {
        "file": path.name,
        "sha256": _sha256(path),
        "bytes": path.stat().st_size,
        "rows": row_count,
        "columns": columns,
        "missing_columns": sorted(missing_columns),
        "invalid_cell_count": len(invalid_cells),
        "invalid_cells_sample": invalid_cells[:10],
    }


def inspect_bundle(directory: Path | str, *, require_lineage: bool = False) -> dict[str, Any]:
    """Return a deterministic governance report without persisting source data."""

    directory = Path(directory)
    meta = validate_bundle(directory)
    manifest = meta["manifest"]
    expected = dict(_EXPECTED_COLUMNS)
    grades = manifest.get("recovery_grades", {})
    period_columns = set(expected["periods.csv"])
    period_columns.update(f"grade_{name}" for name in grades)
    expected["periods.csv"] = period_columns

    files = []
    for name in REQUIRED_FILES:
        if name == "manifest.json":
            continue
        report = _file_quality(directory / name, expected.get(name, set()))
        files.append(report)

    schema_ok = all(not item["missing_columns"] and item["rows"] > 0 for item in files)
    numeric_ok = all(item["invalid_cell_count"] == 0 for item in files)
    lineage = _lineage(manifest)
    missing_lineage = [key for key, value in lineage.items() if not value]
    if lineage.get("as_of_utc") and not _valid_timestamp(lineage["as_of_utc"]):
        missing_lineage.append("as_of_utc_valid_iso8601")
    lineage_ok = not missing_lineage

    checks = {
        "schema_integrity": {
            "status": "PASS" if schema_ok else "FAIL",
            "detail": "required columns and non-empty rows are present" if schema_ok else "one or more required columns or rows are missing",
        },
        "numeric_quality": {
            "status": "PASS" if numeric_ok else "FAIL",
            "detail": "numeric cells are finite" if numeric_ok else "one or more numeric cells are blank, invalid, or non-finite",
        },
        "lineage_completeness": {
            "status": "PASS" if lineage_ok else ("FAIL" if require_lineage else "PENDING"),
            "detail": "source, owner, facility, classification, and UTC validity metadata are complete"
            if lineage_ok else "missing lineage fields: " + ", ".join(sorted(set(missing_lineage))),
        },
    }
    validation_status = "PASS" if schema_ok and numeric_ok else "FAIL"
    governance_status = "PASS" if lineage_ok else "PENDING"
    accepted = validation_status == "PASS" and (not require_lineage or governance_status == "PASS")
    identity = {
        "bundle_hash_sha256": meta["bundle_hash_sha256"],
        "lineage": lineage,
        "files": [{"file": item["file"], "sha256": item["sha256"], "rows": item["rows"]} for item in files],
    }
    return {
        "schema_version": "1.0",
        "ingestion_id": "ing_" + stable_hash(identity)[:16],
        "bundle_hash_sha256": meta["bundle_hash_sha256"],
        "evidence_class": manifest["evidence_class"],
        "lineage": lineage,
        "files": files,
        "checks": checks,
        "validation_status": validation_status,
        "governance_status": governance_status,
        "accepted_for_optimization": accepted,
        "claim_boundary": "Schema and data-quality checks do not independently verify source truth, measurement accuracy, or realized operational outcomes.",
    }


def validate_governed_bundle(directory: Path | str) -> dict[str, Any]:
    """Require complete lineage before a bundle is eligible for a pilot."""

    report = inspect_bundle(directory, require_lineage=True)
    if not report["accepted_for_optimization"]:
        raise ValidationError(
            "Bundle is not eligible for governed optimization.",
            details={"ingestion_id": report["ingestion_id"], "checks": report["checks"]},
        )
    return report
