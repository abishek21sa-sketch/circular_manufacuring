from __future__ import annotations
import csv, json
from dataclasses import asdict
from pathlib import Path

from circular_battery.lifecycle.models import MaterialSpec, ProductDesign, RecoveryGrade, LifecyclePeriod
from circular_battery.lifecycle.engine import evaluate_lifecycle_horizon
from circular_battery.lifecycle.metrics import circularity_metrics, pathway_economics
from circular_battery.lifecycle.impact import lifecycle_material_impact
from circular_battery.logistics.models import CollectionNode, FacilityCandidate, ReverseLogisticsScenario
from circular_battery.logistics.optimizer import solve_reverse_logistics
from circular_battery.planning.models import PlanningScenario
from circular_battery.planning.optimizer import solve_production_plan
from circular_battery.planning.ie_metrics import planning_ie_metrics
from circular_battery.platform.errors import ValidationError
from circular_battery.evidence.registry import stable_hash

REQUIRED_FILES=("manifest.json","materials.csv","periods.csv","collections.csv","facilities.csv","planning.csv")

def _rows(path:Path):
    if not path.exists():
        raise ValidationError(f"Missing required bundle file: {path.name}")
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    if not rows:
        raise ValidationError(f"{path.name} contains no data rows.")
    return rows

def _float(row,key,file):
    raw=row.get(key)
    try: return float(raw)
    except (TypeError,ValueError) as exc:
        raise ValidationError(f"{file}: column {key} must be numeric.",details={"value":raw}) from exc

def _bool(row,key,file):
    raw=str(row.get(key,"")).strip().lower()
    if raw in {"1","true","yes","y"}: return True
    if raw in {"0","false","no","n",""}: return False
    raise ValidationError(f"{file}: column {key} must be boolean-like.")

