from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from circular_battery.simulation.uncertainty import CircularUncertaintyScenario

@dataclass(frozen=True)
class StrategicFacility:
    name: str
    kind: str
    base_capacity_kg: float
    expansion_unit_kg: float
    max_expansion_units: int
    fixed_open_cost: float
    expansion_cost_per_unit: float
    processing_cost_per_kg: float
    processing_carbon_per_kg: float

@dataclass(frozen=True)
class StochasticNetworkConfig:
    facilities: tuple[StrategicFacility,...]
    initial_inventory_kg: float = 80_000.
    max_inventory_kg: float = 350_000.
    inventory_cost_per_kg: float = .07
    virgin_cost_per_kg: float = 7.20
    virgin_carbon_per_kg: float = 8.5
    disposal_cost_per_kg: float = .60
    disposal_carbon_per_kg: float = .75
    shortage_penalty_per_kg: float = 40.0
    max_shortage_share: float = .025
    max_disposal_share: float = .25
    risk_alpha: float = .90
    risk_aversion: float = .12
    carbon_price_per_kg: float = .10
    virgin_penalty_per_kg: float = .0
    n_minus_one_min_capacity_kg: float = 0.0

@dataclass
class StochasticNetworkSolution:
    status: str
    objective: float
    first_stage_cost: float
    expected_operating_cost: float
    cvar_operating_cost: float
    expected_total_cost: float
    expected_carbon_kgco2e: float
    expected_virgin_kg: float
    expected_shortage_kg: float
    expected_service_level: float
    open_facilities: dict[str,int]
    expansion_units: dict[str,int]
    scenario_metrics: list[dict]
    max_constraint_violation: float
    solver: str
    mip_gap: float|None
    def to_dict(self): return asdict(self)

def demo_stochastic_config():
    return StochasticNetworkConfig(facilities=(
        StrategicFacility('R-Chicago','recycle',140_000,45_000,3,220_000,70_000,2.30,2.05),
        StrategicFacility('R-Ohio','recycle',125_000,40_000,3,195_000,65_000,2.22,1.95),
        StrategicFacility('M-Detroit','reman',70_000,30_000,3,320_000,85_000,2.35,.35),
    ))

