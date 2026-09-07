from circular_battery.domain.models import BatteryChemistry, PeriodInput, PeriodResult

TOL = 1e-7

def pack_mass_kg(chemistry: BatteryChemistry) -> float:
    return sum(chemistry.bill_of_materials_kg_per_pack.values())

def calculate_period(chemistry: BatteryChemistry, p: PeriodInput) -> PeriodResult:
    if not (0 <= p.manufacturing_scrap_rate < 1):
        raise ValueError("manufacturing_scrap_rate must be in [0,1).")
    for name, value in {
        "collection_rate": p.collection_rate,
        "second_life_share": p.second_life_share,
        "remanufacture_share": p.remanufacture_share,
        "recycling_share": p.recycling_share,
        "recycling_yield": p.recycling_yield,
    }.items():
        if not (0 <= value <= 1):
            raise ValueError(f"{name} must be in [0,1].")
    pathway_sum = p.second_life_share + p.remanufacture_share + p.recycling_share
    if pathway_sum > 1 + TOL:
        raise ValueError("Circular pathway shares cannot exceed 1.")

    mass = pack_mass_kg(chemistry)
    product_material = p.production_packs * mass
    total_input = product_material / (1 - p.manufacturing_scrap_rate)
    scrap = total_input - product_material

    returned = p.eol_returns_packs * mass
    collected = returned * p.collection_rate
    uncollected = returned - collected
    second_life = collected * p.second_life_share
    reman = collected * p.remanufacture_share
    recycle_feed = collected * p.recycling_share
    direct_disposal = collected - second_life - reman - recycle_feed

    recovered = recycle_feed * p.recycling_yield
    recycling_loss = recycle_feed - recovered

    # Phase 1 policy: all recovered feedstock is immediately available to offset virgin input;
    # excess recovered material is carried as inventory.
    recovered_available = p.opening_recovered_inventory_kg + recovered + scrap
    recycled_use = min(product_material, recovered_available)
    closing_inventory = recovered_available - recycled_use
    virgin = product_material - recycled_use

    mfg_err = total_input - product_material - scrap
    return_err = returned - (uncollected + second_life + reman + recycle_feed + direct_disposal)
    recycling_err = recycle_feed - recovered - recycling_loss
    inv_err = p.opening_recovered_inventory_kg + recovered + scrap - recycled_use - closing_inventory

    recovery_eff = (second_life + reman + recovered) / collected if collected else 0.0
    disposed = uncollected + direct_disposal + recycling_loss
    landfill_diversion = 1 - disposed / returned if returned else 0.0
    productivity = p.production_packs / (total_input / 1000.0) if total_input else 0.0

    return PeriodResult(
        period=p.period,
        production_packs=p.production_packs,
        total_material_input_kg=total_input,
        product_material_kg=product_material,
        manufacturing_scrap_kg=scrap,
        collected_return_material_kg=collected,
        uncollected_return_material_kg=uncollected,
        second_life_material_kg=second_life,
        remanufacture_feed_kg=reman,
        recycling_feed_kg=recycle_feed,
        direct_disposal_kg=direct_disposal,
        recovered_material_kg=recovered,
        recycling_loss_kg=recycling_loss,
        closing_recovered_inventory_kg=closing_inventory,
        virgin_requirement_kg=virgin,
        recycled_content_rate=recycled_use/product_material if product_material else 0.0,
        collection_efficiency=p.collection_rate,
        recovery_efficiency=recovery_eff,
        landfill_diversion_rate=landfill_diversion,
        material_productivity_packs_per_tonne=productivity,
        manufacturing_balance_error_kg=mfg_err,
        return_balance_error_kg=return_err,
        recycling_balance_error_kg=recycling_err,
        inventory_balance_error_kg=inv_err,
    )

def calculate_horizon(chemistry, periods):
    results = []
    inventory = 0.0
    for p in periods:
        p = PeriodInput(
            period=p.period, production_packs=p.production_packs, demand_packs=p.demand_packs,
            manufacturing_scrap_rate=p.manufacturing_scrap_rate, eol_returns_packs=p.eol_returns_packs,
            collection_rate=p.collection_rate, second_life_share=p.second_life_share,
            remanufacture_share=p.remanufacture_share, recycling_share=p.recycling_share,
            recycling_yield=p.recycling_yield, opening_recovered_inventory_kg=inventory
        )
        r = calculate_period(chemistry, p)
        inventory = r.closing_recovered_inventory_kg
        results.append(r)
    return results
