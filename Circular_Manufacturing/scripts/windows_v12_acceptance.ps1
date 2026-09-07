$ErrorActionPreference = "Stop"
function Invoke-PythonChecked {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python command failed ($LASTEXITCODE): python $($Arguments -join ' ')" }
}
Write-Host "Circular Manufacturing V1.2.1 - Circular Operations Decision Studio Acceptance"
Invoke-PythonChecked @("--version")
Invoke-PythonChecked @("scripts\verify_locked_core.py")
Invoke-PythonChecked @("scripts\build_frontend.py")
Invoke-PythonChecked @("scripts\v12_diagnostics.py")
Invoke-PythonChecked @("scripts\v1_live_smoke.py")
Invoke-PythonChecked @("-m","pytest","-q",
    "tests\test_v121_stochastic_value.py",
    "tests\test_v12_integrated_workbench.py",
    "tests\test_v1_api.py",
    "tests\test_phase4_workbench.py")
Write-Host ""
Write-Host "CIRCULAR MANUFACTURING V1.2.1 DECISION STUDIO ACCEPTANCE PASSED"
