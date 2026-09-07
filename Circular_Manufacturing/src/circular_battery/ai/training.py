from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
import joblib
from circular_battery.data.ai_synthetic import (
    generate_monthly_demand, generate_return_person_period,
    generate_recovery_quality, generate_scrap,
)
from circular_battery.ai.models import (
    DemandForecaster, ReturnHazardModel,
    RecoveryPathwayClassifier, ScrapPredictor,
)


def fit_all_in_memory():
    """Fit the four deterministic synthetic-validation models in the current runtime.

    This is the portable execution path. It does not deserialize estimators created
    by another scikit-learn build, so compiled/private estimator internals never
    cross environment boundaries.
    """
    datasets = {
        "demand": generate_monthly_demand(),
        "returns": generate_return_person_period(),
        "recovery": generate_recovery_quality(),
        "scrap": generate_scrap(),
    }
    models = {
        "demand": DemandForecaster(),
        "returns": ReturnHazardModel(),
        "recovery": RecoveryPathwayClassifier(),
        "scrap": ScrapPredictor(),
    }
    evidence = {}
    for key, model in models.items():
        evidence[key] = asdict(model.fit_validate(datasets[key]))
    return models, evidence, datasets


def train_all(model_dir: Path | str, persist_models: bool = True):
    """Fit current-runtime models and optionally persist local cache artifacts.

    Persisted scikit-learn/joblib objects are explicitly a same-environment cache,
    not a portable release interface. Portable application execution uses
    ``fit_all_in_memory`` / ``circular_battery.ai.runtime``.
    """
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)
    models, evidence, datasets = fit_all_in_memory()
    if persist_models:
        for key, model in models.items():
            joblib.dump(model, model_dir / f"{key}_model.joblib")
    (model_dir / "model_evidence.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    return models, evidence, datasets
