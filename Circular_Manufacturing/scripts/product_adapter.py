from __future__ import annotations
import json
from pathlib import Path
from circular_battery.decision.circular_mass_bridge import build_circular_mass_decision
ROOT=Path(__file__).resolve().parents[1]
PROJECT="Circular Manufacturing — Closed-Loop Material Network Planner"
ALGORITHM="CIRCULAR-MASS"
SUBTITLE="Recovery routing, facility activation, virgin fallback, recycled-content policy, uncertain yield, and shortage-tail-risk planning."
PORT=8812
THEME="circular"
CONTROLS=[
 {"key":"min_recycled_content","label":"Minimum recycled content","default":0.20,"min":0,"max":0.85,"step":0.05},
 {"key":"risk_aversion","label":"Shortage risk aversion","default":0.35,"min":0,"max":2,"step":0.05},
 {"key":"max_virgin_share","label":"Maximum virgin share","default":0.72,"min":0.2,"max":1,"step":0.04},
]
DEFAULTS={x["key"]:x["default"] for x in CONTROLS}
DEMO_STRESS={"min_recycled_content":0.65,"risk_aversion":0.75,"max_virgin_share":0.55}
def _fmt(v):
    if v is None:return "N/A"
    return f"{v:,.4f}" if isinstance(v,float) else str(v)
def compute(params):
    raw=build_circular_mass_decision(min_recycled_content=float(params['min_recycled_content']),risk_aversion=float(params['risk_aversion']),max_virgin_share=float(params['max_virgin_share']))
    sol=raw['solution']
    metrics=[["Recovered material",f"{sol['expected_recovered_kg']:,.0f} kg"],["Recycled content",f"{100*sol['recycled_content_share']:.1f}%"],["Expected shortage",f"{sol['expected_shortage_kg']:,.2f} kg"],["Shortage CVaR",f"{sol['cvar_shortage_kg']:,.2f} kg"],["Objective",f"{sol['objective']:,.0f}"],["Solver",sol.get('solver','unknown')],["Solver runtime",f"{sol.get('runtime_seconds',0):.3f} s"]]
    actions=[{"Facility":a['facility'],"Open":"YES" if a['open'] else 'NO',"Recovery route":f"{a['route_kg']:,.0f} kg"} for a in raw['facility_actions']]
    b={}; p=ROOT/'artifacts/circular_mass/evidence.json'
    if p.exists(): b=json.loads(p.read_text(encoding='utf-8')).get('baselines',{})
    baselines=[["Virgin-only objective",_fmt(b.get('virgin_only',{}).get('objective'))],["Average-yield objective",_fmt(b.get('deterministic_average_yield',{}).get('objective'))],["Reference shortage CVaR",_fmt(sol.get('cvar_shortage_kg'))]]
    return {"gate":raw['decision_gate'],"decision_id":raw['decision_id'],"metrics":metrics,"actions":actions,"baselines":baselines,"objective_components":sol.get('objective_components',{}),"scenario_details":sol.get('scenario_details',[]),"checks":raw.get('checks',{}),"diagnostics":sol.get('diagnostics',{}),"claim":raw['operator_message']+' '+raw['tail_risk_note'],"raw":raw}
