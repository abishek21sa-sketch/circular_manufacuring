from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Mapping

@dataclass(frozen=True)
class MaterialSpec:
    name: str
    kg_per_pack: float
    virgin_cost_per_kg: float
    recycled_cost_per_kg: float
    virgin_kgco2e_per_kg: float
    recycled_kgco2e_per_kg: float
    recycling_yield: float
    critical: bool = False

@dataclass(frozen=True)
class ProductDesign:
    name: str
    materials: tuple[MaterialSpec, ...]
    manufacturing_scrap_rate: float
    max_recycled_content: float
    remanufacture_material_retention: float

    @property
    def pack_mass_kg(self) -> float:
        return sum(m.kg_per_pack for m in self.materials)

@dataclass(frozen=True)
class RecoveryGrade:
    name: str
    second_life_probability: float
    remanufacture_probability: float
    recycle_probability: float
    disposal_probability: float

    def validate(self) -> None:
        vals = (
            self.second_life_probability,
            self.remanufacture_probability,
            self.recycle_probability,
            self.disposal_probability,
        )
        if any(v < 0 or v > 1 for v in vals):
            raise ValueError("Recovery probabilities must be in [0,1].")
        if abs(sum(vals) - 1.0) > 1e-9:
            raise ValueError("Recovery probabilities must sum to 1.")

@dataclass(frozen=True)
class LifecyclePeriod:
    period: int
    production_packs: float
    eol_returns_packs: float
    collection_rate: float
    grade_mix: Mapping[str, float]

@dataclass
class MaterialLifecycleResult:
    period: int
    material: str
    manufacturing_input_kg: float
    embedded_product_kg: float
    manufacturing_scrap_kg: float
    returned_kg: float
    collected_kg: float
    second_life_kg: float
    remanufactured_retained_kg: float
    recycle_feed_kg: float
    recycled_output_kg: float
    direct_disposal_kg: float
    recycling_loss_kg: float
    uncollected_kg: float
    material_balance_error_kg: float

    def to_dict(self):
        return asdict(self)
