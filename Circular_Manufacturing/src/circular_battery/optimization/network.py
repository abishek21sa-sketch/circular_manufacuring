from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

@dataclass(frozen=True)
class NetworkScenario:
    periods: int = 3
    demand_kg: tuple[float,...] = (900_000., 960_000., 1_020_000.)
    returns_kg: tuple[float,...] = (360_000., 430_000., 510_000.)
    collection_rate: float = .86
    recycle_yield: float = .90
    reman_yield: float = .82
    recycle_capacity_kg: float = 350_000.
    reman_capacity_kg: float = 150_000.
    fixed_recycle_cost: float = 175_000.
    fixed_reman_cost: float = 650_000.
    virgin_cost_per_kg: float = 7.2
    recycle_cost_per_kg: float = 2.4
    reman_cost_per_kg: float = 3.1
    disposal_cost_per_kg: float = .55
    inventory_cost_per_kg: float = .08
    virgin_carbon_per_kg: float = 8.5
    recycle_carbon_per_kg: float = 2.2
    reman_carbon_per_kg: float = 1.6
    disposal_carbon_per_kg: float = .7
    initial_inventory_kg: float = 0.
    max_inventory_kg: float = 250_000.

@dataclass
class NetworkSolution:
    status: str
    objective: float
    total_cost: float
    total_carbon_kgco2e: float
    virgin_kg: float
    recovered_use_kg: float
    disposal_kg: float
    recycle_open: int
    reman_open: int
    recycled_content_rate: float
    max_constraint_violation: float
    solver: str
    mip_gap: float | None
    runtime_seconds: float | None
    period_rows: list[dict]
    def to_dict(self): return asdict(self)

def _indices(T):
    # per period: virgin, recycle_feed, reman_feed, inventory, disposal
    names = ("virgin","recycle","reman","inventory","disposal")
    idx = {(n,t): t*5+i for t in range(T) for i,n in enumerate(names)}
    idx["open_recycle"] = T*5
    idx["open_reman"] = T*5+1
    return idx, T*5+2

