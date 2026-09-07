$ErrorActionPreference = "Stop"
Write-Host "Circular Manufacturing Phase 2 - Windows Acceptance"
python --version
python scripts\phase1_diagnostics.py
python scripts\train_phase2_ai.py
python scripts\phase2_diagnostics.py
python scripts\run_phase2_decision.py
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "PHASE 2 ACCEPTANCE FAILED" }
Write-Host "PHASE 2 ACCEPTANCE PASSED"
