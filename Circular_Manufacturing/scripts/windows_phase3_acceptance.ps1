$ErrorActionPreference = "Stop"
Write-Host "Circular Manufacturing Phase 3 - Windows/Gurobi Acceptance"
python --version
python scripts\phase1_diagnostics.py
python scripts\phase2_diagnostics.py
python scripts\phase3_diagnostics.py
python scripts\run_phase3.py
python scripts\gurobi_phase3_check.py
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "PHASE 3 ACCEPTANCE FAILED" }
Write-Host "PHASE 3 ACCEPTANCE PASSED"
