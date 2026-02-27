# Crear instalador (Windows)

Este documento describe el flujo para generar un instalador tipo “Next, Next, Finish”.

## Requisitos
- Inno Setup instalado

## 1) Crear instalador con Inno Setup
1. Abrir Inno Setup.
2. Compilar el script `installer\zempervideos.iss`.
3. El instalador queda en `installer\ZEMPERvideos_Setup.exe`.

### Que hace el instalador
- Copia el proyecto a `{pf}\ZEMPERvideos`.
- Ejecuta `scripts\install_windows.ps1` para instalar:
  - Python (ultima version desde python.org).
  - FFmpeg (ultima version desde gyan.dev).
  - ngrok (ultima version desde ngrok.com).
  - Crea `venv` e instala `requirements.txt`.

> Nota: el script necesita permisos de Administrador para escribir en `Program Files` y actualizar `PATH`.

## 3) Distribución
El instalador generado queda en la carpeta `installer/`.

## Notas
- El instalador descarga siempre la version mas reciente en el momento de ejecutar.
- Para firmar el instalador, usar un certificado de firma de código.
