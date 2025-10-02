
````markdown
# 🎬 Transcriptor de Video a Texto (con Whisper + Tkinter)

Este proyecto permite **extraer el audio de un video**, dividirlo en partes, y **transcribirlo a texto en español** usando el modelo Whisper de OpenAI.  
Incluye una interfaz gráfica de escritorio simple hecha con **Tkinter**.

---

## 🚀 Requisitos

- **Python** 3.11+ (funciona también en 3.13)  
- **FFmpeg** instalado y agregado al PATH  
- **Git** (opcional, si deseas clonar desde GitHub)

---

## 📥 Instalación paso a paso

1. **Clonar o copiar el proyecto**

   ```powershell
   git clone https://github.com/tuusuario/transcriptor_video.git
   cd transcriptor_video
````

O copia manualmente la carpeta `transcriptor_video` en tu PC.

---

2. **Crear el entorno virtual**

   ```powershell
   python -m venv venv
   ```

   Activar el entorno:

   ```powershell
   .\venv\Scripts\activate
   ```

   (Si ves `(venv)` al inicio de la línea de comandos, está bien activado).

---

3. **Instalar dependencias**

   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   El archivo `requirements.txt` ya contiene todas las librerías necesarias:

   * `moviepy` (extracción de audio de videos)
   * `openai-whisper` (transcripción)
   * `torch` (backend de Whisper)
   * `tqdm`, `numpy`, `pillow`, etc.

---

4. **Verificar FFmpeg**

   ```powershell
   ffmpeg -version
   ```

   Si no lo reconoce:

   ```powershell
   winget install ffmpeg
   ```

   o bien con Chocolatey:

   ```powershell
   choco install ffmpeg -y
   ```

---

## ▶️ Uso

Ejecutar la aplicación:

```powershell
python app.py
```

1. Aparecerá una ventana de Tkinter.
2. Selecciona un video en tu PC.
3. El sistema:

   * Extraerá el audio.
   * Lo dividirá automáticamente en **5 fragmentos**.
   * Transcribirá cada parte en **español**.
   * Guardará los resultados en:

     ```
     output/transcripciones/tu_video_parte1.txt
     output/transcripciones/tu_video_parte2.txt
     ...
     ```

---

## 📂 Estructura del proyecto

```
transcriptor_video/
│── app.py                  # Punto de entrada (inicia la interfaz gráfica)
│── requirements.txt         # Dependencias
│
├── ui/                      # Interfaz gráfica
│   ├── main_window.py       # Ventana principal (Tkinter)
│   └── dialogs.py           # Ventanas emergentes (selección de archivo, mensajes)
│
├── core/                    # Lógica principal
│   ├── extractor.py         # Extraer audio desde un video (MoviePy)
│   ├── transcriber.py       # Transcribir audio con Whisper
│   └── utils.py             # Utilidades (dividir audio con ffmpeg, nombres de archivo, etc.)
│
├── output/
│   └── transcripciones/     # Carpeta donde se guardan las transcripciones
│
└── venv/                    # Entorno virtual (no se sube a GitHub)
```

---

## ⚡ Ejecución rápida con `.bat`

Crea un archivo `iniciar.bat` en la raíz del proyecto con:

```bat
@echo off
cd /d %~dp0
call venv\Scripts\activate.bat
python app.py
pause
```

Haz doble clic en `iniciar.bat` y la app se abrirá directamente.

---

## ℹ️ Notas

* El aviso `FP16 is not supported on CPU; using FP32 instead` es normal si no usas GPU. Solo significa que será más **lento** pero **funcionará bien**.
* Si el texto sale raro o en otro idioma, asegúrate de que en `transcriber.py` se esté usando:

  ```python
  result = model.transcribe(audio_path, language="es", fp16=False)
  ```

---

## 📌 Futuras mejoras

* Opción de **unir todas las partes transcritas en un solo archivo**.
* Elegir cantidad de fragmentos para dividir el audio.
* Selección de modelo Whisper (`tiny`, `small`, `medium`) según la capacidad del equipo.

---

```
