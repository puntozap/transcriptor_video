import os
import tempfile
import moviepy as mp

def extraer_audio(video_path: str, audio_path: str | None = None) -> str:
    """
    Extrae el audio de un video usando moviepy (FFmpeg por debajo).
    Devuelve la ruta del archivo WAV generado.
    """
    # Archivo temporal por defecto
    if audio_path is None:
        tmpdir = tempfile.gettempdir()
        audio_path = os.path.join(tmpdir, "temp_audio.wav")

    # Procesar
    clip = mp.VideoFileClip(video_path)
    if clip.audio is None:
        raise ValueError("El video no contiene pista de audio.")
    # 16-bit PCM WAV por compatibilidad con Whisper
    clip.audio.write_audiofile(audio_path, codec="pcm_s16le", fps=16000, logger=None)
    clip.close()

    if not os.path.exists(audio_path):
        raise RuntimeError("No se pudo generar el archivo de audio.")

    return audio_path
