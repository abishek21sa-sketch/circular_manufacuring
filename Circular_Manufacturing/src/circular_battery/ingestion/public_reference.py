"""Read-only access to the validated EPA facility reference extract.

This module deliberately exposes benchmark context only.  It does not map a
public facility record to a customer plant or infer operational performance.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

from circular_battery.paths import find_repo_root

ROOT = find_repo_root()
CSV_PATH = ROOT / "data" / "public" / "epa_ghgrp_2023_facilities.csv"
METADATA_PATH = ROOT / "data" / "public" / "epa_ghgrp_2023_metadata.json"


@lru_cache(maxsize=1)
def _metadata() -> dict:
    return json.loads(METADATA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _rows() -> tuple[dict[str, str], ...]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(csv.DictReader(handle))


def _evidence(metadata: dict) -> dict[str, str]:
    return {
        "dataset_id": metadata["dataset_id"],
        "source_name": metadata["source_name"],
        "source_page": metadata["source_page"],
        "source_archive_url": metadata["source_archive_url"],
        "source_workbook_sha256": metadata["source_workbook_sha256"],
        "evidence_class": metadata["evidence_class"],
        "data_classification": metadata["data_classification"],
        "claim_boundary": metadata["claim_boundary"],
    }


def public_reference_summary() -> dict:
    metadata = _metadata()
    rows = _rows()
    state_counts = Counter(row.get("state", "") for row in rows if row.get("state"))
    sector_counts = Counter(row.get("industry_type_sectors", "") for row in rows if row.get("industry_type_sectors"))
    total_emissions = sum(
        float(row["total_reported_direct_emissions_mtco2e"])
        for row in rows
        if row.get("total_reported_direct_emissions_mtco2e")
    )
    return {
        "reporting_year": metadata["reporting_year"],
        "record_count": len(rows),
        "total_reported_direct_emissions_mtco2e": round(total_emissions, 2),
        "top_states_by_record_count": dict(state_counts.most_common(20)),
        "top_sectors_by_record_count": dict(sector_counts.most_common(20)),
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "evidence": _evidence(metadata),
    }


def public_reference_facilities(
    *,
    state: str | None = None,
    naics: str | None = None,
    query: str | None = None,
    limit: int = 50,
) -> dict:
    metadata = _metadata()
    state = (state or "").strip().upper()
    naics = (naics or "").strip()
    query = (query or "").strip().casefold()
    if state and (len(state) != 2 or not state.isalpha()):
        raise ValueError("state must be a two-letter code")
    if naics and (not naics.isdigit() or not 2 <= len(naics) <= 6):
        raise ValueError("naics must contain 2–6 digits")
    if len(query) > 120:
        raise ValueError("query must be <= 120 characters")
    limit = max(1, min(int(limit), 100))

    matched = []
    for row in _rows():
        if state and row.get("state", "").upper() != state:
            continue
        if naics and not row.get("primary_naics_code", "").startswith(naics):
            continue
        if query and query not in " ".join(
            (row.get("facility_name", ""), row.get("city", ""), row.get("state", ""))
        ).casefold():
            continue
        matched.append(
            {
                "reporting_year": int(row["reporting_year"]),
                "facility_id": row["facility_id"],
                "facility_name": row["facility_name"],
                "city": row["city"],
                "state": row["state"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "primary_naics_code": row["primary_naics_code"],
                "industry_type_sectors": row["industry_type_sectors"],
                "total_reported_direct_emissions_mtco2e": float(row["total_reported_direct_emissions_mtco2e"]),
            }
        )
    return {
        "reporting_year": metadata["reporting_year"],
        "matched_count": len(matched),
        "returned_count": min(len(matched), limit),
        "filters": {"state": state or None, "naics": naics or None, "query": query or None},
        "facilities": matched[:limit],
        "evidence": _evidence(metadata),
    }
