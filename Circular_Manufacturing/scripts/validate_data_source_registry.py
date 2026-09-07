"""Validate the source inventory and its explicit synthetic fallback policy."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "data" / "public" / "data_source_registry.json"
ALLOWED_STATUSES = {
    "integrated_reference",
    "candidate_context_only",
    "candidate_research_only",
    "discovery_only",
    "schema_only",
    "requires_subscription",
    "public_aggregate_only",
    "requires_contract",
}


def _display_path(path: Path) -> str:
    """Return repository-relative evidence paths when possible."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def validate_registry(path: Path | str) -> dict:
    registry_path = Path(path)
    errors: list[str] = []
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "source_count": 0, "errors": [f"registry: {exc}"]}
    if not isinstance(registry, dict):
        return {"status": "FAIL", "source_count": 0, "errors": ["registry root must be a JSON object"]}

    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
        sources = []

    ids: set[str] = set()
    integrated = 0
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"source {index} is not an object")
            continue
        source_id = str(source.get("source_id", "")).strip()
        status = str(source.get("status", "")).strip()
        if not source_id:
            errors.append(f"source {index} is missing source_id")
        elif source_id in ids:
            errors.append(f"duplicate source_id: {source_id}")
        ids.add(source_id)
        if status not in ALLOWED_STATUSES:
            errors.append(f"{source_id or index} has unsupported status: {status}")
        if not isinstance(source.get("data_role"), list) or not source["data_role"]:
            errors.append(f"{source_id or index} is missing data_role")
        if not str(source.get("limitation", "")).strip():
            errors.append(f"{source_id or index} is missing limitation")
        url = str(source.get("url", "")).strip()
        if url:
            parsed = urlparse(url)
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{source_id or index} url is not an HTTPS URL")
        if status == "integrated_reference":
            integrated += 1
            if source.get("usable_for_current_benchmark") is not True:
                errors.append(f"{source_id} integrated source must be usable_for_current_benchmark=true")

    fallback = registry.get("fallback_policy", {})
    if fallback.get("canonical_dataset") != "data/synthetic/enterprise_120k/":
        errors.append("fallback canonical_dataset is not the governed enterprise synthetic dataset")
    if fallback.get("row_count", 0) < 120000:
        errors.append("fallback dataset must declare at least 120,000 rows")
    if fallback.get("evidence_class") != "SYNTHETIC VALIDATION":
        errors.append("fallback dataset must remain labeled SYNTHETIC VALIDATION")
    if not str(registry.get("github_disclosure", "")).strip():
        errors.append("github_disclosure is required")

    checks = {
        "registry_json": not errors or bool(registry),
        "source_inventory_nonempty": bool(sources),
        "unique_source_ids": len(ids) == len(sources),
        "integrated_reference_declared": integrated >= 1,
        "synthetic_fallback_declared": fallback.get("evidence_class") == "SYNTHETIC VALIDATION" and fallback.get("row_count", 0) >= 120000,
        "github_disclosure_present": bool(str(registry.get("github_disclosure", "")).strip()),
    }
    passed = not errors and all(checks.values())
    return {
        "status": "PASS" if passed else "FAIL",
        "registry": _display_path(registry_path),
        "source_count": len(sources),
        "integrated_reference_count": integrated,
        "checks": checks,
        "errors": errors,
        "claim_boundary": "The registry describes access and evidence boundaries; it does not grant permission or prove source truth.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = validate_registry(args.registry)
    if args.out:
        output = args.out if args.out.is_absolute() else ROOT / args.out
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"DATA_SOURCE_REGISTRY status={report['status']} sources={report['source_count']} integrated={report['integrated_reference_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
