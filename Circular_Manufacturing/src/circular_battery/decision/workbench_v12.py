from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

from circular_battery.lifecycle.demo import demo_design
from circular_battery.planning.models import PlanningScenario
from circular_battery.planning.optimizer import solve_production_plan
from circular_battery.planning.ie_metrics import planning_ie_metrics
from circular_battery.optimization.critical_materials import (
    CriticalMaterial,
    CriticalMaterialConfig,
    demo_critical_material_config,
    solve_critical_material_plan,
)
from circular_battery.routing.models import RouteNode, CVRPScenario
from circular_battery.routing.demo import demo_cvrp_scenario
from circular_battery.routing.cvrp import solve_cvrp
from circular_battery.decision.bridge import ai_to_uncertainty_scenarios
from circular_battery.optimization.stochastic_value import stochastic_value_metrics

ROOT=Path(__file__).resolve().parents[3]


def _reference_core():
    path=ROOT/"artifacts"/"v1_reference_decision_report.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _chosen_policy(core):
    name=core["decision"]["recommended_policy"]
    return next(x for x in core["advanced_strategy_frontier"]["candidates"] if x["policy"]==name)


def _expected_period_recovery(chosen):
    if not chosen["scenario_metrics"]:
        return []
    periods=len(chosen["scenario_metrics"][0]["period_rows"])
    out=[]
    for t in range(periods):
        recovered=sum(
            sc["probability"]*sc["period_rows"][t]["recovered_output_kg"]
            for sc in chosen["scenario_metrics"]
        )
        inventory=sum(
            sc["probability"]*sc["period_rows"][t]["inventory_kg"]
            for sc in chosen["scenario_metrics"]
        )
        disposal=sum(
            sc["probability"]*sc["period_rows"][t]["disposal_kg"]
            for sc in chosen["scenario_metrics"]
        )
        out.append({
            "period":t+1,
            "expected_recovered_output_kg":recovered,
            "expected_recovery_inventory_kg":inventory,
            "expected_disposal_kg":disposal,
        })
    return out


def build_coupled_planning(core):
    bridge=core["ai_to_or_bridge"]
    chosen=_chosen_policy(core)
    design=demo_design()
    recovery=_expected_period_recovery(chosen)
    demand_packs=tuple(float(x)/design.pack_mass_kg for x in bridge["derived_base_demand_kg"])
    internal_scrap=tuple(.95*float(x) for x in bridge["derived_internal_scrap_supply_kg"])
    recovered_supply=tuple(
        recovery[t]["expected_recovered_output_kg"] + internal_scrap[t]
        for t in range(len(demand_packs))
    )
    # Capacity assumptions are explicit scenario-design parameters, not observed capacity.
    regular=tuple(d*1.025 for d in demand_packs)
    overtime=tuple(d*.10 for d in demand_packs)
    scenario=PlanningScenario(
        demand_packs=demand_packs,
        recovered_supply_kg=recovered_supply,
        regular_capacity_packs=regular,
        overtime_capacity_packs=overtime,
        pack_mass_kg=design.pack_mass_kg,
        initial_finished_goods_packs=demand_packs[0]*.03,
        initial_recovered_inventory_kg=35_000.,
        safety_stock_fraction_next_period=.04,
        min_recycled_content=.15,
        max_recycled_content=design.max_recycled_content,
    )
    sol=solve_production_plan(scenario)
    return {
        "status":sol.status,
        "scenario":{
            "demand_packs":list(demand_packs),
            "recovered_supply_kg":list(recovered_supply),
            "regular_capacity_packs":list(regular),
            "overtime_capacity_packs":list(overtime),
            "source_contract":{
                "demand":"AI demand forecast -> stochastic bridge",
                "external_recovery":"chosen stochastic policy expected recovered output",
                "internal_recovery":"95% recovery of AI-derived manufacturing scrap",
                "capacity":"explicit synthetic planning assumption",
            },
        },
        "solution":sol.to_dict(),
        "ie_metrics":planning_ie_metrics(sol,scenario),
        "evidence_class":"COUPLED SYNTHETIC IE PLAN; DEMAND/RECOVERY DERIVED FROM CHOSEN DECISION STATE",
    }


