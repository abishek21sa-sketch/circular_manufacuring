from __future__ import annotations
import numpy as np
from scipy.optimize import linprog
from circular_battery.planning.models import PlanningScenario, PlanningSolution

VARS=("regular","overtime","virgin","recovered_use","recovered_inventory","fg_inventory","shortage")

def _indices(T):
    return {(name,t):t*len(VARS)+i for t in range(T) for i,name in enumerate(VARS)}, T*len(VARS)

def solve_production_plan(s: PlanningScenario):
    T=len(s.demand_packs)
    if not all(len(v)==T for v in (s.recovered_supply_kg,s.regular_capacity_packs,s.overtime_capacity_packs)):
        raise ValueError("All planning vectors must have the same length.")
    if not (0 <= s.min_recycled_content <= s.max_recycled_content <= 1):
        raise ValueError("Invalid recycled-content bounds.")

    idx,n=_indices(T)
    c=np.zeros(n)
    bounds=[]
    for t in range(T):
        c[idx["regular",t]]=s.regular_production_cost_per_pack
        c[idx["overtime",t]]=s.overtime_production_cost_per_pack
        c[idx["virgin",t]]=s.virgin_material_cost_per_kg
        c[idx["recovered_use",t]]=s.recovered_material_cost_per_kg
        c[idx["recovered_inventory",t]]=s.recovered_inventory_cost_per_kg
        c[idx["fg_inventory",t]]=s.finished_goods_holding_cost_per_pack
        c[idx["shortage",t]]=s.shortage_penalty_per_pack

    # Equality constraints: material balance, recovered inventory balance, FG balance.
    Aeq=[]; beq=[]
    for t in range(T):
        # virgin + recovered = pack_mass * production
        a=np.zeros(n)
        a[idx["virgin",t]]=1
        a[idx["recovered_use",t]]=1
        a[idx["regular",t]]=-s.pack_mass_kg
        a[idx["overtime",t]]=-s.pack_mass_kg
        Aeq.append(a);beq.append(0.)

        # previous recovered inventory + supply = use + closing recovered inventory
        a=np.zeros(n)
        a[idx["recovered_use",t]]=1
        a[idx["recovered_inventory",t]]=1
        if t>0:
            a[idx["recovered_inventory",t-1]]=-1
            rhs=s.recovered_supply_kg[t]
        else:
            rhs=s.initial_recovered_inventory_kg+s.recovered_supply_kg[t]
        Aeq.append(a);beq.append(rhs)

        # previous FG + production + shortage = demand + closing FG
        a=np.zeros(n)
        a[idx["regular",t]]=1
        a[idx["overtime",t]]=1
        a[idx["shortage",t]]=1
        a[idx["fg_inventory",t]]=-1
        if t>0:
            a[idx["fg_inventory",t-1]]=1
            rhs=s.demand_packs[t]
        else:
            rhs=s.demand_packs[t]-s.initial_finished_goods_packs
        Aeq.append(a);beq.append(rhs)

    Aub=[]; bub=[]
    for t in range(T):
        # capacity
        a=np.zeros(n);a[idx["regular",t]]=1;Aub.append(a);bub.append(s.regular_capacity_packs[t])
        a=np.zeros(n);a[idx["overtime",t]]=1;Aub.append(a);bub.append(s.overtime_capacity_packs[t])

        # recovered content <= max * material requirement
        a=np.zeros(n)
        a[idx["recovered_use",t]]=1
        a[idx["regular",t]]=-s.max_recycled_content*s.pack_mass_kg
        a[idx["overtime",t]]=-s.max_recycled_content*s.pack_mass_kg
        Aub.append(a);bub.append(0.)

        # recovered content >= min * material requirement
        a=np.zeros(n)
        a[idx["recovered_use",t]]=-1
        a[idx["regular",t]]=s.min_recycled_content*s.pack_mass_kg
        a[idx["overtime",t]]=s.min_recycled_content*s.pack_mass_kg
        Aub.append(a);bub.append(0.)

        # safety stock requirement except final period; shortage remains allowed,
        # but safety stock forces proactive capacity planning when feasible.
        if t < T-1:
            target=s.safety_stock_fraction_next_period*s.demand_packs[t+1]
            a=np.zeros(n);a[idx["fg_inventory",t]]=-1
            Aub.append(a);bub.append(-target)

    for t in range(T):
        bounds.extend([
            (0,s.regular_capacity_packs[t]),
            (0,s.overtime_capacity_packs[t]),
            (0,None),
            (0,None),
            (0,s.max_recovered_inventory_kg),
            (0,s.max_finished_goods_inventory_packs),
            (0,None),
        ])

    res=linprog(c,A_ub=np.array(Aub),b_ub=np.array(bub),A_eq=np.array(Aeq),b_eq=np.array(beq),
                bounds=bounds,method="highs")
    if not res.success:
        raise RuntimeError(f"Production planning LP failed: {res.message}")
    x=res.x

    rows=[]
    total_regular=total_ot=total_short=total_v=total_r=0.
    violations=[]
    for t in range(T):
        reg=x[idx["regular",t]];ot=x[idx["overtime",t]]
        v=x[idx["virgin",t]];ru=x[idx["recovered_use",t]]
        rinv=x[idx["recovered_inventory",t]];fg=x[idx["fg_inventory",t]]
        sh=x[idx["shortage",t]]
        production=reg+ot
        material=s.pack_mass_kg*production
        recycled_rate=ru/material if material else 0.
        util=reg/s.regular_capacity_packs[t] if s.regular_capacity_packs[t] else 0.
        prev_r=s.initial_recovered_inventory_kg if t==0 else x[idx["recovered_inventory",t-1]]
        prev_fg=s.initial_finished_goods_packs if t==0 else x[idx["fg_inventory",t-1]]
        mat_err=abs(v+ru-material)
        rinv_err=abs(prev_r+s.recovered_supply_kg[t]-ru-rinv)
        fg_err=abs(prev_fg+production+sh-s.demand_packs[t]-fg)
        violations.extend([mat_err,rinv_err,fg_err,max(0.,reg-s.regular_capacity_packs[t]),max(0.,ot-s.overtime_capacity_packs[t])])
        violations.append(max(0.,recycled_rate-s.max_recycled_content))
        if production>1e-8: violations.append(max(0.,s.min_recycled_content-recycled_rate))
        rows.append({
            "period":t+1,"demand_packs":s.demand_packs[t],"regular_packs":reg,"overtime_packs":ot,
            "production_packs":production,"shortage_packs":sh,"closing_fg_inventory_packs":fg,
            "virgin_kg":v,"recovered_use_kg":ru,"closing_recovered_inventory_kg":rinv,
            "recycled_content_rate":recycled_rate,"regular_capacity_utilization":util,
            "material_balance_error_kg":mat_err,"recovered_inventory_balance_error_kg":rinv_err,
            "finished_goods_balance_error_packs":fg_err,
        })
        total_regular+=reg;total_ot+=ot;total_short+=sh;total_v+=v;total_r+=ru

    demand=sum(s.demand_packs)
    total_material=total_v+total_r
    avg_util=sum(r["regular_capacity_utilization"] for r in rows)/T
    return PlanningSolution(
        status="OPTIMAL",objective_cost=float(res.fun),
        total_regular_packs=total_regular,total_overtime_packs=total_ot,total_shortage_packs=total_short,
        service_level=1-total_short/demand if demand else 1.0,
        total_virgin_kg=total_v,total_recovered_use_kg=total_r,
        recycled_content_rate=total_r/total_material if total_material else 0.,
        avg_regular_capacity_utilization=avg_util,
        max_constraint_violation=max(violations) if violations else 0.,
        period_rows=rows,solver="scipy.optimize.linprog/HiGHS",
    )
