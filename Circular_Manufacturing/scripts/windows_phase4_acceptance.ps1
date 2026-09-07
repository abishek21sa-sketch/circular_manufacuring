$ErrorActionPreference = "Stop"
Write-Host "Circular Manufacturing Phase 4 - Windows Workbench Acceptance"
python --version
python scripts\build_frontend.py
python scripts\phase1_diagnostics.py
python scripts\phase2_diagnostics.py
python scripts\phase3_diagnostics.py
python scripts\phase4_diagnostics.py
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "PHASE 4 ACCEPTANCE FAILED" }
Write-Host ""
Write-Host "Automated acceptance passed."
Write-Host "Start the workbench with: python scripts\run_workbench.py"
Write-Host "Then open: http://127.0.0.1:8765"
Write-Host "PHASE 4 ACCEPTANCE PASSED"
