$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath $projectPython)) {
    $projectPython = (Get-Command python -ErrorAction Stop).Source
}

function Invoke-PythonChecked {
    param([Parameter(Mandatory=$true)][string[]]$Arguments)
    & $projectPython @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Python command failed ($LASTEXITCODE): $projectPython $($Arguments -join ' ')" }
}
Write-Host "Circular Manufacturing V1.0 - Short Final Windows Gate"
Write-Host "Python runtime: $projectPython"
Invoke-PythonChecked @("--version")
Invoke-PythonChecked @("scripts\migrate_phase10_portable_ai.py")
Invoke-PythonChecked @("scripts\verify_locked_core.py")
Invoke-PythonChecked @("scripts\build_frontend.py")
Invoke-PythonChecked @("scripts\dependency_check.py")
Invoke-PythonChecked @("scripts\v1_diagnostics.py")
Invoke-PythonChecked @("scripts\constitution_audit.py")
Invoke-PythonChecked @("scripts\security_scan.py")
Invoke-PythonChecked @("scripts\validate_governed_bundle.py","data\templates\reference_bundle","--require-lineage","--out","artifacts\governed_reference_bundle.json")
Invoke-PythonChecked @("scripts\validate_database_migrations.py","--out","artifacts\database_migration_validation.json")
Invoke-PythonChecked @("scripts\validate_public_reference_dataset.py","data\public\epa_ghgrp_2023_facilities.csv","data\public\epa_ghgrp_2023_metadata.json","--out","artifacts\public_reference_validation.json")
Invoke-PythonChecked @("scripts\validate_data_source_registry.py","--out","artifacts\data_source_registry_validation.json")
Invoke-PythonChecked @("scripts\generate_synthetic_enterprise_dataset.py")
Invoke-PythonChecked @("scripts\validate_synthetic_enterprise_dataset.py")
Invoke-PythonChecked @("scripts\synthetic_enterprise_gurobi_benchmark.py")
Invoke-PythonChecked @("scripts\validate_production_attestations.py","--out","artifacts\production_attestation_validation.json")
Invoke-PythonChecked @("scripts\production_preflight.py")
Invoke-PythonChecked @("scripts\v1_live_smoke.py")
Invoke-PythonChecked @("scripts\gurobi_circular_mass_check.py")
Invoke-PythonChecked @("scripts\gurobi_phase3_check.py")
Invoke-PythonChecked @("scripts\gurobi_phase10_check.py")
Invoke-PythonChecked @("scripts\release_readiness.py")
Invoke-PythonChecked @("scripts\validate_engineering_readiness.py","--out","artifacts\engineering_readiness.json")
Invoke-PythonChecked @("-m","pytest","-q","tests/test_v1_platform.py","tests/test_v1_ingestion.py","tests/test_v1_api.py","tests/test_phase4_workbench.py","tests/test_phase10_release_gate.py","tests/test_synthetic_enterprise_dataset.py","tests/test_data_source_registry.py","tests/test_engineering_readiness.py")
Write-Host ""
Write-Host "CIRCULAR MANUFACTURING V1.0 FINAL WINDOWS GATE PASSED"
