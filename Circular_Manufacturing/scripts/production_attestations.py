"""Validate the evidence register required for commercial production."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


REGISTER = Path("artifacts/production_attestations.json")
FORBIDDEN_APPROVED_REFS = {
    "artifacts/production_attestations.json",
    "artifacts/production_attestation_validation.json",
    "artifacts/release_readiness.json",
}

BLOCKER_DEFINITIONS: dict[str, dict[str, str]] = {
    "commercial_gurobi_entitlement": {
        "owner": "commercial licensing / platform operations",
        "exit_criteria": "document a commercial Gurobi entitlement and production deployment authorization",
        "evidence_boundary": "a redacted authorization record is required; license credentials must never be committed",
    },
    "enterprise_identity_and_transport": {
        "owner": "deployment security",
        "exit_criteria": "deploy behind approved IAM/RBAC, TLS termination, secret management, audit retention, and network controls",
        "evidence_boundary": "an approved architecture and deployment verification record are required",
    },
    "field_calibration_and_data_lineage": {
        "owner": "operations engineering / data governance",
        "exit_criteria": "approve source data lineage, calibrate recovery/yield/cost assumptions, and complete backtesting with governed plant data",
        "evidence_boundary": "plant data must be governed and its validation record must be independently reviewable",
    },
    "realized_benefit_validation": {
        "owner": "business owner / finance / sustainability",
        "exit_criteria": "measure and approve realized service, cost, recovery, emissions, and circularity outcomes against a controlled baseline",
        "evidence_boundary": "benefits must be measured against an approved baseline; synthetic projections do not qualify",
    },
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(value: Any) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value.strip())
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def _valid_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def validate_attestations(
    root: Path,
    register_path: Path = REGISTER,
) -> dict[str, Any]:
    """Return a safe, machine-readable validation result for the register."""

    path = register_path if register_path.is_absolute() else root / register_path
    issues: list[str] = []
    raw: dict[str, Any] = {}
    if not path.is_file():
        issues.append(f"missing {register_path.as_posix()}")
    else:
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                raw = loaded
            else:
                issues.append("register root must be a JSON object")
        except (OSError, json.JSONDecodeError) as exc:
            issues.append(f"unreadable register: {type(exc).__name__}")

    supplied = raw.get("attestations") if isinstance(raw, dict) else None
    supplied_by_id = {
        item.get("id"): item
        for item in supplied
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(supplied, list) else {}

    results: list[dict[str, Any]] = []
    for blocker_id, definition in BLOCKER_DEFINITIONS.items():
        item = supplied_by_id.get(blocker_id, {})
        status = str(item.get("status", "PENDING")).upper()
        item_issues: list[str] = []
        evidence_ref = item.get("evidence_ref")
        evidence_hash = item.get("evidence_sha256")
        if status != "APPROVED":
            item_issues.append("attestation status is not APPROVED")
        evidence_path = _safe_relative_path(evidence_ref)
        if status == "APPROVED" and evidence_path is None:
            item_issues.append("approved attestation requires a safe relative evidence_ref")
        if status == "APPROVED" and evidence_path is not None:
            evidence_ref_posix = evidence_path.as_posix()
            if evidence_ref_posix in FORBIDDEN_APPROVED_REFS:
                item_issues.append("approved evidence cannot reference a generated register or readiness report")
            if evidence_path.parts[:2] == ("data", "templates"):
                item_issues.append("approved evidence cannot reference a repository template")
            absolute_evidence = root / evidence_path
            if not absolute_evidence.is_file():
                item_issues.append("referenced evidence file is missing")
            elif not isinstance(evidence_hash, str) or _sha256(absolute_evidence).lower() != evidence_hash.lower():
                item_issues.append("evidence_sha256 does not match the referenced file")
        if status == "APPROVED" and (
            not isinstance(item.get("approved_by"), str) or not item.get("approved_by", "").strip()
        ):
            item_issues.append("approved_by is required")
        if status == "APPROVED" and not _valid_timestamp(item.get("approved_at_utc")):
            item_issues.append("approved_at_utc must be an ISO-8601 timestamp")
        passed = status == "APPROVED" and not item_issues
        results.append(
            {
                "id": blocker_id,
                "status": "PASS" if passed else "PENDING",
                "owner": definition["owner"],
                "exit_criteria": definition["exit_criteria"],
                "evidence_boundary": definition["evidence_boundary"],
                "evidence_ref": evidence_ref,
                "approved_by": item.get("approved_by"),
                "approved_at_utc": item.get("approved_at_utc"),
                "issues": item_issues,
            }
        )

    unknown_ids = sorted(set(supplied_by_id) - set(BLOCKER_DEFINITIONS))
    if unknown_ids:
        issues.append("unknown attestation ids: " + ", ".join(unknown_ids))
    passed = not issues and all(item["status"] == "PASS" for item in results)
    return {
        "schema_version": "1.0",
        "status": "PASS" if passed else "BLOCKED",
        "passed": passed,
        "attestations": results,
        "unknown_attestation_ids": unknown_ids,
        "register_issues": issues,
        "claim_boundary": (
            "This validator checks evidence references, hashes, and approval metadata. "
            "It cannot independently establish the truth of an external authorization, "
            "security approval, plant-data result, or business-benefit claim."
        ),
    }
