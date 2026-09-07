$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([Parameter(Mandatory=$true)][scriptblock]$Command, [Parameter(Mandatory=$true)][string]$Label)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Circular Manufacturing V1.0.1 - In-place Windows Patch Gate"
Invoke-Checked { python -m pip install -e ".[dev]" } "Editable install"
Invoke-Checked { python scripts\verify_v101_patch.py } "V1.0.1 patch verification"
Invoke-Checked { python scripts\v1_diagnostics.py } "V1 diagnostics"
Invoke-Checked { python -m pytest -q tests\test_v1_platform.py tests\test_v1_api.py } "V1 platform/API regression"
Write-Host ""
Write-Host "CIRCULAR MANUFACTURING V1.0.1 IN-PLACE PATCH PASSED"
