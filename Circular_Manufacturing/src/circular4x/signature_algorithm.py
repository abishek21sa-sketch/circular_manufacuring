from __future__ import annotations
from dataclasses import dataclass, asdict
import math
import os
import time
import numpy as np
from scipy.optimize import milp, Bounds, LinearConstraint

@dataclass(frozen=True)
class RecoveryFacility:
    name: str
    capacity_kg: float
    fixed_cost: float
    recovery_cost_per_kg: float

@dataclass(frozen=True)
class CircularMassScenario:
    name: str
    probability: float
    demand_kg: float
    yields: tuple[float, ...]

@dataclass(frozen=True)
class CircularMassConfig:
    facilities: tuple[RecoveryFacility, ...]
    virgin_cost_per_kg: float = 3.0
    shortage_penalty_per_kg: float = 80.0
    surplus_penalty_per_kg: float = 0.02
    min_recycled_content: float = 0.20
    max_virgin_share: float = 0.72
    risk_alpha: float = 0.90
    risk_aversion: float = 0.35
    # auto prefers the optional licensed Gurobi backend when available and
    # falls back to SciPy/HiGHS for portable installs. Use "gurobi" to make
    # the dependency mandatory for a governed production run.
    solver_backend: str = "auto"

@dataclass
class CircularMassSolution:
    status: str
    objective: float
    routed_kg: dict[str, float]
    open_facilities: dict[str, int]
    virgin_kg: list[float]
    shortage_kg: list[float]
    expected_shortage_kg: float
    cvar_shortage_kg: float
    expected_recovered_kg: float
    recycled_content_share: float
    max_constraint_violation: float
    solver: str = "scipy.optimize.milp"
    eta: float = 0.0
    alpha: float = 0.90
    scenario_details: list[dict] | None = None
    objective_components: dict[str, float] | None = None
    best_bound: float | None = None
    mip_gap: float | None = None
    runtime_seconds: float = 0.0
    variable_count: int = 0
    constraint_count: int = 0
    diagnostics: dict | None = None
    surplus_kg: list[float] | None = None
    def to_dict(self): return asdict(self)


