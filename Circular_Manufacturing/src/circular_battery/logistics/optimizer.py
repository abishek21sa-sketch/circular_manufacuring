from __future__ import annotations
import math
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from circular_battery.logistics.models import ReverseLogisticsScenario, ReverseLogisticsSolution

def distance_km(a, b):
    return math.hypot(a.x_km-b.x_km, a.y_km-b.y_km)

def solve_reverse_logistics(s: ReverseLogisticsScenario):
    if not (0 <= s.collection_rate <= 1):
        raise ValueError("collection_rate must be in [0,1].")
    C=len(s.collections); F=len(s.facilities)
    # Variables:
    # reman flow c->f for reman facilities, recycle flow c->f for recycle facilities,
    # disposal c, open facility f.
    flow_idx={}
    k=0
    for c in range(C):
        for f in range(F):
            flow_idx[(c,f)] = k; k+=1
    disposal_idx={c:k+c for c in range(C)}
    k += C
    open_idx={f:k+f for f in range(F)}
    n=k+F

    cvec=np.zeros(n)
    for ci,col in enumerate(s.collections):
        for fi,fac in enumerate(s.facilities):
            d=distance_km(col,fac)
            cvec[flow_idx[(ci,fi)]] = fac.processing_cost_per_kg + d*s.transport_cost_per_kg_km
        cvec[disposal_idx[ci]]=s.disposal_cost_per_kg
    for fi,fac in enumerate(s.facilities):
        cvec[open_idx[fi]]=fac.fixed_cost

    lb=np.zeros(n); ub=np.full(n,np.inf)
    integrality=np.zeros(n)
    for fi in range(F):
        ub[open_idx[fi]]=1
        integrality[open_idx[fi]]=1

    rows=[]; lows=[]; highs=[]
    collected=[]
    # Every collected kg must go to a facility or disposal.
    for ci,col in enumerate(s.collections):
        supply=col.returns_kg*s.collection_rate
        collected.append(supply)
        a=np.zeros(n)
        for fi in range(F): a[flow_idx[(ci,fi)]]=1
        a[disposal_idx[ci]]=1
        rows.append(a); lows.append(supply); highs.append(supply)

        # Reman flow cannot exceed the reman-eligible share.
        a=np.zeros(n)
        for fi,fac in enumerate(s.facilities):
            if fac.kind=="reman": a[flow_idx[(ci,fi)]]=1
        rows.append(a); lows.append(-np.inf); highs.append(supply*col.reman_eligible_share)

    # Facility capacity gated by open binary.
    for fi,fac in enumerate(s.facilities):
        a=np.zeros(n)
        for ci in range(C): a[flow_idx[(ci,fi)]]=1
        a[open_idx[fi]]=-fac.capacity_kg
        rows.append(a); lows.append(-np.inf); highs.append(0)

    # Network-level maximum disposal share.
    a=np.zeros(n)
    for ci in range(C): a[disposal_idx[ci]]=1
    rows.append(a); lows.append(-np.inf); highs.append(sum(collected)*s.max_disposal_share)

    A=np.array(rows)
    cons=LinearConstraint(A,np.array(lows),np.array(highs))
    res=milp(cvec,integrality=integrality,bounds=Bounds(lb,ub),constraints=cons,
             options={"time_limit":30.0,"mip_rel_gap":1e-9})
    if not res.success:
        raise RuntimeError(f"Reverse-logistics MILP failed: {res.message}")
    x=res.x

    flows=[]
    tcost=pcost=fcost=dcost=0.0
    tco2=pco2=dco2=0.0
    processed=disposed=0.0
    for ci,col in enumerate(s.collections):
        for fi,fac in enumerate(s.facilities):
            q=float(x[flow_idx[(ci,fi)]])
            if q <= 1e-7: continue
            d=distance_km(col,fac)
            tc=q*d*s.transport_cost_per_kg_km
            pc=q*fac.processing_cost_per_kg
            te=q*d*s.transport_kgco2e_per_kg_km
            pe=q*fac.processing_kgco2e_per_kg
            tcost+=tc;pcost+=pc;tco2+=te;pco2+=pe;processed+=q
            flows.append({
                "collection":col.name,"facility":fac.name,"pathway":fac.kind,
                "kg":q,"distance_km":d,"transport_cost":tc,
                "processing_cost":pc,"transport_kgco2e":te,"processing_kgco2e":pe
            })
        q=float(x[disposal_idx[ci]])
        disposed += q; dcost += q*s.disposal_cost_per_kg; dco2 += q*s.disposal_kgco2e_per_kg

    opened={}
    for fi,fac in enumerate(s.facilities):
        val=int(round(x[open_idx[fi]]))
        opened[fac.name]=val
        fcost += val*fac.fixed_cost

    disposal_map={s.collections[ci].name:float(x[disposal_idx[ci]]) for ci in range(C)}

    # Independent post-solve feasibility audit.
    violations=[]
    for ci,col in enumerate(s.collections):
        sent=sum(float(x[flow_idx[(ci,fi)]]) for fi in range(F))+float(x[disposal_idx[ci]])
        violations.append(abs(sent-collected[ci]))
        reman=sum(float(x[flow_idx[(ci,fi)]]) for fi,fac in enumerate(s.facilities) if fac.kind=="reman")
        violations.append(max(0.0,reman-collected[ci]*col.reman_eligible_share))
    for fi,fac in enumerate(s.facilities):
        throughput=sum(float(x[flow_idx[(ci,fi)]]) for ci in range(C))
        violations.append(max(0.0,throughput-fac.capacity_kg*opened[fac.name]))
    violations.append(max(0.0,disposed-sum(collected)*s.max_disposal_share))

    return ReverseLogisticsSolution(
        status="OPTIMAL", objective_cost=float(res.fun),
        transport_cost=tcost,processing_cost=pcost,fixed_cost=fcost,disposal_cost=dcost,
        transport_kgco2e=tco2,processing_kgco2e=pco2,disposal_kgco2e=dco2,
        total_kgco2e=tco2+pco2+dco2,
        opened_facilities=opened,flows=flows,disposal_by_collection=disposal_map,
        collected_kg=sum(collected),processed_kg=processed,disposed_kg=disposed,
        max_constraint_violation=max(violations) if violations else 0.0,
        solver="scipy.optimize.milp",
        mip_gap=float(getattr(res,"mip_gap",0.0)) if getattr(res,"mip_gap",None) is not None else None,
    )
