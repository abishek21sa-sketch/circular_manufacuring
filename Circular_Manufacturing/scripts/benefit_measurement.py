"""Validate and summarize baseline-versus-observed pilot benefit measurements."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_COLUMNS = {"period", "metric", "baseline_value", "observed_value", "unit", "aggregation", "source_ref"}
METRIC_DEFINITIONS = {
    "service_level": {"unit": "fraction", "direction": "higher", "aggregation": "mean"},
    "cost_usd": {"unit": "USD", "direction": "lower", "aggregation": "sum"},
    "recovery_rate": {"unit": "fraction", "direction": "higher", "aggregation": "mean"},
    "emissions_kgco2e": {"unit": "kgCO2e", "direction": "lower", "aggregation": "sum"},
    "virgin_material_kg": {"unit": "kg", "direction": "lower", "aggregation": "sum"},
    "circularity_rate": {"unit": "fraction", "direction": "higher", "aggregation": "mean"},
}


def _number(value: Any) -> float:
    result = float(str(value).strip())
    if not math.isfinite(result):
        raise ValueError("value must be finite")
    return result


def build_measurement_report(records: Iterable[dict[str, Any]], *, baseline_id: str = "") -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    for row_number, row in enumerate(records, start=2):
        missing = sorted(REQUIRED_COLUMNS - set(row))
        if missing:
            errors.append({"row": row_number, "reason": "missing_columns", "columns": missing})
            continue
        metric = str(row.get("metric", "")).strip()
        definition = METRIC_DEFINITIONS.get(metric)
        if definition is None:
            errors.append({"row": row_number, "reason": "unsupported_metric", "metric": metric})
            continue
        try:
            baseline = _number(row["baseline_value"])
            observed = _number(row["observed_value"])
        except (TypeError, ValueError) as exc:
            errors.append({"row": row_number, "reason": "invalid_numeric_value", "detail": str(exc)})
            continue
        unit = str(row.get("unit", "")).strip()
        aggregation = str(row.get("aggregation", "")).strip().lower()
        source_ref = str(row.get("source_ref", "")).strip()
        if unit != definition["unit"]:
            errors.append({"row": row_number, "reason": "unit_mismatch", "expected": definition["unit"], "actual": unit})
        if aggregation != definition["aggregation"]:
            errors.append({"row": row_number, "reason": "aggregation_mismatch", "expected": definition["aggregation"], "actual": aggregation})
        if not source_ref:
            errors.append({"row": row_number, "reason": "missing_source_ref"})
        if definition["unit"] == "fraction" and not (0 <= baseline <= 1 and 0 <= observed <= 1):
            errors.append({"row": row_number, "reason": "fraction_out_of_range"})
        normalized.append({"period": str(row["period"]).strip(), "metric": metric, "baseline": baseline, "observed": observed, "aggregation": aggregation, "direction": definition["direction"], "unit": unit, "source_ref": source_ref})

    summary: list[dict[str, Any]] = []
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in normalized:
        grouped[row["metric"]].append(row)
    for metric, rows in sorted(grouped.items()):
        aggregation = rows[0]["aggregation"]
        if aggregation == "sum":
            baseline = sum(row["baseline"] for row in rows)
            observed = sum(row["observed"] for row in rows)
        else:
            baseline = sum(row["baseline"] for row in rows) / len(rows)
            observed = sum(row["observed"] for row in rows) / len(rows)
        direction = rows[0]["direction"]
        delta = observed - baseline
        improvement = delta if direction == "higher" else -delta
        summary.append({"metric": metric, "unit": rows[0]["unit"], "period_count": len(rows), "aggregation": aggregation, "baseline": baseline, "observed": observed, "delta_observed_minus_baseline": delta, "improvement": improvement, "improvement_pct": None if baseline == 0 else improvement / abs(baseline) * 100})

    valid = bool(normalized) and not errors
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if valid else "BLOCKED",
        "baseline_id": baseline_id.strip(),
        "row_count": len(normalized),
        "errors": errors,
        "summary": summary,
        "evidence_class": "REALIZED_PILOT_MEASUREMENT" if valid else "PENDING_EXTERNAL_VALIDATION",
        "claim_boundary": (
            "This report calculates baseline-versus-observed deltas from supplied records. "
            "It does not independently validate the source system, causal attribution, or business approval."
        ),
    }


def _read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--baseline-id", required=True)
    parser.add_argument("--out", type=Path, default=Path("artifacts/benefit_measurement.json"))
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = build_measurement_report(_read_csv(args.input), baseline_id=args.baseline_id)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"BENEFIT_MEASUREMENT status={report['status']} rows={report['row_count']}")
    return 0 if report["status"] == "PASS" or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
