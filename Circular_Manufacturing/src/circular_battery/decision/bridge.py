from __future__ import annotations
import json
from pathlib import Path
from circular_battery.simulation.uncertainty import generate_raw_scenarios, reduce_scenarios
from circular_battery.ai.runtime import runtime_phase2_payload
from circular_battery.paths import find_repo_root

ROOT=find_repo_root()

def load_phase2_state(path:Path|None=None):
    path=path or ROOT/'artifacts'/'phase2_ai_decision.json'
    return json.loads(path.read_text(encoding='utf-8'))

def ai_to_uncertainty_scenarios(raw_n:int=100,reduced_k:int=10,seed:int=20260817):
    p2=runtime_phase2_payload();state=p2['predicted_state']
    pack_mass=400.0
    demand0=float(state['demand_packs'])*pack_mass
    returns0=float(state['expected_returns_packs'])*pack_mass
    # Forecast horizon preserves the model estimate as period 1 and applies explicit scenario-design growth assumptions.
    base_demand=(demand0,demand0*1.035,demand0*1.075)
    base_returns=(returns0,returns0*1.12,returns0*1.27)
    scrap=float(state['scrap_rate'])
    base_scrap=tuple(d*scrap/(1-scrap) for d in base_demand)
    second=float(state['second_life_share'])
    reman=float(state['remanufacture_share'])
    reman_conditional=reman/max(1-second,1e-9)
    raw=generate_raw_scenarios(
        n=raw_n,seed=seed,base_demand=base_demand,base_returns=base_returns,
        base_collection=.87,base_recycle_yield=.90,base_reman_yield=.88,
        base_scrap_supply=base_scrap,base_second_life_share=second,
        base_reman_eligible_share=reman_conditional,
    )
    reduced=reduce_scenarios(raw,k=reduced_k,seed=seed)
    trace={
        'demand_prediction_packs':state['demand_packs'],
        'return_prediction_packs':state['expected_returns_packs'],
        'scrap_prediction_rate':state['scrap_rate'],
        'recovery_pathway_shares':{
            'second_life':state['second_life_share'],'remanufacture':state['remanufacture_share'],
            'recycle':state['recycling_share'],'dispose':state['dispose_share'],
        },
        'derived_base_demand_kg':base_demand,'derived_base_returns_kg':base_returns,
        'derived_internal_scrap_supply_kg':base_scrap,
        'derived_second_life_share':second,'derived_reman_eligible_share':reman_conditional,
        'evidence_class':'PREDICTED SYNTHETIC STATE -> STOCHASTIC OR INPUT CONTRACT',
    }
    return raw,reduced,trace
