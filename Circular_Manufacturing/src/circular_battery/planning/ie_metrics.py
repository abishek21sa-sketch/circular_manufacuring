from __future__ import annotations

def planning_ie_metrics(solution, scenario):
    demand=sum(scenario.demand_packs)
    production=solution.total_regular_packs+solution.total_overtime_packs
    total_capacity=sum(scenario.regular_capacity_packs)+sum(scenario.overtime_capacity_packs)
    ending_fg=solution.period_rows[-1]["closing_fg_inventory_packs"] if solution.period_rows else 0.
    avg_fg=sum(r["closing_fg_inventory_packs"] for r in solution.period_rows)/len(solution.period_rows)
    avg_rec=sum(r["closing_recovered_inventory_kg"] for r in solution.period_rows)/len(solution.period_rows)

    throughput_material_kg=solution.total_virgin_kg+solution.total_recovered_use_kg
    packs_per_tonne=production/(throughput_material_kg/1000.) if throughput_material_kg else 0.

    return {
        "service_level":solution.service_level,
        "aggregate_capacity_utilization":production/total_capacity if total_capacity else 0.,
        "regular_capacity_utilization":solution.avg_regular_capacity_utilization,
        "overtime_share":solution.total_overtime_packs/production if production else 0.,
        "average_finished_goods_inventory_packs":avg_fg,
        "average_recovered_inventory_kg":avg_rec,
        "ending_finished_goods_inventory_packs":ending_fg,
        "material_productivity_packs_per_tonne":packs_per_tonne,
        "recycled_content_rate":solution.recycled_content_rate,
        "virgin_material_dependency":solution.total_virgin_kg/throughput_material_kg if throughput_material_kg else 0.,
        "evidence_class":"OPTIMIZED IE PLANNING METRICS ON SYNTHETIC BENCHMARK",
    }
