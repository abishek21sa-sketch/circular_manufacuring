from dataclasses import dataclass, asdict
from circular_battery.domain.models import BatteryChemistry, Material

@dataclass
class LCAResult:
    virgin_material_kgco2e: float
    recovered_material_kgco2e: float
    collection_transport_kgco2e: float
    recycling_process_kgco2e: float
    total_kgco2e: float
    functional_unit: str
    evidence_class: str = "ASSUMED / SYNTHETIC PHASE-1 FACTORS"
    def to_dict(self): return asdict(self)

def material_weighted_factor(chemistry: BatteryChemistry, materials: dict[str, Material], recycled=False):
    mass = sum(chemistry.bill_of_materials_kg_per_pack.values())
    total = 0.0
    for name, kg in chemistry.bill_of_materials_kg_per_pack.items():
        m = materials[name]
        total += kg * (m.recycled_kgco2e_per_kg if recycled else m.virgin_kgco2e_per_kg)
    return total / mass

def calculate_lca(chemistry, materials, virgin_kg, recovered_used_kg, collected_return_kg,
                  transport_kgco2e_per_kg=0.08, recycling_process_kgco2e_per_kg=0.45):
    vf = material_weighted_factor(chemistry, materials, recycled=False)
    rf = material_weighted_factor(chemistry, materials, recycled=True)
    virgin = virgin_kg * vf
    recovered = recovered_used_kg * rf
    transport = collected_return_kg * transport_kgco2e_per_kg
    recycling = recovered_used_kg * recycling_process_kgco2e_per_kg
    return LCAResult(
        virgin_material_kgco2e=virgin,
        recovered_material_kgco2e=recovered,
        collection_transport_kgco2e=transport,
        recycling_process_kgco2e=recycling,
        total_kgco2e=virgin + recovered + transport + recycling,
        functional_unit="planning-period battery material requirement",
    )
