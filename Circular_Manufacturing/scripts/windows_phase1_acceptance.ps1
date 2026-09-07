$ErrorActionPreference = "Stop"
Write-Host "Circular Manufacturing Phase 1 - Windows Acceptance"
python --version
python scripts\generate_demo.py
python scripts\run_phase1.py
python scripts\phase1_diagnostics.py
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "PHASE 1 ACCEPTANCE FAILED" }
Write-Host "PHASE 1 ACCEPTANCE PASSED"
