$ErrorActionPreference = "Stop"
Write-Host "Circular Manufacturing Cumulative Phase 7 - Windows Acceptance"
python --version
python scripts\phase1_diagnostics.py
python scripts\phase2_diagnostics.py
python scripts\phase3_diagnostics.py
python scripts\phase4_diagnostics.py
python scripts\phase5_diagnostics.py
python scripts\phase6_diagnostics.py
python scripts\phase7_diagnostics.py
python scripts\gurobi_phase3_check.py
python scripts\run_phase567.py
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "PHASE 7 ACCEPTANCE FAILED" }
Write-Host "PHASE 7 ACCEPTANCE PASSED"
