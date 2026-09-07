from circular_battery.logistics.models import CollectionNode, FacilityCandidate, ReverseLogisticsScenario

def demo_reverse_logistics_scenario():
    return ReverseLogisticsScenario(
        collections=(
            CollectionNode("Chicago", 280_000, .34, 0, 0),
            CollectionNode("Detroit", 240_000, .31, 380, 40),
            CollectionNode("Columbus", 210_000, .28, 520, -120),
            CollectionNode("Indianapolis", 190_000, .30, 300, -160),
        ),
        facilities=(
            FacilityCandidate("R-Chicago", "recycle", 420_000, 240_000, 2.35, 2.10, 45, 10),
            FacilityCandidate("R-Ohio", "recycle", 360_000, 205_000, 2.25, 2.00, 545, -90),
            FacilityCandidate("M-Detroit", "reman", 190_000, 135_000, 1.45, 1.45, 395, 55),
            FacilityCandidate("M-Indiana", "reman", 165_000, 145_000, 1.55, 1.40, 275, -145),
        ),
        collection_rate=.88,
        max_disposal_share=.20,
    )