def solve_network(s: NetworkScenario, carbon_price_per_kg=0.0, virgin_penalty_per_kg=0.0):
    T=s.periods
    if not (len(s.demand_kg)==len(s.returns_kg)==T): raise ValueError("period vector mismatch")
    idx,n=_indices(T)
    c=np.zeros(n)
    for t in range(T):
        c[idx["virgin",t]]=s.virgin_cost_per_kg + carbon_price_per_kg*s.virgin_carbon_per_kg + virgin_penalty_per_kg
        c[idx["recycle",t]]=s.recycle_cost_per_kg + carbon_price_per_kg*s.recycle_carbon_per_kg
        c[idx["reman",t]]=s.reman_cost_per_kg + carbon_price_per_kg*s.reman_carbon_per_kg
        c[idx["inventory",t]]=s.inventory_cost_per_kg
        c[idx["disposal",t]]=s.disposal_cost_per_kg + carbon_price_per_kg*s.disposal_carbon_per_kg
    c[idx["open_recycle"]]=s.fixed_recycle_cost
    c[idx["open_reman"]]=s.fixed_reman_cost
    lb=np.zeros(n); ub=np.full(n,np.inf)
    ub[idx["open_recycle"]]=1; ub[idx["open_reman"]]=1
    for t in range(T): ub[idx["inventory",t]]=s.max_inventory_kg
    integrality=np.zeros(n); integrality[idx["open_recycle"]]=1; integrality[idx["open_reman"]]=1

    rows=[]; lows=[]; highs=[]
    # Material balance: virgin + recovered outputs + prior inventory - closing inventory = demand
    for t in range(T):
        a=np.zeros(n)
        a[idx["virgin",t]]=1
        a[idx["recycle",t]]=s.recycle_yield
        a[idx["reman",t]]=s.reman_yield
        if t>0: a[idx["inventory",t-1]]=1
        a[idx["inventory",t]]=-1
        rows.append(a); lows.append(s.demand_kg[t]); highs.append(s.demand_kg[t])
        # Collected returns split among recycle, reman, disposal.
        a=np.zeros(n); a[idx["recycle",t]]=1; a[idx["reman",t]]=1; a[idx["disposal",t]]=1
        collected=s.returns_kg[t]*s.collection_rate
        rows.append(a); lows.append(collected); highs.append(collected)
        # Facility capacities gated by binaries.
        a=np.zeros(n); a[idx["recycle",t]]=1; a[idx["open_recycle"]]=-s.recycle_capacity_kg
        rows.append(a); lows.append(-np.inf); highs.append(0)
        a=np.zeros(n); a[idx["reman",t]]=1; a[idx["open_reman"]]=-s.reman_capacity_kg
        rows.append(a); lows.append(-np.inf); highs.append(0)

    cons=LinearConstraint(np.array(rows), np.array(lows), np.array(highs))
    res=milp(c, integrality=integrality, bounds=Bounds(lb,ub), constraints=cons,
             options={"time_limit":30.0, "mip_rel_gap":1e-9})
    if not res.success: raise RuntimeError(f"MILP failed: {res.message}")
    x=res.x
    rows_out=[]
    total_cost=0.; carbon=0.; virgin=0.; recovered=0.; disposal=0.
    for t in range(T):
        v=x[idx["virgin",t]]; rf=x[idx["recycle",t]]; mf=x[idx["reman",t]]
        inv=x[idx["inventory",t]]; d=x[idx["disposal",t]]
        ru=rf*s.recycle_yield+mf*s.reman_yield
        cost=v*s.virgin_cost_per_kg+rf*s.recycle_cost_per_kg+mf*s.reman_cost_per_kg+d*s.disposal_cost_per_kg+inv*s.inventory_cost_per_kg
        carb=v*s.virgin_carbon_per_kg+rf*s.recycle_carbon_per_kg+mf*s.reman_carbon_per_kg+d*s.disposal_carbon_per_kg
        total_cost+=cost; carbon+=carb; virgin+=v; recovered+=ru; disposal+=d
        rows_out.append({"period":t+1,"virgin_kg":v,"recycle_feed_kg":rf,"reman_feed_kg":mf,
                         "closing_inventory_kg":inv,"disposal_kg":d,"recovered_use_kg":ru})
    ro=int(round(x[idx["open_recycle"]])); mo=int(round(x[idx["open_reman"]]))
    total_cost += ro*s.fixed_recycle_cost+mo*s.fixed_reman_cost
    audit=audit_solution(s, rows_out, ro, mo)
    return NetworkSolution("OPTIMAL",float(res.fun),total_cost,carbon,virgin,recovered,disposal,ro,mo,
        recovered/sum(s.demand_kg),audit["max_constraint_violation"],"scipy.optimize.milp",
        float(getattr(res,"mip_gap",0.0)) if getattr(res,"mip_gap",None) is not None else None,None,rows_out)

def audit_solution(s, rows, recycle_open, reman_open):
    violations=[]
    prior=s.initial_inventory_kg
    for t,r in enumerate(rows):
        recovered=r["recycle_feed_kg"]*s.recycle_yield+r["reman_feed_kg"]*s.reman_yield
        violations.append(abs(r["virgin_kg"]+recovered+prior-r["closing_inventory_kg"]-s.demand_kg[t]))
        violations.append(abs(r["recycle_feed_kg"]+r["reman_feed_kg"]+r["disposal_kg"]-s.returns_kg[t]*s.collection_rate))
        violations.append(max(0.,r["recycle_feed_kg"]-s.recycle_capacity_kg*recycle_open))
        violations.append(max(0.,r["reman_feed_kg"]-s.reman_capacity_kg*reman_open))
        violations.append(max(0.,r["closing_inventory_kg"]-s.max_inventory_kg))
        prior=r["closing_inventory_kg"]
    return {"max_constraint_violation":max(violations,default=0.),"passed":max(violations,default=0.)<1e-5}

def brute_force_facility_oracle(s):
    # Independent facility-binary oracle: fix each of 4 configurations and solve continuous subproblem.
    best=None
    for ro in (0,1):
        for mo in (0,1):
            ss=NetworkScenario(**{**s.__dict__,
                "recycle_capacity_kg":s.recycle_capacity_kg*ro,
                "reman_capacity_kg":s.reman_capacity_kg*mo,
                "fixed_recycle_cost":0.,"fixed_reman_cost":0.})
            try:
                sol=solve_network(ss)
            except RuntimeError:
                continue
            cost=sol.total_cost+ro*s.fixed_recycle_cost+mo*s.fixed_reman_cost
            candidate=(cost,ro,mo)
            if best is None or candidate[0]<best[0]: best=candidate
    if best is None: raise RuntimeError("oracle found no feasible facility configuration")
    return {"objective":best[0],"recycle_open":best[1],"reman_open":best[2]}

