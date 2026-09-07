@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "VENV_PY=.venv\Scripts\python.exe"
py -3.14 -c "import sys; print(sys.version)" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python 3.14 is required. Ensure py -3.14 works.
  exit /b 2
)
if not exist "%VENV_PY%" (
  echo Creating Python 3.14 product environment...
  py -3.14 -m venv .venv || exit /b 3
)
"%VENV_PY%" -c "import sys; raise SystemExit(0 if sys.version_info[:2]==(3,14) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Rebuilding product environment for Python 3.14...
  rmdir /s /q .venv
  py -3.14 -m venv .venv || exit /b 4
)
set "PRODUCT_RUNTIME_READY=1"
if not exist ".venv\.product_runtime_ready" set "PRODUCT_RUNTIME_READY=0"
if "%PRODUCT_RUNTIME_READY%"=="1" "%VENV_PY%" -c "import gurobipy" >nul 2>nul
if errorlevel 1 set "PRODUCT_RUNTIME_READY=0"
if "%PRODUCT_RUNTIME_READY%"=="0" (
  echo Installing product runtime dependencies...
  "%VENV_PY%" -m pip install --upgrade pip setuptools wheel || exit /b 5
  "%VENV_PY%" -m pip install -r requirements-windows-py314.lock || exit /b 6
  "%VENV_PY%" -m pip install -e ".[gurobi]" --no-deps || exit /b 7
  "%VENV_PY%" -m pip check || exit /b 8
  "%VENV_PY%" -c "from pathlib import Path; Path('.venv/.product_runtime_ready').write_text('PY314 PRODUCT RUNTIME READY', encoding='utf-8')"
)
exit /b 0
