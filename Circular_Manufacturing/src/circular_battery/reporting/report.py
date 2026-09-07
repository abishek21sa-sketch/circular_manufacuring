import json
from pathlib import Path
from circular_battery.data.demo import demo_materials, demo_chemistry, demo_periods
from circular_battery.engineering.material_flow import calculate_horizon
from circular_battery.engineering.lca import calculate_lca
from circular_battery.engineering.value_stream import RecoveryStep, analyze_recovery_value_stream

def build_phase1_report():
    materials = demo_materials()
    chemistry = demo_chemistry()
    results = calculate_horizon(chemistry, demo_periods())
    period_reports = []
    for r in results:
        recovered_used = r.product_material_kg - r.virgin_requirement_kg
        lca = calculate_lca(
            chemistry, materials, r.virgin_requirement_kg, recovered_used,
            r.collected_return_material_kg
        )
        period_reports.append({"material_flow": r.to_dict(), "lca": lca.to_dict()})

    vsm = analyze_recovery_value_stream([
        RecoveryStep("collection", 1.0, 8.0, 0.98),
        RecoveryStep("diagnostic_grading", 2.5, 18.0, 0.96),
        RecoveryStep("disassembly", 3.0, 10.0, 0.95),
        RecoveryStep("recycling", 5.0, 14.0, 0.90),
    ])
    return {
        "project": "Circular Battery Manufacturing & Recovery Decision Intelligence Platform",
        "release": "PHASE-1",
        "version": "0.1.0",
        "data_status": "SYNTHETIC VALIDATION",
        "decision_scope": "Lifecycle material accounting and circular engineering state; AI/OR are intentionally future phases.",
        "periods": period_reports,
        "recovery_value_stream": vsm,
    }

def write_report(path):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    report = build_phase1_report()
    p.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
