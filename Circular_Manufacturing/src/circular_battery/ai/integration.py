from __future__ import annotations
from dataclasses import dataclass
import pandas as pd
from circular_battery.domain.models import PeriodInput
from circular_battery.engineering.material_flow import calculate_period

@dataclass
class PredictedCircularState:
    demand_packs: float
    expected_returns_packs: float
    scrap_rate: float
    second_life_share: float
    remanufacture_share: float
    recycling_share: float
    dispose_share: float


def to_period_input(period:int, production_packs:float, state:PredictedCircularState, collection_rate:float=.86, recycling_yield:float=.90, opening_inventory_kg:float=0.0):
    # Phase-1 engine models only the three circular pathways explicitly; classifier dispose probability becomes direct disposal remainder.
    return PeriodInput(
        period=period, production_packs=production_packs, demand_packs=state.demand_packs,
        manufacturing_scrap_rate=state.scrap_rate, eol_returns_packs=state.expected_returns_packs,
        collection_rate=collection_rate, second_life_share=state.second_life_share,
        remanufacture_share=state.remanufacture_share, recycling_share=state.recycling_share,
        recycling_yield=recycling_yield, opening_recovered_inventory_kg=opening_inventory_kg,
    )


def engineering_consequence(chemistry, state:PredictedCircularState, production_packs:float):
    return calculate_period(chemistry,to_period_input(1,production_packs,state))
