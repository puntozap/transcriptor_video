import threading
import whisper

# Carga perezosa del modelo
_model = None
_lock = threading.Lock()

def _get_model(model_size: str = "small"):  # recomiendo tiny o small en CPU
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                _model = whisper.load_model(model_size)
    return _model

def transcribir(audio_path: str, idioma: str = "es") -> str:
    """
    Transcribe un archivo de audio a texto en un idioma dado.
    Forzado a FP32 en CPU.
    """
    model = _get_model("small")  # cambia tiny ↔ small si quieres más precisión
    kwargs = {"fp16": False}    # 👈 evita el aviso y usa FP32 seguro
    if idioma:
        kwargs["language"] = idioma

    result = model.transcribe(audio_path, **kwargs)
    return result.get("text", "").strip()
