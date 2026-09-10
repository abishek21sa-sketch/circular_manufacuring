from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from circular_battery.optimization.signature_algorithm import reference_problem, solve_circular_mass
from circular_battery.paths import find_repo_root

ROOT = find_repo_root()


def _evidence_artifact() -> dict[str, Any] | None:
    path = ROOT / "artifacts" / "circular_mass" / "evidence.json"
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _decision_id(payload: dict[str, Any]) -> str:
    # Runtime, best-bound and solver-message fields are useful evidence but are
    # volatile measurements. Exclude them from the decision fingerprint so the
    # same governed inputs and mathematical result receive the same ID.
    solution = payload.get("solution", {})
    stable_solution = {
        key: value
        for key, value in solution.items()
        if key not in {"runtime_seconds", "best_bound", "mip_gap", "diagnostics"}
    }
    fingerprint = {
        "algorithm": payload.get("algorithm"),
        "requested_policy": payload.get("requested_policy"),
        "decision_gate": payload.get("decision_gate"),
        "checks": payload.get("checks"),
        "solution": stable_solution,
    }
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "CMASS-" + hashlib.sha256(canonical).hexdigest()[:16].upper()


def build_circular_mass_decision(
    *,
    min_recycled_content: float = 0.20,
    risk_aversion: float = 0.35,
    max_virgin_share: float = 0.72,
) -> dict[str, Any]:
    """Run CIRCULAR-MASS and wrap the optimization in a release/readiness gate.

    The gate is deliberately engineering-oriented. It proves that the reference
    formulation has evidence, is feasible, and respects the requested circularity
    policy; it does not claim field-calibrated environmental or financial benefit.
    """
    if not 0.0 <= min_recycled_content <= 1.0:
        raise ValueError("min_recycled_content must be in [0,1]")
    if not math.isfinite(risk_aversion) or risk_aversion < 0.0:
        raise ValueError("risk_aversion must be finite and nonnegative")
    if not 0.0 <= max_virgin_share <= 1.0:
        raise ValueError("max_virgin_share must be in [0,1]")

    scenarios, cfg = reference_problem(
        risk_aversion=float(risk_aversion),
        min_recycled_content=float(min_recycled_content),
    )
    cfg = replace(cfg, max_virgin_share=float(max_virgin_share))
    solution = solve_circular_mass(scenarios, cfg)
    evidence = _evidence_artifact()

    checks = {
        "validation_artifact_present": evidence is not None,
        "validation_artifact_passed": bool(evidence and all(evidence.get("checks", {}).values())),
        "solver_optimal": solution.status == "OPTIMAL",
        "mass_balance_feasible": solution.max_constraint_violation <= 1e-6,
        "recycled_content_policy_met": solution.recycled_content_share + 1e-8 >= min_recycled_content,
        "service_shortage_zero": solution.expected_shortage_kg <= 1e-6,
        "cvar_variables_reported": (
            solution.diagnostics is not None
            and solution.diagnostics.get("eta_domain") == "R"
            and len(solution.scenario_details or []) == len(scenarios)
        ),
        "objective_reconciles": bool(
            solution.diagnostics
            and solution.diagnostics.get("objective_reconciliation_error", float("inf")) <= 1e-5
        ),
    }
    authorized = all(checks.values())
    gate = "AUTHORIZED" if authorized else "BLOCKED"

    facility_actions = [
        {
            "facility": name,
            "open": bool(solution.open_facilities[name]),
            "route_kg": solution.routed_kg[name],
        }
        for name in solution.routed_kg
    ]
    payload: dict[str, Any] = {
        "algorithm": "CIRCULAR-MASS",
        "decision_object": "first-stage recovery routing and facility activation with scenario-wise virgin/shortage recourse",
        "decision_gate": gate,
        "human_review_required": True,
        "authorization": {
            "status": gate,
            "autonomous_execution": False,
            "review_owner": "qualified circular-manufacturing engineer",
            "required_before_release": ["verify source data lineage", "review binding constraints", "approve facility/sourcing action"],
        },
        "requested_policy": {
            "min_recycled_content": float(min_recycled_content),
            "risk_aversion": float(risk_aversion),
            "max_virgin_share": float(max_virgin_share),
        },
        "solution": solution.to_dict(),
        "facility_actions": facility_actions,
        "checks": checks,
        "scenario_probabilities": {s.name: s.probability for s in scenarios},
        "evidence": {
            "class": "DETERMINISTIC SYNTHETIC FORMULATION VALIDATION",
            "reference_artifact": "artifacts/circular_mass/evidence.json" if evidence else None,
            "reference_checks": evidence.get("checks") if evidence else None,
            "field_calibration": "PENDING",
            "realized_operational_benefits": "NOT CLAIMED",
        },
        "claim_boundary": "Synthetic optimized decision evidence only; no field-calibrated recovery yield, environmental benefit, financial benefit, or realized operational outcome is claimed.",
        "operator_message": (
            "Optimization is eligible for engineer review; no autonomous facility or sourcing action is issued."
            if authorized else
            "Optimization is blocked from promotion because one or more evidence/feasibility gates failed."
        ),
        "tail_risk_note": (
            "Reference scenarios have zero optimized shortage, so the CVaR shortage term is inactive in this run. "
            "Its formulation remains explicit and must be stress-tested under shortage-producing conditions before a tail-risk claim is promoted."
        ),
    }
    payload["decision_id"] = _decision_id(payload)
    return payload


def circular_mass_reference_payload() -> dict[str, Any]:
    scenarios, cfg = reference_problem()
    evidence = _evidence_artifact()
    return {
        "algorithm": "CIRCULAR-MASS",
        "formulation": {
            "decision_object": "recovery-facility use, routed recovery mass, virgin fallback, and scenario shortage",
            "objective": "recovery + facility + virgin + expected-shortage + CVaR-shortage cost",
            "loss_definition": "scenario shortage kg; CVaR is applied to shortage only",
            "variables": ["x_f routed recovery kg", "y_f facility activation binary", "v_s scenario virgin kg", "short_s scenario shortage kg", "w_s scenario surplus/spill kg", "eta VaR threshold in R", "u_s nonnegative CVaR excess kg"],
            "constraints": ["x_f <= capacity_f y_f", "recovered_s + v_s + short_s - w_s = demand_s", "recovered_s - w_s >= min_recycled_content demand_s", "short_s - eta <= u_s", "v_s <= max_virgin_share demand_s"],
            "risk_alpha": cfg.risk_alpha,
            "default_risk_aversion": cfg.risk_aversion,
            "default_min_recycled_content": cfg.min_recycled_content,
            "default_max_virgin_share": cfg.max_virgin_share,
        },
        "facilities": [asdict(f) for f in cfg.facilities],
        "scenarios": [asdict(s) for s in scenarios],
        "validation": evidence,
        "evidence_boundary": "Synthetic formulation evidence only; external lifecycle calibration and realized industrial outcomes remain pending.",
    }