def _scaled_critical_material_config(core, coupled_plan):
    base=demo_critical_material_config()
    design=demo_design()
    kg_per_pack={m.name:m.kg_per_pack for m in design.materials}
    plan=coupled_plan["solution"]["period_rows"]
    T=len(plan)
    materials=[]
    for old in base.materials:
        if old.name not in kg_per_pack:
            continue
        demand=tuple(
            coupled_plan["scenario"]["demand_packs"][t]*kg_per_pack[old.name]
            for t in range(T)
        )
        recovered=tuple(
            plan[t]["recovered_use_kg"]*(kg_per_pack[old.name]/design.pack_mass_kg)
            for t in range(T)
        )
        caps=[]
        for sidx,row in enumerate(old.supplier_capacity_kg):
            vals=[]
            for t in range(T):
                old_d=old.demand_kg[min(t,len(old.demand_kg)-1)]
                ratio=demand[t]/old_d if old_d else 1.
                vals.append(row[min(t,len(row)-1)]*ratio)
            caps.append(tuple(vals))
        materials.append(CriticalMaterial(
            name=old.name,
            demand_kg=demand,
            recovered_supply_kg=recovered,
            supplier_capacity_kg=tuple(caps),
            supplier_cost_per_kg=old.supplier_cost_per_kg,
            supplier_carbon_per_kg=old.supplier_carbon_per_kg,
            supplier_risk_score=old.supplier_risk_score,
            max_single_supplier_share=old.max_single_supplier_share,
            inventory_cap_kg=max(old.inventory_cap_kg,max(demand)*.25),
            initial_inventory_kg=old.initial_inventory_kg,
        ))
    return CriticalMaterialConfig(
        materials=tuple(materials),
        supplier_names=base.supplier_names,
        recovered_cost_per_kg=base.recovered_cost_per_kg,
        recovered_carbon_per_kg=base.recovered_carbon_per_kg,
        inventory_cost_per_kg=base.inventory_cost_per_kg,
        shortage_penalty_per_kg=base.shortage_penalty_per_kg,
        risk_weight_per_kg=base.risk_weight_per_kg,
        carbon_price_per_kgco2e=base.carbon_price_per_kgco2e,
        minimum_recovered_share=.10,
    )


def build_coupled_critical_materials(core,coupled_plan):
    cfg=_scaled_critical_material_config(core,coupled_plan)
    sol=solve_critical_material_plan(cfg)
    return {
        **sol.to_dict(),
        "coupling":{
            "material_demand":"AI-derived pack demand x material BOM kg/pack",
            "recovered_supply":"coupled IE plan recovered-use allocation x BOM share",
            "supplier_landscape":"synthetic Phase-8 supplier structure scaled to coupled demand",
        },
        "evidence_class":"COUPLED SYNTHETIC CRITICAL-MATERIAL OPTIMIZATION",
    }


def build_coupled_routing(core):
    bridge=core["ai_to_or_bridge"]
    chosen=_chosen_policy(core)
    template=demo_cvrp_scenario()
    # Period-1 return state becomes a representative collection batch.
    collected=float(bridge["derived_base_returns_kg"][0])*.87*(1-float(bridge["derived_second_life_share"]))
    shares=(.19,.18,.16,.17,.15,.15)
    # Preserve exact total after rounding-free allocation.
    pickups=[collected*s for s in shares[:-1]]
    pickups.append(collected-sum(pickups))
    customers=tuple(
        RouteNode(n.name,n.x_km,n.y_km,pickups[i])
        for i,n in enumerate(template.customers)
    )
    open_names=[k for k,v in chosen["open_facilities"].items() if v]
    depot_name=(open_names[0] if open_names else "Recovery")+" collection hub"
    scenario=CVRPScenario(
        depot=RouteNode(depot_name,template.depot.x_km,template.depot.y_km,0),
        customers=customers,
        vehicle_capacity_kg=template.vehicle_capacity_kg,
        max_vehicles=max(template.max_vehicles,6),
        vehicle_fixed_cost=template.vehicle_fixed_cost,
        distance_cost_per_km=template.distance_cost_per_km,
        kgco2e_per_km=template.kgco2e_per_km,
    )
    sol=solve_cvrp(scenario)
    return {
        **sol.to_dict(),
        "routing_input":{
            "collected_batch_kg":collected,
            "customer_pickups_kg":{customers[i].name:customers[i].pickup_kg for i in range(len(customers))},
            "primary_hub":depot_name,
            "source_contract":"AI return forecast -> collection/second-life filter -> representative routing batch",
        },
        "evidence_class":"COUPLED SYNTHETIC CVRP; REPRESENTATIVE COLLECTION BATCH",
    }


