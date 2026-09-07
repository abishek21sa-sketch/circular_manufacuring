import json
import pytest
from circular_battery.decision.orchestrator import build_phase10_decision
from circular_battery.ai.explainability import explain_all
from circular_battery.decision.orchestrator import _load_models

def test_ai_explainability_covers_all_models():
    x=explain_all(_load_models())
    assert set(x)=={'demand','returns','recovery','scrap'}
    assert 0 <= x['demand']['empirical_holdout_coverage'] <= 1
    assert 0 <= x['returns']['expected_calibration_error'] <= 1
    assert len(x['recovery']['feature_importance_permutation_macro_f1'])==6
    assert len(x['scrap']['feature_importance'])==5

def test_phase10_decision_trace_is_end_to_end():
    r=build_phase10_decision(seed=201,raw_n=24,reduced_k=4,include_sensitivity=False)
    comps=[x['component'] for x in r['decision_trace']]
    assert comps==['DemandForecaster','ReturnHazardModel','ScrapPredictor','RecoveryPathwayClassifier','ScenarioBridge','TwoStageStochasticMILP','CriticalMaterialPlanner','CVRP','StrategicSensitivity','PolicyReplay','DecisionEngine']
    assert r['decision']['human_approval_required'] is True
    assert 0 < r['decision']['confidence'] < 1
    assert len(r['decision_hash_sha256'])==64

def test_phase10_recommendation_has_required_explanation_fields():
    r=build_phase10_decision(seed=202,raw_n=24,reduced_k=4,include_sensitivity=False)
    d=r['decision']
    assert d['recommended_policy']
    assert d['action']
    assert len(d['tradeoffs'])>=3
    assert len(d['assumptions'])>=3
    assert set(d['expected_impact_vs_cost_policy'])=={'expected_total_cost','expected_carbon_kgco2e','expected_virgin_kg','cvar_operating_cost'}

def test_phase10_ai_predictions_feed_or_contract():
    r=build_phase10_decision(seed=203,raw_n=24,reduced_k=4,include_sensitivity=False)
    b=r['ai_to_or_bridge']
    assert b['derived_base_demand_kg'][0] == pytest.approx(b['demand_prediction_packs']*400)
    assert b['derived_internal_scrap_supply_kg'][0] > 0
    assert 0 < b['derived_second_life_share'] < 1
    assert 0 < b['derived_reman_eligible_share'] < 1

def test_phase10_frontier_and_routing_are_audited():
    r=build_phase10_decision(seed=204,raw_n=24,reduced_k=4,include_sensitivity=False)
    assert len(r['advanced_strategy_frontier']['nondominated'])>=2
    assert r['routing']['status']=='OPTIMAL'
    assert r['routing']['max_constraint_violation']<1e-7
    assert r['routing']['vehicles_used']>=1

def test_phase10_evidence_language_separates_claim_types():
    r=build_phase10_decision(seed=205,raw_n=24,reduced_k=4,include_sensitivity=False)
    assert r['data_status']=='SYNTHETIC VALIDATION'
    assert r['real_world_validation']=='PENDING'
    assert {'PREDICTED','OPTIMIZED','SIMULATED','RECOMMENDED'}.issubset(set(r['evidence_classes']))
    assert 'realized' not in r['decision']['evidence_class'].lower()


def test_phase10_includes_critical_material_and_sensitivity_depth():
    r=build_phase10_decision(seed=206,raw_n=24,reduced_k=4,include_sensitivity=True)
    cm=r['critical_material_resilience']
    assert cm['status']=='OPTIMAL'
    assert cm['max_constraint_violation'] < 1e-7
    assert set(cm['supplier_hhi_by_material'])=={'lithium','nickel','cobalt','graphite'}
    assert len(r['strategic_sensitivity']['experiments']) >= 6
