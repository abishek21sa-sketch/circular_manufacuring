from __future__ import annotations
from dataclasses import replace
from circular_battery.optimization.stochastic_network import demo_stochastic_config, solve_stochastic_network

def advanced_strategy_candidates(scenarios):
    base=demo_stochastic_config()
    designs=(
        ('cost',dict(carbon_price_per_kg=0.,virgin_penalty_per_kg=0.,risk_aversion=0.,n_minus_one_min_capacity_kg=0.)),
        ('balanced',dict(carbon_price_per_kg=.12,virgin_penalty_per_kg=.35,risk_aversion=.12,n_minus_one_min_capacity_kg=0.)),
        ('low_carbon',dict(carbon_price_per_kg=4.0,virgin_penalty_per_kg=.35,risk_aversion=.18,n_minus_one_min_capacity_kg=0.)),
        ('critical_material',dict(carbon_price_per_kg=.18,virgin_penalty_per_kg=8.0,risk_aversion=.18,n_minus_one_min_capacity_kg=0.)),
        ('resilience',dict(carbon_price_per_kg=.12,virgin_penalty_per_kg=.35,risk_aversion=.30,n_minus_one_min_capacity_kg=210_000.)),
        ('resilient_circular',dict(carbon_price_per_kg=3.0,virgin_penalty_per_kg=4.0,risk_aversion=.35,n_minus_one_min_capacity_kg=210_000.)),
    )
    out=[]
    for name,kwargs in designs:
        cfg=replace(base,**kwargs)
        sol=solve_stochastic_network(scenarios,cfg)
        out.append({'policy':name,'settings':kwargs,**sol.to_dict()})
    return out

def nondominated_policies(candidates):
    # Deduplicate policies that resolve to the same operating point before Pareto filtering.
    unique=[]; seen=set()
    for c in candidates:
        key=(round(c['expected_total_cost'],4),round(c['expected_carbon_kgco2e'],4),round(c['expected_virgin_kg'],4),round(c['expected_service_level'],8))
        if key not in seen:
            seen.add(key); unique.append(c)
    nd=[]
    for a in unique:
        dominated=False
        for b in unique:
            if a is b: continue
            no_worse=(
                b['expected_total_cost']<=a['expected_total_cost']+1e-7 and
                b['expected_carbon_kgco2e']<=a['expected_carbon_kgco2e']+1e-7 and
                b['expected_virgin_kg']<=a['expected_virgin_kg']+1e-7 and
                b['expected_service_level']>=a['expected_service_level']-1e-9
            )
            strictly=(
                b['expected_total_cost']<a['expected_total_cost']-1e-7 or
                b['expected_carbon_kgco2e']<a['expected_carbon_kgco2e']-1e-7 or
                b['expected_virgin_kg']<a['expected_virgin_kg']-1e-7 or
                b['expected_service_level']>a['expected_service_level']+1e-9
            )
            if no_worse and strictly:
                dominated=True;break
        if not dominated: nd.append(a)
    return sorted(nd,key=lambda x:x['expected_total_cost'])

def advanced_strategy_frontier(scenarios):
    candidates=advanced_strategy_candidates(scenarios)
    return {'candidates':candidates,'nondominated':nondominated_policies(candidates)}
