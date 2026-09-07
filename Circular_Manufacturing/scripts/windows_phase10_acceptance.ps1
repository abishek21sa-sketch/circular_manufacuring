$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $projectPython)) {
    $projectPython = (Get-Command python -ErrorAction Stop).Source
}

function Invoke-PythonChecked {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & $projectPython @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed ($LASTEXITCODE): $projectPython $($Arguments -join ' ')"
    }
}

Write-Host "Circular Manufacturing Cumulative Phase 10 - Advanced Decision Intelligence Acceptance"
Write-Host "Python runtime: $projectPython"
Invoke-PythonChecked @("--version")
Invoke-PythonChecked @("scripts\migrate_phase10_portable_ai.py")
Invoke-PythonChecked @("scripts\build_frontend.py")
Invoke-PythonChecked @("scripts\phase1_diagnostics.py")
Invoke-PythonChecked @("scripts\phase2_diagnostics.py")
Invoke-PythonChecked @("scripts\phase3_diagnostics.py")
Invoke-PythonChecked @("scripts\phase4_diagnostics.py")
Invoke-PythonChecked @("scripts\phase5_diagnostics.py")
Invoke-PythonChecked @("scripts\phase6_diagnostics.py")
Invoke-PythonChecked @("scripts\phase7_diagnostics.py")
Invoke-PythonChecked @("scripts\phase8_diagnostics.py")
Invoke-PythonChecked @("scripts\phase9_diagnostics.py")
Invoke-PythonChecked @("scripts\phase10_diagnostics.py")
Invoke-PythonChecked @("scripts\gurobi_phase3_check.py")
Invoke-PythonChecked @("scripts\gurobi_phase10_check.py")
Invoke-PythonChecked @("scripts\run_phase10.py")
Invoke-PythonChecked @("-m","pytest","-q")
Write-Host "PHASE 10 ACCEPTANCE PASSED"
