"""Ingest the official EPA GHGRP facility workbook into a bounded public reference CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://www.epa.gov/system/files/other-files/2024-10/2023_data_summary_spreadsheets.zip"
SOURCE_PAGE = "https://www.epa.gov/ghgreporting/data-sets"
SHEET_NAME = "Direct Point Emitters"
REPORTING_YEAR = 2023
OUTPUT_COLUMNS = [
    "reporting_year",
    "facility_id",
    "facility_name",
    "city",
    "state",
    "zip_code",
    "latitude",
    "longitude",
    "primary_naics_code",
    "industry_type_subparts",
    "industry_type_sectors",
    "total_reported_direct_emissions_mtco2e",
    "continuous_emissions_monitoring",
    "source_system",
    "evidence_class",
    "data_classification",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest(source_workbook: Path | str, output_csv: Path | str, metadata_path: Path | str, *, source_archive_sha256: str = "", retrieved_at_utc: str | None = None) -> dict[str, Any]:
    source = Path(source_workbook).resolve()
    output = Path(output_csv)
    metadata = Path(metadata_path)
    if not output.is_absolute():
        output = ROOT / output
    if not metadata.is_absolute():
        metadata = ROOT / metadata
    if not source.is_file():
        raise FileNotFoundError(f"source workbook not found: {source}")

    frame = pd.read_excel(source, sheet_name=SHEET_NAME, header=3, dtype=object)
    frame.columns = [str(column).strip() for column in frame.columns]
    source_columns = {
        "Facility Id": "facility_id",
        "Facility Name": "facility_name",
        "City": "city",
        "State": "state",
        "Zip Code": "zip_code",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "Primary NAICS Code": "primary_naics_code",
        "Industry Type (subparts)": "industry_type_subparts",
        "Industry Type (sectors)": "industry_type_sectors",
        "Total reported direct emissions": "total_reported_direct_emissions_mtco2e",
        "Does the facility employ continuous emissions monitoring?": "continuous_emissions_monitoring",
    }
    missing = sorted(set(source_columns) - set(frame.columns))
    if missing:
        raise ValueError("EPA workbook is missing expected columns: " + ", ".join(missing))

    selected = frame[list(source_columns)].rename(columns=source_columns).copy()
    for column in ("facility_id", "facility_name", "city", "state", "zip_code", "primary_naics_code", "industry_type_subparts", "industry_type_sectors", "continuous_emissions_monitoring"):
        selected[column] = selected[column].fillna("").astype(str).str.strip()
    for column in ("latitude", "longitude", "total_reported_direct_emissions_mtco2e"):
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
    selected = selected[selected["facility_id"] != ""].copy()
    selected.insert(0, "reporting_year", REPORTING_YEAR)
    selected["source_system"] = "US EPA GHGRP"
    selected["evidence_class"] = "PUBLIC_GOVERNMENT_FACILITY_REFERENCE"
    selected["data_classification"] = "PUBLIC_ENVIRONMENTAL_REPORTING"
    selected = selected[OUTPUT_COLUMNS].sort_values("facility_id", kind="stable").reset_index(drop=True)

    output.parent.mkdir(parents=True, exist_ok=True)
    selected.to_csv(output, index=False, encoding="utf-8", na_rep="")
    retrieved = retrieved_at_utc or datetime.now(timezone.utc).isoformat()
    report = {
        "schema_version": "1.0",
        "dataset_id": "epa-ghgrp-2023-direct-point-emitters",
        "reporting_year": REPORTING_YEAR,
        "record_count": int(len(selected)),
        "source_name": "US EPA Greenhouse Gas Reporting Program 2023 Data Summary Spreadsheets",
        "source_page": SOURCE_PAGE,
        "source_archive_url": SOURCE_URL,
        "source_archive_sha256": source_archive_sha256 or None,
        "source_workbook": source.name,
        "source_workbook_sha256": _sha256(source),
        "source_sheet": SHEET_NAME,
        "retrieved_at_utc": retrieved,
        "output_csv": output.relative_to(ROOT).as_posix() if output.is_relative_to(ROOT) else str(output),
        "columns": OUTPUT_COLUMNS,
        "evidence_class": "PUBLIC_GOVERNMENT_FACILITY_REFERENCE",
        "data_classification": "PUBLIC_ENVIRONMENTAL_REPORTING",
        "sector_counts": {str(key): int(value) for key, value in selected["industry_type_sectors"].value_counts(dropna=False).items()},
        "claim_boundary": (
            "This is public EPA facility-level environmental reference data. It is not customer plant telemetry, "
            "does not contain recovery/yield/cost/inventory operations, and cannot close field calibration or "
            "realized-benefit production attestations."
        ),
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_workbook", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/public/epa_ghgrp_2023_facilities.csv"))
    parser.add_argument("--metadata", type=Path, default=Path("data/public/epa_ghgrp_2023_metadata.json"))
    parser.add_argument("--source-archive-sha256", default="")
    parser.add_argument("--retrieved-at-utc")
    args = parser.parse_args()
    report = ingest(args.source_workbook, args.output, args.metadata, source_archive_sha256=args.source_archive_sha256, retrieved_at_utc=args.retrieved_at_utc)
    print(f"EPA_GHGRP_INGEST status=PASS rows={report['record_count']} year={report['reporting_year']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
