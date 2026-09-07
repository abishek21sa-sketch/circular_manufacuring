from __future__ import annotations
import math
from circular_battery.platform.errors import ValidationError

def _finite_number(value, field: str, *, integer: bool = False):
    if isinstance(value, bool):
        raise ValidationError(f"{field} must be numeric.")
    try:
        x = int(value) if integer else float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be numeric.") from exc
    if not math.isfinite(float(x)):
        raise ValidationError(f"{field} must be finite.")
    return x

def validate_decision_run_config(payload: dict | None) -> dict:
    payload = dict(payload or {})
    allowed = {"name","seed","raw_n","reduced_k","include_sensitivity","notes"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValidationError("Unknown decision-run fields.", details={"unknown_fields":unknown})

    name = str(payload.get("name","Decision run")).strip()
    if not name or len(name) > 120:
        raise ValidationError("name must contain 1–120 characters.")

    seed = _finite_number(payload.get("seed",20260817),"seed",integer=True)
    raw_n = _finite_number(payload.get("raw_n",60),"raw_n",integer=True)
    reduced_k = _finite_number(payload.get("reduced_k",8),"reduced_k",integer=True)
    include_sensitivity = payload.get("include_sensitivity",True)
    if not isinstance(include_sensitivity,bool):
        raise ValidationError("include_sensitivity must be boolean.")
    notes = str(payload.get("notes","")).strip()
    if len(notes) > 4000:
        raise ValidationError("notes must be <= 4000 characters.")
    if not 20 <= raw_n <= 500:
        raise ValidationError("raw_n must be between 20 and 500.")
    if not 3 <= reduced_k <= min(raw_n,40):
        raise ValidationError("reduced_k must be between 3 and min(raw_n, 40).")
    return {
        "name":name,"seed":seed,"raw_n":raw_n,"reduced_k":reduced_k,
        "include_sensitivity":include_sensitivity,"notes":notes,
    }
