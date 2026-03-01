@echo off
setlocal

set "ROOT=%~dp0.."
set "PY=%ROOT%\venv\Scripts\python.exe"
set "LOG=%~dp0run-app.log"

echo === ZEMPERvideos ===
echo %DATE% %TIME% Iniciando... >> "%LOG%"

if not exist "%PY%" (
  echo No se encontro el venv en %ROOT%venv. Ejecuta primero install-setup.bat
  echo ERROR: venv no encontrado >> "%LOG%"
  echo.
  echo Presiona Enter para salir...
  pause >nul
  exit /b 1
)

cd /d "%ROOT%"
"%PY%" app.py 1>> "%LOG%" 2>>&1
set "ERR=%ERRORLEVEL%"
echo %DATE% %TIME% Finalizo con codigo %ERR% >> "%LOG%"

if not "%ERR%"=="0" (
  echo.
  echo Ocurrio un error. Revisa: %LOG%
  echo Presiona Enter para salir...
  pause >nul
)
