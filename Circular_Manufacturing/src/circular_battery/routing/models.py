from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class RouteNode:
    name: str
    x_km: float
    y_km: float
    pickup_kg: float = 0.0

@dataclass(frozen=True)
class CVRPScenario:
    depot: RouteNode
    customers: tuple[RouteNode, ...]
    vehicle_capacity_kg: float
    max_vehicles: int
    vehicle_fixed_cost: float = 180.0
    distance_cost_per_km: float = 2.25
    kgco2e_per_km: float = 0.82

@dataclass
class CVRPSolution:
    status: str
    objective_cost: float
    total_distance_km: float
    total_kgco2e: float
    vehicles_used: int
    routes: list[list[str]]
    route_loads_kg: list[float]
    route_distances_km: list[float]
    max_constraint_violation: float
    solver: str
    mip_gap: float | None
    def to_dict(self): return asdict(self)