def solve_circular_mass(scenarios: list[CircularMassScenario], cfg: CircularMassConfig) -> CircularMassSolution:
    if not scenarios: raise ValueError("at least one scenario required")
    if any(not math.isfinite(s.probability) or s.probability < 0 for s in scenarios):
        raise ValueError("scenario probabilities must be finite and nonnegative")
    if abs(sum(s.probability for s in scenarios)-1.0) > 1e-9: raise ValueError("probabilities must sum to one")
    if any(not math.isfinite(s.demand_kg) or s.demand_kg <= 0 for s in scenarios):
        raise ValueError("scenario demand_kg must be finite and positive")
    F=len(cfg.facilities); S=len(scenarios)
    if F == 0: raise ValueError("at least one recovery facility required")
    names=[f.name for f in cfg.facilities]
    if len(set(names)) != len(names): raise ValueError("facility names must be unique")
    if any(len(s.yields)!=F for s in scenarios): raise ValueError("yield dimension mismatch")
    if any(any(not math.isfinite(y) or not 0 <= y <= 1 for y in s.yields) for s in scenarios):
        raise ValueError("scenario yields must be finite and in [0,1]")
    if not 0 < cfg.risk_alpha < 1: raise ValueError("risk_alpha must be in (0,1)")
    if not 0 <= cfg.min_recycled_content <= 1: raise ValueError("min_recycled_content must be in [0,1]")
    if not 0 <= cfg.max_virgin_share <= 1: raise ValueError("max_virgin_share must be in [0,1]")
    if not math.isfinite(cfg.risk_aversion) or cfg.risk_aversion < 0: raise ValueError("risk_aversion must be finite and nonnegative")
    if not math.isfinite(cfg.surplus_penalty_per_kg) or cfg.surplus_penalty_per_kg < 0: raise ValueError("surplus_penalty_per_kg must be finite and nonnegative")
    if cfg.solver_backend not in {"auto", "scipy", "gurobi"}:
        raise ValueError("solver_backend must be one of: auto, scipy, gurobi")
    for fac in cfg.facilities:
        if any(not math.isfinite(v) or v < 0 for v in (fac.capacity_kg, fac.fixed_cost, fac.recovery_cost_per_kg)):
            raise ValueError("facility capacity and costs must be finite and nonnegative")

    idx={}; k=0
    for f in range(F): idx['x',f]=k; k+=1
    for f in range(F): idx['y',f]=k; k+=1
    for s in range(S): idx['v',s]=k; k+=1
    for s in range(S): idx['short',s]=k; k+=1
    for s in range(S): idx['surplus',s]=k; k+=1
    idx['eta']=k; k+=1
    for s in range(S): idx['u',s]=k; k+=1
    n=k
    c=np.zeros(n); lb=np.zeros(n); ub=np.full(n,np.inf); integ=np.zeros(n)
    # VaR is a free real threshold in the Rockafellar-Uryasev CVaR formulation.
    # It is nonnegative at the optimum for nonnegative shortage, but keeping the
    # mathematical domain explicit prevents the implementation from silently
    # changing the formulation if loss conventions evolve.
    lb[idx['eta']]=-np.inf
    for f,fac in enumerate(cfg.facilities):
        c[idx['x',f]]=fac.recovery_cost_per_kg
        c[idx['y',f]]=fac.fixed_cost; ub[idx['y',f]]=1; integ[idx['y',f]]=1
    for s,sc in enumerate(scenarios):
        ub[idx['v',s]]=cfg.max_virgin_share*sc.demand_kg
        c[idx['v',s]]=sc.probability*cfg.virgin_cost_per_kg
        c[idx['short',s]]=sc.probability*cfg.shortage_penalty_per_kg
        c[idx['surplus',s]]=sc.probability*cfg.surplus_penalty_per_kg
        c[idx['u',s]]=cfg.risk_aversion*sc.probability/(1-cfg.risk_alpha)
    c[idx['eta']]=cfg.risk_aversion

    rows=[]; lo=[]; hi=[]
    # Facility activation/capacity.
    for f,fac in enumerate(cfg.facilities):
        a=np.zeros(n); a[idx['x',f]]=1; a[idx['y',f]]=-fac.capacity_kg
        rows.append(a); lo.append(-np.inf); hi.append(0)
    # Scenario mass balance, recycled-content floor, and CVaR excess.
    for s,sc in enumerate(scenarios):
        a=np.zeros(n)
        for f in range(F): a[idx['x',f]]=sc.yields[f]
        a[idx['v',s]]=1; a[idx['short',s]]=1; a[idx['surplus',s]]=-1
        # The output of a shared first-stage recovery plan can exceed a
        # scenario's demand. Surplus is an explicit, auditable destination;
        # it prevents recycled-content reporting from exceeding 100% while
        # preserving the approved recourse variables.
        rows.append(a); lo.append(sc.demand_kg); hi.append(sc.demand_kg)
        a=np.zeros(n)
        for f in range(F): a[idx['x',f]]=-sc.yields[f]
        a[idx['surplus',s]]=1
        rows.append(a); lo.append(-np.inf); hi.append(-cfg.min_recycled_content*sc.demand_kg)
        a=np.zeros(n); a[idx['short',s]]=1; a[idx['eta']]-=1; a[idx['u',s]]-=1
        rows.append(a); lo.append(-np.inf); hi.append(0)

    A=np.asarray(rows); L=np.asarray(lo); H=np.asarray(hi)
    requested_backend = cfg.solver_backend
    effective_backend = "scipy"
    solver_name = "scipy.optimize.milp"
    best_bound = None
    mip_gap = None
    solver_message = ""
    objective_value = None
    started=time.perf_counter()
    if requested_backend in {"auto", "gurobi"}:
        try:
            import gurobipy as gp
        except ImportError:
            if requested_backend == "gurobi":
                raise RuntimeError("CIRCULAR-MASS requested solver_backend='gurobi' but gurobipy is not installed")
        else:
            model=gp.Model("circular_mass")
            model.Params.OutputFlag=0
            model.Params.TimeLimit=30.0
            model.Params.MIPGap=1e-9
            model.Params.NumericFocus=2
            model.Params.Seed=20260904
            variables=[]
            for j in range(n):
                lower=-gp.GRB.INFINITY if not np.isfinite(lb[j]) else float(lb[j])
                upper=gp.GRB.INFINITY if not np.isfinite(ub[j]) else float(ub[j])
                vtype=gp.GRB.INTEGER if integ[j] else gp.GRB.CONTINUOUS
                variables.append(model.addVar(lb=lower, ub=upper, vtype=vtype, name=f"z_{j}"))
            model.update()
            for i,row in enumerate(A):
                terms=gp.quicksum(float(row[j])*variables[j] for j in np.flatnonzero(row))
                if np.isfinite(L[i]) and np.isfinite(H[i]) and abs(L[i]-H[i]) <= 1e-12:
                    model.addConstr(terms == float(L[i]), name=f"c_{i}")
                else:
                    if np.isfinite(L[i]): model.addConstr(terms >= float(L[i]), name=f"c_{i}_lo")
                    if np.isfinite(H[i]): model.addConstr(terms <= float(H[i]), name=f"c_{i}_hi")
            model.setObjective(gp.quicksum(float(c[j])*variables[j] for j in range(n)), gp.GRB.MINIMIZE)
            model.optimize()
            if model.Status != gp.GRB.OPTIMAL:
                raise RuntimeError(f"CIRCULAR-MASS Gurobi MILP failed: status={model.Status}, message={model.Status}")
            z=np.asarray([v.X for v in variables], dtype=float)
            objective_value=float(model.ObjVal)
            runtime=float(model.Runtime)
            best_bound=float(model.ObjBound)
            mip_gap=float(model.MIPGap)
            solver_message=f"Gurobi {gp.gurobi.version()} status={model.Status}"
            effective_backend="gurobi"
            solver_name="gurobi"
    if effective_backend == "scipy":
        res=milp(c,integrality=integ,bounds=Bounds(lb,ub),constraints=LinearConstraint(A,L,H),
                 options={'time_limit':30.0,'mip_rel_gap':1e-9})
        runtime=time.perf_counter()-started
        if not res.success: raise RuntimeError(f"CIRCULAR-MASS MILP failed: {res.message}")
        z=res.x
        objective_value=float(res.fun)
        best_bound=getattr(res,'mip_dual_bound',None)
        mip_gap=getattr(res,'mip_gap',None)
        solver_message=str(res.message)
    routed={fac.name:float(z[idx['x',f]]) for f,fac in enumerate(cfg.facilities)}
    opens={fac.name:int(round(z[idx['y',f]])) for f,fac in enumerate(cfg.facilities)}
    virgin=[float(z[idx['v',s]]) for s in range(S)]
    shortage=[float(z[idx['short',s]]) for s in range(S)]
    surplus=[float(z[idx['surplus',s]]) for s in range(S)]
    recovered_output=[sum(sc.yields[f]*z[idx['x',f]] for f in range(F)) for sc in scenarios]
    recovered=[max(0.0,recovered_output[s]-surplus[s]) for s in range(S)]
    exp_short=sum(sc.probability*shortage[s] for s,sc in enumerate(scenarios))
    eta=float(z[idx['eta']])
    cvar=eta+sum(sc.probability*max(0.0,shortage[s]-eta) for s,sc in enumerate(scenarios))/(1-cfg.risk_alpha)
    exp_rec=sum(sc.probability*recovered[s] for s,sc in enumerate(scenarios))
    exp_dem=sum(sc.probability*sc.demand_kg for sc in scenarios)
    vals=A@z
    violations=[]
    for i,val in enumerate(vals):
        if np.isfinite(L[i]): violations.append(max(0.0,L[i]-val))
        if np.isfinite(H[i]): violations.append(max(0.0,val-H[i]))
    scenario_details=[]
    for s,sc in enumerate(scenarios):
        excess=max(0.0,shortage[s]-eta)
        scenario_details.append({
            'name':sc.name,
            'probability':float(sc.probability),
            'demand_kg':float(sc.demand_kg),
            'yields':list(map(float,sc.yields)),
            'recovery_output_kg':float(recovered_output[s]),
            'recovered_kg':float(recovered[s]),
            'surplus_kg':float(surplus[s]),
            'virgin_kg':float(virgin[s]),
            'shortage_kg':float(shortage[s]),
            'loss_kg':float(shortage[s]),
            'cvar_excess_kg':float(excess),
            'recycled_content_share':float(recovered[s]/sc.demand_kg),
        })
    components={
        'facility_fixed_cost':float(sum(fixed_cost for fixed_cost in (fac.fixed_cost*opens[fac.name] for fac in cfg.facilities))),
        'recovery_variable_cost':float(sum(fac.recovery_cost_per_kg*routed[fac.name] for fac in cfg.facilities)),
        'expected_virgin_cost':float(sum(sc.probability*cfg.virgin_cost_per_kg*virgin[s] for s,sc in enumerate(scenarios))),
        'expected_shortage_cost':float(sum(sc.probability*cfg.shortage_penalty_per_kg*shortage[s] for s,sc in enumerate(scenarios))),
        'expected_surplus_handling_cost':float(sum(sc.probability*cfg.surplus_penalty_per_kg*surplus[s] for s,sc in enumerate(scenarios))),
        'cvar_risk_premium':float(cfg.risk_aversion*cvar),
    }
    diagnostics={
        'message':solver_message,
        'success':True,
        'requested_solver_backend':requested_backend,
        'effective_solver_backend':effective_backend,
        'solver_name':solver_name,
        'integrality_verified':bool(np.all(np.abs(z*integ-np.rint(z*integ)) <= 1e-6)),
        'eta_domain':'R',
        'loss_definition':'scenario shortage kg; CVaR is applied to shortage only',
        'surplus_definition':'scenario recovery output not consumed by demand; explicitly spilled/held out of recycled-content numerator',
            'objective_reconciliation_error':float(abs(sum(components.values())-float(objective_value))),
        'expected_demand_kg':float(exp_dem),
    }
    return CircularMassSolution('OPTIMAL',float(objective_value),routed,opens,virgin,shortage,float(exp_short),float(cvar),
        float(exp_rec),float(exp_rec/exp_dem),float(max(violations,default=0.0)),
        eta=float(eta),alpha=float(cfg.risk_alpha),scenario_details=scenario_details,
        objective_components=components,best_bound=float(best_bound) if best_bound is not None else None,
        mip_gap=float(mip_gap) if mip_gap is not None else None,runtime_seconds=float(runtime),
        variable_count=int(n),constraint_count=int(len(rows)),diagnostics=diagnostics,surplus_kg=surplus,
        solver=solver_name)


def reference_problem(risk_aversion: float=.35, min_recycled_content: float=.20, solver_backend: str | None = None):
    selected_backend = (solver_backend or os.getenv("CIRCULAR_SOLVER_BACKEND", "auto")).strip().lower()
    cfg=CircularMassConfig(facilities=(
        RecoveryFacility('Hydro-North',500_000,180_000,2.1),
        RecoveryFacility('Direct-Midwest',360_000,240_000,1.7),
        RecoveryFacility('Pyro-East',420_000,155_000,2.6),
    ), min_recycled_content=min_recycled_content, risk_aversion=risk_aversion, solver_backend=selected_backend)
    scenarios=[
        CircularMassScenario('nominal',.55,1_000_000,(.91,.95,.84)),
        CircularMassScenario('yield-down',.25,1_040_000,(.77,.82,.70)),
        CircularMassScenario('severe',.20,1_080_000,(.62,.70,.58)),
    ]
    return scenarios,cfg
