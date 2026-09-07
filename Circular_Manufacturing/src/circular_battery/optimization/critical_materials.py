from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from scipy.optimize import linprog

@dataclass(frozen=True)
class CriticalMaterial:
    name: str
    demand_kg: tuple[float, ...]
    recovered_supply_kg: tuple[float, ...]
    supplier_capacity_kg: tuple[tuple[float, ...], ...]  # supplier x period
    supplier_cost_per_kg: tuple[float, ...]
    supplier_carbon_per_kg: tuple[float, ...]
    supplier_risk_score: tuple[float, ...]
    max_single_supplier_share: float = .70
    inventory_cap_kg: float = 150_000.
    initial_inventory_kg: float = 0.

@dataclass(frozen=True)
class CriticalMaterialConfig:
    materials: tuple[CriticalMaterial, ...]
    supplier_names: tuple[str, ...]
    recovered_cost_per_kg: float = 2.60
    recovered_carbon_per_kg: float = 2.0
    inventory_cost_per_kg: float = .06
    shortage_penalty_per_kg: float = 100.
    risk_weight_per_kg: float = .80
    carbon_price_per_kgco2e: float = .10
    minimum_recovered_share: float = .10

@dataclass
class CriticalMaterialSolution:
    status: str
    objective: float
    total_cost: float
    total_carbon_kgco2e: float
    total_risk_weighted_kg: float
    total_virgin_kg: float
    total_recovered_use_kg: float
    total_shortage_kg: float
    recovered_share: float
    supplier_hhi_by_material: dict[str, float]
    material_rows: list[dict]
    max_constraint_violation: float
    solver: str
    def to_dict(self): return asdict(self)


def demo_critical_material_config() -> CriticalMaterialConfig:
    suppliers=("NorthAmerica","Australia","GlobalImport")
    def caps(a,b,c): return ((a,a*1.05,a*1.08),(b,b*1.03,b*1.06),(c,c*1.04,c*1.09))
    mats=(
        CriticalMaterial("lithium",(22_000.,23_500.,25_000.),(5_000.,6_800.,8_500.),caps(11_000,10_000,15_000),(19.,18.,17.),(7.0,7.7,9.0),(.15,.22,.48),.65,15_000.,1_500.),
        CriticalMaterial("nickel",(88_000.,94_000.,100_000.),(18_000.,24_000.,31_000.),caps(38_000,42_000,55_000),(15.,14.2,13.6),(6.5,6.9,8.0),(.12,.20,.42),.68,50_000.,4_000.),
        CriticalMaterial("cobalt",(22_000.,23_500.,25_000.),(6_000.,8_000.,10_000.),caps(8_000,9_000,14_000),(35.,33.,30.),(13.,14.,17.),(.18,.30,.70),.60,15_000.,1_000.),
        CriticalMaterial("graphite",(123_000.,130_000.,138_000.),(24_000.,31_000.,39_000.),caps(50_000,45_000,80_000),(5.2,5.0,4.7),(4.0,4.3,5.5),(.18,.25,.55),.65,70_000.,7_000.),
    )
    return CriticalMaterialConfig(materials=mats,supplier_names=suppliers)


