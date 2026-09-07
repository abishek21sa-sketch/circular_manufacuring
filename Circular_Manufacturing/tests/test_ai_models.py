import numpy as np
from circular_battery.data.ai_synthetic import generate_monthly_demand,generate_return_person_period,generate_recovery_quality,generate_scrap
from circular_battery.ai.models import DemandForecaster,ReturnHazardModel,RecoveryPathwayClassifier,ScrapPredictor

def test_demand_model_beats_seasonal_naive():
    e=DemandForecaster().fit_validate(generate_monthly_demand())
    assert e.metrics["mae"] < e.baseline_metrics["mae"]

def test_return_hazard_beats_constant_baseline_brier():
    e=ReturnHazardModel().fit_validate(generate_return_person_period(n_cohorts=900))
    assert e.metrics["brier"] < e.baseline_metrics["brier"]

def test_recovery_classifier_probabilities_and_baseline():
    df=generate_recovery_quality(2200); m=RecoveryPathwayClassifier(); e=m.fit_validate(df)
    assert e.metrics["macro_f1"] > e.baseline_metrics["macro_f1"]
    p=m.predict_proba(df.head(20))
    assert np.allclose(p.sum(axis=1),1.0)

def test_scrap_model_beats_mean_baseline():
    e=ScrapPredictor().fit_validate(generate_scrap())
    assert e.metrics["mae"] < e.baseline_metrics["mae"]
