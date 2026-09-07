from pathlib import Path

from scripts.validate_public_reference_dataset import validate_public_reference_dataset


ROOT = Path(__file__).resolve().parents[1]


def test_epa_public_reference_extract_is_validated_and_labeled():
    report = validate_public_reference_dataset(
        ROOT / "data/public/epa_ghgrp_2023_facilities.csv",
        ROOT / "data/public/epa_ghgrp_2023_metadata.json",
    )

    assert report["status"] == "PASS"
    assert report["record_count"] > 6000
    assert report["unique_facility_count"] == report["record_count"]


def test_public_reference_validator_rejects_unapproved_source_metadata(tmp_path):
    csv_path = tmp_path / "facilities.csv"
    csv_path.write_text(
        "reporting_year,facility_id,facility_name,city,state,latitude,longitude,primary_naics_code,industry_type_sectors,total_reported_direct_emissions_mtco2e,source_system,evidence_class,data_classification\n"
        "2023,1,Example,Test,TX,30,-97,111111,Metals,1,unknown,SYNTHETIC,SYNTHETIC\n",
        encoding="utf-8",
    )
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(
        '{"record_count": 1, "evidence_class": "SYNTHETIC", "source_archive_url": "https://example.invalid/source", "retrieved_at_utc": "2026-09-05T00:00:00+00:00"}',
        encoding="utf-8",
    )

    report = validate_public_reference_dataset(csv_path, metadata_path)

    assert report["status"] == "BLOCKED"
    assert report["errors"]
