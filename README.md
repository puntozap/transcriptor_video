# ZEMPERvideos - Transcriptor de Video

`ZEMPERvideos` aloja "Transcriptor de Video", una app de escritorio (CustomTkinter + Python) para cortar, subtitular, enriquecer con IA y publicar videos o audios desde una sola interfaz. El flujo integra generacion de metadata, exportacion vertical, subida a Drive, YouTube, Instagram y TikTok, y envios masivos por WhatsApp con media alojada en Drive.

## Arquitectura rapida
- `ui/`: cada pestana lee y muta el estado compartido en `ui/shared/state.py`.
- `core/`: logica de negocio (procesamiento de video, OAuth, Drive, YouTube, Instagram, TikTok, WhatsApp) y helpers reutilizables.
- `credentials/`: secretos y tokens persistidos (Drive OAuth, cuentas de servicio, etc.).
- `venv/`: entorno virtual. `requirements.txt` lista dependencias.

## Funcionalidades destacadas
- Corte por minutos con sliders, validaciones, exportacion de MP3, SRT y clips.
- Subtitulos, visualizadores y filtros con configuracion en UI.
- Fondo con imagen o video loop (sin audio) en corte sin bordes.
- Intro opcional para corte sin bordes, con concatenacion compatible de audio.
- Corte + Zoom: recorte porcentual, encuadre centrado, zoom, y fondo en loop.
- Cintas (nombre y rol) configurables y posicionables en corte sin bordes y Corte + Zoom.
- Integracion con Drive, YouTube, Instagram, TikTok y WhatsApp.
- Historias de Instagram con espera de procesamiento, auto-clip si supera 60s y tags.

## Requisitos
- Python 3.11+ (probado en 3.13).
- FFmpeg disponible en `PATH`.
- Windows recomendado por CustomTkinter.

## Instalacion en Windows (recomendada)
Desde la raiz del proyecto:
```powershell
installer\install-setup.bat
```
Esto instala Python 3.11, FFmpeg, ngrok, crea el `venv` en la raiz e instala dependencias.

Crear acceso directo en el escritorio:
```powershell
installer\create-shortcut.bat
```

Si quieres ejecutar sin acceso directo:
```powershell
installer\run-app.bat
```

## Instalador Windows (Inno Setup)
- Script: `installer\\zempervideos.iss`
- El instalador descarga siempre la version mas reciente de Python, FFmpeg y ngrok al momento de ejecutar.
- Ejecuta `scripts\\install_windows.ps1` para crear `venv` e instalar `requirements.txt`.

## Instalacion en macOS (recomendada)
Desde la raiz del proyecto:
```bash
bash installer/install-setup-macos.sh
```

Crear acceso directo en el escritorio:
```bash
bash installer/create-shortcut-macos.sh
```

Ejecutar manualmente:
```bash
installer/run-app.command
```

## Variables de entorno (opcional)
Para IA y metadata:
```text
OPENAI_API_KEY=tu_token
```
Guarda ese valor en `.env`.

## Ejecucion manual (si no usas instaladores)
Windows:
```powershell
venv\Scripts\python.exe app.py
```
macOS:
```bash
./venv/bin/python app.py
```

## Solucion de problemas
- Error `cannot import name '_imaging' from 'PIL'`:
  - Ejecuta `installer/install-setup.bat` (Windows) o `installer/install-setup-macos.sh` (macOS).
  - Verifica que Pillow sea `<12` porque `moviepy` lo requiere.
- Error `ModuleNotFoundError: No module named 'yt_dlp'`:
  - Ejecuta el instalador otra vez o instala manualmente con:
    - `venv\Scripts\python.exe -m pip install yt-dlp` (Windows)
    - `./venv/bin/python -m pip install yt-dlp` (macOS)
- Si el acceso directo no abre:
  - Ejecuta `installer/run-app.bat` (Windows) o `installer/run-app.command` (macOS) y revisa el log en `installer/`.
La UI inicia maximizada y escucha `localhost:4850` para capturar OAuth cuando se autoriza Drive o YouTube.

## Configuracion rapida
- Crea `.env` con `OPENAI_API_KEY=tu_token` para habilitar generacion asistida de titulos, descripciones y hashtags.
- La carpeta de Drive se persiste en `credentials/drive_config.json`.
- Configuracion del Corte + Zoom en `core/config_corte_zoom.py`.
- Configuracion de corte sin bordes en `core/corte_config.py`.

## Flujo destacado
1. Procesamiento: cortes, subtitulos, visualizadores y exportacion vertical.
2. IA y metadata: propuestas de titulo, descripcion y etiquetas.
3. Drive configurado: carga de JSON y tokens persistidos.
4. Integracion YouTube/Instagram/TikTok: subida con tokens persistidos.
5. WhatsApp + Drive: envio masivo con media alojada en Drive.
6. Actividad y logs: trazas visibles en la pestaña de actividad.

## Salidas
- `output/{base}/cortes/` -> clips normales.
- `output/{base}/audios/` -> MP3.
- `output/{base}/subtitulos/` -> SRT.
- `output/{base}/verticales/` -> versiones 9:16.
- `output/{base}/subtitulados/` -> videos con subtitulos quemados.
- `output/{base}/download/` -> descargas generadas.

## Documentacion adicional
- `docs/instagram_reel_upload.md`: guia para subir Reels manualmente y via API.
- `docs/youtube_credentials.md` y `docs/youtube_upload.md`: ayuda para registrar JSON y subir videos con OAuth.
- `api-tik-tok.md` y otros archivos en `docs/` explican flujos especificos.
