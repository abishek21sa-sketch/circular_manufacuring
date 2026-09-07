# Phase 1 Architecture Decisions

| Component | Choice | Why it fits Circular Manufacturing | Why not the portfolio default |
|---|---|---|---|
| Core | Python package | Strong numerical/AI/OR ecosystem; easy mathematical testing | Core engineering is library-first, not API-first |
| Phase-1 persistence | CSV/JSON artifacts | Zero external dependency and clean-extraction reproducibility | DuckDB/Parquet arrives when analytical volume justifies it |
| IE engine | Explicit Python equations | Auditable mass/lifecycle accounting | Avoids hiding physical balances in dashboard queries |
| LCA | Transparent activity-factor engine | Makes assumptions and system boundary inspectable | Avoids black-box sustainability scores |
| UI | None in Phase 1 | Mathematical foundation must be validated first | Prevents premature dashboard-first architecture |
| API | None in Phase 1 | No service boundary is needed yet | Prevents automatically copying FastAPI from other projects |
