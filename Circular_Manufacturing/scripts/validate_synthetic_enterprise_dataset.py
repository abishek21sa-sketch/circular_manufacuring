"""Validate the deterministic synthetic enterprise dataset and its manifest."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "synthetic" / "enterprise_120k"
DEFAULT_OUT = ROOT / "artifacts" / "synthetic_enterprise_validation.json"
EXPECTED_CASES = {
    "baseline", "seasonal_peak", "demand_downturn", "scrap_spike", "quality_degradation",
    "transport_disruption", "facility_outage", "material_shortage", "grid_carbon_spike",
    "return_surge", "reman_eligibility_low", "service_infeasible",
}


def _display_path(path: Path) -> str:
    """Return repository-relative evidence paths when possible."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)
REQUIRED_COLUMNS = {
    "record_id", "scenario_id", "period", "facility_id", "case_type", "chemistry", "pack_mass_kg",
    "demand_packs", "demand_kg", "production_packs", "regular_capacity_packs", "overtime_capacity_packs",
    "service_gap_packs", "eol_returns_packs", "eol_returns_kg", "collection_rate", "grade_A_share",
    "grade_B_share", "grade_C_share", "soh", "cycles", "damage_index", "temperature_c",
    "recovery_quality_score", "quality_grade", "pathway", "recycle_yield", "reman_yield",
    "second_life_share", "reman_eligible_share", "expected_recovered_kg", "recycled_content_share",
    "material_price_index", "transport_distance_km", "facility_available", "facility_uptime",
    "energy_kwh_per_pack", "grid_kgco2e_per_kwh", "scrap_rate", "safety_stock_packs", "imputation_required",
    "data_quality_state",
}
TEXT_COLUMNS = {
    "record_id", "scenario_id", "facility_id", "public_context_sector", "public_context_emissions_tier",
    "trend_profile", "case_type", "chemistry", "quality_grade", "pathway", "data_quality_state",
}
NUMERIC_COLUMNS = REQUIRED_COLUMNS - TEXT_COLUMNS
RANGES = {
    "period": (1, 120), "pack_mass_kg": (300, 550), "demand_packs": (1, 10000), "demand_kg": (100, 5_000_000),
    "production_packs": (0, 10000), "regular_capacity_packs": (0, 12000), "overtime_capacity_packs": (0, 5000),
    "service_gap_packs": (0, 10000), "eol_returns_packs": (0, 10000), "eol_returns_kg": (0, 5_000_000),
    "collection_rate": (0, 1), "grade_A_share": (0, 1), "grade_B_share": (0, 1), "grade_C_share": (0, 1),
    "soh": (0, 1), "cycles": (0, 10000), "damage_index": (0, 1), "temperature_c": (-40, 80),
    "recovery_quality_score": (0, 1), "recycle_yield": (0, 1), "reman_yield": (0, 1),
    "second_life_share": (0, 1), "reman_eligible_share": (0, 1), "expected_recovered_kg": (0, 5_000_000),
    "recycled_content_share": (0, 1), "material_price_index": (0.1, 5), "transport_distance_km": (0, 5000),
    "facility_available": (0, 1), "facility_uptime": (0, 1), "energy_kwh_per_pack": (0, 2000),
    "grid_kgco2e_per_kwh": (0, 5), "scrap_rate": (0, 1), "safety_stock_packs": (0, 10000), "imputation_required": (0, 1),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def validate_dataset(directory: Path | str) -> dict:
    directory = Path(directory)
    checks: dict[str, bool] = {}
    issues: list[str] = []
    manifest_path = directory / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        checks["manifest_json"] = True
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "checks": {"manifest_json": False}, "issues": [f"manifest: {exc}"]}

    observations_path = directory / "observations.csv"
    fields, rows = _rows(observations_path)
    checks["canonical_row_count_at_least_10000"] = len(rows) >= 10000
    if not checks["canonical_row_count_at_least_10000"]:
        issues.append(f"canonical rows={len(rows)}; expected at least 10000")
    checks["required_columns"] = REQUIRED_COLUMNS <= set(fields)
    if not checks["required_columns"]:
        issues.append("observations.csv is missing required columns")
    checks["unique_record_ids"] = len({row.get("record_id") for row in rows}) == len(rows)
    if not checks["unique_record_ids"]:
        issues.append("record_id values are not unique")

    case_counts = Counter(row.get("case_type", "") for row in rows)
    checks["all_case_families_present"] = EXPECTED_CASES <= set(case_counts)
    if not checks["all_case_families_present"]:
        issues.append("one or more required case families are absent")
    checks["case_family_minimum_coverage"] = all(case_counts[case] >= 50 for case in EXPECTED_CASES)
    if not checks["case_family_minimum_coverage"]:
        issues.append("each case family must have at least 50 rows")

    checks["public_context_columns_present"] = {
        "public_context_sector", "public_context_emissions_tier", "trend_profile", "period_year",
    } <= set(fields)
    if not checks["public_context_columns_present"]:
        issues.append("public-data context and trend columns are missing")

    range_errors = []
    missing_values = []
    balance_errors = []
    physical_errors = []
    for row_number, row in enumerate(rows, start=2):
        for column in NUMERIC_COLUMNS:
            raw = row.get(column, "")
            if raw is None or not str(raw).strip():
                missing_values.append({"row": row_number, "column": column})
                continue
            try:
                value = float(raw)
            except ValueError:
                range_errors.append({"row": row_number, "column": column, "reason": "not_numeric"})
                continue
            if not math.isfinite(value):
                range_errors.append({"row": row_number, "column": column, "reason": "non_finite"})
                continue
            low, high = RANGES[column]
            if not low <= value <= high:
                range_errors.append({"row": row_number, "column": column, "value": value, "expected": [low, high]})
        try:
            grade_sum = sum(float(row[f"grade_{grade}_share"]) for grade in "ABC")
            if abs(grade_sum - 1.0) > 1e-5:
                balance_errors.append({"row": row_number, "reason": "grade_mix_not_one", "value": grade_sum})
            if float(row["expected_recovered_kg"]) > float(row["eol_returns_kg"]) + 1e-5:
                physical_errors.append({"row": row_number, "reason": "recovered_exceeds_returns"})
            expected_gap = max(0.0, float(row["demand_packs"]) - float(row["regular_capacity_packs"]) - float(row["overtime_capacity_packs"]))
            if abs(expected_gap - float(row["service_gap_packs"])) > 0.02:
                physical_errors.append({"row": row_number, "reason": "service_gap_not_reconciled"})
            if row["case_type"] == "service_infeasible" and float(row["service_gap_packs"]) <= 0:
                physical_errors.append({"row": row_number, "reason": "infeasible_case_has_no_gap"})
            if row["case_type"] != "service_infeasible" and float(row["service_gap_packs"]) > 0.02:
                physical_errors.append({"row": row_number, "reason": "non_infeasible_case_has_gap"})
            if int(float(row["facility_available"])) not in {0, 1}:
                physical_errors.append({"row": row_number, "reason": "facility_flag_not_binary"})
        except (KeyError, TypeError, ValueError):
            physical_errors.append({"row": row_number, "reason": "physical_reconciliation_unreadable"})

    checks["no_missing_numeric_values"] = not missing_values
    checks["numeric_ranges"] = not range_errors
    checks["grade_mix_closes"] = not balance_errors
    checks["physical_reconciliations"] = not physical_errors
    if missing_values:
        issues.append(f"missing numeric values={len(missing_values)}")
    if range_errors:
        issues.append(f"numeric range errors={len(range_errors)}")
    if balance_errors:
        issues.append(f"grade balance errors={len(balance_errors)}")
    if physical_errors:
        issues.append(f"physical reconciliation errors={len(physical_errors)}")

    adversarial_fields, adversarial_rows = _rows(directory / "adversarial_cases.csv")
    expected_negative_types = {"missing_required_value", "fraction_out_of_range", "non_finite_numeric", "duplicate_record_id", "service_capacity_violation", "invalid_facility_flag"}
    negative_types = {row.get("case_type") for row in adversarial_rows}
    checks["adversarial_fixture_separate_and_complete"] = expected_negative_types <= negative_types and all(row.get("expected_validator_result") == "FAIL" for row in adversarial_rows)
    if not checks["adversarial_fixture_separate_and_complete"]:
        issues.append("adversarial fixture does not cover all expected negative cases")

    files_match = True
    for name, spec in manifest.get("files", {}).items():
        path = directory / name
        actual_rows = sum(1 for _ in path.open("r", encoding="utf-8")) - 1
        if actual_rows != spec.get("rows") or _sha256(path) != spec.get("sha256"):
            files_match = False
            issues.append(f"manifest fingerprint mismatch for {name}")
    checks["manifest_fingerprints"] = files_match
    checks["manifest_evidence_class"] = manifest.get("evidence_class") == "SYNTHETIC VALIDATION"
    if not checks["manifest_evidence_class"]:
        issues.append("dataset must remain labeled SYNTHETIC VALIDATION")
    public_context_profile = manifest.get("public_context_profile", {})
    checks["public_context_profile_declared"] = (
        public_context_profile.get("source_record_count", 0) >= 1000
        and bool(public_context_profile.get("sector_counts"))
        and "sampling_method" in public_context_profile
    )
    if not checks["public_context_profile_declared"]:
        issues.append("manifest must declare the public reference distribution and sampling method")
    checks["trend_profiles_declared"] = set(manifest.get("trend_profiles", {})) >= {
        "demand_growth", "recycling_feedstock_lag", "manufacturing_scale_up", "energy_price_stress",
    }
    if not checks["trend_profiles_declared"]:
        issues.append("manifest must declare all bounded industrial trend profiles")

    passed = all(checks.values()) and not issues
    return {
        "schema_version": "1.0",
        "status": "PASS" if passed else "FAIL",
        "dataset": _display_path(directory),
        "manifest": manifest,
        "row_count": len(rows),
        "case_counts": dict(sorted(case_counts.items())),
        "checks": checks,
        "issues": issues,
        "error_samples": {
            "missing_values": missing_values[:10],
            "range_errors": range_errors[:10],
            "balance_errors": balance_errors[:10],
            "physical_errors": physical_errors[:10],
        },
        "claim_boundary": "This validates deterministic synthetic data quality and generator integrity only; it does not prove plant truth, external validity, or realized benefit.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = validate_dataset(args.dataset)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"SYNTHETIC_DATASET_VALIDATION status={report['status']} rows={report['row_count']} cases={len(report['case_counts'])}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
