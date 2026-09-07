# Phase 2 — Lifecycle Prediction & Recovery Intelligence

All bundled evaluation is **SYNTHETIC VALIDATION**. It demonstrates model plumbing, validation discipline, baseline comparison, leakage controls, uncertainty-compatible outputs, and coupling into the material-flow engine; it is not a claim of real-world predictive accuracy.

## 1. Demand forecasting
- **Target:** monthly battery-pack demand.
- **Features:** chronological month index, synthetic price index, EV-demand index.
- **Model:** regularized ridge regression on chronological/exogenous demand drivers.
- **Baseline:** 12-month seasonal naive forecast.
- **Validation:** final 18 months held out chronologically.
- **Metrics:** MAE and RMSE.
- **Decision use:** sets production/material requirement entering circular production planning.

## 2. End-of-life return hazard
- **Target:** probability of return during the next discrete age interval.
- **Features:** age, chemistry code, duty index, climate stress.
- **Model:** scaled logistic discrete-time hazard model.
- **Baseline:** constant event-rate hazard from training cohorts.
- **Validation:** entire cohorts are separated; final 20% of cohort IDs are never present in training.
- **Metrics:** Brier score and log loss.
- **Decision use:** expected return quantity becomes prospective feedstock for recovery planning.

For represented installed base `N` with hazards `h_i`, next-interval expected returns are:

`E[R] = N × mean(h_i)`

## 3. Recovery-pathway classification
- **Target:** second-life, remanufacture, recycle, or dispose.
- **Features:** age, state of health, cycles, damage, temperature stress, chemistry.
- **Model:** histogram gradient boosting classifier.
- **Baseline:** majority class for hard classification and empirical class frequencies for log loss.
- **Validation:** final 20% held out before refit.
- **Metrics:** accuracy, macro-F1, multiclass log loss.
- **Decision use:** predicted pathway probabilities become circular-pathway shares in the engineering state.

## 4. Manufacturing scrap prediction
- **Target:** monthly scrap rate.
- **Features:** month, throughput, changeovers, operator experience, moisture index.
- **Model:** random forest regression.
- **Baseline:** training-mean scrap rate.
- **Validation:** final 24 months held out chronologically.
- **Metrics:** MAE and RMSE.
- **Decision use:** changes recoverable manufacturing scrap and virgin-material requirement.

## AI → IE coupling
Predictions are converted into a `PredictedCircularState` and passed into the already-validated Phase-1 material-flow equations. Tests explicitly verify that higher predicted recoverable returns reduce virgin-material requirement and that predicted scrap changes physical recovery feed. AI therefore changes an engineering consequence rather than terminating as a dashboard metric.
