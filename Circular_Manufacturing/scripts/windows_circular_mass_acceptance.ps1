$ErrorActionPreference = "Stop"
Write-Host "CIRCULAR-MASS Windows Acceptance"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (Test-Path ".venv\Scripts\python.exe") { $py = ".venv\Scripts\python.exe" } else { $py = "python" }

& $py scripts/build_frontend.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $py -m pytest tests/test_signature_algorithm.py tests/test_circular_mass_product.py tests/test_circular_mass_ui_contract.py tests/test_v1_api.py tests/test_phase8_advanced_or.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $py scripts/circular_mass_evidence.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $py scripts/circular_mass_product_evidence.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "CIRCULAR_MASS_WINDOWS_ACCEPTANCE=PASS"
