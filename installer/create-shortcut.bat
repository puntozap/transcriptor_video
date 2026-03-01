@echo off
setlocal

set "ROOT=%~dp0.."
set "TARGET=%~dp0run-app.bat"
set "ICON=%ROOT%\assets\icon.ico"
set "NAME=ZEMPERvideos"

if not exist "%TARGET%" (
  echo No se encontro %TARGET%
  pause
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$Desktop = [Environment]::GetFolderPath('Desktop');" ^
  "$Lnk = Join-Path $Desktop ('%NAME%.lnk');" ^
  "$W = New-Object -ComObject WScript.Shell;" ^
  "$S = $W.CreateShortcut($Lnk);" ^
  "$S.TargetPath = '%TARGET%';" ^
  "$S.WorkingDirectory = '%ROOT%';" ^
  "if (Test-Path '%ICON%') { $S.IconLocation = '%ICON%'; }" ^
  "$S.Save();" ^
  "Write-Host ('Acceso directo creado en: ' + $Lnk)"

if %errorlevel% neq 0 (
  echo Error creando el acceso directo.
  echo.
  echo Presiona Enter para salir...
  pause >nul
  exit /b 1
)

echo.
echo Presiona Enter para salir...
pause >nul
