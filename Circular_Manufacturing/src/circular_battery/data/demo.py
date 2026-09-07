from circular_battery.domain.models import Material, BatteryChemistry, PeriodInput

def demo_materials():
    # Explicitly synthetic engineering factors for Phase 1.
    return {
        "lithium": Material("lithium", 15.0, 4.5),
        "nickel": Material("nickel", 9.0, 3.0),
        "cobalt": Material("cobalt", 22.0, 6.5),
        "graphite": Material("graphite", 5.0, 2.0),
        "aluminum": Material("aluminum", 10.0, 2.0),
        "copper": Material("copper", 4.0, 1.5),
        "other": Material("other", 3.0, 2.0),
    }

def demo_chemistry():
    # Synthetic 400 kg NMC-like pack for deterministic validation.
    return BatteryChemistry(
        name="NMC-DEMO",
        bill_of_materials_kg_per_pack={
            "lithium": 8.0,
            "nickel": 32.0,
            "cobalt": 8.0,
            "graphite": 45.0,
            "aluminum": 55.0,
            "copper": 30.0,
            "other": 222.0,
        },
    )

def demo_periods():
    return [
        PeriodInput(1, 1000, 980, 0.050, 420, 0.82, 0.18, 0.22, 0.55, 0.88, 0),
        PeriodInput(2, 1100, 1080, 0.047, 500, 0.84, 0.19, 0.23, 0.54, 0.89, 0),
        PeriodInput(3, 1200, 1180, 0.045, 590, 0.86, 0.20, 0.24, 0.53, 0.90, 0),
    ]
