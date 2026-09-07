from __future__ import annotations

def lifecycle_material_impact(results, design):
    specs={m.name:m for m in design.materials}
    rows=[]
    total_avoided_cost=total_avoided_gwp=0.0
    for material_name,spec in specs.items():
        rs=[r for r in results if r.material==material_name]
        circular=sum(r.recycled_output_kg+r.remanufactured_retained_kg for r in rs)
        virgin_equiv_cost=circular*spec.virgin_cost_per_kg
        circular_cost=circular*spec.recycled_cost_per_kg
        virgin_equiv_gwp=circular*spec.virgin_kgco2e_per_kg
        circular_gwp=circular*spec.recycled_kgco2e_per_kg
        total_avoided_cost+=virgin_equiv_cost-circular_cost
        total_avoided_gwp+=virgin_equiv_gwp-circular_gwp
        rows.append({
            "material":material_name,
            "critical":spec.critical,
            "circular_output_kg":circular,
            "virgin_equivalent_cost":virgin_equiv_cost,
            "circular_material_cost":circular_cost,
            "modeled_cost_difference":virgin_equiv_cost-circular_cost,
            "virgin_equivalent_kgco2e":virgin_equiv_gwp,
            "circular_kgco2e":circular_gwp,
            "modeled_gwp_difference_kgco2e":virgin_equiv_gwp-circular_gwp,
        })
    return {
        "functional_unit":"material recovered across synthetic planning horizon",
        "system_boundary":"material production comparison for recovered secondary feed; transport/process logistics reported separately",
        "material_rows":rows,
        "modeled_total_cost_difference":total_avoided_cost,
        "modeled_total_gwp_difference_kgco2e":total_avoided_gwp,
        "evidence_class":"MODELED COMPARATIVE LIFECYCLE IMPACT; EXTERNAL FACTOR VALIDATION PENDING",
    }
