"""Generate a deterministic, governed synthetic circular-manufacturing dataset.

The canonical observations are complete and physically bounded so they can be
used for repeatable engineering/model tests.  Adversarial cases are kept in a
separate fixture because intentionally invalid rows must never be mistaken for
valid pilot data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "synthetic" / "enterprise_120k"
DEFAULT_PUBLIC_REFERENCE = ROOT / "data" / "public" / "epa_ghgrp_2023_facilities.csv"
SEED = 20260906
AS_OF_UTC = "2026-09-06T00:00:00+00:00"
DEFAULT_START_YEAR = 2026

CASE_TYPES = (
    "baseline",
    "seasonal_peak",
    "demand_downturn",
    "scrap_spike",
    "quality_degradation",
    "transport_disruption",
    "facility_outage",
    "material_shortage",
    "grid_carbon_spike",
    "return_surge",
    "reman_eligibility_low",
    "service_infeasible",
)

CHEMISTRIES = ("NMC811", "NMC622", "NMC111", "LFP", "NCA", "LMO")
PACK_MASS_KG = {
    "NMC811": 410.0,
    "NMC622": 420.0,
    "NMC111": 425.0,
    "LFP": 390.0,
    "NCA": 405.0,
    "LMO": 400.0,
}

OBSERVATION_COLUMNS = (
    "record_id",
    "scenario_id",
    "period",
    "facility_id",
    "public_context_sector",
    "public_context_emissions_tier",
    "trend_profile",
    "period_year",
    "case_type",
    "chemistry",
    "pack_mass_kg",
    "demand_packs",
    "demand_kg",
    "production_packs",
    "regular_capacity_packs",
    "overtime_capacity_packs",
    "service_gap_packs",
    "eol_returns_packs",
    "eol_returns_kg",
    "collection_rate",
    "grade_A_share",
    "grade_B_share",
    "grade_C_share",
    "soh",
    "cycles",
    "damage_index",
    "temperature_c",
    "recovery_quality_score",
    "quality_grade",
    "pathway",
    "recycle_yield",
    "reman_yield",
    "second_life_share",
    "reman_eligible_share",
    "expected_recovered_kg",
    "recycled_content_share",
    "material_price_index",
    "transport_distance_km",
    "facility_available",
    "facility_uptime",
    "energy_kwh_per_pack",
    "grid_kgco2e_per_kwh",
    "scrap_rate",
    "safety_stock_packs",
    "imputation_required",
    "data_quality_state",
)

CASE_DESCRIPTIONS = {
    "baseline": "Nominal demand, quality, capacity, recovery and transport conditions.",
    "seasonal_peak": "Seasonal demand peak with higher throughput and moderate capacity pressure.",
    "demand_downturn": "Lower demand regime with excess capacity and lower return flow.",
    "scrap_spike": "Manufacturing scrap event increases loss and reduces available output.",
    "quality_degradation": "Lower state of health and higher damage reduce reuse/remanufacture yield.",
    "transport_disruption": "Longer routes and lower collection performance increase logistics friction.",
    "facility_outage": "A recovery facility is unavailable for a subset of periods.",
    "material_shortage": "Material-price pressure and lower recycled-content availability.",
    "grid_carbon_spike": "Higher grid carbon intensity changes lifecycle impact pressure.",
    "return_surge": "Unusually high end-of-life returns increase recovery workload.",
    "reman_eligibility_low": "A smaller share of collected material is eligible for remanufacture.",
    "service_infeasible": "Demand exceeds regular plus overtime capacity and creates a measured service gap.",
}

TREND_PROFILES = {
    "demand_growth": {
        "weight": 0.45,
        "description": "Conservative demand expansion stress profile.",
        "annual_demand_growth": 0.025,
        "annual_return_growth": 0.010,
        "annual_material_price_growth": 0.000,
    },
    "recycling_feedstock_lag": {
        "weight": 0.25,
        "description": "Demand grows ahead of end-of-life feedstock availability.",
        "annual_demand_growth": 0.018,
        "annual_return_growth": 0.004,
        "annual_material_price_growth": 0.006,
    },
    "manufacturing_scale_up": {
        "weight": 0.20,
        "description": "Capacity expansion with temporary throughput and quality pressure.",
        "annual_demand_growth": 0.020,
        "annual_return_growth": 0.008,
        "annual_material_price_growth": 0.004,
    },
    "energy_price_stress": {
        "weight": 0.10,
        "description": "Energy-intensive operations face a bounded price-pressure scenario.",
        "annual_demand_growth": 0.010,
        "annual_return_growth": 0.006,
        "annual_material_price_growth": 0.012,
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _clip(value: float, low: float, high: float) -> float:
    return float(np.clip(value, low, high))


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _load_public_context(path: Path) -> dict:
    """Load only public distributional context; never copy facility identity into synthetic rows."""
    if not path.is_file():
        raise FileNotFoundError(f"public reference dataset not found: {path}")
    contexts: list[dict[str, str | float]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            sector = str(row.get("industry_type_sectors", "Other")).strip() or "Other"
            try:
                emissions = float(row.get("total_reported_direct_emissions_mtco2e", ""))
            except (TypeError, ValueError):
                continue
            if math.isfinite(emissions) and emissions >= 0:
                contexts.append({"sector": sector, "emissions": emissions})
    if not contexts:
        raise ValueError(f"public reference dataset has no usable context rows: {path}")
    emissions_values = np.asarray([float(item["emissions"]) for item in contexts], dtype=float)
    q33, q67 = (float(value) for value in np.quantile(emissions_values, [0.33, 0.67]))
    sector_counts: dict[str, int] = {}
    for item in contexts:
        sector = str(item["sector"])
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        emissions = float(item["emissions"])
        item["emissions_tier"] = "low" if emissions <= q33 else ("mid" if emissions <= q67 else "high")
    return {
        "records": contexts,
        "source_path": str(path.relative_to(ROOT).as_posix()) if path.is_relative_to(ROOT) else str(path),
        "source_record_count": len(contexts),
        "sector_counts": dict(sorted(sector_counts.items())),
        "emissions_tier_thresholds_mtco2e": {"low_max": round(q33, 6), "mid_max": round(q67, 6)},
        "sampling_method": "Uniform sampling with replacement from public EPA sector/emissions records; facility identifiers and names are not copied.",
    }


def _case_rows(
    case_type: str,
    scenario_number: int,
    periods: int,
    rng: np.random.Generator,
    public_context: dict,
    start_year: int = DEFAULT_START_YEAR,
) -> list[dict]:
    case_index = CASE_TYPES.index(case_type)
    scenario_id = f"SCN-{case_index + 1:02d}-{scenario_number:03d}"
    facility_id = f"PLANT-{rng.integers(1, 13):02d}"
    chemistry = str(rng.choice(CHEMISTRIES))
    pack_mass = _clip(PACK_MASS_KG[chemistry] + rng.normal(0.0, 5.5), 360.0, 480.0)
    base_demand = float(rng.uniform(1800.0, 3600.0))
    context = public_context["records"][int(rng.integers(0, len(public_context["records"])))].copy()
    trend_profile = str(rng.choice(list(TREND_PROFILES), p=[item["weight"] for item in TREND_PROFILES.values()]))
    trend = TREND_PROFILES[trend_profile]
    context_tier = str(context["emissions_tier"])
    context_energy_factor = {"low": 0.96, "mid": 1.00, "high": 1.06}[context_tier]
    quality_pressure = 0.18 if case_type == "quality_degradation" else 0.0
    scrap_pressure = 0.055 if case_type == "scrap_spike" else 0.0
    demand_factor = {
        "seasonal_peak": 1.28,
        "demand_downturn": 0.64,
        "return_surge": 1.04,
        "service_infeasible": 1.20,
    }.get(case_type, 1.0)
    return_factor = 1.85 if case_type == "return_surge" else (0.78 if case_type == "demand_downturn" else 1.0)
    rows: list[dict] = []

    for period in range(1, periods + 1):
        trend_index = period - 1
        demand_trend = (1.0 + float(trend["annual_demand_growth"])) ** trend_index
        return_trend = (1.0 + float(trend["annual_return_growth"])) ** trend_index
        price_trend = (1.0 + float(trend["annual_material_price_growth"])) ** trend_index
        season = 1.0 + 0.14 * math.sin(2.0 * math.pi * (period - 1) / max(periods, 1))
        demand = max(250.0, base_demand * demand_factor * demand_trend * season * rng.lognormal(0.0, 0.045))

        if case_type == "service_infeasible":
            regular_capacity = demand * rng.uniform(0.70, 0.88)
            overtime_capacity = demand * rng.uniform(0.03, 0.08)
        else:
            capacity_buffer = rng.uniform(0.06, 0.20)
            if case_type == "seasonal_peak":
                capacity_buffer *= 0.55
            regular_capacity = demand * (1.0 + capacity_buffer)
            overtime_capacity = demand * rng.uniform(0.08, 0.20)
        service_gap = max(0.0, demand - regular_capacity - overtime_capacity)
        production = min(demand * rng.uniform(0.985, 1.02), regular_capacity + overtime_capacity)

        eol_returns = demand * rng.uniform(0.10, 0.28) * return_factor * return_trend
        if trend_profile == "recycling_feedstock_lag":
            eol_returns *= 0.92
        collection_rate = rng.uniform(0.82, 0.95)
        if case_type == "transport_disruption":
            collection_rate -= rng.uniform(0.10, 0.20)
        collection_rate = _clip(collection_rate, 0.60, 0.98)

        soh = _clip(rng.normal(0.79, 0.085) - quality_pressure - 0.015 * (period / periods), 0.30, 0.98)
        damage = _clip(rng.beta(2.0, 8.0) + quality_pressure * 0.55 + rng.normal(0.0, 0.018), 0.0, 0.98)
        cycles = max(50.0, rng.normal(850.0, 280.0) * (1.0 + 0.55 * (1.0 - soh)))
        temperature = _clip(rng.normal(25.0, 7.0) + (10.0 if case_type == "quality_degradation" else 0.0), -20.0, 55.0)
        quality_score = _clip(0.72 * soh - 0.48 * damage + 0.12 * (1.0 - min(abs(temperature - 25.0) / 40.0, 1.0)), 0.0, 1.0)
        quality_grade = "A" if quality_score >= 0.62 else ("B" if quality_score >= 0.40 else "C")

        grade_a = _clip(0.20 + 0.48 * quality_score + rng.normal(0.0, 0.025), 0.06, 0.62)
        grade_c = _clip(0.52 - 0.40 * quality_score + rng.normal(0.0, 0.025), 0.12, 0.82)
        if grade_a + grade_c > 0.92:
            grade_c = 0.92 - grade_a
        grade_b = 1.0 - grade_a - grade_c
        if grade_b < 0.06:
            grade_b = 0.06
            grade_c = 1.0 - grade_a - grade_b

        recycle_yield = _clip(0.91 - 0.12 * damage - (0.06 if case_type == "material_shortage" else 0.0) + rng.normal(0.0, 0.018), 0.62, 0.97)
        reman_yield = _clip(0.85 + 0.10 * (soh - 0.75) - 0.14 * damage + rng.normal(0.0, 0.018), 0.55, 0.96)
        second_life_share = _clip(0.05 + 0.23 * grade_a + rng.normal(0.0, 0.012), 0.02, 0.30)
        reman_eligible = _clip(0.12 + 0.48 * (0.65 * grade_a + 0.35 * grade_b) + rng.normal(0.0, 0.02), 0.04, 0.55)
        if case_type == "reman_eligibility_low":
            reman_eligible = _clip(reman_eligible * 0.40, 0.02, 0.25)

        pathway_draw = rng.random()
        if quality_grade == "A" and pathway_draw < 0.48:
            pathway = "second_life"
        elif quality_grade in {"A", "B"} and pathway_draw < 0.78:
            pathway = "remanufacture"
        elif pathway_draw < 0.97:
            pathway = "recycle"
        else:
            pathway = "disposal"

        material_price = _clip(rng.lognormal(0.0, 0.10) * price_trend * (1.42 if case_type == "material_shortage" else 1.0), 0.70, 2.10)
        transport_distance = _clip(rng.normal(460.0, 210.0) * (2.25 if case_type == "transport_disruption" else 1.0), 20.0, 2000.0)
        facility_available = 0 if case_type == "facility_outage" and rng.random() < 0.42 else 1
        facility_uptime = _clip(rng.normal(0.985, 0.008) if facility_available else rng.uniform(0.62, 0.84), 0.60, 0.999)
        energy = _clip(rng.normal(315.0, 34.0) * context_energy_factor * (1.0 + min(scrap_pressure, 0.08)), 220.0, 600.0)
        grid_factor = 1.72 if case_type == "grid_carbon_spike" else 1.0
        grid_carbon = _clip(rng.normal(0.38, 0.11) * grid_factor, 0.05, 0.95)
        scrap_rate = _clip(rng.normal(0.038, 0.006) + scrap_pressure + 0.008 * (1.0 - facility_uptime) + 0.004 * (1.0 - soh), 0.01, 0.12)
        recycled_content = _clip(rng.normal(0.30, 0.09) - (0.10 if case_type == "material_shortage" else 0.0), 0.0, 0.60)
        safety_stock = demand * rng.uniform(0.04, 0.12)
        recovered = eol_returns * pack_mass * collection_rate * (1.0 - second_life_share) * max(recycle_yield, reman_yield) * facility_available
        data_quality_state = "IMPUTATION_REQUIRED" if case_type == "quality_degradation" and period in {3, 7} else "COMPLETE"
        imputation_required = int(data_quality_state == "IMPUTATION_REQUIRED")

        rows.append({
            "record_id": f"OBS-{len(rows) + 1:05d}-{scenario_id}",
            "scenario_id": scenario_id,
            "period": period,
            "facility_id": facility_id,
            "public_context_sector": context["sector"],
            "public_context_emissions_tier": context_tier,
            "trend_profile": trend_profile,
            "period_year": start_year + period - 1,
            "case_type": case_type,
            "chemistry": chemistry,
            "pack_mass_kg": _round(pack_mass, 3),
            "demand_packs": _round(demand, 3),
            "demand_kg": _round(demand * pack_mass, 3),
            "production_packs": _round(production, 3),
            "regular_capacity_packs": _round(regular_capacity, 3),
            "overtime_capacity_packs": _round(overtime_capacity, 3),
            "service_gap_packs": _round(service_gap, 3),
            "eol_returns_packs": _round(eol_returns, 3),
            "eol_returns_kg": _round(eol_returns * pack_mass, 3),
            "collection_rate": _round(collection_rate, 6),
            "grade_A_share": _round(grade_a, 6),
            "grade_B_share": _round(grade_b, 6),
            "grade_C_share": _round(grade_c, 6),
            "soh": _round(soh, 6),
            "cycles": _round(cycles, 3),
            "damage_index": _round(damage, 6),
            "temperature_c": _round(temperature, 3),
            "recovery_quality_score": _round(quality_score, 6),
            "quality_grade": quality_grade,
            "pathway": pathway,
            "recycle_yield": _round(recycle_yield, 6),
            "reman_yield": _round(reman_yield, 6),
            "second_life_share": _round(second_life_share, 6),
            "reman_eligible_share": _round(reman_eligible, 6),
            "expected_recovered_kg": _round(recovered, 3),
            "recycled_content_share": _round(recycled_content, 6),
            "material_price_index": _round(material_price, 6),
            "transport_distance_km": _round(transport_distance, 3),
            "facility_available": facility_available,
            "facility_uptime": _round(facility_uptime, 6),
            "energy_kwh_per_pack": _round(energy, 3),
            "grid_kgco2e_per_kwh": _round(grid_carbon, 6),
            "scrap_rate": _round(scrap_rate, 6),
            "safety_stock_packs": _round(safety_stock, 3),
            "imputation_required": imputation_required,
            "data_quality_state": data_quality_state,
        })
    return rows


def generate_dataset(
    output: Path,
    *,
    rows_per_case: int = 1000,
    periods: int = 10,
    seed: int = SEED,
    public_reference: Path = DEFAULT_PUBLIC_REFERENCE,
    start_year: int = DEFAULT_START_YEAR,
) -> dict:
    if rows_per_case < 1 or periods < 1:
        raise ValueError("rows_per_case and periods must be positive")
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    public_context = _load_public_context(public_reference)
    observations: list[dict] = []
    for case_type in CASE_TYPES:
        for scenario_number in range(1, rows_per_case + 1):
            scenario_rows = _case_rows(case_type, scenario_number, periods, rng, public_context, start_year)
            for row_number, row in enumerate(scenario_rows, start=1):
                row["record_id"] = f"OBS-{len(observations) + 1:05d}-{row['scenario_id']}-P{row_number:02d}"
                observations.append(row)

    cases = [
        {
            "case_type": case,
            "description": CASE_DESCRIPTIONS[case],
            "expected_behavior": {
                "service_infeasible": "positive_service_gap",
                "facility_outage": "facility_available_zero_present",
                "quality_degradation": "lower_quality_and_imputation_flags",
                "transport_disruption": "higher_transport_distance",
                "return_surge": "higher_return_ratio",
            }.get(case, "bounded_complete_rows"),
        }
        for case in CASE_TYPES
    ]
    adversarial = [
        {"case_id": "NEG-001", "case_type": "missing_required_value", "field": "collection_rate", "raw_value": "", "expected_validator_result": "FAIL"},
        {"case_id": "NEG-002", "case_type": "fraction_out_of_range", "field": "recycle_yield", "raw_value": "1.25", "expected_validator_result": "FAIL"},
        {"case_id": "NEG-003", "case_type": "non_finite_numeric", "field": "demand_packs", "raw_value": "NaN", "expected_validator_result": "FAIL"},
        {"case_id": "NEG-004", "case_type": "duplicate_record_id", "field": "record_id", "raw_value": "OBS-00001", "expected_validator_result": "FAIL"},
        {"case_id": "NEG-005", "case_type": "service_capacity_violation", "field": "service_gap_packs", "raw_value": "-50", "expected_validator_result": "FAIL"},
        {"case_id": "NEG-006", "case_type": "invalid_facility_flag", "field": "facility_available", "raw_value": "2", "expected_validator_result": "FAIL"},
    ]
    _write_csv(output / "observations.csv", OBSERVATION_COLUMNS, observations)
    _write_csv(output / "case_catalog.csv", ("case_type", "description", "expected_behavior"), cases)
    _write_csv(output / "adversarial_cases.csv", ("case_id", "case_type", "field", "raw_value", "expected_validator_result"), adversarial)

    files = {}
    for name in ("observations.csv", "case_catalog.csv", "adversarial_cases.csv"):
        path = output / name
        files[name] = {"rows": sum(1 for _ in path.open("r", encoding="utf-8")) - 1, "sha256": _sha256(path), "bytes": path.stat().st_size}
    manifest = {
        "dataset_name": "CIRCULAR_ENTERPRISE_SYNTHETIC_120K",
        "schema_version": "1.1",
        "evidence_class": "SYNTHETIC VALIDATION",
        "seed": seed,
        "as_of_utc": AS_OF_UTC,
        "canonical_observation_rows": len(observations),
        "case_count": len(CASE_TYPES),
        "periods_per_scenario": periods,
        "scenarios_per_case": rows_per_case,
        "source_basis": [
            "https://www.epa.gov/ghgreporting/data-sets",
            "https://greet.anl.gov/greet_battcf",
            "https://www.energy.gov/cmei/vehicles/articles/fotw-1350-july-8-2024-2023-united-states-had-battery-recycling-facilities",
            "https://www.iea.org/reports/global-ev-outlook-2026/electric-vehicle-batteries",
            "https://www.eia.gov/consumption/manufacturing/",
        ],
        "lineage": {
            "source_system": "deterministic-synthetic-generator",
            "source_owner": "circular-engineering",
            "facility_id": "synthetic-multi-facility",
            "as_of_utc": AS_OF_UTC,
            "data_classification": "synthetic-validation",
        },
        "files": files,
        "case_types": list(CASE_TYPES),
        "public_context_profile": {key: value for key, value in public_context.items() if key != "records"},
        "trend_profiles": TREND_PROFILES,
        "trend_horizon": {"start_year": start_year, "periods": periods, "interpretation": "bounded scenario stress horizon, not a forecast"},
        "claim_boundary": "Synthetic rows are for software, optimization, robustness, and training-pipeline validation. They are not plant telemetry, measured emissions, or realized-benefit evidence.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--rows-per-case", type=int, default=1000)
    parser.add_argument("--periods", type=int, default=10)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--public-reference", type=Path, default=DEFAULT_PUBLIC_REFERENCE)
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    args = parser.parse_args()
    manifest = generate_dataset(
        args.out,
        rows_per_case=args.rows_per_case,
        periods=args.periods,
        seed=args.seed,
        public_reference=args.public_reference,
        start_year=args.start_year,
    )
    print(f"SYNTHETIC_DATASET path={args.out.resolve()} rows={manifest['canonical_observation_rows']} cases={manifest['case_count']} seed={manifest['seed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
