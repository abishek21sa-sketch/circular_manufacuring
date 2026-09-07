from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, HistGradientBoostingClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, log_loss, brier_score_loss, accuracy_score, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

@dataclass
class ModelEvidence:
    task: str
    model_name: str
    baseline_name: str
    metrics: dict
    baseline_metrics: dict
    validation_design: str
    evidence_class: str = "SYNTHETIC VALIDATION"

class DemandForecaster:
    features = ["month", "price_index", "ev_index"]
    def __init__(self):
        self.model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        self.evidence = None
    def fit_validate(self, df: pd.DataFrame, holdout: int = 18):
        tr, te = df.iloc[:-holdout], df.iloc[-holdout:]
        self.model.fit(tr[self.features], tr["demand_packs"])
        pred = self.model.predict(te[self.features])
        seasonal = np.array([df.iloc[i-12]["demand_packs"] for i in range(len(df)-holdout, len(df))])
        metrics = {"mae": float(mean_absolute_error(te.demand_packs,pred)), "rmse": float(mean_squared_error(te.demand_packs,pred)**0.5)}
        base = {"mae": float(mean_absolute_error(te.demand_packs,seasonal)), "rmse": float(mean_squared_error(te.demand_packs,seasonal)**0.5)}
        self.evidence = ModelEvidence("monthly battery demand forecasting","Ridge regression with exogenous drivers","12-month seasonal naive",metrics,base,"Last 18 months held out; no future rows used in training.")
        self.model.fit(df[self.features], df["demand_packs"])
        return self.evidence
    def predict(self, rows): return self.model.predict(rows[self.features])

class ReturnHazardModel:
    features = ["age_months","chemistry_code","duty_index","climate_stress"]
    def __init__(self):
        self.model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=800, random_state=20260816))
        self.evidence = None
    def fit_validate(self, df: pd.DataFrame):
        # cohort-level split prevents rows from one product appearing in both train/test
        cutoff = int(df.cohort_id.max()*0.8)
        tr, te = df[df.cohort_id<=cutoff], df[df.cohort_id>cutoff]
        self.model.fit(tr[self.features], tr.returned)
        p = self.model.predict_proba(te[self.features])[:,1]
        base_p = np.repeat(tr.returned.mean(), len(te))
        metrics = {"brier": float(brier_score_loss(te.returned,p)), "log_loss": float(log_loss(te.returned,p,labels=[0,1]))}
        base = {"brier": float(brier_score_loss(te.returned,base_p)), "log_loss": float(log_loss(te.returned,base_p,labels=[0,1]))}
        self.evidence = ModelEvidence("discrete-time end-of-life return hazard","scaled logistic discrete-time hazard","constant train-event-rate hazard",metrics,base,"Hold out entire final 20% of cohorts; person-period rows never cross split.")
        self.model.fit(df[self.features], df.returned)
        return self.evidence
    def hazard(self, rows): return self.model.predict_proba(rows[self.features])[:,1]
    def expected_returns(self, rows: pd.DataFrame, installed_base: float) -> float:
        # For a population represented by rows at current age, expected returns next interval = sum hazard * represented units.
        h = self.hazard(rows)
        return float(installed_base * np.mean(h))

class RecoveryPathwayClassifier:
    features=["age_months","soh","cycles","damage_index","temperature_stress","chemistry_code"]
    labels={0:"second_life",1:"remanufacture",2:"recycle",3:"dispose"}
    def __init__(self):
        self.model=HistGradientBoostingClassifier(max_depth=5, learning_rate=.07, max_iter=220, random_state=20260816)
        self.evidence=None
    def fit_validate(self, df: pd.DataFrame):
        split=int(len(df)*.8); tr,te=df.iloc[:split],df.iloc[split:]
        self.model.fit(tr[self.features],tr.pathway)
        pred=self.model.predict(te[self.features]); proba=self.model.predict_proba(te[self.features])
        majority=int(tr.pathway.mode().iloc[0]); bpred=np.repeat(majority,len(te))
        class_freq=tr.pathway.value_counts(normalize=True).reindex([0,1,2,3],fill_value=1e-9).values
        bproba=np.tile(class_freq,(len(te),1))
        metrics={"accuracy":float(accuracy_score(te.pathway,pred)),"macro_f1":float(f1_score(te.pathway,pred,average="macro")),"log_loss":float(log_loss(te.pathway,proba,labels=[0,1,2,3]))}
        base={"accuracy":float(accuracy_score(te.pathway,bpred)),"macro_f1":float(f1_score(te.pathway,bpred,average="macro")),"log_loss":float(log_loss(te.pathway,bproba,labels=[0,1,2,3]))}
        self.evidence=ModelEvidence("recovery pathway classification","HistGradientBoostingClassifier","majority-class / empirical-frequency",metrics,base,"Final 20% synthetic return records held out before training.")
        self.model.fit(df[self.features],df.pathway)
        return self.evidence
    def predict_proba(self, rows): return self.model.predict_proba(rows[self.features])
    def aggregate_shares(self, rows):
        p=self.predict_proba(rows)
        avg=p.mean(axis=0)
        return {self.labels[i]:float(avg[i]) for i in range(4)}

class ScrapPredictor:
    features=["month","throughput_packs","changeovers","operator_experience_years","moisture_index"]
    def __init__(self):
        self.model=RandomForestRegressor(n_estimators=280,min_samples_leaf=3,random_state=20260816,n_jobs=1)
        self.evidence=None
    def fit_validate(self,df:pd.DataFrame,holdout:int=24):
        tr,te=df.iloc[:-holdout],df.iloc[-holdout:]
        self.model.fit(tr[self.features],tr.scrap_rate)
        pred=self.model.predict(te[self.features]); base=np.repeat(tr.scrap_rate.mean(),len(te))
        metrics={"mae":float(mean_absolute_error(te.scrap_rate,pred)),"rmse":float(mean_squared_error(te.scrap_rate,pred)**0.5)}
        baseline={"mae":float(mean_absolute_error(te.scrap_rate,base)),"rmse":float(mean_squared_error(te.scrap_rate,base)**0.5)}
        self.evidence=ModelEvidence("manufacturing scrap-rate prediction","RandomForestRegressor","training-mean scrap rate",metrics,baseline,"Last 24 months held out chronologically.")
        self.model.fit(df[self.features],df.scrap_rate)
        return self.evidence
    def predict(self,rows): return np.clip(self.model.predict(rows[self.features]),0,0.25)
