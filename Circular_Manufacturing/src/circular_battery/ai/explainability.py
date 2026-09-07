from __future__ import annotations
import math
import numpy as np
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error
from circular_battery.data.ai_synthetic import (
    generate_monthly_demand, generate_return_person_period,
    generate_recovery_quality, generate_scrap,
)

def _ranked(features, values):
    pairs=sorted(zip(features,[float(v) for v in values]),key=lambda x:abs(x[1]),reverse=True)
    return [{'feature':f,'importance':v,'abs_importance':abs(v)} for f,v in pairs]

def demand_uncertainty(model):
    df=generate_monthly_demand();holdout=18;tr,te=df.iloc[:-holdout],df.iloc[-holdout:]
    m=clone(model.model);m.fit(tr[model.features],tr.demand_packs)
    pred=m.predict(te[model.features]);res=np.abs(te.demand_packs.to_numpy()-pred)
    q90=float(np.quantile(res,.90,method='higher'))
    coverage=float(np.mean((te.demand_packs.to_numpy()>=pred-q90)&(te.demand_packs.to_numpy()<=pred+q90)))
    coef=m.named_steps['ridge'].coef_
    return {
        'interval_method':'split holdout absolute-residual conformal-style band',
        'nominal_coverage':.90,'empirical_holdout_coverage':coverage,'half_width_packs':q90,
        'feature_effects_standardized':_ranked(model.features,coef),
        'evidence_class':'SYNTHETIC HOLDOUT UNCERTAINTY / EXPLAINABILITY',
    }

def return_calibration(model):
    df=generate_return_person_period();cutoff=int(df.cohort_id.max()*.8);te=df[df.cohort_id>cutoff]
    p=model.hazard(te);y=te.returned.to_numpy()
    bins=np.linspace(0,1,11);ece=0.;rows=[]
    for lo,hi in zip(bins[:-1],bins[1:]):
        mask=(p>=lo)&(p<(hi if hi<1 else hi+1e-12))
        if not mask.any(): continue
        conf=float(p[mask].mean());obs=float(y[mask].mean());w=float(mask.mean())
        ece+=w*abs(conf-obs);rows.append({'lo':float(lo),'hi':float(hi),'predicted':conf,'observed':obs,'n':int(mask.sum())})
    lr=model.model.named_steps['logisticregression'];coef=lr.coef_[0]
    return {
        'expected_calibration_error':float(ece),'calibration_bins':rows,
        'feature_effects_standardized_log_odds':_ranked(model.features,coef),
        'evidence_class':'SYNTHETIC COHORT HOLDOUT CALIBRATION',
    }

def recovery_explainability(model):
    df=generate_recovery_quality();split=int(len(df)*.8);te=df.iloc[split:]
    pi=permutation_importance(model.model,te[model.features],te.pathway,scoring='f1_macro',n_repeats=6,random_state=20260817,n_jobs=1)
    proba=model.predict_proba(te);pred=proba.argmax(axis=1);conf=proba.max(axis=1)
    top_acc=float(np.mean(pred==te.pathway.to_numpy()));mean_conf=float(conf.mean())
    entropy=-np.sum(np.clip(proba,1e-12,1)*np.log(np.clip(proba,1e-12,1)),axis=1)/math.log(proba.shape[1])
    return {
        'feature_importance_permutation_macro_f1':_ranked(model.features,pi.importances_mean),
        'top_label_accuracy':top_acc,'mean_top_probability':mean_conf,
        'mean_normalized_entropy':float(entropy.mean()),
        'confidence_gap':float(mean_conf-top_acc),
        'evidence_class':'SYNTHETIC HOLDOUT EXPLAINABILITY',
    }

def scrap_uncertainty(model):
    df=generate_scrap();holdout=24;te=df.iloc[-holdout:]
    # Existing persisted model is fit on full synthetic benchmark; tree spread is model uncertainty evidence,
    # while holdout MAE remains in Phase-2 evidence.
    X=te[model.features]
    tree=np.vstack([est.predict(X.to_numpy()) for est in model.model.estimators_])
    lo=np.quantile(tree,.10,axis=0);hi=np.quantile(tree,.90,axis=0)
    width=float(np.mean(hi-lo))
    return {
        'tree_ensemble_p10_p90_mean_width':width,
        'feature_importance':_ranked(model.features,model.model.feature_importances_),
        'evidence_class':'SYNTHETIC ENSEMBLE DISPERSION / EXPLAINABILITY',
    }

def explain_all(models):
    return {
        'demand':demand_uncertainty(models['demand']),
        'returns':return_calibration(models['returns']),
        'recovery':recovery_explainability(models['recovery']),
        'scrap':scrap_uncertainty(models['scrap']),
    }
