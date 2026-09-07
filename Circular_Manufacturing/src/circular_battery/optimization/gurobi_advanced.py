from __future__ import annotations
from dataclasses import asdict
from circular_battery.optimization.stochastic_network import demo_stochastic_config

SERVICE_OBJECTIVE_ABS_TOL = 1e-6


def _collect_multiobjective_pass_metrics(model):
    """Return documented per-pass metrics for a Gurobi multi-objective solve.

    Gurobi intentionally does not expose the ordinary model-level MIPGap
    attribute for multi-objective models. Each optimization pass has its own
    bound/gap/status, queried through ObjPassN* attributes.
    """
    count = int(model.NumObjPasses)
    passes = []
    for pass_number in range(count):
        model.Params.ObjPassNumber = pass_number
        passes.append({
            "pass_number": pass_number,
            "status": int(model.ObjPassNStatus),
            "mip_gap": float(model.ObjPassNMipGap),
            "runtime_seconds": float(model.ObjPassNRuntime),
            "objective_value": float(model.ObjPassNObjVal),
            "objective_bound": float(model.ObjPassNObjBound),
        })
    model.Params.ObjPassNumber = -1
    return passes


def solve_gurobi_multiobjective(scenario):
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except Exception as e:
        raise RuntimeError('gurobipy is required for licensed advanced acceptance') from e
    cfg=demo_stochastic_config();F=len(cfg.facilities);T=len(scenario.demand_kg)
    m=gp.Model('circular_phase10_multiobjective');m.Params.OutputFlag=0
    TT=range(T);FF=range(F)
    y=m.addVars(FF,vtype=GRB.BINARY,name='open')
    e=m.addVars(FF,vtype=GRB.INTEGER,lb=0,name='expand')
    v=m.addVars(TT,lb=0,name='virgin');inv=m.addVars(TT,lb=0,ub=cfg.max_inventory_kg,name='inventory')
    d=m.addVars(TT,lb=0,name='disposal');sh=m.addVars(TT,lb=0,name='shortage')
    q=m.addVars(TT,FF,lb=0,name='feed')
    for f,fac in enumerate(cfg.facilities): m.addConstr(e[f]<=fac.max_expansion_units*y[f],name=f'expansion_gate_{f}')
    for t in TT:
        recovered=gp.quicksum(q[t,f]*(scenario.recycle_yield if cfg.facilities[f].kind=='recycle' else scenario.reman_yield) for f in FF)
        prior=cfg.initial_inventory_kg if t==0 else inv[t-1]
        scrap=.95*scenario.internal_scrap_supply_kg[t]
        m.addConstr(v[t]+recovered+scrap+prior+sh[t]-inv[t]==scenario.demand_kg[t],name=f'material_{t}')
        collected=scenario.returns_kg[t]*scenario.collection_rate*(1-scenario.second_life_share)
        m.addConstr(gp.quicksum(q[t,f] for f in FF)+d[t]==collected,name=f'returns_{t}')
        m.addConstr(gp.quicksum(q[t,f] for f in FF if cfg.facilities[f].kind=='reman')<=collected*scenario.reman_eligible_share,name=f'reman_elig_{t}')
        m.addConstr(sh[t]<=cfg.max_shortage_share*scenario.demand_kg[t],name=f'service_{t}')
        m.addConstr(d[t]<=cfg.max_disposal_share*collected,name=f'disposal_{t}')
        for f,fac in enumerate(cfg.facilities):
            cap=(fac.base_capacity_kg*y[f]+fac.expansion_unit_kg*e[f])*scenario.facility_availability[f]
            m.addConstr(q[t,f]<=cap,name=f'capacity_{t}_{f}')
    fixed=gp.quicksum(y[f]*cfg.facilities[f].fixed_open_cost+e[f]*cfg.facilities[f].expansion_cost_per_unit for f in FF)
    cost=fixed+gp.quicksum(
        v[t]*cfg.virgin_cost_per_kg*scenario.virgin_cost_multiplier+inv[t]*cfg.inventory_cost_per_kg+d[t]*cfg.disposal_cost_per_kg+sh[t]*cfg.shortage_penalty_per_kg+
        gp.quicksum(q[t,f]*(cfg.facilities[f].processing_cost_per_kg+.10*scenario.transport_cost_multiplier) for f in FF)
        for t in TT)
    carbon=gp.quicksum(
        v[t]*cfg.virgin_carbon_per_kg*scenario.carbon_multiplier+d[t]*cfg.disposal_carbon_per_kg*scenario.carbon_multiplier+
        gp.quicksum(q[t,f]*cfg.facilities[f].processing_carbon_per_kg*scenario.carbon_multiplier for f in FF)
        for t in TT)
    virgin=gp.quicksum(v[t] for t in TT);shortage=gp.quicksum(sh[t] for t in TT)
    # Hierarchical decision priorities: protect service first, then economics, then environmental burden, then virgin dependency.
    m.ModelSense=GRB.MINIMIZE
    m.setObjectiveN(shortage,0,priority=4,weight=1.0,abstol=SERVICE_OBJECTIVE_ABS_TOL,reltol=0.0,name='service')
    m.setObjectiveN(cost,1,priority=3,weight=1.0,abstol=1000.0,reltol=.002,name='cost')
    m.setObjectiveN(carbon,2,priority=2,weight=1.0,abstol=1000.0,reltol=.002,name='carbon')
    m.setObjectiveN(virgin,3,priority=1,weight=1.0,abstol=1000.0,reltol=.002,name='virgin')
    m.optimize()
    if m.Status!=GRB.OPTIMAL: raise RuntimeError(f'Gurobi status {m.Status}')
    opens={cfg.facilities[f].name:int(round(y[f].X)) for f in FF};exp={cfg.facilities[f].name:int(round(e[f].X)) for f in FF}
    objective_passes=_collect_multiobjective_pass_metrics(m)
    max_pass_gap=max((row['mip_gap'] for row in objective_passes), default=0.0)
    # The final hierarchical solution may differ from the first-pass service
    # optimum by the configured objective absolute tolerance, while primal
    # feasibility is itself evaluated using Gurobi's FeasibilityTol.
    # Acceptance therefore reports and uses their sum instead of a hidden
    # hard-coded epsilon.
    feasibility_tol=float(m.Params.FeasibilityTol)
    service_acceptance_tol_kg=SERVICE_OBJECTIVE_ABS_TOL + feasibility_tol
    return {
        'status':'OPTIMAL','solver':'gurobi','is_multiobjective':bool(m.IsMultiObj),
        'runtime_seconds':float(m.Runtime),
        'mip_gap':max_pass_gap,
        'objective_passes':objective_passes,
        'feasibility_tolerance':feasibility_tol,
        'service_objective_abs_tolerance_kg':SERVICE_OBJECTIVE_ABS_TOL,
        'service_acceptance_tolerance_kg':service_acceptance_tol_kg,
        'max_constraint_violation':float(m.ConstrVio),'max_integrality_violation':float(m.IntVio),
        'shortage_kg':float(shortage.getValue()),'cost':float(cost.getValue()),'carbon_kgco2e':float(carbon.getValue()),'virgin_kg':float(virgin.getValue()),
        'open_facilities':opens,'expansion_units':exp,
        'evidence_class':'LICENSED GUROBI MULTI-OBJECTIVE VALIDATION',
    }
