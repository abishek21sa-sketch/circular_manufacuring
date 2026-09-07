from circular_battery.lifecycle.models import MaterialSpec, ProductDesign, RecoveryGrade, LifecyclePeriod

def demo_design() -> ProductDesign:
    return ProductDesign(
        name="NMC-811-CIRCULAR-DEMO",
        materials=(
            MaterialSpec("lithium", 8.0, 18.0, 11.0, 15.0, 4.5, .92, True),
            MaterialSpec("nickel", 32.0, 16.0, 9.0, 9.0, 3.0, .94, True),
            MaterialSpec("cobalt", 8.0, 34.0, 20.0, 22.0, 6.5, .95, True),
            MaterialSpec("graphite", 45.0, 5.0, 3.0, 5.0, 2.0, .88, True),
            MaterialSpec("aluminum", 55.0, 3.1, 1.9, 10.0, 2.0, .96, False),
            MaterialSpec("copper", 30.0, 9.0, 6.0, 4.0, 1.5, .97, False),
            MaterialSpec("other", 222.0, 2.0, 1.6, 3.0, 2.0, .70, False),
        ),
        manufacturing_scrap_rate=.045,
        max_recycled_content=.60,
        remanufacture_material_retention=.93,
    )

def demo_grades():
    return {
        "A": RecoveryGrade("A", .55, .30, .13, .02),
        "B": RecoveryGrade("B", .15, .35, .45, .05),
        "C": RecoveryGrade("C", .02, .08, .78, .12),
    }

def demo_periods():
    return [
        LifecyclePeriod(1, 2200, 720, .84, {"A":.22,"B":.46,"C":.32}),
        LifecyclePeriod(2, 2350, 820, .86, {"A":.20,"B":.47,"C":.33}),
        LifecyclePeriod(3, 2500, 960, .88, {"A":.18,"B":.48,"C":.34}),
        LifecyclePeriod(4, 2650, 1110, .89, {"A":.17,"B":.47,"C":.36}),
    ]
