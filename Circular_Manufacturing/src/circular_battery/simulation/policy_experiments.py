from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import linprog
from circular_battery.optimization.stochastic_network import StochasticNetworkConfig
from circular_battery.simulation.uncertainty import CircularUncertaintyScenario

@dataclass(frozen=True)
class FixedStrategicPolicy:
    name: str
    open_facilities: dict[str,int]
    expansion_units: dict[str,int]

@dataclass
class PolicyExperimentResult:
    policy: str
    scenarios: int
    expected_total_cost: float
    p90_total_cost: float
    cvar95_total_cost: float
    expected_carbon_kgco2e: float
    expected_virgin_kg: float
    expected_shortage_kg: float
    expected_service_level: float
    expected_emergency_recovery_kg: float
    emergency_recovery_probability: float
    scenario_rows: list[dict]
    evidence_class: str='SEEDED SYNTHETIC POLICY REPLAY'
    def to_dict(self): return asdict(self)

def _fixed_cost(cfg,policy):
    by={f.name:f for f in cfg.facilities}
    return sum(
        policy.open_facilities.get(name,0)*fac.fixed_open_cost +
        policy.expansion_units.get(name,0)*fac.expansion_cost_per_unit
        for name,fac in by.items()
    )

def _recourse(sc:CircularUncertaintyScenario,cfg:StochasticNetworkConfig,policy:FixedStrategicPolicy):
    F=len(cfg.facilities);T=len(sc.demand_kg)
    # variables per period: virgin, feeds[F], inventory, disposal, shortage, emergency recovery feed
    idx={};k=0
    for t in range(T):
        idx['virgin',t]=k;k+=1
        for f in range(F): idx['feed',t,f]=k;k+=1
        idx['inventory',t]=k;k+=1;idx['disposal',t]=k;k+=1;idx['shortage',t]=k;k+=1;idx['emergency',t]=k;k+=1
    n=k;c=np.zeros(n);bounds=[(0,None)]*n
    for t in range(T):
        c[idx['virgin',t]]=cfg.virgin_cost_per_kg*sc.virgin_cost_multiplier
        for f,fac in enumerate(cfg.facilities): c[idx['feed',t,f]]=fac.processing_cost_per_kg+.10*sc.transport_cost_multiplier
        c[idx['inventory',t]]=cfg.inventory_cost_per_kg;c[idx['disposal',t]]=cfg.disposal_cost_per_kg
        c[idx['shortage',t]]=cfg.shortage_penalty_per_kg;c[idx['emergency',t]]=12.0
        bounds[idx['inventory',t]]=(0,cfg.max_inventory_kg)
        bounds[idx['shortage',t]]=(0,cfg.max_shortage_share*sc.demand_kg[t])
    Aeq=[];beq=[];Aub=[];bub=[]
    for t in range(T):
        # demand balance; emergency processor yields 80% recovered feed.
        a=np.zeros(n);a[idx['virgin',t]]=1;a[idx['emergency',t]]=.80
        for f,fac in enumerate(cfg.facilities):
            a[idx['feed',t,f]]=sc.recycle_yield if fac.kind=='recycle' else sc.reman_yield
        if t>0: a[idx['inventory',t-1]]=1;rhs=sc.demand_kg[t]-.95*sc.internal_scrap_supply_kg[t]
        else: rhs=sc.demand_kg[t]-cfg.initial_inventory_kg-.95*sc.internal_scrap_supply_kg[t]
        a[idx['inventory',t]]=-1;a[idx['shortage',t]]=1
        Aeq.append(a);beq.append(rhs)
        # returns flow incl emergency processor; second-life is outside current-horizon recovery feed.
        collected=sc.returns_kg[t]*sc.collection_rate*(1-sc.second_life_share)
        a=np.zeros(n)
        for f in range(F): a[idx['feed',t,f]]=1
        a[idx['disposal',t]]=1;a[idx['emergency',t]]=1
        Aeq.append(a);beq.append(collected)
        # reman eligibility
        a=np.zeros(n)
        for f,fac in enumerate(cfg.facilities):
            if fac.kind=='reman': a[idx['feed',t,f]]=1
        Aub.append(a);bub.append(collected*sc.reman_eligible_share)
        # capacity fixed by policy and realized availability
        for f,fac in enumerate(cfg.facilities):
            cap=(fac.base_capacity_kg*policy.open_facilities.get(fac.name,0)+fac.expansion_unit_kg*policy.expansion_units.get(fac.name,0))*sc.facility_availability[f]
            a=np.zeros(n);a[idx['feed',t,f]]=1;Aub.append(a);bub.append(cap)
        a=np.zeros(n);a[idx['disposal',t]]=1;Aub.append(a);bub.append(cfg.max_disposal_share*collected)
    res=linprog(c,A_ub=np.asarray(Aub),b_ub=np.asarray(bub),A_eq=np.asarray(Aeq),b_eq=np.asarray(beq),bounds=bounds,method='highs')
    if not res.success: raise RuntimeError(f'policy recourse failed: {res.message}')
    x=res.x;op=float(res.fun);carbon=virgin=shortage=emergency=0.
    for t in range(T):
        v=x[idx['virgin',t]];d=x[idx['disposal',t]];sh=x[idx['shortage',t]];em=x[idx['emergency',t]]
        virgin+=v;shortage+=sh;emergency+=em
        carbon+=v*cfg.virgin_carbon_per_kg*sc.carbon_multiplier+d*cfg.disposal_carbon_per_kg*sc.carbon_multiplier+em*5.0
        for f,fac in enumerate(cfg.facilities): carbon+=x[idx['feed',t,f]]*fac.processing_carbon_per_kg*sc.carbon_multiplier
    return {'operating_cost':op,'carbon_kgco2e':carbon,'virgin_kg':virgin,'shortage_kg':shortage,'emergency_kg':emergency,'service_level':1-shortage/sum(sc.demand_kg)}

