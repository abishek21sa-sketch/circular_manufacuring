from pathlib import Path
import sys, json
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from circular_battery.ai.runtime import runtime_phase2_payload

root = Path(__file__).resolve().parents[1]
out = runtime_phase2_payload()
path = root / "artifacts" / "phase2_ai_decision.json"
path.write_text(json.dumps(out, indent=2), encoding="utf-8")
state = out["predicted_state"]
consequence = out["engineering_consequence"]
print(f"PHASE2_DECISION={path}")
print(f"PREDICTED_DEMAND_PACKS={state['demand_packs']:.2f}")
print(f"EXPECTED_RETURNS_PACKS={state['expected_returns_packs']:.2f}")
print(f"PREDICTED_SCRAP_RATE={state['scrap_rate']:.5f}")
print(f"VIRGIN_REQUIREMENT_KG={consequence['virgin_requirement_kg']:.2f}")