def mathematical_inventory(core):
    reduced=int(core["uncertainty_design"]["scenario_count"])
    n_customers=6
    F=3;T=3
    return [
        {
            "model":"Closed-loop material network MILP",
            "role":"facility activation + virgin/recycle/reman/inventory/disposal",
            "variables":5*3+2,"constraints":4*3,
            "integer_variables":2,"solver":"SciPy HiGHS MILP",
            "verification":"balance audit + 4-configuration facility oracle",
        },
        {
            "model":"Reverse-logistics facility/flow MILP",
            "role":"collection-region allocation + recovery siting",
            "variables":4*4+4+4,"constraints":4+4+4+1,
            "integer_variables":4,"solver":"SciPy HiGHS MILP",
            "verification":"node balance + capacity/disposal audit",
        },
        {
            "model":"Circular production/inventory LP",
            "role":"regular/overtime + FG/recovered inventory + virgin substitution",
            "variables":7*3,"constraints":3*3 + 2*3 + 2*3 + 2,
            "integer_variables":0,"solver":"SciPy HiGHS LP",
            "verification":"three independent period-balance residuals",
        },
        {
            "model":"Two-stage stochastic MILP + CVaR",
            "role":"first-stage facilities/expansion + scenario recourse",
            "variables":2*F + reduced*T*(F+4) + 1 + reduced,
            "constraints":F + F + reduced*T*(5+F) + reduced,
            "integer_variables":2*F,
            "solver":"SciPy HiGHS MILP",
            "verification":"scenario feasibility + CVaR + N-1 tests",
        },
        {
            "model":"Critical-material sourcing LP",
            "role":"Li/Ni/Co/graphite supplier mix + recovered feed + inventory",
            "variables":4*3*6,"constraints":4*3 + 4*3*3 + 4*3*3 + 4*3,
            "integer_variables":0,"solver":"SciPy HiGHS LP",
            "verification":"material balance + supplier concentration + HHI",
        },
        {
            "model":"Exact capacitated vehicle routing MILP",
            "role":"collection tours, load capacity and subtour elimination",
            "variables":(n_customers+1)*n_customers+n_customers,
            "constraints":2*n_customers+2+n_customers*(n_customers-1),
            "integer_variables":(n_customers+1)*n_customers,
            "solver":"SciPy HiGHS MILP",
            "verification":"route reconstruction + two-customer exact oracle",
        },
        {
            "model":"Licensed hierarchical multi-objective MILP",
            "role":"service -> cost -> carbon -> virgin-material priority",
            "variables":27,"constraints":27,
            "integer_variables":6,"objectives":4,"solver":"Gurobi",
            "verification":"Windows licensed per-objective-pass status/gap + ConstrVio/IntVio",
        },
    ]


def build_workbench_v12(core=None):
    core=core or _reference_core()
    planning=build_coupled_planning(core)
    critical=build_coupled_critical_materials(core,planning)
    routing=build_coupled_routing(core)
    # Reconstruct the deterministic seeded representative scenario set used by
    # the accepted reference decision, then compute classical RP/EEV/WS value metrics.
    _, reduced_for_value, _ = ai_to_uncertainty_scenarios(raw_n=80,reduced_k=10,seed=20260817)
    info_value=stochastic_value_metrics(reduced_for_value)
    chosen=_chosen_policy(core)
    return {
        "release":"V1.2-INTEGRATED-WORKBENCH",
        "version":"1.2.1",
        "data_status":"SYNTHETIC VALIDATION",
        "core_decision_hash_sha256":core["decision_hash_sha256"],
        "decision":core["decision"],
        "bridge":core["ai_to_or_bridge"],
        "frontier":core["advanced_strategy_frontier"],
        "policy_scores":core["policy_scores"],
        "uncertainty":core["uncertainty_design"],
        "policy_replay":core["policy_digital_experiments"],
        "ai_evidence":core["ai_model_evidence"],
        "ai_explainability":core["ai_uncertainty_and_explainability"],
        "sensitivity":core["strategic_sensitivity"],
        "decision_trace":core["decision_trace"],
        "evidence_classes":core["evidence_classes"],
        "chosen_stochastic_policy":chosen,
        "coupled_planning":planning,
        "coupled_critical_materials":critical,
        "coupled_routing":routing,
        "math_inventory":mathematical_inventory(core),
        "stochastic_information_value":info_value,
        "integration_contract":[
            {"from":"DemandForecaster","to":"StochasticNetwork","status":"COUPLED","detail":"forecast -> kg demand horizon"},
            {"from":"RecoveryPathwayClassifier","to":"StochasticNetwork","status":"COUPLED","detail":"second-life withholding + reman eligibility"},
            {"from":"StochasticNetwork","to":"IEProductionPlan","status":"COUPLED_V1_2","detail":"expected recovered output -> recovered material availability"},
            {"from":"IEProductionPlan","to":"CriticalMaterialPlanner","status":"COUPLED_V1_2","detail":"pack demand/BOM + recovered-use allocation"},
            {"from":"ReturnHazardModel","to":"CVRP","status":"COUPLED_V1_2","detail":"forecast returns -> collection batch pickup demand"},
            {"from":"StochasticNetwork","to":"DecisionEngine","status":"COUPLED","detail":"Pareto policies + tail risk -> recommendation"},
        ],
        "known_model_boundaries":[
            "Routing uses a representative collection batch rather than a full multi-period multi-depot split-delivery fleet schedule.",
            "Critical-material supplier disruption is represented by risk penalties/concentration limits rather than endogenous supplier-failure scenarios.",
            "The displayed policy frontier is the nondominated subset of an explicit six-policy scalarization design, not a continuous Pareto surface.",
            "Lifecycle emission factors remain synthetic/external-calibration-pending.",
        ],
    }
