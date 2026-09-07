$ErrorActionPreference = "Stop"
Write-Host "Circular Manufacturing Phase 4A - Material Circularity Studio Acceptance"
python --version
python scripts\build_frontend.py
python scripts\phase1_diagnostics.py
python scripts\phase2_diagnostics.py
python scripts\phase3_diagnostics.py
python scripts\phase4_diagnostics.py
python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "PHASE 4A ACCEPTANCE FAILED" }
Write-Host ""
Write-Host "Automated acceptance passed."
Write-Host "Start with: python scripts\run_workbench.py"
Write-Host "Open: http://127.0.0.1:8765"
Write-Host "PHASE 4A ACCEPTANCE PASSED"
