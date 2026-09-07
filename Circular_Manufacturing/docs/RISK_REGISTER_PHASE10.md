# Phase 10 Engineering Risk Register

| Risk | Current control | Residual status |
|---|---|---|
| Synthetic benchmark may overstate field performance | Every result and model metric carries synthetic/offline evidence language | External validation pending |
| Scenario reduction may omit rare futures | Policies are optimized on reduced scenarios but replayed against the unreduced raw ensemble | Residual tail-model risk remains |
| Recovery-factor uncertainty | Yield, collection, price, outage and carbon factors are varied in digital experiments | External calibration pending |
| Optimization infeasibility | Emergency/shortage recourse, explicit solver-state checks and post-solve audits | Low for benchmark; production inputs still require validation |
| Single-site recovery dependency | Optional N−1 recovery-capacity constraint and resilience policy | Cost/resilience trade-off remains |
| Critical-material supplier concentration | Per-material supplier-share caps and HHI reporting | Real supplier network pending |
| AI leakage | Time/cohort holdouts are preserved from Phase 2 | Real-source temporal validation pending |
| AI miscalibration | Demand interval coverage and return ECE are explicitly reported | Synthetic-only calibration evidence |
| Recommendation automation risk | `human_approval_required=true`; LLM is not required for numeric decision generation | Human review remains mandatory |
| Solver portability | SciPy/HiGHS is portable reference; Gurobi is separate licensed Windows verification path | Gurobi license required for licensed gate |
| UI hides computational limitations | Dedicated EVIDENCE and TRACE modes expose assumptions/evidence classes | Human-factors validation pending |
