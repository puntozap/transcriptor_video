from __future__ import annotations

import os
import re
from typing import Optional, Tuple

from core.extractor import extraer_audio
from core.transcriber import transcribir, transcribir_srt
from core.utils import output_base_dir, output_subtitulados_dir, nombre_base_principal

MAX_TRANSCRIPTION_CHARS = 9000
DEFAULT_SRT_MODEL = "base"


def obtener_transcripcion_para_video(
    video_path: str,
    idioma: str = "es",
    logs=None,
    max_chars: int = MAX_TRANSCRIPTION_CHARS,
) -> str:
    srt_path = _buscar_srt_existente(video_path, logs=logs)
    if srt_path:
        texto = _extraer_texto_srt(srt_path)
        if not texto:
            if logs:
                logs("SRT encontrado pero sin texto util. Reintentando con transcripcion...")
        else:
            if logs:
                logs(f"Usando SRT existente para IA: {srt_path}")
            if len(texto) > max_chars:
                if logs:
                    logs(f"Texto truncado a {max_chars} caracteres para IA.")
                texto = texto[:max_chars]
            return texto

    if logs:
        logs("Transcribiendo video para IA...")
    texto = transcribir(video_path, idioma=idioma, model_size="small")
    if not texto:
        raise RuntimeError("La transcripcion no devolvio texto valido.")
    if len(texto) > max_chars:
        if logs:
            logs(f"Transcripcion truncada a {max_chars} caracteres.")
        texto = texto[:max_chars]
    return texto


def _extraer_texto_srt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
    except Exception:
        return ""
    data = data.replace("\r\n", "\n")
    lines = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue
        line = re.sub(r"\{\\.*?\}", "", line)
        lines.append(line)
    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _buscar_srt_existente(video_path: str, logs=None) -> Optional[str]:
    base = nombre_base_principal(video_path)

    vid_dir = os.path.dirname(video_path)
    direct_srt = os.path.join(vid_dir, f"{base}.srt")
    if os.path.exists(direct_srt) and os.path.getsize(direct_srt) > 0:
        return direct_srt

    subs_dir = output_subtitulados_dir(video_path)
    if not os.path.isdir(subs_dir):
        return None

    candidates: list[str] = []
    for name in os.listdir(subs_dir):
        if not name.lower().endswith(".srt"):
            continue
        path = os.path.join(subs_dir, name)
        if not os.path.isfile(path):
            continue
        if os.path.getsize(path) == 0:
            continue
        candidates.append(path)

    if not candidates:
        return None

    exact = []
    for path in candidates:
        if nombre_base_principal(path) == base:
            exact.append(path)
    if exact:
        exact.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return exact[0]

    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    if logs:
        logs("SRT existente encontrado pero no coincide con el nombre base. Usando el mas reciente.")
    return candidates[0]


def extraer_audio_y_subtitulos(
    video_path: str,
    idioma: str,
    logs=None,
    model_size: str = DEFAULT_SRT_MODEL,
) -> Tuple[str, Optional[str]]:
    base_dir = output_base_dir(video_path)
    audio_dir = os.path.join(base_dir, "audios")
    os.makedirs(audio_dir, exist_ok=True)
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    safe_name = re.sub(r"[<>:\"/\\|?*]", "_", video_name)
    audio_name = f"{safe_name}_whatsapp_audio.mp3"
    audio_path = os.path.join(audio_dir, audio_name)
    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
        if logs:
            logs(f"Usando audio existente para subtítulos: {audio_path}")
    else:
        extraer_audio(video_path, audio_path, log_fn=logs)

    subs_dir = output_subtitulados_dir(video_path)
    os.makedirs(subs_dir, exist_ok=True)
    srt_path = None
    try:
        srt_path = transcribir_srt(
            audio_path,
            subs_dir,
            idioma=idioma,
            model_size=model_size,
        )
        if logs:
            logs(f"SRT generado: {srt_path}")
    except Exception as exc:
        if logs:
            logs(f"Advertencia: no se pudo generar el SRT ({exc})")
    return audio_path, srt_path