def solve_with_gurobi(s: NetworkScenario, carbon_price_per_kg=0.0, virgin_penalty_per_kg=0.0):
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except Exception as e:
        raise RuntimeError("gurobipy is not installed; install it for licensed Phase 3 acceptance.") from e
    m=gp.Model("circular_closed_loop")
    m.Params.OutputFlag=0
    T=range(s.periods)
    v=m.addVars(T,lb=0,name="virgin"); r=m.addVars(T,lb=0,name="recycle")
    q=m.addVars(T,lb=0,name="reman"); inv=m.addVars(T,lb=0,ub=s.max_inventory_kg,name="inventory")
    d=m.addVars(T,lb=0,name="disposal"); yr=m.addVar(vtype=GRB.BINARY,name="open_recycle"); ym=m.addVar(vtype=GRB.BINARY,name="open_reman")
    for t in T:
        prior=s.initial_inventory_kg if t==0 else inv[t-1]
        m.addConstr(v[t]+s.recycle_yield*r[t]+s.reman_yield*q[t]+prior-inv[t]==s.demand_kg[t])
        m.addConstr(r[t]+q[t]+d[t]==s.returns_kg[t]*s.collection_rate)
        m.addConstr(r[t]<=s.recycle_capacity_kg*yr)
        m.addConstr(q[t]<=s.reman_capacity_kg*ym)
    cost=gp.quicksum(v[t]*s.virgin_cost_per_kg+r[t]*s.recycle_cost_per_kg+q[t]*s.reman_cost_per_kg+d[t]*s.disposal_cost_per_kg+inv[t]*s.inventory_cost_per_kg for t in T)+yr*s.fixed_recycle_cost+ym*s.fixed_reman_cost
    carbon=gp.quicksum(v[t]*s.virgin_carbon_per_kg+r[t]*s.recycle_carbon_per_kg+q[t]*s.reman_carbon_per_kg+d[t]*s.disposal_carbon_per_kg for t in T)
    virgin=gp.quicksum(v[t] for t in T)
    m.setObjective(cost+carbon_price_per_kg*carbon+virgin_penalty_per_kg*virgin,GRB.MINIMIZE)
    m.optimize()
    if m.Status != GRB.OPTIMAL: raise RuntimeError(f"Gurobi status {m.Status}")
    rows=[]; tc=0.; carb=0.; vv=0.; rec=0.; disp=0.
    for t in T:
        ru=s.recycle_yield*r[t].X+s.reman_yield*q[t].X
        cc=v[t].X*s.virgin_cost_per_kg+r[t].X*s.recycle_cost_per_kg+q[t].X*s.reman_cost_per_kg+d[t].X*s.disposal_cost_per_kg+inv[t].X*s.inventory_cost_per_kg
        cb=v[t].X*s.virgin_carbon_per_kg+r[t].X*s.recycle_carbon_per_kg+q[t].X*s.reman_carbon_per_kg+d[t].X*s.disposal_carbon_per_kg
        tc+=cc; carb+=cb; vv+=v[t].X; rec+=ru; disp+=d[t].X
        rows.append({"period":t+1,"virgin_kg":v[t].X,"recycle_feed_kg":r[t].X,"reman_feed_kg":q[t].X,"closing_inventory_kg":inv[t].X,"disposal_kg":d[t].X,"recovered_use_kg":ru})
    ro=int(round(yr.X)); mo=int(round(ym.X)); tc+=ro*s.fixed_recycle_cost+mo*s.fixed_reman_cost
    audit=audit_solution(s,rows,ro,mo)
    return NetworkSolution("OPTIMAL",m.ObjVal,tc,carb,vv,rec,disp,ro,mo,rec/sum(s.demand_kg),
        audit["max_constraint_violation"],"gurobi",m.MIPGap,m.Runtime,rows)
