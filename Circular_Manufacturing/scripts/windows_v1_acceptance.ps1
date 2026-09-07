$ErrorActionPreference = "Stop"

function Invoke-PythonChecked {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed ($LASTEXITCODE): python $($Arguments -join ' ')"
    }
}

Write-Host "Circular Manufacturing Intelligence Platform V1.0 - Final Windows Acceptance"
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
Invoke-PythonChecked @("scripts\migrate_phase10_portable_ai.py")
Invoke-PythonChecked @("scripts\run_data_bundle.py","data\templates\reference_bundle","--validate-only")
Invoke-PythonChecked @("scripts\validate_governed_bundle.py","data\templates\reference_bundle","--require-lineage","--out","artifacts\governed_reference_bundle.json")
Invoke-PythonChecked @("scripts\validate_production_attestations.py","--out","artifacts\production_attestation_validation.json")
Invoke-PythonChecked @("scripts\v1_diagnostics.py")
Invoke-PythonChecked @("scripts\constitution_audit.py")
Invoke-PythonChecked @("scripts\security_scan.py")
Invoke-PythonChecked @("scripts\v1_live_smoke.py")
Invoke-PythonChecked @("scripts\dependency_check.py")
Invoke-PythonChecked @("-m","pytest","-q")
Write-Host ""
Write-Host "CIRCULAR MANUFACTURING V1.0 ACCEPTANCE PASSED"
