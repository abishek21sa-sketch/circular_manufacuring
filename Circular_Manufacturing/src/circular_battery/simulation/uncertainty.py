from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from sklearn.cluster import KMeans

@dataclass(frozen=True)
class CircularUncertaintyScenario:
    name: str
    probability: float
    demand_kg: tuple[float,...]
    returns_kg: tuple[float,...]
    collection_rate: float
    recycle_yield: float
    reman_yield: float
    virgin_cost_multiplier: float
    transport_cost_multiplier: float
    carbon_multiplier: float
    facility_availability: tuple[float,...]
    internal_scrap_supply_kg: tuple[float,...]
    second_life_share: float
    reman_eligible_share: float
    def to_dict(self): return asdict(self)

def generate_raw_scenarios(
    n:int=80, seed:int=20260817,
    base_demand=(900_000.,960_000.,1_020_000.),
    base_returns=(360_000.,430_000.,510_000.),
    base_collection=.86, base_recycle_yield=.90, base_reman_yield=.82,
    facilities:int=3, base_scrap_supply=(45_000.,48_000.,52_000.),
    base_second_life_share:float=.13, base_reman_eligible_share:float=.22,
):
    if n<4: raise ValueError('n must be >= 4')
    rng=np.random.default_rng(seed)
    out=[]
    # Common factors create realistic temporal dependence rather than iid period noise.
    for i in range(n):
        macro=rng.normal(0,1)
        demand_growth=rng.normal(0,.025)
        return_macro=.45*macro+rng.normal(0,.9)
        demand=[];returns=[]
        for t,(d,r) in enumerate(zip(base_demand,base_returns)):
            dm=np.clip(1+.055*macro+demand_growth*t+rng.normal(0,.025),.78,1.28)
            rm=np.clip(1+.11*return_macro+rng.normal(0,.06),.58,1.42)
            demand.append(float(d*dm));returns.append(float(r*rm))
        collection=float(np.clip(base_collection+rng.normal(0,.035),.68,.96))
        ry=float(np.clip(base_recycle_yield+rng.normal(0,.025),.76,.97))
        my=float(np.clip(base_reman_yield+rng.normal(0,.03),.68,.94))
        virgin_price=float(np.clip(np.exp(rng.normal(0,.12)),.72,1.45))
        transport=float(np.clip(np.exp(rng.normal(0,.10)),.75,1.38))
        carbon=float(np.clip(rng.normal(1,.07),.82,1.20))
        # Rare but material capacity disruptions; recycle sites are slightly more reliable.
        scrap=[float(max(0.,x*rng.normal(1,.10))) for x in base_scrap_supply]
        second_life=float(np.clip(base_second_life_share+rng.normal(0,.025),.02,.35))
        reman_eligible=float(np.clip(base_reman_eligible_share+rng.normal(0,.035),.05,.45))
        avail=[]
        for f in range(facilities):
            p_down=.045 if f<2 else .065
            avail.append(0.0 if rng.random()<p_down else 1.0)
        # Avoid all-facility outage in the benchmark; that case belongs to emergency planning.
        if sum(avail)==0: avail[rng.integers(0,facilities)]=1.0
        out.append(CircularUncertaintyScenario(
            name=f'raw-{i:03d}',probability=1/n,demand_kg=tuple(demand),returns_kg=tuple(returns),
            collection_rate=collection,recycle_yield=ry,reman_yield=my,
            virgin_cost_multiplier=virgin_price,transport_cost_multiplier=transport,
            carbon_multiplier=carbon,facility_availability=tuple(avail),
            internal_scrap_supply_kg=tuple(scrap),second_life_share=second_life,reman_eligible_share=reman_eligible
        ))
    return out

def _feature(s:CircularUncertaintyScenario):
    d=np.array(s.demand_kg);r=np.array(s.returns_kg)
    return np.array([
        d.mean()/1_000_000,d[-1]/d[0],r.mean()/500_000,r[-1]/max(r[0],1),
        s.collection_rate,s.recycle_yield,s.reman_yield,s.virgin_cost_multiplier,
        s.transport_cost_multiplier,s.carbon_multiplier,s.second_life_share,s.reman_eligible_share,
        np.mean(s.internal_scrap_supply_kg)/50_000,*s.facility_availability
    ],dtype=float)

def reduce_scenarios(raw:list[CircularUncertaintyScenario], k:int=10, seed:int=20260817):
    if not 1<=k<=len(raw): raise ValueError('invalid k')
    X=np.vstack([_feature(s) for s in raw])
    # Standardize feature scales before clustering.
    mu=X.mean(axis=0);sd=X.std(axis=0);sd[sd<1e-12]=1
    Z=(X-mu)/sd
    km=KMeans(n_clusters=k,random_state=seed,n_init=20).fit(Z)
    reduced=[]
    for cluster in range(k):
        members=np.where(km.labels_==cluster)[0]
        centroid=km.cluster_centers_[cluster]
        local=Z[members]
        medoid_idx=members[int(np.argmin(((local-centroid)**2).sum(axis=1)))]
        s=raw[int(medoid_idx)]
        reduced.append(CircularUncertaintyScenario(
            name=f'scenario-{cluster+1:02d}',probability=float(len(members)/len(raw)),
            demand_kg=s.demand_kg,returns_kg=s.returns_kg,collection_rate=s.collection_rate,
            recycle_yield=s.recycle_yield,reman_yield=s.reman_yield,
            virgin_cost_multiplier=s.virgin_cost_multiplier,
            transport_cost_multiplier=s.transport_cost_multiplier,carbon_multiplier=s.carbon_multiplier,
            facility_availability=s.facility_availability,internal_scrap_supply_kg=s.internal_scrap_supply_kg,
            second_life_share=s.second_life_share,reman_eligible_share=s.reman_eligible_share,
        ))
    reduced.sort(key=lambda x:x.name)
    # floating-point cleanup so probability sums exactly enough for audit.
    total=sum(s.probability for s in reduced)
    if abs(total-1)>1e-12:
        last=reduced[-1]
        reduced[-1]=CircularUncertaintyScenario(**{**last.__dict__,'probability':last.probability+(1-total)})
    return reduced

def scenario_summary(scenarios):
    p=np.array([s.probability for s in scenarios])
    expected_demand=sum(p[i]*sum(s.demand_kg) for i,s in enumerate(scenarios))
    expected_returns=sum(p[i]*sum(s.returns_kg) for i,s in enumerate(scenarios))
    outage_prob=[]
    F=len(scenarios[0].facility_availability)
    for f in range(F):
        outage_prob.append(sum(s.probability*(1-s.facility_availability[f]) for s in scenarios))
    return {
        'scenario_count':len(scenarios),'probability_sum':float(p.sum()),
        'expected_total_demand_kg':float(expected_demand),
        'expected_total_returns_kg':float(expected_returns),
        'facility_outage_probability':outage_prob,
        'evidence_class':'SEEDED SYNTHETIC UNCERTAINTY EXPERIMENT',
    }
