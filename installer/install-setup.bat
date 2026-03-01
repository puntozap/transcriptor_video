@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0.."
cd /d "%ROOT%"

set "LOG=%~dp0install-setup.log"

call :log "=== Instalacion desde cero ==="

where winget >nul 2>&1
if %errorlevel%==0 (
  call :log "Usando winget..."
  call :log "Instalando Python..."
  winget install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements
  call :log "Instalando FFmpeg..."
  winget install --id Gyan.FFmpeg -e --source winget --accept-package-agreements --accept-source-agreements
  call :log "Instalando ngrok..."
  winget install --id Ngrok.Ngrok -e --source winget --accept-package-agreements --accept-source-agreements
) else (
  call :log "winget no esta disponible. Instala winget o agrega tus instaladores manualmente."
  goto :deps
)

:deps
call :log "Creando venv (si no existe)..."
if not exist "%ROOT%\venv\Scripts\python.exe" (
  py -3.11 -m venv "%ROOT%\venv" 2>nul || python -m venv "%ROOT%\venv"
)
if not exist "%ROOT%\venv\Scripts\python.exe" (
  call :log "No se pudo crear el venv. Verifica la instalacion de Python."
  goto :eof
)

call :log "Actualizando pip..."
%ROOT%\venv\Scripts\python.exe -m pip install --upgrade pip

call :log "Instalando dependencias del proyecto..."
%ROOT%\venv\Scripts\python.exe -m pip install -r "%ROOT%\requirements.txt"

call :log "Reinstalando Pillow compatible (moviepy requiere <12)..."
%ROOT%\venv\Scripts\python.exe -m pip install --upgrade --force-reinstall --no-cache-dir "pillow<12"

call :log "Listo."

echo.
echo Presiona Enter para salir...
pause >nul
exit /b 0

:log
set "MSG=%~1"
echo %MSG%
>> "%LOG%" echo %DATE% %TIME% %MSG%
exit /b 0
