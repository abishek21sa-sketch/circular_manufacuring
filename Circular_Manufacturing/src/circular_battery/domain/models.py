from dataclasses import dataclass, asdict
from typing import Dict, List

@dataclass(frozen=True)
class Material:
    name: str
    virgin_kgco2e_per_kg: float
    recycled_kgco2e_per_kg: float

@dataclass(frozen=True)
class BatteryChemistry:
    name: str
    bill_of_materials_kg_per_pack: Dict[str, float]

@dataclass(frozen=True)
class PeriodInput:
    period: int
    production_packs: float
    demand_packs: float
    manufacturing_scrap_rate: float
    eol_returns_packs: float
    collection_rate: float
    second_life_share: float
    remanufacture_share: float
    recycling_share: float
    recycling_yield: float
    opening_recovered_inventory_kg: float = 0.0

@dataclass
class PeriodResult:
    period: int
    production_packs: float
    total_material_input_kg: float
    product_material_kg: float
    manufacturing_scrap_kg: float
    collected_return_material_kg: float
    uncollected_return_material_kg: float
    second_life_material_kg: float
    remanufacture_feed_kg: float
    recycling_feed_kg: float
    direct_disposal_kg: float
    recovered_material_kg: float
    recycling_loss_kg: float
    closing_recovered_inventory_kg: float
    virgin_requirement_kg: float
    recycled_content_rate: float
    collection_efficiency: float
    recovery_efficiency: float
    landfill_diversion_rate: float
    material_productivity_packs_per_tonne: float
    manufacturing_balance_error_kg: float
    return_balance_error_kg: float
    recycling_balance_error_kg: float
    inventory_balance_error_kg: float

    def to_dict(self):
        return asdict(self)
