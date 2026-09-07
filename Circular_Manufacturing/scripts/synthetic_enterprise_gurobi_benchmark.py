"""Solve a case-stratified synthetic benchmark through the Gurobi backend."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

from circular4x.signature_algorithm import CircularMassConfig, CircularMassScenario, RecoveryFacility, solve_circular_mass


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "data" / "synthetic" / "enterprise_120k"
DEFAULT_OUT = ROOT / "artifacts" / "synthetic_enterprise_gurobi_validation.json"


def _display_path(path: Path) -> str:
    """Return repository-relative evidence paths when possible."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _load_rows(path: Path) -> list[dict[str, str]]:
    with (path / "observations.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def run_benchmark(dataset: Path | str) -> dict:
    dataset = Path(dataset)
    rows = _load_rows(dataset)
    grouped: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["case_type"]].append(row)
    total = sum(len(items) for items in grouped.values())
    scenarios = []
    for case_type in sorted(grouped):
        items = grouped[case_type]
        demand = sum(float(row["demand_kg"]) for row in items) / len(items)
        recycle = sum(float(row["recycle_yield"]) for row in items) / len(items)
        reman = sum(float(row["reman_yield"]) for row in items) / len(items)
        availability = sum(float(row["facility_available"]) for row in items) / len(items)
        scenarios.append(CircularMassScenario(
            name=case_type,
            probability=len(items) / total,
            demand_kg=demand,
            yields=(recycle, reman, max(0.55, min(0.96, 0.5 * recycle + 0.5 * reman)),),
        ))

    config = CircularMassConfig(
        facilities=(
            RecoveryFacility("Synthetic-Recycle-East", 2_000_000.0, 180_000.0, 2.20),
            RecoveryFacility("Synthetic-Reman-Midwest", 1_600_000.0, 210_000.0, 1.85),
            RecoveryFacility("Synthetic-Recovery-West", 1_800_000.0, 160_000.0, 2.45),
        ),
        min_recycled_content=0.18,
        max_virgin_share=0.86,
        risk_alpha=0.90,
        risk_aversion=0.30,
        solver_backend="gurobi",
    )
    solution = solve_circular_mass(scenarios, config)
    checks = {
        "backend_is_gurobi": solution.solver == "gurobi",
        "status_optimal": solution.status == "OPTIMAL",
        "zero_mip_gap": solution.mip_gap is not None and solution.mip_gap <= 1e-9,
        "feasible": solution.max_constraint_violation <= 1e-6,
        "case_stratified_scenarios": len(scenarios) == 12,
        "probabilities_close": abs(sum(s.probability for s in scenarios) - 1.0) <= 1e-9,
    }
    return {
        "schema_version": "1.0",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "dataset": _display_path(dataset),
        "input_rows": len(rows),
        "scenario_count": len(scenarios),
        "solver": solution.solver,
        "requested_license_policy": "Academic Gurobi for research/engineering validation only; commercial production authorization remains external.",
        "checks": checks,
        "solution": solution.to_dict(),
        "claim_boundary": "This is a synthetic Gurobi formulation benchmark. It is not a commercial-license approval, plant-performance result, or realized-benefit claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = run_benchmark(args.dataset)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"SYNTHETIC_GUROBI_BENCHMARK status={report['status']} rows={report['input_rows']} scenarios={report['scenario_count']} solver={report['solver']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
