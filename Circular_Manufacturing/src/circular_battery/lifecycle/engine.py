from __future__ import annotations
from collections import defaultdict
from circular_battery.lifecycle.models import ProductDesign, RecoveryGrade, LifecyclePeriod, MaterialLifecycleResult

TOL = 1e-8

def _validate_period(period: LifecyclePeriod, grades: dict[str, RecoveryGrade]):
    if period.production_packs < 0 or period.eol_returns_packs < 0:
        raise ValueError("Production and returns cannot be negative.")
    if not (0 <= period.collection_rate <= 1):
        raise ValueError("collection_rate must be in [0,1].")
    if abs(sum(period.grade_mix.values()) - 1.0) > 1e-9:
        raise ValueError("grade_mix must sum to 1.")
    for g, share in period.grade_mix.items():
        if g not in grades:
            raise ValueError(f"Unknown recovery grade: {g}")
        if share < 0:
            raise ValueError("grade shares cannot be negative.")
        grades[g].validate()

def weighted_pathway_shares(period: LifecyclePeriod, grades: dict[str, RecoveryGrade]):
    _validate_period(period, grades)
    out = defaultdict(float)
    for grade_name, mix in period.grade_mix.items():
        g = grades[grade_name]
        out["second_life"] += mix * g.second_life_probability
        out["remanufacture"] += mix * g.remanufacture_probability
        out["recycle"] += mix * g.recycle_probability
        out["disposal"] += mix * g.disposal_probability
    if abs(sum(out.values()) - 1.0) > TOL:
        raise AssertionError("Weighted recovery pathway shares do not close.")
    return dict(out)

def evaluate_lifecycle_period(design: ProductDesign, grades: dict[str, RecoveryGrade], period: LifecyclePeriod):
    shares = weighted_pathway_shares(period, grades)
    results = []
    for material in design.materials:
        embedded = period.production_packs * material.kg_per_pack
        manufacturing_input = embedded / (1 - design.manufacturing_scrap_rate)
        scrap = manufacturing_input - embedded

        returned = period.eol_returns_packs * material.kg_per_pack
        collected = returned * period.collection_rate
        uncollected = returned - collected

        second = collected * shares["second_life"]
        reman_feed = collected * shares["remanufacture"]
        reman_retained = reman_feed * design.remanufacture_material_retention
        reman_loss = reman_feed - reman_retained

        recycle_feed = collected * shares["recycle"] + reman_loss
        recycled_output = recycle_feed * material.recycling_yield
        recycling_loss = recycle_feed - recycled_output
        direct_disposal = collected * shares["disposal"]

        # Returned-material closure tracks all physical fates. Reman retained material
        # remains embodied in remanufactured products; reman loss is routed to recycling.
        err = returned - (
            uncollected + second + reman_retained + recycled_output +
            recycling_loss + direct_disposal
        )

        results.append(MaterialLifecycleResult(
            period=period.period,
            material=material.name,
            manufacturing_input_kg=manufacturing_input,
            embedded_product_kg=embedded,
            manufacturing_scrap_kg=scrap,
            returned_kg=returned,
            collected_kg=collected,
            second_life_kg=second,
            remanufactured_retained_kg=reman_retained,
            recycle_feed_kg=recycle_feed,
            recycled_output_kg=recycled_output,
            direct_disposal_kg=direct_disposal,
            recycling_loss_kg=recycling_loss,
            uncollected_kg=uncollected,
            material_balance_error_kg=err,
        ))
    return results

def evaluate_lifecycle_horizon(design, grades, periods):
    return [r for p in periods for r in evaluate_lifecycle_period(design, grades, p)]
