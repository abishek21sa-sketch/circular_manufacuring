from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.production_attestations import BLOCKER_DEFINITIONS, validate_attestations


ROOT = Path(__file__).resolve().parents[1]


def test_default_production_attestations_are_explicitly_blocked():
    report = validate_attestations(ROOT)

    assert report["status"] == "BLOCKED"
    assert report["passed"] is False
    assert {item["id"] for item in report["attestations"]} == set(BLOCKER_DEFINITIONS)
    assert all(item["status"] == "PENDING" for item in report["attestations"])


def test_approved_attestations_require_matching_evidence_hash_and_metadata(tmp_path):
    evidence = tmp_path / "approved-evidence.txt"
    evidence.write_text("approved by an external control owner\n", encoding="utf-8")
    evidence_hash = hashlib.sha256(evidence.read_bytes()).hexdigest()
    attestations = [
        {
            "id": blocker_id,
            "status": "APPROVED",
            "evidence_ref": "approved-evidence.txt",
            "evidence_sha256": evidence_hash,
            "approved_by": "control-owner@example.invalid",
            "approved_at_utc": "2026-09-05T12:00:00+00:00",
        }
        for blocker_id in BLOCKER_DEFINITIONS
    ]
    register = tmp_path / "register.json"
    register.write_text(json.dumps({"attestations": attestations}), encoding="utf-8")

    report = validate_attestations(tmp_path, register)

    assert report["status"] == "PASS"
    assert report["passed"] is True
    assert all(item["status"] == "PASS" for item in report["attestations"])


def test_approved_attestation_with_tampered_evidence_does_not_pass(tmp_path):
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("original\n", encoding="utf-8")
    register = tmp_path / "register.json"
    register.write_text(
        json.dumps(
            {
                "attestations": [
                    {
                        "id": blocker_id,
                        "status": "APPROVED",
                        "evidence_ref": "evidence.txt",
                        "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                        "approved_by": "control-owner@example.invalid",
                        "approved_at_utc": "2026-09-05T12:00:00+00:00",
                    }
                    for blocker_id in BLOCKER_DEFINITIONS
                ]
            }
        ),
        encoding="utf-8",
    )
    evidence.write_text("tampered\n", encoding="utf-8")

    report = validate_attestations(tmp_path, register)

    assert report["status"] == "BLOCKED"
    tampered = next(item for item in report["attestations"] if item["id"] == next(iter(BLOCKER_DEFINITIONS)))
    assert "evidence_sha256 does not match the referenced file" in tampered["issues"]


def test_approved_attestation_rejects_templates_and_naive_approval_time(tmp_path):
    template = tmp_path / "data" / "templates" / "placeholder.md"
    template.parent.mkdir(parents=True)
    template.write_text("template only\n", encoding="utf-8")
    evidence_hash = hashlib.sha256(template.read_bytes()).hexdigest()
    attestations = [
        {
            "id": blocker_id,
            "status": "APPROVED",
            "evidence_ref": "data/templates/placeholder.md",
            "evidence_sha256": evidence_hash,
            "approved_by": "control-owner@example.invalid",
            "approved_at_utc": "2026-09-05T12:00:00",
        }
        for blocker_id in BLOCKER_DEFINITIONS
    ]
    register = tmp_path / "register.json"
    register.write_text(json.dumps({"attestations": attestations}), encoding="utf-8")

    report = validate_attestations(tmp_path, register)

    assert report["status"] == "BLOCKED"
    assert all(any("repository template" in issue for issue in item["issues"]) for item in report["attestations"])
    assert all(any("ISO-8601 timestamp" in issue for issue in item["issues"]) for item in report["attestations"])
