"""Validate a governed scenario bundle for non-synthetic pilot eligibility."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from circular_battery.ingestion.governance import inspect_bundle


ROOT = Path(__file__).resolve().parents[1]


def validate_pilot_bundle(directory: Path | str) -> dict[str, Any]:
    report = inspect_bundle(directory, require_lineage=True)
    lineage = report["lineage"]
    evidence_class = str(report.get("evidence_class", "")).strip().upper()
    synthetic_values = {"SYNTHETIC", "SYNTHETIC VALIDATION", "SYNTHETIC-VALIDATION", "REFERENCE-TEMPLATE", "SYNTHETIC-REFERENCE"}
    real_data_ok = all(
        str(lineage.get(field, "")).strip().upper() not in synthetic_values
        for field in ("source_system", "facility_id", "data_classification")
    ) and evidence_class not in synthetic_values
    report["checks"]["non_synthetic_pilot_evidence"] = {
        "status": "PASS" if real_data_ok else "BLOCKED",
        "detail": "lineage identifies an operational source and facility"
        if real_data_ok
        else "synthetic/reference lineage is not eligible for a plant pilot",
    }
    report["pilot_status"] = "PASS" if report["accepted_for_optimization"] and real_data_ok else "BLOCKED"
    report["pilot_eligible"] = report["pilot_status"] == "PASS"
    report["claim_boundary"] = (
        "Pilot eligibility validates schema, lineage declarations, and non-synthetic labels. "
        "It does not independently prove that a plant, supplier, or measurement source is truthful."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = validate_pilot_bundle(args.directory)
    if args.out:
        output = args.out if args.out.is_absolute() else ROOT / args.out
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PILOT_BUNDLE status={report['pilot_status']} eligible={report['pilot_eligible']}")
    return 0 if report["pilot_eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
