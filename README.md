
███████╗ █████╗ ██████╗  █████╗ ████████╗ █████╗ 
╚══███╔╝██╔══██╗██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
  ███╔╝ ███████║██████╔╝███████║   ██║   ███████║
 ███╔╝  ██╔══██║██╔═══╝ ██╔══██║   ██║   ██╔══██║
███████╗██║  ██║██║     ██║  ██║   ██║   ██║  ██║
╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝

# 🎬 Transcriptor de Video a Texto  

Este proyecto permite **extraer el audio de un video**, dividirlo en fragmentos y **transcribirlo a texto en español** usando el modelo **Whisper de OpenAI**.  
Incluye una **interfaz gráfica de escritorio** construida con **Tkinter**.  

---

## 📖 Características
- Convierte cualquier video en texto.
- Divide el audio automáticamente en fragmentos para facilitar la transcripción.
- Interfaz gráfica simple con Tkinter.
- Exporta las transcripciones en archivos `.txt`.

---

## 🚀 Requisitos

- **Python** 3.11+ (funciona también en 3.13)  
- **FFmpeg** instalado y agregado al PATH  
- **Git** (opcional, si deseas clonar desde GitHub)  

---

## 📥 Instalación

### 1. Clonar o copiar el proyecto
```powershell
git clone https://github.com/puntozap/transcriptor_video.git
cd transcriptor_video
```
> También puedes copiar manualmente la carpeta `transcriptor_video` en tu PC.

### 2. Crear el entorno virtual
```powershell
python -m venv venv
```
Activar el entorno:
```powershell
.venv\Scripts\Activate
```
(Verás `(venv)` al inicio de la terminal cuando esté activo).  

### 3. Instalar dependencias
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Dependencias principales:
- `moviepy` → extracción de audio  
- `openai-whisper` → transcripción  
- `torch` → backend de Whisper  
- `tqdm`, `numpy`, `pillow`, etc.  

### 4. Verificar FFmpeg
```powershell
ffmpeg -version
```
Si no está instalado:  
```powershell
winget install ffmpeg
```
o con Chocolatey:
```powershell
choco install ffmpeg -y
```

---

## ▶️ Uso

Ejecutar la aplicación:
```powershell
python app.py
```

1. Se abrirá la ventana de Tkinter.  
2. Selecciona un video desde tu PC.  
3. El sistema:  
   - Extrae el audio.  
   - Lo divide en **5 fragmentos**.  
   - Transcribe cada parte en **español**.  
   - Guarda los resultados en:  
     ```
     output/transcripciones/tu_video_parte1.txt
     output/transcripciones/tu_video_parte2.txt
     ...
     ```

---

## 📂 Estructura del proyecto

```
transcriptor_video/
│── app.py                  # Punto de entrada (Tkinter)
│── requirements.txt         # Dependencias
│
├── ui/                      # Interfaz gráfica
│   ├── main_window.py       # Ventana principal
│   └── dialogs.py           # Ventanas emergentes
│
├── core/                    # Lógica principal
│   ├── extractor.py         # Extraer audio con MoviePy
│   ├── transcriber.py       # Transcribir audio con Whisper
│   └── utils.py             # Utilidades (dividir audio con ffmpeg, etc.)
│
├── output/
│   └── transcripciones/     # Archivos de salida
│
└── venv/                    # Entorno virtual (ignorado en GitHub)
```

---

## ⚡ Ejecución rápida en Windows

Crea un archivo `iniciar.bat` en la raíz del proyecto con:

```bat
@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python app.py
pause
```

Doble clic en `iniciar.bat` → ¡la app se abrirá directo! 🎉

---

## ℹ️ Notas

- El aviso:
  ```
  FP16 is not supported on CPU; using FP32 instead
  ```
  es **normal** si no tienes GPU. La transcripción será más lenta, pero funciona.  

- Para forzar el idioma español, en `transcriber.py` asegúrate de usar:  
  ```python
  result = model.transcribe(audio_path, language="es", fp16=False)
  ```

---

## 📌 Futuras mejoras
- Unir todas las partes transcritas en un solo archivo.  
- Configurar la cantidad de fragmentos al dividir el audio.  
- Selección de modelo Whisper (`tiny`, `small`, `medium`, etc.) según tu equipo.  

---
