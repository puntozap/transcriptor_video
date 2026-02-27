@echo off
setlocal
set "APP_DIR=%~dp0.."
set "PY=%APP_DIR%\venv\Scripts\python.exe"
if not exist "%PY%" (
  echo No se encontro el entorno virtual. Ejecuta el instalador o corre scripts\install_windows.ps1
  pause
  exit /b 1
)
"%PY%" "%APP_DIR%\app.py"
