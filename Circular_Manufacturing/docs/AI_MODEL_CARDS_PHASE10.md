# AI Model Cards — Phase 10

## Demand Forecast
- Model: Ridge regression with exogenous synthetic drivers.
- Baseline: 12-month seasonal naive.
- Validation: final 18 months held out chronologically.
- Decision use: future material demand and stochastic planning demand base.
- Added Phase-10 evidence: holdout residual prediction band and standardized coefficient effects.

## End-of-Life Return Hazard
- Model: scaled logistic discrete-time hazard.
- Baseline: constant training event-rate hazard.
- Validation: entire final cohort block held out; person-period records never cross split.
- Decision use: expected return feed and stochastic return base.
- Added Phase-10 evidence: calibration bins, ECE, standardized log-odds effects.

## Recovery Pathway Classifier
- Model: HistGradientBoosting multiclass classifier.
- Baseline: empirical majority/frequency strategy.
- Validation: final 20% synthetic return records held out.
- Decision use: second-life withholding and remanufacturing eligibility.
- Added Phase-10 evidence: permutation importance, predictive confidence, normalized entropy.

## Manufacturing Scrap Predictor
- Model: RandomForestRegressor.
- Baseline: training-mean scrap rate.
- Validation: last 24 months held out chronologically.
- Decision use: internal circular feedstock available to the stochastic network.
- Added Phase-10 evidence: tree-ensemble P10–P90 dispersion and feature importance.

## Limitation
All current model performance is **synthetic validation**. No field-accuracy or external-validity claim is made.
