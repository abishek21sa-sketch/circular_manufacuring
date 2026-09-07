from circular_battery.optimization.network import solve_network

def circular_strategy_frontier(scenario):
    # Carbon shadow-price sweep creates candidate efficient policies.
    prices=(0.0,0.05,0.15,0.35,0.75,1.5,3.0,6.0)
    sols=[solve_network(scenario, carbon_price_per_kg=p) for p in prices]
    unique={}
    for p,s in zip(prices,sols):
        key=(round(s.total_cost,4),round(s.total_carbon_kgco2e,4),round(s.virgin_kg,4))
        unique[key]={"carbon_price":p,**s.to_dict()}
    candidates=list(unique.values())
    nd=[]
    for a in candidates:
        dominated=False
        for b in candidates:
            if a is b: continue
            no_worse=(b["total_cost"]<=a["total_cost"] and b["total_carbon_kgco2e"]<=a["total_carbon_kgco2e"] and b["virgin_kg"]<=a["virgin_kg"])
            strictly=(b["total_cost"]<a["total_cost"] or b["total_carbon_kgco2e"]<a["total_carbon_kgco2e"] or b["virgin_kg"]<a["virgin_kg"])
            if no_worse and strictly: dominated=True; break
        if not dominated: nd.append(a)
    return sorted(nd,key=lambda x:x["total_cost"])
