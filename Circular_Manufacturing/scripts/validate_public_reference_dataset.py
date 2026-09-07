"""Validate a public facility reference CSV and its provenance metadata."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {
    "reporting_year",
    "facility_id",
    "facility_name",
    "city",
    "state",
    "latitude",
    "longitude",
    "primary_naics_code",
    "industry_type_sectors",
    "total_reported_direct_emissions_mtco2e",
    "source_system",
    "evidence_class",
    "data_classification",
}


def _number(value: str, *, allow_blank: bool = False) -> float | None:
    if not str(value).strip() and allow_blank:
        return None
    result = float(str(value).strip())
    if not math.isfinite(result):
        raise ValueError("value must be finite")
    return result


def validate_public_reference_dataset(csv_path: Path | str, metadata_path: Path | str) -> dict[str, Any]:
    data_path = Path(csv_path)
    metadata_file = Path(metadata_path)
    if not data_path.is_absolute():
        data_path = ROOT / data_path
    if not metadata_file.is_absolute():
        metadata_file = ROOT / metadata_file
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    metadata: dict[str, Any] = {}
    if not data_path.is_file():
        errors.append("public reference CSV is missing")
    else:
        try:
            with data_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                columns = set(reader.fieldnames or [])
                missing = sorted(REQUIRED_COLUMNS - columns)
                if missing:
                    errors.append("CSV is missing required columns: " + ", ".join(missing))
                rows = list(reader)
        except (OSError, csv.Error) as exc:
            errors.append(f"CSV is unreadable: {type(exc).__name__}")
    if not metadata_file.is_file():
        errors.append("public reference metadata is missing")
    else:
        try:
            loaded = json.loads(metadata_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                metadata = loaded
            else:
                errors.append("metadata root must be a JSON object")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"metadata is unreadable: {type(exc).__name__}")

    facility_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        facility_id = str(row.get("facility_id", "")).strip()
        if not facility_id:
            errors.append(f"row {row_number} has no facility_id")
        elif facility_id in facility_ids:
            errors.append(f"duplicate facility_id at row {row_number}: {facility_id}")
        facility_ids.add(facility_id)
        if str(row.get("reporting_year", "")).strip() != "2023":
            errors.append(f"row {row_number} has unexpected reporting_year")
        try:
            emissions = _number(row.get("total_reported_direct_emissions_mtco2e", ""))
            if emissions is not None and emissions < 0:
                errors.append(f"row {row_number} has negative emissions")
            _number(row.get("latitude", ""), allow_blank=True)
            _number(row.get("longitude", ""), allow_blank=True)
        except (TypeError, ValueError):
            errors.append(f"row {row_number} has invalid numeric values")
        if str(row.get("source_system", "")).strip() != "US EPA GHGRP":
            errors.append(f"row {row_number} has an unexpected source_system")
        if str(row.get("evidence_class", "")).strip() != "PUBLIC_GOVERNMENT_FACILITY_REFERENCE":
            errors.append(f"row {row_number} is missing the public evidence class")

    if metadata.get("record_count") != len(rows):
        errors.append("metadata record_count does not match CSV rows")
    if metadata.get("evidence_class") != "PUBLIC_GOVERNMENT_FACILITY_REFERENCE":
        errors.append("metadata evidence_class is not the public reference class")
    if not str(metadata.get("source_archive_url", "")).startswith("https://www.epa.gov/"):
        errors.append("metadata source_archive_url is not an official EPA HTTPS URL")
    for field in ("source_archive_sha256", "source_workbook_sha256"):
        value = metadata.get(field)
        if value is None or not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
            errors.append(f"metadata {field} is not a SHA-256 value")
    timestamp = metadata.get("retrieved_at_utc")
    try:
        parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
    except (TypeError, ValueError):
        errors.append("metadata retrieved_at_utc must be timezone-aware ISO-8601")

    passed = bool(rows) and not errors
    return {
        "schema_version": "1.0",
        "status": "PASS" if passed else "BLOCKED",
        "passed": passed,
        "csv": data_path.relative_to(ROOT).as_posix() if data_path.is_relative_to(ROOT) else str(data_path),
        "metadata": metadata_file.relative_to(ROOT).as_posix() if metadata_file.is_relative_to(ROOT) else str(metadata_file),
        "record_count": len(rows),
        "unique_facility_count": len(facility_ids),
        "errors": errors,
        "claim_boundary": (
            "Validation checks the CSV contract and provenance metadata. It does not independently verify EPA source truth, "
            "plant operations, causal performance, recovery yields, costs, or realized benefits."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--out", type=Path, default=Path("artifacts/public_reference_validation.json"))
    args = parser.parse_args()
    report = validate_public_reference_dataset(args.csv, args.metadata)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PUBLIC_REFERENCE_DATASET status={report['status']} rows={report['record_count']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
