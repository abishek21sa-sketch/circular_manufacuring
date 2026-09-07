@echo off
setlocal EnableExtensions
cd /d "%~dp0Circular_Manufacturing"
set "CIRCULAR_SOLVER_BACKEND=gurobi"
call scripts\product_bootstrap.cmd
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe scripts\product_runtime.py --accept
exit /b %errorlevel%
