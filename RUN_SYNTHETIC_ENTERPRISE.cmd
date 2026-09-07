@echo off
setlocal
set "ROOT=%~dp0Circular_Manufacturing"
set "PY=%ROOT%\.venv\Scripts\python.exe"
set "CIRCULAR_SOLVER_BACKEND=gurobi"
if not exist "%PY%" (
  echo Missing project virtual environment: %PY%
  exit /b 2
)
pushd "%ROOT%"
"%PY%" scripts\generate_synthetic_enterprise_dataset.py
if errorlevel 1 exit /b 3
"%PY%" scripts\validate_synthetic_enterprise_dataset.py
if errorlevel 1 exit /b 4
"%PY%" scripts\synthetic_enterprise_gurobi_benchmark.py
if errorlevel 1 exit /b 5
echo SYNTHETIC ENTERPRISE DATASET AND ACADEMIC GUROBI BENCHMARK PASSED
popd
exit /b 0
