from __future__ import annotations
from functools import lru_cache
import copy
import numpy as np
import sklearn

from circular_battery.ai.training import fit_all_in_memory
from circular_battery.ai.integration import PredictedCircularState, engineering_consequence
from circular_battery.data.demo import demo_chemistry


@lru_cache(maxsize=1)
def _runtime_bundle():
    models, evidence, datasets = fit_all_in_memory()
    return models, evidence, datasets


def runtime_models():
    return _runtime_bundle()[0]


def runtime_model_evidence():
    return copy.deepcopy(_runtime_bundle()[1])


def runtime_predicted_state():
    models, evidence, ds = _runtime_bundle()

    demand_row = ds["demand"].tail(1).copy()
    demand_row["month"] = demand_row["month"] + 1
    predicted_demand = float(models["demand"].predict(demand_row)[0])

    return_rows = (
        ds["returns"].groupby("cohort_id", as_index=False).tail(1)
        .sample(500, random_state=7)
    )
    expected_returns = models["returns"].expected_returns(
        return_rows, installed_base=2600
    )

    recovery_rows = ds["recovery"].sample(600, random_state=9)
    shares = models["recovery"].aggregate_shares(recovery_rows)

    scrap_row = ds["scrap"].tail(1).copy()
    scrap_row["month"] = scrap_row["month"] + 1
    scrap = float(models["scrap"].predict(scrap_row)[0])

    state = PredictedCircularState(
        predicted_demand,
        expected_returns,
        scrap,
        shares["second_life"],
        shares["remanufacture"],
        shares["recycle"],
        shares["dispose"],
    )
    return state


def runtime_phase2_payload():
    state = runtime_predicted_state()
    consequence = engineering_consequence(
        demo_chemistry(), state, production_packs=state.demand_packs
    )
    return {
        "evidence_class": "SYNTHETIC VALIDATION",
        "predicted_state": state.__dict__,
        "engineering_consequence": consequence.to_dict(),
        "model_evidence": runtime_model_evidence(),
        "runtime_model_provenance": {
            "strategy": "DETERMINISTIC CURRENT-RUNTIME RETRAINING",
            "scikit_learn_version": sklearn.__version__,
            "portable_pickle_dependency": False,
            "model_binary_role": "OPTIONAL SAME-ENVIRONMENT CACHE ONLY",
        },
    }
