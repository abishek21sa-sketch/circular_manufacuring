from __future__ import annotations
from dataclasses import replace
from circular_battery.optimization.stochastic_network import demo_stochastic_config, solve_stochastic_network


def strategic_sensitivity(scenarios):
    base=demo_stochastic_config()
    experiments=[
        ("base",base),
        ("high_carbon_price",replace(base,carbon_price_per_kg=5.0)),
        ("high_virgin_penalty",replace(base,virgin_penalty_per_kg=2.0)),
        ("risk_averse",replace(base,risk_aversion=.45)),
        ("n_minus_one",replace(base,risk_aversion=.30,n_minus_one_min_capacity_kg=210_000.)),
        ("tight_disposal",replace(base,max_disposal_share=.10)),
    ]
    rows=[]
    for name,cfg in experiments:
        sol=solve_stochastic_network(scenarios,cfg)
        rows.append({"experiment":name,"expected_total_cost":sol.expected_total_cost,"cvar_operating_cost":sol.cvar_operating_cost,"expected_carbon_kgco2e":sol.expected_carbon_kgco2e,"expected_virgin_kg":sol.expected_virgin_kg,"expected_service_level":sol.expected_service_level,"open_facilities":sol.open_facilities,"expansion_units":sol.expansion_units,"max_constraint_violation":sol.max_constraint_violation})
    b=rows[0]
    for r in rows:
        r["delta_vs_base"]={k:r[k]-b[k] for k in ("expected_total_cost","cvar_operating_cost","expected_carbon_kgco2e","expected_virgin_kg","expected_service_level")}
    return {"experiments":rows,"evidence_class":"SEEDED SYNTHETIC STRATEGIC SENSITIVITY ANALYSIS"}
