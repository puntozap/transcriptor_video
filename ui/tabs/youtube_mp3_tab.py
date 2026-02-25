import threading
import os
import json
import customtkinter as ctk

from core.youtube_downloader import descargar_audio_youtube
from ui import dialogs
from ui.shared import helpers

CONFIG_PATH = "credentials/youtube_download_config.json"

def _load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_config(data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_tab(parent, context):
    log = context["log"]
    limpiar_entry = context["limpiar_entry"]
    alerta_busy = context["alerta_busy"]
    stop_control = context["stop_control"]
    beep_fin = context["beep_fin"]
    abrir_descargas = context["abrir_descargas"]

    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    container.grid_columnconfigure(0, weight=1)
    container.grid_columnconfigure(1, weight=0)
    container.grid_rowconfigure(0, weight=1)

    yt_card = ctk.CTkFrame(container, corner_radius=12)
    yt_card.grid(row=0, column=0, sticky="nsew")
    yt_card.grid_columnconfigure(0, weight=1)

    lbl_yt_title = ctk.CTkLabel(
        yt_card,
        text="Extraer audio de YouTube (MP3)",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    lbl_yt_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))

    lbl_yt_hint = ctk.CTkLabel(
        yt_card,
        text="Pega el link y descarga el audio en MP3.",
        font=ctk.CTkFont(size=12),
        text_color="#9aa4b2",
    )
    lbl_yt_hint.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    yt_row = ctk.CTkFrame(yt_card, fg_color="transparent")
    yt_row.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
    yt_row.grid_columnconfigure(0, weight=1)

    yt_entry = ctk.CTkEntry(yt_row, placeholder_text="https://www.youtube.com/watch?v=...")
    yt_entry.grid(row=0, column=0, sticky="ew")

    btn_clear_yt = ctk.CTkButton(
        yt_row,
        text="Limpiar",
        width=90,
        height=28,
        command=lambda: limpiar_entry(yt_entry),
    )
    btn_clear_yt.grid(row=0, column=1, sticky="e", padx=(8, 0))

    yt_cookies_row = ctk.CTkFrame(yt_card, fg_color="transparent")
    yt_cookies_row.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
    yt_cookies_row.grid_columnconfigure(1, weight=1)
    yt_cookies_row.grid_columnconfigure(2, weight=0)

    lbl_cookies = ctk.CTkLabel(
        yt_cookies_row,
        text="Cookies .txt (recomendado):",
        font=ctk.CTkFont(size=12),
        text_color="#9aa4b2",
    )
    lbl_cookies.grid(row=0, column=0, sticky="w", padx=(0, 10))

    yt_cookies_entry = ctk.CTkEntry(
        yt_cookies_row,
        placeholder_text="Ruta a cookies.txt",
    )
    yt_cookies_entry.grid(row=0, column=1, sticky="ew")
    cfg = _load_config()
    default_cookies = cfg.get("cookies_source") or ""
    if default_cookies:
        yt_cookies_entry.insert(0, default_cookies)

    def _persist_cookies():
        data = _load_config()
        data["cookies_source"] = (yt_cookies_entry.get() or "").strip()
        _save_config(data)

    yt_cookies_entry.bind("<FocusOut>", lambda _e: _persist_cookies())
    yt_cookies_entry.bind("<Return>", lambda _e: _persist_cookies())

    def _select_cookies_file():
        f = dialogs.seleccionar_archivo(
            "Seleccionar cookies.txt",
            [("Cookies TXT", "*.txt"), ("Todos", "*.*")],
        )
        if f:
            yt_cookies_entry.delete(0, "end")
            yt_cookies_entry.insert(0, f)
            _persist_cookies()

    btn_cookies = ctk.CTkButton(
        yt_cookies_row,
        text="Seleccionar",
        width=110,
        height=28,
        command=_select_cookies_file,
    )
    btn_cookies.grid(row=0, column=2, sticky="e", padx=(8, 0))

    def descargar_mp3_youtube():
        url = yt_entry.get().strip()
        if not url:
            log("Pega un link de YouTube primero.")
            return
        if stop_control.is_busy():
            alerta_busy()
            return
        stop_control.clear_stop()
        stop_control.set_busy(True)
        log_seccion("YouTube MP3")
        log("Descargando audio de YouTube...")
        try:
            cookies_from_browser = (yt_cookies_entry.get() or "").strip() or None
            _persist_cookies()
            out_path = descargar_audio_youtube(url, cookies_from_browser=cookies_from_browser, log_fn=log)
            log(f"OK Audio MP3 guardado: {out_path}")
            log("Finalizado proceso de YouTube MP3.")
            log("Fin de la automatizacion.")
            beep_fin()
        except Exception as e:
            log(f"Error descargando MP3 de YouTube: {e}")
        finally:
            stop_control.set_busy(False)

    def iniciar_descarga_youtube():
        threading.Thread(target=descargar_mp3_youtube, daemon=True).start()

    btn_yt = ctk.CTkButton(
        yt_card,
        text="Descargar MP3",
        command=iniciar_descarga_youtube,
        height=46,
    )
    btn_yt.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 8))

    btn_yt_open = ctk.CTkButton(
        yt_card,
        text="Abrir Descargas YouTube",
        command=abrir_descargas,
        height=40,
    )
    btn_yt_open.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 16))

    log_card, _log_widget, log_local = helpers.create_log_panel(
        container,
        title="Actividad",
        height=220,
        mirror_fn=context.get("log_global"),
    )
    log_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

    def log_seccion(titulo):
        log_local("")
        log_local("========================================")
        log_local(f"=== {titulo}")
        log_local("========================================")

    log = log_local
    log(
        "Tip cookies.txt: abre Chrome en incognito, inicia sesion en YouTube, "
        "visita https://www.youtube.com/robots.txt en la misma pestaña, "
        "exporta cookies con 'Get cookies.txt' y selecciona el archivo."
    )

    return {}
