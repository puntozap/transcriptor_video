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

## Instalacion en Windows (detallada)
### 1) Instalar Python
Opciones recomendadas:
- Winget (recomendado):
```powershell
winget install Python.Python.3.11
```
- Chocolatey:
```powershell
choco install python --version=3.11.8
```

Links oficiales (si quieres descargar manualmente):
```text
https://www.python.org/downloads/windows/
```

Verifica instalacion:
```powershell
python --version
pip --version
```

### 2) Instalar FFmpeg
Opciones recomendadas:
- Winget:
```powershell
winget install Gyan.FFmpeg
```
- Chocolatey:
```powershell
choco install ffmpeg
```

Links oficiales:
```text
https://ffmpeg.org/download.html
```

Verifica instalacion:
```powershell
ffmpeg -version
```

### 3) Crear entorno virtual e instalar dependencias
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Si `pip install -r requirements.txt` falla por permisos, prueba:
```powershell
python -m pip install -r requirements.txt
```

### 4) (Opcional) Variables de entorno
Para IA y metadata:
```text
OPENAI_API_KEY=tu_token
```
Guarda ese valor en `.env`.

## Instalador Windows (Inno Setup)
- Script: `installer\\zempervideos.iss`
- El instalador descarga siempre la version mas reciente de Python, FFmpeg y ngrok al momento de ejecutar.
- Ejecuta `scripts\\install_windows.ps1` para crear `venv` e instalar `requirements.txt`.

## Instalacion en macOS (detallada)
### 1) Instalar Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2) Instalar Python
```bash
brew install python@3.11
```

Link oficial (descarga manual):
```text
https://www.python.org/downloads/macos/
```

Verifica instalacion:
```bash
python3 --version
pip3 --version
```

### 3) Instalar FFmpeg
```bash
brew install ffmpeg
```

Link oficial:
```text
https://ffmpeg.org/download.html
```

Verifica instalacion:
```bash
ffmpeg -version
```

### 4) Crear entorno virtual e instalar dependencias
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5) (Opcional) Variables de entorno
Para IA y metadata:
```text
OPENAI_API_KEY=tu_token
```
Guarda ese valor en `.env`.

## Instalacion del proyecto
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion
```powershell
python app.py
```
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
