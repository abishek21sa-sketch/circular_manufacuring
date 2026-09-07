$ErrorActionPreference = "Stop"

function Invoke-PythonChecked {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed ($LASTEXITCODE): python $($Arguments -join ' ')"
    }
}

Write-Host "Circular Manufacturing V1.0.1 - Windows SQLite Hotfix Gate"
Invoke-PythonChecked @("--version")
Invoke-PythonChecked @("scripts\verify_locked_core.py")
Invoke-PythonChecked @("scripts\v1_diagnostics.py")
Invoke-PythonChecked @("scripts\v1_live_smoke.py")
Invoke-PythonChecked @("-m","pytest","-q",
    "tests\test_v1_platform.py",
    "tests\test_v1_api.py")
Write-Host ""
Write-Host "CIRCULAR MANUFACTURING V1.0.1 SQLITE HOTFIX GATE PASSED"