def solve_stochastic_network(scenarios:list[CircularUncertaintyScenario], cfg:StochasticNetworkConfig|None=None):
    cfg=cfg or demo_stochastic_config()
    if not scenarios: raise ValueError('at least one scenario required')
    if abs(sum(s.probability for s in scenarios)-1)>1e-8: raise ValueError('scenario probabilities must sum to 1')
    S=len(scenarios);F=len(cfg.facilities);T=len(scenarios[0].demand_kg)
    if any(len(s.demand_kg)!=T or len(s.returns_kg)!=T or len(s.internal_scrap_supply_kg)!=T or len(s.facility_availability)!=F for s in scenarios):
        raise ValueError('scenario dimension mismatch')
    if not (0<cfg.risk_alpha<1): raise ValueError('risk_alpha must be in (0,1)')

    # First-stage y[f] binary, e[f] integer expansion units.
    idx={};k=0
    for f in range(F): idx['open',f]=k;k+=1
    for f in range(F): idx['expand',f]=k;k+=1
    # Recourse per scenario/period: virgin, facility feeds, inv, disposal, shortage.
    for si in range(S):
        for t in range(T):
            idx['virgin',si,t]=k;k+=1
            for f in range(F): idx['feed',si,t,f]=k;k+=1
            idx['inventory',si,t]=k;k+=1
            idx['disposal',si,t]=k;k+=1
            idx['shortage',si,t]=k;k+=1
    idx['eta']=k;k+=1
    for si in range(S): idx['excess',si]=k;k+=1
    n=k
    c=np.zeros(n);lb=np.zeros(n);ub=np.full(n,np.inf);integ=np.zeros(n)
    # first stage coefficients
    for f,fac in enumerate(cfg.facilities):
        c[idx['open',f]]=fac.fixed_open_cost
        c[idx['expand',f]]=fac.expansion_cost_per_unit
        ub[idx['open',f]]=1;integ[idx['open',f]]=1
        ub[idx['expand',f]]=fac.max_expansion_units;integ[idx['expand',f]]=1
    # CVaR eta may be nonnegative because scenario costs are nonnegative.
    c[idx['eta']]=cfg.risk_aversion
    for si,sc in enumerate(scenarios):
        c[idx['excess',si]]=cfg.risk_aversion*sc.probability/(1-cfg.risk_alpha)
        for t in range(T):
            p=sc.probability
            c[idx['virgin',si,t]]=p*(cfg.virgin_cost_per_kg*sc.virgin_cost_multiplier + cfg.carbon_price_per_kg*cfg.virgin_carbon_per_kg*sc.carbon_multiplier + cfg.virgin_penalty_per_kg)
            for f,fac in enumerate(cfg.facilities):
                # transport multiplier proxies network line-haul uncertainty already derived in Phase 6.
                transport_component=.10*sc.transport_cost_multiplier
                c[idx['feed',si,t,f]]=p*(fac.processing_cost_per_kg+transport_component+cfg.carbon_price_per_kg*fac.processing_carbon_per_kg*sc.carbon_multiplier)
            c[idx['inventory',si,t]]=p*cfg.inventory_cost_per_kg
            c[idx['disposal',si,t]]=p*(cfg.disposal_cost_per_kg+cfg.carbon_price_per_kg*cfg.disposal_carbon_per_kg*sc.carbon_multiplier)
            c[idx['shortage',si,t]]=p*cfg.shortage_penalty_per_kg

    rows=[];lo=[];hi=[]
    scenario_cost_coeff=[]
    # expansion requires facility open
    for f,fac in enumerate(cfg.facilities):
        a=np.zeros(n);a[idx['expand',f]]=1;a[idx['open',f]]=-fac.max_expansion_units
        rows.append(a);lo.append(-np.inf);hi.append(0)

    # Optional N-1 recovery-capacity robustness: after loss of any one facility,
    # remaining installed capacity must exceed a declared strategic reserve threshold.
    if cfg.n_minus_one_min_capacity_kg > 0:
        for failed in range(F):
            a=np.zeros(n)
            for f,fac in enumerate(cfg.facilities):
                if f==failed: continue
                a[idx['open',f]]=-fac.base_capacity_kg
                a[idx['expand',f]]=-fac.expansion_unit_kg
            rows.append(a);lo.append(-np.inf);hi.append(-cfg.n_minus_one_min_capacity_kg)

    for si,sc in enumerate(scenarios):
        cost_a=np.zeros(n)
        for t in range(T):
            # material/demand balance: virgin + recovered + prior inventory + shortage - close inv = demand
            a=np.zeros(n);a[idx['virgin',si,t]]=1
            for f,fac in enumerate(cfg.facilities):
                yield_factor=sc.recycle_yield if fac.kind=='recycle' else sc.reman_yield
                a[idx['feed',si,t,f]]=yield_factor
            scrap_recovered=.95*sc.internal_scrap_supply_kg[t]
            if t==0:
                rhs=sc.demand_kg[t]-cfg.initial_inventory_kg-scrap_recovered
            else:
                a[idx['inventory',si,t-1]]=1;rhs=sc.demand_kg[t]-scrap_recovered
            a[idx['inventory',si,t]]=-1;a[idx['shortage',si,t]]=1
            rows.append(a);lo.append(rhs);hi.append(rhs)
            # collected returns split to facilities or disposal
            a=np.zeros(n)
            for f in range(F): a[idx['feed',si,t,f]]=1
            a[idx['disposal',si,t]]=1
            collected=sc.returns_kg[t]*sc.collection_rate*(1-sc.second_life_share)
            rows.append(a);lo.append(collected);hi.append(collected)
            # AI-derived recovery state limits how much of the available return feed is remanufacturable.
            a=np.zeros(n)
            for f,fac in enumerate(cfg.facilities):
                if fac.kind=='reman': a[idx['feed',si,t,f]]=1
            rows.append(a);lo.append(-np.inf);hi.append(collected*sc.reman_eligible_share)
            # facility capacities include expansion and outage availability
            for f,fac in enumerate(cfg.facilities):
                av=sc.facility_availability[f]
                a=np.zeros(n);a[idx['feed',si,t,f]]=1
                a[idx['open',f]]=-fac.base_capacity_kg*av
                a[idx['expand',f]]=-fac.expansion_unit_kg*av
                rows.append(a);lo.append(-np.inf);hi.append(0)
            # service and disposal policy constraints
            a=np.zeros(n);a[idx['shortage',si,t]]=1
            rows.append(a);lo.append(-np.inf);hi.append(cfg.max_shortage_share*sc.demand_kg[t])
            a=np.zeros(n);a[idx['disposal',si,t]]=1
            rows.append(a);lo.append(-np.inf);hi.append(cfg.max_disposal_share*collected)

            # scenario operating-cost expression for CVaR (not probability weighted; excludes carbon/virgin penalties).
            cost_a[idx['virgin',si,t]]+=cfg.virgin_cost_per_kg*sc.virgin_cost_multiplier
            for f,fac in enumerate(cfg.facilities): cost_a[idx['feed',si,t,f]]+=fac.processing_cost_per_kg+.10*sc.transport_cost_multiplier
            cost_a[idx['inventory',si,t]]+=cfg.inventory_cost_per_kg
            cost_a[idx['disposal',si,t]]+=cfg.disposal_cost_per_kg
            cost_a[idx['shortage',si,t]]+=cfg.shortage_penalty_per_kg
        scenario_cost_coeff.append(cost_a)
        # excess >= scenario operating cost - eta -> scenario_cost - eta - excess <= 0
        a=cost_a.copy();a[idx['eta']]-=1;a[idx['excess',si]]-=1
        rows.append(a);lo.append(-np.inf);hi.append(0)

    cons=LinearConstraint(np.asarray(rows),np.asarray(lo),np.asarray(hi))
    res=milp(c,integrality=integ,bounds=Bounds(lb,ub),constraints=cons,
             options={'time_limit':60.0,'mip_rel_gap':1e-8})
    if not res.success: raise RuntimeError(f'stochastic MILP failed: {res.message}')
    x=res.x
    opens={fac.name:int(round(x[idx['open',f]])) for f,fac in enumerate(cfg.facilities)}
    expands={fac.name:int(round(x[idx['expand',f]])) for f,fac in enumerate(cfg.facilities)}
    first=sum(opens[fac.name]*fac.fixed_open_cost+expands[fac.name]*fac.expansion_cost_per_unit for fac in cfg.facilities)
    metrics=[];expected_op=expected_carbon=expected_virgin=expected_short=expected_demand=0.
    raw_costs=[]
    violations=[]
    for f,fac in enumerate(cfg.facilities):
        violations.append(max(0.,expands[fac.name]-fac.max_expansion_units*opens[fac.name]))
    if cfg.n_minus_one_min_capacity_kg > 0:
        for failed in range(F):
            remaining=sum(
                cfg.facilities[f].base_capacity_kg*opens[cfg.facilities[f].name] +
                cfg.facilities[f].expansion_unit_kg*expands[cfg.facilities[f].name]
                for f in range(F) if f!=failed
            )
            violations.append(max(0.,cfg.n_minus_one_min_capacity_kg-remaining))
    for si,sc in enumerate(scenarios):
        op=carbon=virgin=shortage=0.;prior=cfg.initial_inventory_kg
        period=[]
        for t in range(T):
            v=x[idx['virgin',si,t]];inv=x[idx['inventory',si,t]];disp=x[idx['disposal',si,t]];sh=x[idx['shortage',si,t]]
            feeds=[];recovered=0.
            for f,fac in enumerate(cfg.facilities):
                q=x[idx['feed',si,t,f]];feeds.append(float(q))
                y=sc.recycle_yield if fac.kind=='recycle' else sc.reman_yield
                recovered+=q*y
                op+=q*(fac.processing_cost_per_kg+.10*sc.transport_cost_multiplier)
                carbon+=q*fac.processing_carbon_per_kg*sc.carbon_multiplier
                cap=(fac.base_capacity_kg*opens[fac.name]+fac.expansion_unit_kg*expands[fac.name])*sc.facility_availability[f]
                violations.append(max(0.,q-cap))
            op+=v*cfg.virgin_cost_per_kg*sc.virgin_cost_multiplier+inv*cfg.inventory_cost_per_kg+disp*cfg.disposal_cost_per_kg+sh*cfg.shortage_penalty_per_kg
            carbon+=v*cfg.virgin_carbon_per_kg*sc.carbon_multiplier+disp*cfg.disposal_carbon_per_kg*sc.carbon_multiplier
            scrap_recovered=.95*sc.internal_scrap_supply_kg[t]
            collected=sc.returns_kg[t]*sc.collection_rate*(1-sc.second_life_share)
            violations.append(abs(v+recovered+scrap_recovered+prior+sh-inv-sc.demand_kg[t]))
            violations.append(abs(sum(feeds)+disp-collected))
            reman_feed=sum(feeds[f] for f,fac in enumerate(cfg.facilities) if fac.kind=='reman')
            violations.append(max(0.,reman_feed-collected*sc.reman_eligible_share))
            violations.append(max(0.,sh-cfg.max_shortage_share*sc.demand_kg[t]))
            violations.append(max(0.,disp-cfg.max_disposal_share*collected))
            period.append({'period':t+1,'virgin_kg':float(v),'recovered_output_kg':float(recovered),'inventory_kg':float(inv),'disposal_kg':float(disp),'shortage_kg':float(sh),'feeds_kg':feeds})
            virgin+=v;shortage+=sh;prior=inv
        raw_costs.append(op)
        p=sc.probability
        expected_op+=p*op;expected_carbon+=p*carbon;expected_virgin+=p*virgin;expected_short+=p*shortage;expected_demand+=p*sum(sc.demand_kg)
        metrics.append({'scenario':sc.name,'probability':p,'operating_cost':float(op),'carbon_kgco2e':float(carbon),'virgin_kg':float(virgin),'shortage_kg':float(shortage),'service_level':float(1-shortage/sum(sc.demand_kg)),'period_rows':period})
    eta=float(x[idx['eta']]);cvar=eta+sum(sc.probability*max(0.,raw_costs[i]-eta) for i,sc in enumerate(scenarios))/(1-cfg.risk_alpha)
    return StochasticNetworkSolution(
        status='OPTIMAL',objective=float(res.fun),first_stage_cost=float(first),expected_operating_cost=float(expected_op),
        cvar_operating_cost=float(cvar),expected_total_cost=float(first+expected_op),expected_carbon_kgco2e=float(expected_carbon),
        expected_virgin_kg=float(expected_virgin),expected_shortage_kg=float(expected_short),
        expected_service_level=float(1-expected_short/expected_demand),open_facilities=opens,expansion_units=expands,
        scenario_metrics=metrics,max_constraint_violation=float(max(violations,default=0.)),solver='scipy.optimize.milp',
        mip_gap=float(getattr(res,'mip_gap',0.0)) if getattr(res,'mip_gap',None) is not None else None,
    )
