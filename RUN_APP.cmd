@echo off
setlocal EnableExtensions
cd /d "%~dp0Circular_Manufacturing"
set "CIRCULAR_SOLVER_BACKEND=gurobi"
set "CIRCULAR_PLATFORM_DB=%CD%\artifacts\platform\studio_local.sqlite3"
call scripts\product_bootstrap.cmd
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe scripts\build_frontend.py
if errorlevel 1 exit /b %errorlevel%
.venv\Scripts\python.exe scripts\run_workbench.py
exit /b %errorlevel%
