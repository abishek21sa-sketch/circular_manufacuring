from pathlib import Path
from circular_battery.reporting.phase567 import write_phase567_report

out=Path("artifacts/phase567_integrated_report.json")
r=write_phase567_report(out)
print(f"PHASE567_REPORT={out.resolve()}")
print(f"MAX_PHASE5_MASS_ERROR_KG={r['phase5']['max_material_balance_error_kg']:.10f}")
rl=r["phase6"]["reverse_logistics"]
print(f"REVERSE_STATUS={rl['status']}")
print(f"REVERSE_PROCESSED_KG={rl['processed_kg']:.2f}")
print(f"REVERSE_DISPOSED_KG={rl['disposed_kg']:.2f}")
plan=r["phase7"]["production_plan"]
print(f"PLANNING_STATUS={plan['status']}")
print(f"SERVICE_LEVEL={plan['service_level']:.6f}")
print(f"RECYCLED_CONTENT={plan['recycled_content_rate']:.6f}")
print(f"MAX_PLANNING_VIOLATION={plan['max_constraint_violation']:.10f}")
