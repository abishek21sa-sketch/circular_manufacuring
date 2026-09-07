from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path

from circular_battery.lifecycle.demo import demo_design, demo_grades, demo_periods
from circular_battery.lifecycle.engine import evaluate_lifecycle_horizon
from circular_battery.lifecycle.metrics import circularity_metrics, pathway_economics
from circular_battery.lifecycle.impact import lifecycle_material_impact
from circular_battery.logistics.demo import demo_reverse_logistics_scenario
from circular_battery.logistics.optimizer import solve_reverse_logistics
from circular_battery.planning.models import PlanningScenario
from circular_battery.planning.optimizer import solve_production_plan
from circular_battery.planning.ie_metrics import planning_ie_metrics

def build_phase567_report():
    design=demo_design(); grades=demo_grades(); periods=demo_periods()
    lifecycle=evaluate_lifecycle_horizon(design,grades,periods)
    circ=circularity_metrics(lifecycle,design)
    economics=pathway_economics(lifecycle,design)
    impact=lifecycle_material_impact(lifecycle,design)

    reverse_scenario=demo_reverse_logistics_scenario()
    reverse=solve_reverse_logistics(reverse_scenario)
    network_capture=reverse.processed_kg/reverse.collected_kg if reverse.collected_kg else 0.0

    recovered_supply=[]
    per_period=[]
    for p in periods:
        rs=[r for r in lifecycle if r.period==p.period]
        external=sum(r.recycled_output_kg+r.remanufactured_retained_kg for r in rs)
        internal_scrap=sum(r.manufacturing_scrap_kg for r in rs)*.95
        available=external*network_capture+internal_scrap
        recovered_supply.append(available)
        per_period.append({
            "period":p.period,
            "external_technical_recovery_kg":external,
            "reverse_network_capture_rate":network_capture,
            "internal_scrap_recovery_kg":internal_scrap,
            "available_recovered_supply_kg":available,
        })

    planning_scenario=PlanningScenario(
        demand_packs=tuple(p.production_packs for p in periods),
        recovered_supply_kg=tuple(recovered_supply),
        regular_capacity_packs=(2250.,2380.,2520.,2630.),
        overtime_capacity_packs=(180.,220.,250.,300.),
        pack_mass_kg=design.pack_mass_kg,
        initial_finished_goods_packs=110.,
        initial_recovered_inventory_kg=45_000.,
        safety_stock_fraction_next_period=.05,
        min_recycled_content=.15,
        max_recycled_content=design.max_recycled_content,
    )
    plan=solve_production_plan(planning_scenario)
    ie=planning_ie_metrics(plan,planning_scenario)

    return {
        "release":"PHASE-7-CUMULATIVE",
        "version":"0.7.0",
        "data_status":"SYNTHETIC VALIDATION",
        "phase5":{
            "design":{"name":design.name,"pack_mass_kg":design.pack_mass_kg,
                      "manufacturing_scrap_rate":design.manufacturing_scrap_rate,
                      "max_recycled_content":design.max_recycled_content,
                      "materials":[asdict(m) for m in design.materials]},
            "circularity_metrics":circ,
            "pathway_economics":economics,
            "lifecycle_impact":impact,
            "max_material_balance_error_kg":max(abs(r.material_balance_error_kg) for r in lifecycle),
        },
        "phase6":{
            "reverse_logistics":reverse.to_dict(),
            "network_capture_rate":network_capture,
        },
        "integration":{
            "recovered_supply_to_planning":per_period,
        },
        "phase7":{
            "production_plan":plan.to_dict(),
            "ie_metrics":ie,
        },
        "claims":{
            "implemented":"material-specific lifecycle accounting, recovery pathways, reverse-logistics facility/flow optimization, multi-period circular production and inventory planning",
            "not_claimed":"real factory/recycler performance, realized savings, externally calibrated lifecycle factors",
        }
    }

def write_phase567_report(path):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    report=build_phase567_report()
    p.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report