def solve_critical_material_plan(cfg: CriticalMaterialConfig | None=None) -> CriticalMaterialSolution:
    cfg=cfg or demo_critical_material_config()
    if not cfg.materials: raise ValueError("at least one material required")
    S=len(cfg.supplier_names);T=len(cfg.materials[0].demand_kg)
    if any(len(m.demand_kg)!=T or len(m.recovered_supply_kg)!=T or len(m.supplier_capacity_kg)!=S for m in cfg.materials):
        raise ValueError("critical-material dimensions mismatch")
    idx={};k=0
    for mi,m in enumerate(cfg.materials):
        for t in range(T):
            for s in range(S): idx["virgin",mi,t,s]=k;k+=1
            idx["recovered",mi,t]=k;k+=1
            idx["inventory",mi,t]=k;k+=1
            idx["shortage",mi,t]=k;k+=1
    n=k;c=np.zeros(n);bounds=[(0,None)]*n
    for mi,m in enumerate(cfg.materials):
        for t in range(T):
            for s in range(S):
                c[idx["virgin",mi,t,s]]=(m.supplier_cost_per_kg[s]+cfg.risk_weight_per_kg*m.supplier_risk_score[s]+cfg.carbon_price_per_kgco2e*m.supplier_carbon_per_kg[s])
            c[idx["recovered",mi,t]]=cfg.recovered_cost_per_kg+cfg.carbon_price_per_kgco2e*cfg.recovered_carbon_per_kg
            c[idx["inventory",mi,t]]=cfg.inventory_cost_per_kg
            c[idx["shortage",mi,t]]=cfg.shortage_penalty_per_kg
            bounds[idx["recovered",mi,t]]=(0,m.recovered_supply_kg[t])
            bounds[idx["inventory",mi,t]]=(0,m.inventory_cap_kg)

    Aeq=[];beq=[];Aub=[];bub=[]
    for mi,m in enumerate(cfg.materials):
        for t in range(T):
            # material balance: virgin + recovered + prior inventory + shortage = demand + closing inventory
            a=np.zeros(n)
            for s in range(S): a[idx["virgin",mi,t,s]]=1
            a[idx["recovered",mi,t]]=1;a[idx["shortage",mi,t]]=1;a[idx["inventory",mi,t]]=-1
            rhs=m.demand_kg[t]-(m.initial_inventory_kg if t==0 else 0.)
            if t>0: a[idx["inventory",mi,t-1]]=1
            Aeq.append(a);beq.append(rhs)
            # supplier capacity
            for s in range(S):
                a=np.zeros(n);a[idx["virgin",mi,t,s]]=1
                Aub.append(a);bub.append(m.supplier_capacity_kg[s][t])
            # concentration cap: x_s <= share * total virgin
            for s in range(S):
                a=np.zeros(n);a[idx["virgin",mi,t,s]]=1-m.max_single_supplier_share
                for o in range(S):
                    if o!=s: a[idx["virgin",mi,t,o]]=-m.max_single_supplier_share
                Aub.append(a);bub.append(0.)
            # minimum recovered share of consumed demand (unless supply itself cannot support it; demo is feasible)
            a=np.zeros(n);a[idx["recovered",mi,t]]=-1
            Aub.append(a);bub.append(-cfg.minimum_recovered_share*m.demand_kg[t])

    res=linprog(c,A_ub=np.asarray(Aub),b_ub=np.asarray(bub),A_eq=np.asarray(Aeq),b_eq=np.asarray(beq),bounds=bounds,method="highs")
    if not res.success: raise RuntimeError(f"critical-material LP failed: {res.message}")
    x=res.x;rows=[];viol=[];tot_cost=tot_carbon=tot_risk=tot_v=tot_rec=tot_short=0.
    hhi={}
    for mi,m in enumerate(cfg.materials):
        virgin_by_supplier=np.zeros(S)
        for t in range(T):
            virgin=[float(x[idx["virgin",mi,t,s]]) for s in range(S)]
            rec=float(x[idx["recovered",mi,t]]);inv=float(x[idx["inventory",mi,t]]);sh=float(x[idx["shortage",mi,t]])
            prev=m.initial_inventory_kg if t==0 else float(x[idx["inventory",mi,t-1]])
            bal=abs(sum(virgin)+rec+prev+sh-m.demand_kg[t]-inv);viol.append(bal)
            totalv=sum(virgin)
            for s,q in enumerate(virgin):
                virgin_by_supplier[s]+=q
                viol.append(max(0.,q-m.supplier_capacity_kg[s][t]))
                viol.append(max(0.,q-m.max_single_supplier_share*totalv))
                tot_cost+=q*m.supplier_cost_per_kg[s];tot_carbon+=q*m.supplier_carbon_per_kg[s];tot_risk+=q*m.supplier_risk_score[s]
            viol.append(max(0.,cfg.minimum_recovered_share*m.demand_kg[t]-rec))
            tot_cost+=rec*cfg.recovered_cost_per_kg+inv*cfg.inventory_cost_per_kg+sh*cfg.shortage_penalty_per_kg
            tot_carbon+=rec*cfg.recovered_carbon_per_kg
            tot_v+=totalv;tot_rec+=rec;tot_short+=sh
            rows.append({"material":m.name,"period":t+1,"demand_kg":m.demand_kg[t],"virgin_by_supplier_kg":dict(zip(cfg.supplier_names,virgin)),"recovered_use_kg":rec,"closing_inventory_kg":inv,"shortage_kg":sh,"balance_error_kg":bal})
        vtot=float(virgin_by_supplier.sum())
        hhi[m.name]=float(np.sum((virgin_by_supplier/vtot)**2)) if vtot else 0.
    return CriticalMaterialSolution(
        status="OPTIMAL",objective=float(res.fun),total_cost=tot_cost,total_carbon_kgco2e=tot_carbon,total_risk_weighted_kg=tot_risk,
        total_virgin_kg=tot_v,total_recovered_use_kg=tot_rec,total_shortage_kg=tot_short,recovered_share=tot_rec/(tot_rec+tot_v) if tot_rec+tot_v else 0.,
        supplier_hhi_by_material=hhi,material_rows=rows,max_constraint_violation=max(viol,default=0.),solver="scipy.optimize.linprog/HiGHS")
