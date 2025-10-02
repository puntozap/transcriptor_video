import os
import subprocess

def asegurar_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def nombre_salida_por_video(video_path: str, base_dir="output/transcripciones"):
    """
    Genera un nombre de archivo de salida basado en el nombre del video.
    """
    base = os.path.splitext(os.path.basename(video_path))[0]
    return os.path.join(base_dir, f"{base}.txt")

def dividir_audio_ffmpeg(audio_path: str, partes: int = 5, log_fn=None):
    """
    Divide un audio en N partes iguales usando ffmpeg.
    Devuelve una lista con las rutas de los archivos resultantes.
    log_fn: función opcional para escribir logs en la interfaz.
    """
    # Obtener duración del audio con ffprobe
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    duracion = float(result.stdout.strip())
    duracion_segmento = duracion / partes

    base, _ = os.path.splitext(audio_path)
    paths = []

    for i in range(partes):
        inicio = i * duracion_segmento
        out_path = f"{base}_parte{i+1}.wav"

        if log_fn:
            log_fn(f"✂️ Generando fragmento {i+1}/{partes}...")

        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-ss", str(inicio),
            "-t", str(duracion_segmento),
            out_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        paths.append(out_path)

        if log_fn:
            log_fn(f"✔ Fragmento {i+1}/{partes} listo: {out_path}")

    return paths

def limpiar_temp(path: str):
    """
    Borra un archivo temporal si existe.
    """
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"No se pudo borrar {path}: {e}")
