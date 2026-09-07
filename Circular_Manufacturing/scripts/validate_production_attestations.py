"""Validate the commercial-production evidence register without exposing secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from scripts.production_attestations import REGISTER, validate_attestations
except ModuleNotFoundError:  # direct CLI execution from the repository root
    from production_attestations import REGISTER, validate_attestations


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=REGISTER)
    parser.add_argument("--out", type=Path, default=Path("artifacts/production_attestation_validation.json"))
    parser.add_argument("--strict", action="store_true", help="return non-zero while any attestation is pending")
    args = parser.parse_args()
    report = validate_attestations(ROOT, args.input)
    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    passed = sum(item["status"] == "PASS" for item in report["attestations"])
    total = len(report["attestations"])
    print(f"PRODUCTION_ATTESTATIONS status={report['status']} passed={passed}/{total}")
    return 0 if report["passed"] or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
