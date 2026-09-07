$ErrorActionPreference = "Stop"

function Invoke-PythonChecked {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed ($LASTEXITCODE): python $($Arguments -join ' ')"
    }
}

Write-Host "Circular Manufacturing Phase 10 - Final Windows Gate"
Invoke-PythonChecked @("--version")
Invoke-PythonChecked @("scripts\migrate_phase10_portable_ai.py")
Invoke-PythonChecked @("scripts\gurobi_phase10_check.py")
Invoke-PythonChecked @("scripts\phase10_diagnostics.py")
Invoke-PythonChecked @("-m","pytest","-q","tests/test_phase10_release_gate.py")
Write-Host "PHASE 10 FINAL WINDOWS GATE PASSED"
