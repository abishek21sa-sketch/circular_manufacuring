from __future__ import annotations
import math
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint
from circular_battery.routing.models import CVRPScenario, CVRPSolution

def _dist(a,b):
    return math.hypot(a.x_km-b.x_km,a.y_km-b.y_km)

def solve_cvrp(s: CVRPScenario) -> CVRPSolution:
    if s.vehicle_capacity_kg <= 0 or s.max_vehicles <= 0:
        raise ValueError('vehicle capacity and max_vehicles must be positive')
    nodes=(s.depot,)+s.customers
    n=len(nodes); customers=range(1,n)
    if any(c.pickup_kg<=0 for c in s.customers):
        raise ValueError('customer pickup_kg must be positive')
    if any(c.pickup_kg>s.vehicle_capacity_kg for c in s.customers):
        raise ValueError('single customer exceeds vehicle capacity')

    # Directed arc binaries x[i,j], i != j, plus load/order-like continuous u[i]
    arcs=[(i,j) for i in range(n) for j in range(n) if i!=j]
    xidx={a:k for k,a in enumerate(arcs)}
    uidx={i:len(arcs)+(i-1) for i in customers}
    N=len(arcs)+len(s.customers)
    c=np.zeros(N)
    for (i,j),k in xidx.items():
        c[k]=_dist(nodes[i],nodes[j])*s.distance_cost_per_km
        if i==0: c[k]+=s.vehicle_fixed_cost
    integ=np.zeros(N)
    lb=np.zeros(N); ub=np.full(N,np.inf)
    for k in xidx.values(): integ[k]=1; ub[k]=1
    for i in customers:
        lb[uidx[i]]=nodes[i].pickup_kg
        ub[uidx[i]]=s.vehicle_capacity_kg

    rows=[]; lows=[]; highs=[]
    # Each customer has exactly one incoming and outgoing arc.
    for j in customers:
        a=np.zeros(N)
        for i in range(n):
            if i!=j: a[xidx[(i,j)]]=1
        rows.append(a);lows.append(1);highs.append(1)
        a=np.zeros(N)
        for k in range(n):
            if k!=j: a[xidx[(j,k)]]=1
        rows.append(a);lows.append(1);highs.append(1)
    # depot departures = depot arrivals, bounded by vehicle count.
    out=np.zeros(N); inc=np.zeros(N)
    for j in customers: out[xidx[(0,j)]]=1; inc[xidx[(j,0)]]=1
    rows.append(out-inc);lows.append(0);highs.append(0)
    rows.append(out);lows.append(1);highs.append(s.max_vehicles)

    # Capacity/subtour elimination: cumulative pickup load MTZ.
    Q=s.vehicle_capacity_kg
    for i in customers:
        for j in customers:
            if i==j: continue
            # u_i - u_j + Q*x_ij <= Q - demand_j
            a=np.zeros(N);a[uidx[i]]=1;a[uidx[j]]=-1;a[xidx[(i,j)]]=Q
            rows.append(a);lows.append(-np.inf);highs.append(Q-nodes[j].pickup_kg)

    cons=LinearConstraint(np.asarray(rows),np.asarray(lows),np.asarray(highs))
    res=milp(c,integrality=integ,bounds=Bounds(lb,ub),constraints=cons,
             options={'time_limit':30.0,'mip_rel_gap':1e-9})
    if not res.success:
        raise RuntimeError(f'CVRP MILP failed: {res.message}')
    x=res.x
    selected={(i,j) for (i,j),k in xidx.items() if x[k]>.5}

    routes=[]; route_loads=[]; route_dists=[]
    starts=sorted(j for j in customers if (0,j) in selected)
    visited=set()
    for start in starts:
        route=[0,start];visited.add(start);cur=start
        guard=0
        while cur!=0 and guard<n+2:
            nxt=[j for j in range(n) if j!=cur and (cur,j) in selected]
            if len(nxt)!=1: raise RuntimeError('route reconstruction failed')
            cur=nxt[0];route.append(cur)
            if cur!=0: visited.add(cur)
            guard+=1
        if route[-1]!=0: raise RuntimeError('route does not return to depot')
        routes.append([nodes[i].name for i in route])
        route_loads.append(sum(nodes[i].pickup_kg for i in route if i!=0))
        route_dists.append(sum(_dist(nodes[route[k]],nodes[route[k+1]]) for k in range(len(route)-1)))
    if visited!=set(customers):
        raise RuntimeError('not all customers reconstructed in routes')

    violations=[]
    violations += [max(0.,load-Q) for load in route_loads]
    violations.append(max(0.,len(routes)-s.max_vehicles))
    violations.append(abs(len(visited)-len(s.customers)))
    # Every customer once.
    for j in customers:
        count=sum(1 for r in routes for name in r[1:-1] if name==nodes[j].name)
        violations.append(abs(count-1))
    total_distance=sum(route_dists)
    variable=total_distance*s.distance_cost_per_km
    objective=variable+len(routes)*s.vehicle_fixed_cost
    return CVRPSolution(
        status='OPTIMAL',objective_cost=objective,total_distance_km=total_distance,
        total_kgco2e=total_distance*s.kgco2e_per_km,vehicles_used=len(routes),
        routes=routes,route_loads_kg=route_loads,route_distances_km=route_dists,
        max_constraint_violation=max(violations,default=0.),solver='scipy.optimize.milp',
        mip_gap=float(getattr(res,'mip_gap',0.0)) if getattr(res,'mip_gap',None) is not None else None,
    )
