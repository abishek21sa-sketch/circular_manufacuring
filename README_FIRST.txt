CIRCULAR PRODUCT V1
Signature algorithm: CIRCULAR-MASS

WINDOWS COMMANDS
----------------
.\RUN_ACCEPTANCE.cmd          engineering/math/release gate
.\RUN_PRODUCT_ACCEPTANCE.cmd  new interactive product-runtime gate
.\RUN_DEMO.cmd                deterministic portfolio demo + evidence
.\RUN_APP.cmd                 full multi-view Material Circularity Studio
.\RUN_PRODUCT_RUNTIME.cmd     lightweight CIRCULAR-MASS decision gate
.\RUN_SYNTHETIC_ENTERPRISE.cmd 120,000-row synthetic benchmark + Academic Gurobi

Primary studio URL: http://127.0.0.1:8765/
Lightweight product URL: http://127.0.0.1:8812/

VALIDATION STATE
----------------
Full Python 3.14 Windows regression: 160 tests collected; final Windows engineering gate PASS
Product runtime acceptance in build environment: PASS
Windows: RC3 + product-runtime + CIRCULAR-MASS/Phase 3/Phase 10 Gurobi validation PASS; local license is Academic, so commercial production authorization remains pending

The engineering/commercial readiness split is written to
Circular_Manufacturing\artifacts\release_readiness.json and documented in
Circular_Manufacturing\docs\PRODUCTION_READINESS.md.

Hosted deployment uses the explicit PostgreSQL backend and governed bundle
lineage checks; local/offline operation continues to use SQLite. The five-track
readiness controls are documented in
Circular_Manufacturing\docs\ENTERPRISE_OPERATIONS.md and
Circular_Manufacturing\docs\PILOT_DATA_AND_BENEFITS.md.

The PostgreSQL deployment path includes a versioned migration and a checked-in
SQL migration validator. Staging/production does not auto-bootstrap the schema;
the runtime gate requires the recorded migration. Live provider migration,
restore, and concurrency evidence remain external production controls.

The public benchmark includes a validated EPA GHGRP 2023 facility extract;
public environmental reference data remains distinct from customer plant data.

The full public/research/Kaggle/commercial/private source review is in
Circular_Manufacturing\docs\DATA_SOURCE_REVIEW.md. Restricted or unlicensed
sources are not represented as if they were used; the 120,000-row enterprise
benchmark remains synthetic validation.

The IE/math/AI/ML engineering readiness rubric is in
Circular_Manufacturing\docs\ENGINEERING_READINESS.md. The detailed technical
foundations are in Circular_Manufacturing\docs\TECHNICAL_FOUNDATIONS.md and
the cross-layer promotion plan is in
Circular_Manufacturing\docs\NEXT_LEVEL_ROADMAP.md.

Production evidence intake requirements are documented in
Circular_Manufacturing\docs\PRODUCTION_EVIDENCE_INTAKE.md.

The engineering baseline is the Windows-passed repository. Product-runtime files were added on top and do not replace the signature algorithm.
Modeled/synthetic/simulated/historical results remain bounded evidence, not realized operational/financial claims.
