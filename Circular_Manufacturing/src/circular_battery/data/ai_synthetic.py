from __future__ import annotations
import numpy as np
import pandas as pd

SEED = 20260816


def generate_monthly_demand(n_months: int = 96, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    t = np.arange(n_months)
    seasonal = 140 * np.sin(2 * np.pi * t / 12) + 55 * np.cos(2 * np.pi * t / 6)
    trend = 14 * t
    price_index = 1.0 + 0.05 * np.sin(2 * np.pi * t / 18) + rng.normal(0, 0.018, n_months)
    ev_index = 100 + 1.35 * t + rng.normal(0, 2.5, n_months)
    demand = 850 + trend + seasonal - 190 * (price_index - 1) + 2.8 * (ev_index - 100) + rng.normal(0, 45, n_months)
    return pd.DataFrame({"month": t, "price_index": price_index, "ev_index": ev_index, "demand_packs": np.maximum(demand, 100)})


def generate_return_person_period(n_cohorts: int = 2200, max_age_months: int = 96, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1)
    rows = []
    chem = rng.integers(0, 3, n_cohorts)
    duty = rng.uniform(0.6, 1.45, n_cohorts)
    climate = rng.normal(0, 1, n_cohorts)
    # discrete-time hazard rises with age and severe duty/climate
    for cid in range(n_cohorts):
        event_age = None
        for age in range(12, max_age_months + 1, 3):
            logit = -7.2 + 0.075 * age + 0.95 * (duty[cid]-1) + 0.38 * climate[cid] + 0.22 * chem[cid]
            hazard = 1 / (1 + np.exp(-logit))
            event = int(rng.random() < hazard)
            rows.append({"cohort_id": cid, "age_months": age, "chemistry_code": int(chem[cid]), "duty_index": duty[cid], "climate_stress": climate[cid], "returned": event})
            if event:
                event_age = age
                break
    return pd.DataFrame(rows)


def generate_recovery_quality(n: int = 4500, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 2)
    age = rng.uniform(18, 120, n)
    soh = np.clip(1.02 - 0.0046 * age + rng.normal(0, 0.07, n), 0.25, 0.98)
    cycles = np.maximum(100, age * rng.uniform(12, 28, n) + rng.normal(0, 120, n))
    damage = np.clip(rng.beta(1.5, 5.5, n) + 0.0022 * age, 0, 1)
    temp = rng.normal(0, 1, n)
    chemistry = rng.integers(0, 3, n)
    score = 1.7*soh - 1.25*damage - 0.0010*cycles - 0.10*np.abs(temp) + 0.06*chemistry
    # deterministic-ish labels with noise; 0 second-life, 1 remanufacture, 2 recycle, 3 dispose
    noise = rng.normal(0, 0.10, n)
    z = score + noise
    label = np.select([z > 0.55, z > 0.05, z > -0.45], [0,1,2], default=3)
    return pd.DataFrame({"age_months": age, "soh": soh, "cycles": cycles, "damage_index": damage, "temperature_stress": temp, "chemistry_code": chemistry, "pathway": label.astype(int)})


def generate_scrap(n_months: int = 120, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 3)
    t = np.arange(n_months)
    throughput = 700 + 8*t + rng.normal(0, 55, n_months)
    changeovers = rng.integers(2, 15, n_months)
    operator_exp = np.clip(4.5 + 0.025*t + rng.normal(0, 0.55, n_months), 1, 8)
    moisture = np.clip(rng.normal(0.48, 0.08, n_months), 0.25, 0.75)
    defect_pressure = 0.038 + 0.000010*throughput + 0.0011*changeovers - 0.0022*operator_exp + 0.030*np.abs(moisture-0.48) + rng.normal(0,0.0025,n_months)
    scrap_rate = np.clip(defect_pressure, 0.015, 0.12)
    return pd.DataFrame({"month":t,"throughput_packs":throughput,"changeovers":changeovers,"operator_experience_years":operator_exp,"moisture_index":moisture,"scrap_rate":scrap_rate})
