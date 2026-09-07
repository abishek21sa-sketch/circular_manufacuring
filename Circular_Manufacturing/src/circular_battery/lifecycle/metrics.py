from __future__ import annotations

def circularity_metrics(results, design):
    total_embedded = sum(r.embedded_product_kg for r in results)
    total_input = sum(r.manufacturing_input_kg for r in results)
    total_returns = sum(r.returned_kg for r in results)
    total_collected = sum(r.collected_kg for r in results)
    recycled_output = sum(r.recycled_output_kg for r in results)
    reman_retained = sum(r.remanufactured_retained_kg for r in results)
    second_life = sum(r.second_life_kg for r in results)
    total_losses = sum(r.uncollected_kg + r.direct_disposal_kg + r.recycling_loss_kg for r in results)
    scrap = sum(r.manufacturing_scrap_kg for r in results)

    critical_names = {m.name for m in design.materials if m.critical}
    critical_recovered = sum(
        r.recycled_output_kg + r.remanufactured_retained_kg
        for r in results if r.material in critical_names
    )
    critical_returns = sum(r.returned_kg for r in results if r.material in critical_names)

    return {
        "material_productivity": total_embedded / total_input if total_input else 0.0,
        "manufacturing_scrap_rate": scrap / total_input if total_input else 0.0,
        "collection_efficiency": total_collected / total_returns if total_returns else 0.0,
        "technical_recovery_rate": (recycled_output + reman_retained) / total_collected if total_collected else 0.0,
        "circular_pathway_rate": (recycled_output + reman_retained + second_life) / total_returns if total_returns else 0.0,
        "landfill_or_loss_rate": total_losses / total_returns if total_returns else 0.0,
        "critical_material_recovery_rate": critical_recovered / critical_returns if critical_returns else 0.0,
        "evidence_class": "CALCULATED FROM SYNTHETIC LIFECYCLE STATE",
    }

def pathway_economics(results, design):
    mat = {m.name:m for m in design.materials}
    virgin_equivalent_cost = 0.0
    recovered_cost = 0.0
    virgin_equivalent_carbon = 0.0
    recovered_carbon = 0.0
    recovered_mass = 0.0
    for r in results:
        m = mat[r.material]
        circular_mass = r.recycled_output_kg + r.remanufactured_retained_kg
        recovered_mass += circular_mass
        virgin_equivalent_cost += circular_mass * m.virgin_cost_per_kg
        recovered_cost += circular_mass * m.recycled_cost_per_kg
        virgin_equivalent_carbon += circular_mass * m.virgin_kgco2e_per_kg
        recovered_carbon += circular_mass * m.recycled_kgco2e_per_kg
    return {
        "recovered_mass_kg": recovered_mass,
        "modeled_material_cost_avoidance": virgin_equivalent_cost - recovered_cost,
        "modeled_gwp_avoidance_kgco2e": virgin_equivalent_carbon - recovered_carbon,
        "evidence_class": "MODELED COMPARATIVE IMPACT; NOT REALIZED BENEFIT",
    }
