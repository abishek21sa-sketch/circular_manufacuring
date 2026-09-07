from circular_battery.reporting.phase10 import write_phase10_report
r,record,path=write_phase10_report()
d=r['decision'];route=r['routing'];cm=r['critical_material_resilience']
by={x['policy']:x for x in r['advanced_strategy_frontier']['candidates']}
chosen=by[d['recommended_policy']]
print('PHASE10_REPORT=artifacts/phase10_decision_report.json')
print(f"RECOMMENDED_POLICY={d['recommended_policy']}")
print(f"CONFIDENCE={d['confidence']:.4f}")
print(f"EXPECTED_COST={chosen['expected_total_cost']:.2f}")
print(f"EXPECTED_CARBON_KGCO2E={chosen['expected_carbon_kgco2e']:.2f}")
print(f"EXPECTED_VIRGIN_KG={chosen['expected_virgin_kg']:.2f}")
print(f"CVAR_OPERATING_COST={chosen['cvar_operating_cost']:.2f}")
print(f"ROUTE_VEHICLES={route['vehicles_used']}")
print(f"ROUTE_DISTANCE_KM={route['total_distance_km']:.2f}")
print(f"CRITICAL_RECOVERED_SHARE={cm['recovered_share']:.6f}")
print(f"PARETO_POINTS={len(r['advanced_strategy_frontier']['nondominated'])}")
print(f"SENSITIVITY_EXPERIMENTS={len(r['strategic_sensitivity']['experiments'])}")
print(f"TRACE_STEPS={len(r['decision_trace'])}")
print(f"RUN_ID={record['run_id']}")
print(f"DECISION_HASH={r['decision_hash_sha256']}")
