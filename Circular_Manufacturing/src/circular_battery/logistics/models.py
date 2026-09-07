from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class CollectionNode:
    name: str
    returns_kg: float
    reman_eligible_share: float
    x_km: float
    y_km: float

@dataclass(frozen=True)
class FacilityCandidate:
    name: str
    kind: str  # "reman" or "recycle"
    capacity_kg: float
    fixed_cost: float
    processing_cost_per_kg: float
    processing_kgco2e_per_kg: float
    x_km: float
    y_km: float

@dataclass(frozen=True)
class ReverseLogisticsScenario:
    collections: tuple[CollectionNode, ...]
    facilities: tuple[FacilityCandidate, ...]
    collection_rate: float = .88
    transport_cost_per_kg_km: float = .0018
    transport_kgco2e_per_kg_km: float = .00012
    disposal_cost_per_kg: float = .65
    disposal_kgco2e_per_kg: float = .75
    max_disposal_share: float = .25

@dataclass
class ReverseLogisticsSolution:
    status: str
    objective_cost: float
    transport_cost: float
    processing_cost: float
    fixed_cost: float
    disposal_cost: float
    transport_kgco2e: float
    processing_kgco2e: float
    disposal_kgco2e: float
    total_kgco2e: float
    opened_facilities: dict[str, int]
    flows: list[dict]
    disposal_by_collection: dict[str, float]
    collected_kg: float
    processed_kg: float
    disposed_kg: float
    max_constraint_violation: float
    solver: str
    mip_gap: float | None

    def to_dict(self):
        return asdict(self)
