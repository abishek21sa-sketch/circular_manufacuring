import pytest
from circular_battery.lifecycle.demo import demo_design,demo_grades,demo_periods
from circular_battery.lifecycle.engine import evaluate_lifecycle_period,evaluate_lifecycle_horizon,weighted_pathway_shares
from circular_battery.lifecycle.metrics import circularity_metrics,pathway_economics
from circular_battery.lifecycle.impact import lifecycle_material_impact
from circular_battery.lifecycle.models import LifecyclePeriod, RecoveryGrade

def test_phase5_pack_mass_and_bom():
    d=demo_design()
    assert d.pack_mass_kg == pytest.approx(400.0)
    assert sum(m.kg_per_pack for m in d.materials) == pytest.approx(400.0)
    assert {"lithium","nickel","cobalt"}.issubset({m.name for m in d.materials if m.critical})

def test_phase5_weighted_pathways_close():
    shares=weighted_pathway_shares(demo_periods()[0],demo_grades())
    assert sum(shares.values()) == pytest.approx(1.0)
    assert all(0 <= v <= 1 for v in shares.values())

def test_phase5_each_material_balance_closes():
    results=evaluate_lifecycle_horizon(demo_design(),demo_grades(),demo_periods())
    assert max(abs(r.material_balance_error_kg) for r in results) < 1e-7

def test_phase5_scrap_accounting_reference():
    d=demo_design();p=demo_periods()[0]
    r=evaluate_lifecycle_period(d,demo_grades(),p)[0]
    expected_embedded=p.production_packs*d.materials[0].kg_per_pack
    expected_input=expected_embedded/(1-d.manufacturing_scrap_rate)
    assert r.embedded_product_kg == pytest.approx(expected_embedded)
    assert r.manufacturing_scrap_kg == pytest.approx(expected_input-expected_embedded)

def test_phase5_circularity_metrics_are_physical():
    d=demo_design();rs=evaluate_lifecycle_horizon(d,demo_grades(),demo_periods())
    m=circularity_metrics(rs,d)
    for key in ("material_productivity","manufacturing_scrap_rate","collection_efficiency",
                "technical_recovery_rate","circular_pathway_rate","landfill_or_loss_rate",
                "critical_material_recovery_rate"):
        assert 0 <= m[key] <= 1

def test_phase5_comparative_economics_and_impact_are_labeled():
    d=demo_design();rs=evaluate_lifecycle_horizon(d,demo_grades(),demo_periods())
    econ=pathway_economics(rs,d)
    impact=lifecycle_material_impact(rs,d)
    assert econ["recovered_mass_kg"] > 0
    assert econ["modeled_material_cost_avoidance"] > 0
    assert impact["modeled_total_gwp_difference_kgco2e"] > 0
    assert "NOT REALIZED" in econ["evidence_class"]
    assert "EXTERNAL FACTOR VALIDATION PENDING" in impact["evidence_class"]

def test_phase5_invalid_grade_probabilities_rejected():
    bad={"A":RecoveryGrade("A",.5,.5,.5,0)}
    p=LifecyclePeriod(1,10,10,.8,{"A":1.0})
    with pytest.raises(ValueError):
        weighted_pathway_shares(p,bad)
