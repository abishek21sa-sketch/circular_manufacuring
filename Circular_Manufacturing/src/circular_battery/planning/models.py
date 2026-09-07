from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class PlanningScenario:
    demand_packs: tuple[float, ...]
    recovered_supply_kg: tuple[float, ...]
    regular_capacity_packs: tuple[float, ...]
    overtime_capacity_packs: tuple[float, ...]
    pack_mass_kg: float = 400.0
    initial_finished_goods_packs: float = 120.0
    initial_recovered_inventory_kg: float = 40_000.0
    max_recovered_inventory_kg: float = 350_000.0
    max_finished_goods_inventory_packs: float = 500.0
    safety_stock_fraction_next_period: float = .08
    max_recycled_content: float = .60
    min_recycled_content: float = .20
    regular_production_cost_per_pack: float = 420.0
    overtime_production_cost_per_pack: float = 535.0
    virgin_material_cost_per_kg: float = 7.20
    recovered_material_cost_per_kg: float = 2.70
    recovered_inventory_cost_per_kg: float = .05
    finished_goods_holding_cost_per_pack: float = 18.0
    shortage_penalty_per_pack: float = 12_000.0

@dataclass
class PlanningSolution:
    status: str
    objective_cost: float
    total_regular_packs: float
    total_overtime_packs: float
    total_shortage_packs: float
    service_level: float
    total_virgin_kg: float
    total_recovered_use_kg: float
    recycled_content_rate: float
    avg_regular_capacity_utilization: float
    max_constraint_violation: float
    period_rows: list[dict]
    solver: str

    def to_dict(self):
        return asdict(self)
