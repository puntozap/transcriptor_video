import os
import sys
import subprocess
import time
import shutil
import yt_dlp
from yt_dlp.utils import DownloadError
from core import stop_control
from core.utils import output_base_dir

def _actualizar_yt_dlp(log_fn=None):
    if log_fn:
        log_fn("Actualizando yt-dlp...")
    cmd = [sys.executable, "-m", "yt_dlp", "-U"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _descargar_youtube(
    url: str,
    opciones: dict,
    output_dir: str,
    retry_update: bool,
    retry_android: bool,
    retry_no_cookies: bool,
    retry_best: bool,
    player_client: str | None,
    cookies_from_browser: str | None,
    log_fn=None
):
    if log_fn:
        state = {"last_percent": -1, "last_log_ts": 0.0}

        def _format_bytes(num):
            try:
                num = float(num)
            except Exception:
                return "?"
            for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
                if num < 1024.0:
                    return f"{num:.2f}{unit}"
                num /= 1024.0
            return f"{num:.2f}PiB"

        def _progress_hook(d):
            if stop_control.should_stop():
                raise DownloadError("Stop requested")
            status = d.get("status")
            if status == "finished":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                total_txt = _format_bytes(total) if total else "?"
                log_fn(f"[download] 100% of {total_txt} in 00:00:00")
                return
            if status != "downloading":
                return
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes") or 0
            if not total:
                return
            percent = int((downloaded / total) * 100)
            now = time.time()
            if percent == state["last_percent"] and (now - state["last_log_ts"]) < 1.0:
                return
            state["last_percent"] = percent
            state["last_log_ts"] = now
            speed = d.get("speed")
            eta = d.get("eta")
            total_txt = _format_bytes(total)
            speed_txt = _format_bytes(speed) + "/s" if speed else "?"
            eta_txt = time.strftime("%H:%M:%S", time.gmtime(eta)) if isinstance(eta, (int, float)) else "?"
            log_fn(f"[download] {percent}% of {total_txt} at {speed_txt}, ETA {eta_txt}")

        opciones["progress_hooks"] = [_progress_hook]

    if player_client:
        opciones["extractor_args"] = {"youtube": {"player_client": [player_client]}}
    cookies_file = None
    if cookies_from_browser:
        if _is_cookie_file(cookies_from_browser):
            cookies_file = cookies_from_browser
            opciones["cookiefile"] = cookies_from_browser
        else:
            opciones["cookiesfrombrowser"] = _parse_cookies_from_browser(cookies_from_browser)

    try:
        if stop_control.should_stop():
            raise DownloadError("Stop requested")
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            out_path = ydl.prepare_filename(info)
            try:
                if not out_path or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                    raise DownloadError("The downloaded file is empty")
            except DownloadError:
                raise
            except Exception:
                pass
            return out_path
    except DownloadError as e:
        msg = str(e)
        if ("downloaded file is empty" in msg.lower() or "file is empty" in msg.lower()) and retry_update:
            if log_fn:
                log_fn("Archivo descargado vacio. Actualizando yt-dlp y reintentando...")
            _actualizar_yt_dlp(log_fn=log_fn)
            return _descargar_youtube(
                url,
                opciones,
                output_dir=output_dir,
                retry_update=False,
                retry_android=retry_android,
                retry_no_cookies=retry_no_cookies,
                retry_best=retry_best,
                player_client=player_client,
                cookies_from_browser=cookies_from_browser,
                log_fn=log_fn
            )
        if retry_no_cookies and cookies_from_browser and ("DPAPI" in msg or "Failed to decrypt" in msg):
            if log_fn:
                log_fn("Error de cookies del navegador. Reintentando sin cookies...")
            opciones_retry = dict(opciones)
            opciones_retry.pop("cookiefile", None)
            opciones_retry.pop("cookiesfrombrowser", None)
            return _descargar_youtube(
                url,
                opciones_retry,
                output_dir=output_dir,
                retry_update=retry_update,
                retry_android=retry_android,
                retry_no_cookies=False,
                retry_best=retry_best,
                player_client=player_client,
                cookies_from_browser=None,
                log_fn=log_fn
            )
        if retry_best and ("Requested format is not available" in msg or "format is not available" in msg):
            if log_fn:
                log_fn("Formato no disponible. Reintentando con 'best'...")
            opciones_retry = dict(opciones)
            opciones_retry["format"] = "bestvideo*+bestaudio/best"
            return _descargar_youtube(
                url,
                opciones_retry,
                output_dir=output_dir,
                retry_update=retry_update,
                retry_android=retry_android,
                retry_no_cookies=retry_no_cookies,
                retry_best=False,
                player_client=player_client,
                cookies_from_browser=cookies_from_browser,
                log_fn=log_fn
            )
        is_antibot = ("Sign in to confirm you're not a bot" in msg) or ("not a bot" in msg) or ("confirm you\u2019re not a bot" in msg)
        if is_antibot and retry_android and (player_client or "") != "android":
            if log_fn:
                log_fn("Reintentando con cliente Android (posible bypass anti-bot)...")
            return _descargar_youtube(
                url,
                opciones,
                output_dir=output_dir,
                retry_update=retry_update,
                retry_android=False,
                retry_no_cookies=retry_no_cookies,
                retry_best=retry_best,
                player_client="android",
                cookies_from_browser=cookies_from_browser,
                log_fn=log_fn
            )
        if is_antibot:
            extra = ""
            if cookies_file:
                extra = " Verifica que el cookies.txt sea reciente y provenga de youtube.com."
            raise DownloadError(
                "YouTube esta bloqueando la descarga (verificacion anti-bot). "
                "Solucion: pasar cookies del navegador (por ejemplo: edge o chrome) o un cookies.txt valido."
                + extra
            )
        if retry_update and ("403" in msg or "HTTP Error 403" in msg):
            _actualizar_yt_dlp(log_fn=log_fn)
            return _descargar_youtube(
                url,
                opciones,
                output_dir=output_dir,
                retry_update=False,
                retry_android=retry_android,
                retry_no_cookies=retry_no_cookies,
                retry_best=retry_best,
                player_client=player_client,
                cookies_from_browser=cookies_from_browser,
                log_fn=log_fn
            )
        if retry_android and ("403" in msg or "HTTP Error 403" in msg):
            if log_fn:
                log_fn("Reintentando con cliente Android...")
            return _descargar_youtube(
                url,
                opciones,
                output_dir=output_dir,
                retry_update=False,
                retry_android=False,
                retry_no_cookies=retry_no_cookies,
                retry_best=retry_best,
                player_client="android",
                cookies_from_browser=cookies_from_browser,
                log_fn=log_fn
            )
        raise

def _parse_cookies_from_browser(spec: str):
    """
    Convierte un string tipo "chrome:Default" a la tupla esperada por yt-dlp.
    Formato: browser[:profile[:keyring[:container]]]
    """
    if not isinstance(spec, str):
        return spec
    raw = spec.strip()
    if not raw:
        return None
    parts = [p.strip() for p in raw.split(":", 3)]
    parts = [p for p in parts if p != ""]
    if not parts:
        return None
    return tuple(parts)

def _is_cookie_file(value: str) -> bool:
    if not isinstance(value, str):
        return False
    path = value.strip().strip('"')
    if not path:
        return False
    if os.path.isfile(path):
        return True
    lower = path.lower()
    return lower.endswith(".txt") and ("cookies" in lower)

def descargar_audio_youtube(
    url: str,
    output_dir: str = os.path.join("output", "_downloads_tmp"),
    retry_update: bool = True,
    retry_android: bool = True,
    player_client: str | None = None,
    cookies_from_browser: str | None = None,
    log_fn=None
) -> str:
    """
    Descarga el audio de un video de YouTube en formato MP3.
    Devuelve la ruta al archivo descargado.
    """
    _actualizar_yt_dlp(log_fn=log_fn)
    os.makedirs(output_dir, exist_ok=True)

    # Plantilla de salida (sin espacios raros en el nombre del archivo)
    output_path = os.path.join(output_dir, "%(title).20s", "%(title).20s.%(ext)s")

    opciones = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    archivo_salida = _descargar_youtube(
        url,
        opciones,
        output_dir=output_dir,
        retry_update=retry_update,
        retry_android=retry_android,
        retry_no_cookies=True,
        retry_best=False,
        player_client=player_client,
        cookies_from_browser=cookies_from_browser,
        log_fn=log_fn
    )
    archivo_mp3 = os.path.splitext(archivo_salida)[0] + ".mp3"
    base_dir = output_base_dir(archivo_mp3)
    final_dir = os.path.join(base_dir, "download")
    os.makedirs(final_dir, exist_ok=True)
    final_path = os.path.join(final_dir, os.path.basename(archivo_mp3))
    try:
        shutil.move(archivo_mp3, final_path)
    except Exception:
        final_path = archivo_mp3
    return final_path

def descargar_video_youtube_mp4(
    url: str,
    output_dir: str = os.path.join("output", "_downloads_tmp"),
    retry_update: bool = True,
    retry_android: bool = True,
    player_client: str | None = None,
    cookies_from_browser: str | None = None,
    log_fn=None
) -> str:
    """
    Descarga un video de YouTube en MP4.
    Devuelve la ruta al archivo descargado.
    """
    _actualizar_yt_dlp(log_fn=log_fn)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "%(title).20s", "%(title).20s.%(ext)s")

    opciones = {
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": output_path,
        "noplaylist": True,
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}
        ],
    }

    archivo_salida = _descargar_youtube(
        url,
        opciones,
        output_dir=output_dir,
        retry_update=retry_update,
        retry_android=retry_android,
        retry_no_cookies=True,
        retry_best=True,
        player_client=player_client,
        cookies_from_browser=cookies_from_browser,
        log_fn=log_fn
    )
    base, _ext = os.path.splitext(archivo_salida)
    archivo_mp4 = base + ".mp4"
    base_dir = output_base_dir(archivo_mp4)
    final_dir = os.path.join(base_dir, "download")
    os.makedirs(final_dir, exist_ok=True)
    final_path = os.path.join(final_dir, os.path.basename(archivo_mp4))
    try:
        shutil.move(archivo_mp4, final_path)
    except Exception:
        final_path = archivo_mp4
    return final_path

