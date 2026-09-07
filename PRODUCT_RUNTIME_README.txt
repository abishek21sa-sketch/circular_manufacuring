Circular Manufacturing — Closed-Loop Material Network Planner — Product Runtime RC1

COMMANDS
--------
RUN_ACCEPTANCE.cmd          Existing Windows engineering/release acceptance gate.
RUN_APP.cmd                 Launch the full multi-view Material Circularity Studio.
RUN_PRODUCT_RUNTIME.cmd     Launch the lightweight CIRCULAR-MASS product surface.
RUN_DEMO.cmd                Regenerate deterministic demo evidence, then launch the product.
RUN_PRODUCT_ACCEPTANCE.cmd  Verify algorithm invocation, parameter counterfactuals, evidence artifact, and HTTP lifecycle.

PRODUCT SURFACE
---------------
Primary studio URL: http://127.0.0.1:8765/
Lightweight decision URL: http://127.0.0.1:8812/
Evidence artifact: Circular_Manufacturing/artifacts/product_runtime/latest_product_evidence.json
Stop either app with Ctrl+C in its command window.

The operator surface includes policy controls, first-stage facility/routing
decisions, scenario-wise demand/recovery/virgin/shortage outcomes, explicit
shortage CVaR tail values, objective decomposition, solver diagnostics,
governance checks, baseline context, claim boundary and raw evidence download.
The decision fingerprint excludes volatile runtime measurements so repeated
solves with the same inputs remain identifiable.

The product bootstrap installs the optional Gurobi Python binding. When the
licensed runtime is available, CIRCULAR-MASS uses Gurobi automatically and
reports the solver, bound, MIP gap, runtime, and audit residual in the UI and
evidence payload.

The validation machine currently reports an Academic Gurobi license. This
validates solver integration and formulation behavior; confirm commercial
Gurobi licensing and terms before any enterprise production deployment.

CLAIM BOUNDARY
--------------
The runtime preserves each repository's human-review gate and source claim boundary. Modeled, synthetic, simulated, historical, optimized, and realized evidence are not conflated.