def validate_bundle(directory:Path|str):
    d=Path(directory)
    if not d.is_dir(): raise ValidationError("Bundle directory does not exist.")
    missing=[name for name in REQUIRED_FILES if not (d/name).is_file()]
    if missing: raise ValidationError("Scenario bundle is incomplete.",details={"missing_files":missing})
    try: manifest=json.loads((d/"manifest.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: raise ValidationError("manifest.json is invalid JSON.") from exc
    required_manifest={"name","manufacturing_scrap_rate","max_recycled_content","remanufacture_material_retention","evidence_class"}
    missing_keys=sorted(required_manifest-set(manifest))
    if missing_keys: raise ValidationError("manifest.json missing required fields.",details={"missing_fields":missing_keys})
    return {"directory":str(d.resolve()),"manifest":manifest,"files":list(REQUIRED_FILES),"bundle_hash_sha256":bundle_hash(d)}

def bundle_hash(directory:Path|str):
    d=Path(directory)
    payload={}
    for name in REQUIRED_FILES:
        p=d/name
        if p.exists(): payload[name]=p.read_text(encoding="utf-8-sig")
    return stable_hash(payload)

def load_bundle(directory:Path|str):
    d=Path(directory); meta=validate_bundle(d); m=meta["manifest"]

    material_rows=_rows(d/"materials.csv")
    materials=tuple(MaterialSpec(
        name=r["name"].strip(),
        kg_per_pack=_float(r,"kg_per_pack","materials.csv"),
        virgin_cost_per_kg=_float(r,"virgin_cost_per_kg","materials.csv"),
        recycled_cost_per_kg=_float(r,"recycled_cost_per_kg","materials.csv"),
        virgin_kgco2e_per_kg=_float(r,"virgin_kgco2e_per_kg","materials.csv"),
        recycled_kgco2e_per_kg=_float(r,"recycled_kgco2e_per_kg","materials.csv"),
        recycling_yield=_float(r,"recycling_yield","materials.csv"),
        critical=_bool(r,"critical","materials.csv"),
    ) for r in material_rows)
    if not materials or any(x.kg_per_pack<=0 for x in materials):
        raise ValidationError("materials.csv must define positive material masses.")
    if any(not 0<=x.recycling_yield<=1 for x in materials):
        raise ValidationError("Material recycling_yield must be in [0,1].")

    design=ProductDesign(
        name=str(m["name"]),
        materials=materials,
        manufacturing_scrap_rate=float(m["manufacturing_scrap_rate"]),
        max_recycled_content=float(m["max_recycled_content"]),
        remanufacture_material_retention=float(m["remanufacture_material_retention"]),
    )
    if not 0<=design.manufacturing_scrap_rate<1: raise ValidationError("manufacturing_scrap_rate must be in [0,1).")
    if not 0<=design.max_recycled_content<=1: raise ValidationError("max_recycled_content must be in [0,1].")
    if not 0<=design.remanufacture_material_retention<=1: raise ValidationError("remanufacture_material_retention must be in [0,1].")

    grade_cfg=m.get("recovery_grades",{
        "A":{"second_life":.55,"remanufacture":.30,"recycle":.13,"disposal":.02},
        "B":{"second_life":.15,"remanufacture":.35,"recycle":.45,"disposal":.05},
        "C":{"second_life":.02,"remanufacture":.08,"recycle":.78,"disposal":.12},
    })
    grades={}
    for name,g in grade_cfg.items():
        grade=RecoveryGrade(name,float(g["second_life"]),float(g["remanufacture"]),float(g["recycle"]),float(g["disposal"]))
        grade.validate();grades[name]=grade

    period_rows=_rows(d/"periods.csv")
    periods=[]
    for r in period_rows:
        mix={g:_float(r,f"grade_{g}","periods.csv") for g in grades}
        periods.append(LifecyclePeriod(
            period=int(_float(r,"period","periods.csv")),
            production_packs=_float(r,"production_packs","periods.csv"),
            eol_returns_packs=_float(r,"eol_returns_packs","periods.csv"),
            collection_rate=_float(r,"collection_rate","periods.csv"),
            grade_mix=mix,
        ))
    periods=tuple(sorted(periods,key=lambda x:x.period))

    collections=tuple(CollectionNode(
        name=r["name"].strip(),returns_kg=_float(r,"returns_kg","collections.csv"),
        reman_eligible_share=_float(r,"reman_eligible_share","collections.csv"),
        x_km=_float(r,"x_km","collections.csv"),y_km=_float(r,"y_km","collections.csv"),
    ) for r in _rows(d/"collections.csv"))

    facilities=tuple(FacilityCandidate(
        name=r["name"].strip(),kind=r["kind"].strip().lower(),
        capacity_kg=_float(r,"capacity_kg","facilities.csv"),
        fixed_cost=_float(r,"fixed_cost","facilities.csv"),
        processing_cost_per_kg=_float(r,"processing_cost_per_kg","facilities.csv"),
        processing_kgco2e_per_kg=_float(r,"processing_kgco2e_per_kg","facilities.csv"),
        x_km=_float(r,"x_km","facilities.csv"),y_km=_float(r,"y_km","facilities.csv"),
    ) for r in _rows(d/"facilities.csv"))
    if any(f.kind not in {"reman","recycle"} for f in facilities):
        raise ValidationError("facilities.csv kind must be reman or recycle.")

    logistics_cfg=m.get("reverse_logistics",{})
    reverse=ReverseLogisticsScenario(
        collections=collections,facilities=facilities,
        collection_rate=float(logistics_cfg.get("collection_rate",.88)),
        transport_cost_per_kg_km=float(logistics_cfg.get("transport_cost_per_kg_km",.0018)),
        transport_kgco2e_per_kg_km=float(logistics_cfg.get("transport_kgco2e_per_kg_km",.00012)),
        disposal_cost_per_kg=float(logistics_cfg.get("disposal_cost_per_kg",.65)),
        disposal_kgco2e_per_kg=float(logistics_cfg.get("disposal_kgco2e_per_kg",.75)),
        max_disposal_share=float(logistics_cfg.get("max_disposal_share",.25)),
    )

    planning_rows=sorted(_rows(d/"planning.csv"),key=lambda r:int(float(r["period"])))
    if len(planning_rows)!=len(periods):
        raise ValidationError("planning.csv row count must match periods.csv row count.")

    return {
        "meta":meta,"design":design,"grades":grades,"periods":periods,
        "reverse_logistics":reverse,"planning_rows":planning_rows,
    }

def run_bundle(directory:Path|str):
    b=load_bundle(directory)
    design=b["design"]; periods=b["periods"]
    lifecycle=evaluate_lifecycle_horizon(design,b["grades"],periods)
    reverse=solve_reverse_logistics(b["reverse_logistics"])
    capture=reverse.processed_kg/reverse.collected_kg if reverse.collected_kg else 0.0

    recovered_supply=[]
    for p in periods:
        rs=[r for r in lifecycle if r.period==p.period]
        external=sum(r.recycled_output_kg+r.remanufactured_retained_kg for r in rs)
        internal=sum(r.manufacturing_scrap_kg for r in rs)*.95
        recovered_supply.append(external*capture+internal)

    pr=b["planning_rows"]
    cfg=b["meta"]["manifest"].get("planning",{})
    plan_s=PlanningScenario(
        demand_packs=tuple(_float(r,"demand_packs","planning.csv") for r in pr),
        recovered_supply_kg=tuple(recovered_supply),
        regular_capacity_packs=tuple(_float(r,"regular_capacity_packs","planning.csv") for r in pr),
        overtime_capacity_packs=tuple(_float(r,"overtime_capacity_packs","planning.csv") for r in pr),
        pack_mass_kg=design.pack_mass_kg,
        initial_finished_goods_packs=float(cfg.get("initial_finished_goods_packs",0)),
        initial_recovered_inventory_kg=float(cfg.get("initial_recovered_inventory_kg",0)),
        max_recovered_inventory_kg=float(cfg.get("max_recovered_inventory_kg",350000)),
        max_finished_goods_inventory_packs=float(cfg.get("max_finished_goods_inventory_packs",500)),
        safety_stock_fraction_next_period=float(cfg.get("safety_stock_fraction_next_period",.05)),
        max_recycled_content=design.max_recycled_content,
        min_recycled_content=float(cfg.get("min_recycled_content",0)),
        shortage_penalty_per_pack=float(cfg.get("shortage_penalty_per_pack",12000)),
    )
    plan=solve_production_plan(plan_s)
    return {
        "bundle":{
            **b["meta"],
            "evidence_class":b["meta"]["manifest"]["evidence_class"],
        },
        "lifecycle":{
            "design":{"name":design.name,"pack_mass_kg":design.pack_mass_kg,"materials":[asdict(x) for x in design.materials]},
            "circularity_metrics":circularity_metrics(lifecycle,design),
            "pathway_economics":pathway_economics(lifecycle,design),
            "lifecycle_impact":lifecycle_material_impact(lifecycle,design),
            "max_material_balance_error_kg":max(abs(r.material_balance_error_kg) for r in lifecycle),
        },
        "reverse_logistics":reverse.to_dict(),
        "planning":{"solution":plan.to_dict(),"ie_metrics":planning_ie_metrics(plan,plan_s)},
        "integration":{
            "network_capture_rate":capture,
            "recovered_supply_to_planning_kg":recovered_supply,
        },
        "claims_boundary":"User-supplied data are processed as provided; ingestion validates schema/physics but does not independently verify source truth.",
    }