def evaluate_policy(scenarios:list[CircularUncertaintyScenario],cfg:StochasticNetworkConfig,policy:FixedStrategicPolicy):
    fixed=_fixed_cost(cfg,policy);rows=[]
    for sc in scenarios:
        r=_recourse(sc,cfg,policy);r={'scenario':sc.name,'probability':sc.probability,'total_cost':fixed+r['operating_cost'],**r};rows.append(r)
    p=np.array([s.probability for s in scenarios]);cost=np.array([r['total_cost'] for r in rows])
    # weighted quantile by deterministic scenario ordering
    order=np.argsort(cost);cum=np.cumsum(p[order]);p90=float(cost[order][np.searchsorted(cum,.90,side='left')])
    var95=float(cost[order][np.searchsorted(cum,.95,side='left')]);tail=np.maximum(cost-var95,0)
    tail_prob=float(np.sum(p[cost>=var95]));cvar=float(np.sum(p[cost>=var95]*cost[cost>=var95])/tail_prob) if tail_prob else var95
    expected=lambda key: float(sum(r['probability']*r[key] for r in rows))
    demand=float(sum(s.probability*sum(s.demand_kg) for s in scenarios));short=expected('shortage_kg')
    return PolicyExperimentResult(
        policy=policy.name,scenarios=len(scenarios),expected_total_cost=expected('total_cost'),p90_total_cost=p90,cvar95_total_cost=cvar,
        expected_carbon_kgco2e=expected('carbon_kgco2e'),expected_virgin_kg=expected('virgin_kg'),expected_shortage_kg=short,
        expected_service_level=1-short/demand,expected_emergency_recovery_kg=expected('emergency_kg'),
        emergency_recovery_probability=float(sum(r['probability'] for r in rows if r['emergency_kg']>1e-6)),scenario_rows=rows,
    )

def compare_policies(scenarios,cfg,policies):
    results=[evaluate_policy(scenarios,cfg,p) for p in policies]
    base=results[0]
    out=[]
    for r in results:
        d=r.to_dict();d['delta_vs_first_policy']={
            'expected_cost':r.expected_total_cost-base.expected_total_cost,
            'cvar95_cost':r.cvar95_total_cost-base.cvar95_total_cost,
            'carbon_kgco2e':r.expected_carbon_kgco2e-base.expected_carbon_kgco2e,
            'virgin_kg':r.expected_virgin_kg-base.expected_virgin_kg,
            'emergency_recovery_kg':r.expected_emergency_recovery_kg-base.expected_emergency_recovery_kg,
        };out.append(d)
    return out
