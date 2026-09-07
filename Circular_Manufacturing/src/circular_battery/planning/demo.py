from circular_battery.planning.models import PlanningScenario

def demo_planning_scenario():
    return PlanningScenario(
        demand_packs=(2150., 2320., 2480., 2640.),
        recovered_supply_kg=(230_000., 280_000., 350_000., 420_000.),
        regular_capacity_packs=(2200., 2350., 2450., 2550.),
        overtime_capacity_packs=(220., 220., 260., 300.),
        initial_finished_goods_packs=120.,
        initial_recovered_inventory_kg=60_000.,
        safety_stock_fraction_next_period=.06,
        min_recycled_content=.18,
        max_recycled_content=.55,
    )
