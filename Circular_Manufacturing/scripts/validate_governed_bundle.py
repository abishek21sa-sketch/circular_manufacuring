"""Validate a scenario bundle's schema, data quality, and lineage controls."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from circular_battery.ingestion.governance import inspect_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--require-lineage", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = inspect_bundle(args.directory, require_lineage=args.require_lineage)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        f"GOVERNED_BUNDLE ingestion_id={report['ingestion_id']} "
        f"validation={report['validation_status']} "
        f"governance={report['governance_status']} "
        f"accepted={report['accepted_for_optimization']}"
    )
    return 0 if report["accepted_for_optimization"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
