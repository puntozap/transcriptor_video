import os
import json
import threading
import time
import urllib.parse
import urllib.request
import shutil
import subprocess
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

from ui.shared.tab_shell import create_tab_shell
from ui.shared import helpers
from core.instagram_api import InstagramUploader
from core.ai_instagram import generar_descripcion_instagram
from core.instagram_auth import exchange_long_lived_token
from core.instagram_oauth import oauth_login_flow

CONFIG_PATH = "credentials/instagram_config.json"
IG_LOCAL_PORT = 4532
IG_TUNNEL_DIR = os.path.join("output", "ig_ngrok_tmp")
tunnel_state = {"http_proc": None, "ngrok_proc": None, "root": None}


def _stop_tunnel(log):
    http_proc = tunnel_state.get("http_proc")
    ngrok_proc = tunnel_state.get("ngrok_proc")
    for proc in (ngrok_proc, http_proc):
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
    tunnel_state["http_proc"] = None
    tunnel_state["ngrok_proc"] = None
    tunnel_state["root"] = None
    if log:
        log("IG: Tunnel cerrado.")


def _start_tunnel_for_dir(root_dir: str, log):
    if not shutil.which("ngrok"):
        log("IG: No se encontro ngrok en PATH.")
        return None
    try:
        os.makedirs(root_dir, exist_ok=True)
        http_proc = subprocess.Popen(
            ["python", "-m", "http.server", str(IG_LOCAL_PORT)],
            cwd=root_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ngrok_proc = subprocess.Popen(
            ["ngrok", "http", str(IG_LOCAL_PORT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        tunnel_state["http_proc"] = http_proc
        tunnel_state["ngrok_proc"] = ngrok_proc
        tunnel_state["root"] = root_dir
    except Exception as e:
        log(f"IG: Error iniciando tunnel: {e}")
        _stop_tunnel(log)
        return None

    public_url = None
    for _ in range(30):
        try:
            with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tunnels = data.get("tunnels") or []
            https_tunnel = next((t for t in tunnels if str(t.get("public_url", "")).startswith("https://")), None)
            if https_tunnel:
                public_url = https_tunnel.get("public_url")
                break
        except Exception:
            time.sleep(0.5)
            continue
        time.sleep(0.5)
    if not public_url:
        log("IG: No se pudo obtener URL publica de ngrok.")
        _stop_tunnel(log)
        return None
    log(f"IG: Tunnel listo: {public_url}")
    return public_url


def _add_files_via_tunnel(files: list[str], log) -> list[str]:
    if not files:
        return []
    for f in files:
        if not os.path.exists(f):
            log(f"IG: Archivo no encontrado: {f}")
            return []
    root = tunnel_state.get("root") or IG_TUNNEL_DIR
    if not tunnel_state.get("http_proc") or not tunnel_state.get("ngrok_proc"):
        log("IG: Iniciando tunnel local...")
        public = _start_tunnel_for_dir(root, log)
        if not public:
            return []
    else:
        public = _start_tunnel_for_dir(root, log) if tunnel_state.get("root") != root else None
        public = public or None
    if not public:
        # if already running, fetch current URL
        try:
            with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=2) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tunnels = data.get("tunnels") or []
            https_tunnel = next((t for t in tunnels if str(t.get("public_url", "")).startswith("https://")), None)
            public = https_tunnel.get("public_url") if https_tunnel else None
        except Exception:
            public = None
    if not public:
        log("IG: Tunnel activo no disponible.")
        return []

    urls = []
    for f in files:
        dest = os.path.join(root, os.path.basename(f))
        try:
            shutil.copy2(f, dest)
        except Exception as e:
            log(f"IG: No se pudo copiar archivo a tunnel: {e}")
            return []
        filename = os.path.basename(dest).replace(" ", "%20")
        urls.append(f"{public}/{filename}")
    return urls

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

def create_instagram_tab(parent, context):
    """
    Crea la pestaña de Instagram con subpestañas para Configuración y Subida.
    """
    # Layout base
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    # Shell con scroll
    container, scroll_body = create_tab_shell(parent, padx=10, pady=10)
    
    # Configurar layout para panel lateral de logs
    container.grid_columnconfigure(0, weight=1)
    container.grid_columnconfigure(1, weight=0)

    # Panel de Actividad (Log)
    log_card, _, log_local = helpers.create_log_panel(
        container,
        title="Actividad Instagram",
        height=0, # Altura automática
        mirror_fn=context.get("log"),
    )
    log_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
    
    # Actualizar el contexto para que las funciones usen este log local
    context["log"] = log_local
    
    # Tabview para sub-pestañas
    tabview = ctk.CTkTabview(scroll_body)
    tabview.pack(fill="both", expand=True, padx=5, pady=5)
    
    tab_upload = tabview.add("Subir Reel")
    tab_post = tabview.add("Post links")
    tab_story = tabview.add("Story video")
    tab_config = tabview.add("Configuracion")
    
    _setup_config_tab(tab_config, context)
    _setup_upload_tab(tab_upload, context)
    _setup_post_links_tab(tab_post, context)
    _setup_story_video_tab(tab_story, context)


def _setup_story_video_tab(parent, context):
    log = context.get("log", print)
    config = _load_config()

    ctk.CTkLabel(parent, text="Publicar Story (link)", font=("Arial", 16, "bold")).pack(pady=15)
    ctk.CTkLabel(
        parent,
        text="Links directos a MP4 o imagen (publicos). Si supera 60s, el video se recorta.",
        text_color="gray",
    ).pack(pady=(0, 10))

    ctk.CTkLabel(parent, text="URLs (una por linea):").pack(anchor="w", padx=20, pady=(6, 0))
    txt_urls = ctk.CTkTextbox(parent, height=120)
    txt_urls.pack(fill="x", padx=20, pady=(5, 10))
    btn_row = ctk.CTkFrame(parent, fg_color="transparent")
    btn_row.pack(fill="x", padx=20, pady=(0, 10))
    def _add_story_files():
        files = filedialog.askopenfilenames(filetypes=[("Media", "*.mp4;*.mov;*.m4v;*.webm;*.png;*.jpg;*.jpeg;*.webp")])
        if not files:
            return
        urls = _add_files_via_tunnel(list(files), log)
        if not urls:
            return
        current = txt_urls.get("1.0", "end").strip()
        new_text = ("\n".join(urls) if not current else current + "\n" + "\n".join(urls))
        txt_urls.delete("1.0", "end")
        txt_urls.insert("1.0", new_text)
        log("IG: URLs agregadas desde archivos locales.")
    ctk.CTkButton(btn_row, text="Agregar archivos", command=_add_story_files).pack(side="left")

    story_tag_row = ctk.CTkFrame(parent, fg_color="transparent")
    story_tag_row.pack(fill="x", padx=20, pady=(0, 8))
    ctk.CTkLabel(story_tag_row, text="Etiqueta @ (opcional):", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_tag = ctk.CTkEntry(story_tag_row, width=200, placeholder_text="usuario")
    entry_story_tag.pack(side="left", padx=(8, 8))
    if config.get("story_tag_username"):
        entry_story_tag.insert(0, config.get("story_tag_username"))
    ctk.CTkLabel(story_tag_row, text="x", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_x = ctk.CTkEntry(story_tag_row, width=60)
    entry_story_x.pack(side="left", padx=(6, 8))
    entry_story_x.insert(0, str(config.get("story_tag_x", 0.5)))
    ctk.CTkLabel(story_tag_row, text="y", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_y = ctk.CTkEntry(story_tag_row, width=60)
    entry_story_y.pack(side="left", padx=(6, 0))
    entry_story_y.insert(0, str(config.get("story_tag_y", 0.85)))

    def _build_story_tags():
        username = entry_story_tag.get().strip().lstrip("@")
        if not username:
            return None
        try:
            x = float(entry_story_x.get().strip().replace(",", "."))
        except Exception:
            x = 0.5
        try:
            y = float(entry_story_y.get().strip().replace(",", "."))
        except Exception:
            y = 0.85
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        data = _load_config()
        data["story_tag_username"] = username
        data["story_tag_x"] = x
        data["story_tag_y"] = y
        _save_config(data)
        return [{"username": username, "x": x, "y": y}]

    def _parse_urls():
        raw = txt_urls.get("1.0", "end").strip()
        if not raw:
            return []
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        return [l for l in lines if l.lower().startswith("http")]

    def _is_video_url(url: str) -> bool:
        low = url.lower()
        return low.endswith(".mp4") or low.endswith(".mov") or low.endswith(".m4v") or low.endswith(".webm")

    def _is_image_url(url: str) -> bool:
        low = url.lower()
        return low.endswith(".png") or low.endswith(".jpg") or low.endswith(".jpeg") or low.endswith(".webp")

    def publish_story():
        urls = _parse_urls()
        if not config.get("account_id") or not config.get("access_token"):
            log("Error: Faltan credenciales en la pestana Configuracion.")
            return
        if not urls:
            log("Error: Debes pegar al menos una URL valida.")
            return

        def _update_tokens(data: dict):
            fresh = _load_config()
            fresh["access_token"] = data.get("access_token", fresh.get("access_token"))
            if data.get("expires_at"):
                fresh["token_expires_at"] = data.get("expires_at")
            _save_config(fresh)

        def _run():
            uploader = InstagramUploader(
                config["access_token"],
                config["account_id"],
                app_id=config.get("app_id"),
                app_secret=config.get("app_secret"),
                token_expires_at=config.get("token_expires_at"),
                on_token_update=_update_tokens,
            )
            total = len(urls)
            for idx, media_url in enumerate(urls, start=1):
                is_video = _is_video_url(media_url)
                is_image = _is_image_url(media_url)
                if not (is_video or is_image):
                    log(f"❌ [{idx}/{total}] URL invalida (debe ser MP4 o imagen): {media_url}")
                    continue
                log(f"IG: Publicando story {idx}/{total}...")
                if is_video:
                    uploader.upload_story_video_auto(media_url, log_fn=log, user_tags=_build_story_tags())
                else:
                    uploader.upload_story_image(media_url, log_fn=log, user_tags=_build_story_tags())
            _stop_tunnel(log)

        threading.Thread(target=_run, daemon=True).start()

    ctk.CTkButton(parent, text="Publicar Story", command=publish_story, fg_color="#E1306C", hover_color="#C13584").pack(pady=(10, 20))

def _setup_config_tab(parent, context):
    log = context.get("log", print)
    config = _load_config()

    ctk.CTkLabel(parent, text="Credenciales Instagram Graph API", font=("Arial", 16, "bold")).pack(pady=(15, 5))
    ctk.CTkLabel(parent, text="Necesitas un Token de Usuario y el ID de tu cuenta de Instagram Business.", text_color="gray").pack(pady=(0, 15))

    ctk.CTkLabel(parent, text="Instagram Account ID:").pack(anchor="w", padx=20)
    entry_id = ctk.CTkEntry(parent, width=400, placeholder_text="Ej: 17841400000000000")
    entry_id.pack(anchor="w", padx=20, pady=(0, 10))
    entry_id.insert(0, config.get("account_id", ""))

    ctk.CTkLabel(parent, text="Access Token:").pack(anchor="w", padx=20)
    entry_token = ctk.CTkEntry(parent, width=400, placeholder_text="EAAG...")
    entry_token.pack(anchor="w", padx=20, pady=(0, 10))
    entry_token.insert(0, config.get("access_token", ""))

    ctk.CTkLabel(parent, text="Redirect URI:").pack(anchor="w", padx=20)
    entry_redirect = ctk.CTkEntry(parent, width=400, placeholder_text="http://127.0.0.1:8766/callback")
    entry_redirect.pack(anchor="w", padx=20, pady=(0, 10))
    entry_redirect.insert(0, config.get("redirect_uri", "http://127.0.0.1:8766/callback"))

    ctk.CTkLabel(parent, text="Scopes:").pack(anchor="w", padx=20)
    entry_scopes = ctk.CTkEntry(parent, width=400)
    entry_scopes.pack(anchor="w", padx=20, pady=(0, 10))
    entry_scopes.insert(0, config.get("scopes", "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement"))

    ctk.CTkLabel(parent, text="App ID (opcional):").pack(anchor="w", padx=20)
    entry_app_id = ctk.CTkEntry(parent, width=400, placeholder_text="App ID")
    entry_app_id.pack(anchor="w", padx=20, pady=(0, 10))
    entry_app_id.insert(0, config.get("app_id", ""))

    ctk.CTkLabel(parent, text="App Secret (opcional):").pack(anchor="w", padx=20)
    entry_app_secret = ctk.CTkEntry(parent, width=400, show="*", placeholder_text="App Secret")
    entry_app_secret.pack(anchor="w", padx=20, pady=(0, 10))
    entry_app_secret.insert(0, config.get("app_secret", ""))

    expires_at = config.get("token_expires_at")
    expires_txt = "Token: sin expiración registrada"
    if expires_at:
        try:
            expires_txt = "Token expira: " + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(expires_at)))
        except Exception:
            expires_txt = f"Token expira: {expires_at}"
    lbl_exp = ctk.CTkLabel(parent, text=expires_txt, text_color="gray")
    lbl_exp.pack(anchor="w", padx=20, pady=(0, 10))

    def save():
        data = {
            "account_id": entry_id.get().strip(),
            "access_token": entry_token.get().strip(),
            "app_id": entry_app_id.get().strip(),
            "app_secret": entry_app_secret.get().strip(),
            "token_expires_at": config.get("token_expires_at"),
            "redirect_uri": entry_redirect.get().strip(),
            "scopes": entry_scopes.get().strip(),
        }
        _save_config(data)
        log("✅ Configuración de Instagram guardada.")

    def renovar():
        try:
            data = exchange_long_lived_token(
                short_lived_token=entry_token.get().strip(),
                app_id=entry_app_id.get().strip(),
                app_secret=entry_app_secret.get().strip(),
            )
            new_token = data.get("access_token", "")
            entry_token.delete(0, "end")
            entry_token.insert(0, new_token)
            config["token_expires_at"] = data.get("expires_at")
            save()
            if data.get("expires_at"):
                lbl_exp.configure(
                    text="Token expira: "
                    + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(data["expires_at"])))
                )
            log("✅ Token renovado (long-lived).")
        except Exception as e:
            log(f"❌ Error renovando token: {e}")

    def conectar():
        def _run():
            try:
                redirect_uri = entry_redirect.get().strip()
                parsed = urllib.parse.urlparse(redirect_uri)
                if parsed.hostname in ("127.0.0.1", "localhost"):
                    listen_host = parsed.hostname
                    listen_port = parsed.port or 80
                else:
                    # Cuando usamos ngrok (https), el servidor local sigue escuchando en 127.0.0.1:8766
                    listen_host = "127.0.0.1"
                    listen_port = 8766
                data = oauth_login_flow(
                    app_id=entry_app_id.get().strip(),
                    app_secret=entry_app_secret.get().strip(),
                    redirect_uri=redirect_uri,
                    scopes=entry_scopes.get().strip(),
                    log_fn=log,
                    timeout_sec=600,
                    listen_host=listen_host,
                    listen_port=listen_port,
                )
                entry_token.delete(0, "end")
                entry_token.insert(0, data.get("access_token", ""))
                config["token_expires_at"] = data.get("expires_at")
                save()
                if data.get("expires_at"):
                    lbl_exp.configure(
                        text="Token expira: "
                        + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(data["expires_at"])))
                    )
                log("✅ OAuth completado. Token guardado.")
            except Exception as e:
                log(f"❌ Error OAuth: {e}")

        threading.Thread(target=_run, daemon=True).start()

    ctk.CTkButton(parent, text="Guardar Credenciales", command=save).pack(pady=(10, 6))
    ctk.CTkButton(parent, text="Conectar con Facebook (OAuth)", command=conectar).pack(pady=(0, 6))
    ctk.CTkButton(parent, text="Renovar token (60 días)", command=renovar).pack(pady=(0, 20))

def _setup_upload_tab(parent, context):
    log = context.get("log", print)
    config = _load_config()
    
    ctk.CTkLabel(parent, text="Publicar Reel", font=("Arial", 16, "bold")).pack(pady=15)

    # Selector de archivo
    frame_file = ctk.CTkFrame(parent, fg_color="transparent")
    frame_file.pack(fill="x", padx=20, pady=5)
    entry_file = ctk.CTkEntry(frame_file, placeholder_text="Selecciona un video vertical (.mp4)")
    entry_file.pack(side="left", fill="x", expand=True, padx=(0, 10))
    batch_state = {"paths": []}
    lbl_batch = ctk.CTkLabel(parent, text="Lote: (sin videos)", text_color="gray")
    lbl_batch.pack(anchor="w", padx=20, pady=(4, 0))
    
    def browse():
        f = filedialog.askopenfilename(filetypes=[("MP4 Video", "*.mp4")])
        if f:
            entry_file.delete(0, "end")
            entry_file.insert(0, f)
            # Auto-tunnel y URL publica para subir como Reel
            def _run_tunnel():
                urls = _add_files_via_tunnel([f], log)
                if not urls:
                    return
                entry_url.delete(0, "end")
                entry_url.insert(0, urls[0])
                log(f"IG: URL publica lista: {urls[0]}")
            threading.Thread(target=_run_tunnel, daemon=True).start()

    def browse_batch():
        files = filedialog.askopenfilenames(filetypes=[("MP4 Video", "*.mp4")])
        if files:
            batch_state["paths"] = list(files)
            lbl_batch.configure(text=f"Lote: {len(files)} video(s) seleccionado(s)")

    btns = ctk.CTkFrame(frame_file, fg_color="transparent")
    btns.pack(side="right")
    ctk.CTkButton(btns, text="Examinar", width=100, command=browse).pack(side="left", padx=(0, 8))
    ctk.CTkButton(btns, text="Lote", width=80, command=browse_batch).pack(side="left")

    ctk.CTkLabel(parent, text="URL publica del video (opcional):").pack(anchor="w", padx=20, pady=(8, 0))
    entry_url = ctk.CTkEntry(parent, placeholder_text="https://tu-dominio.com/videos/mi_reel.mp4")
    entry_url.pack(fill="x", padx=20, pady=(5, 10))
    ctk.CTkLabel(
        parent,
        text="Si usas URL, debe ser publica y directa al MP4 (sin redirects).",
        text_color="gray",
    ).pack(anchor="w", padx=20, pady=(0, 6))

    # Caption
    ctk.CTkLabel(parent, text="Descripción (Caption):").pack(anchor="w", padx=20, pady=(10, 0))
    txt_caption = ctk.CTkTextbox(parent, height=100)
    txt_caption.pack(fill="x", padx=20, pady=(5, 10))

    ai_row = ctk.CTkFrame(parent, fg_color="transparent")
    ai_row.pack(fill="x", padx=20, pady=(0, 6))
    ai_row.grid_columnconfigure(3, weight=1)

    ctk.CTkLabel(ai_row, text="Hashtags IA:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")
    entry_hashtags = ctk.CTkEntry(ai_row, width=80)
    entry_hashtags.insert(0, "8")
    entry_hashtags.grid(row=0, column=1, sticky="w", padx=(8, 12))

    ctk.CTkLabel(ai_row, text="Menciones (opcional):", font=ctk.CTkFont(size=12)).grid(row=0, column=2, sticky="w")
    entry_mentions = ctk.CTkEntry(ai_row)
    entry_mentions.grid(row=0, column=3, sticky="ew", padx=(8, 0))

    def _build_caption(ai_result: dict, extra_mentions: str) -> str:
        parts = []
        if ai_result.get("descripcion"):
            parts.append(ai_result["descripcion"])
        if ai_result.get("hashtags"):
            parts.append(ai_result["hashtags"])
        if ai_result.get("menciones"):
            parts.append(ai_result["menciones"])
        if extra_mentions:
            parts.append(extra_mentions)
        return "\n".join(p for p in parts if p)

    def _get_hashtags_count() -> int:
        raw = entry_hashtags.get().strip()
        try:
            value = int(raw)
        except Exception:
            value = 8
        return max(1, min(20, value))

    def generar_caption_ia():
        video_path = entry_file.get().strip()
        def _run():
            try:
                ai = generar_descripcion_instagram(
                    video_path,
                    hashtags=_get_hashtags_count(),
                    logs=log,
                )
                caption = _build_caption(ai, entry_mentions.get().strip())
                txt_caption.delete("1.0", "end")
                txt_caption.insert("1.0", caption)
                log("✅ Descripción IA generada.")
            except Exception as e:
                log(f"❌ Error IA: {e}")
        threading.Thread(target=_run, daemon=True).start()

    ctk.CTkButton(parent, text="✨ Generar descripción con IA", command=generar_caption_ia).pack(pady=(0, 10))

    chk_feed = ctk.CTkCheckBox(parent, text="Publicar también en el Feed")
    chk_feed.pack(anchor="w", padx=20, pady=5)
    chk_feed.select()

    chk_story = ctk.CTkCheckBox(parent, text="Publicar tambien en Stories")
    chk_story.pack(anchor="w", padx=20, pady=(0, 5))

    story_tag_row = ctk.CTkFrame(parent, fg_color="transparent")
    story_tag_row.pack(fill="x", padx=20, pady=(0, 8))
    ctk.CTkLabel(story_tag_row, text="Story tag @ (opcional):", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_tag = ctk.CTkEntry(story_tag_row, width=200, placeholder_text="usuario")
    entry_story_tag.pack(side="left", padx=(8, 8))
    if config.get("story_tag_username"):
        entry_story_tag.insert(0, config.get("story_tag_username"))
    ctk.CTkLabel(story_tag_row, text="x", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_x = ctk.CTkEntry(story_tag_row, width=60)
    entry_story_x.pack(side="left", padx=(6, 8))
    entry_story_x.insert(0, str(config.get("story_tag_x", 0.5)))
    ctk.CTkLabel(story_tag_row, text="y", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_y = ctk.CTkEntry(story_tag_row, width=60)
    entry_story_y.pack(side="left", padx=(6, 0))
    entry_story_y.insert(0, str(config.get("story_tag_y", 0.85)))

    def _build_story_tags():
        username = entry_story_tag.get().strip().lstrip("@")
        if not username:
            return None
        try:
            x = float(entry_story_x.get().strip().replace(",", "."))
        except Exception:
            x = 0.5
        try:
            y = float(entry_story_y.get().strip().replace(",", "."))
        except Exception:
            y = 0.85
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        data = _load_config()
        data["story_tag_username"] = username
        data["story_tag_x"] = x
        data["story_tag_y"] = y
        _save_config(data)
        return [{"username": username, "x": x, "y": y}]

    chunk_row = ctk.CTkFrame(parent, fg_color="transparent")
    chunk_row.pack(fill="x", padx=20, pady=(6, 0))
    ctk.CTkLabel(chunk_row, text="Chunk size (MB, opcional):", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_chunk = ctk.CTkEntry(chunk_row, width=80, placeholder_text="Ej: 4")
    entry_chunk.pack(side="left", padx=(8, 0))
    if config.get("ig_chunk_size_mb"):
        entry_chunk.insert(0, str(config.get("ig_chunk_size_mb")))

    def _get_chunk_size_mb():
        raw = entry_chunk.get().strip()
        if not raw:
            return None
        try:
            value = int(raw)
        except Exception:
            return None
        return max(1, value)

    def _persist_chunk_size(chunk_size_mb):
        if chunk_size_mb is None:
            return
        data = _load_config()
        data["ig_chunk_size_mb"] = chunk_size_mb
        _save_config(data)

    def process_upload():
        video_path = entry_file.get().strip()
        video_url = entry_url.get().strip()
        caption = txt_caption.get("1.0", "end").strip()
        share_feed = True #bool(chk_feed.get())
        share_story = bool(chk_story.get())
        chunk_size_mb = _get_chunk_size_mb()
        _persist_chunk_size(chunk_size_mb)
        config = _load_config()

        if not config.get("account_id") or not config.get("access_token"):
            log("Error: Faltan credenciales en la pestana Configuracion.")
            return
        if not video_url and (not video_path or not os.path.exists(video_path)):
            log("Error: Debes seleccionar un archivo o pegar una URL publica.")
            return


        def _update_tokens(data: dict):
            fresh = _load_config()
            fresh["access_token"] = data.get("access_token", fresh.get("access_token"))
            if data.get("expires_at"):
                fresh["token_expires_at"] = data.get("expires_at")
            _save_config(fresh)

        def _run():
            uploader = InstagramUploader(
                config["access_token"],
                config["account_id"],
                app_id=config.get("app_id"),
                app_secret=config.get("app_secret"),
                token_expires_at=config.get("token_expires_at"),
                on_token_update=_update_tokens,
            )
            if video_url:
                log("IG: Subiendo desde URL publica...")
                media_id = uploader.upload_reel(
                    video_url,
                    caption,
                    share_feed,
                    log_fn=log,
                )
                if share_story and media_id:
                    uploader.upload_story_video_auto(video_url, log_fn=log, user_tags=_build_story_tags())
            else:
                media_id = uploader.upload_reel_resumable(
                    video_path,
                    caption,
                    share_feed,
                    log_fn=log,
                    chunk_size_mb=chunk_size_mb,
                )
                if share_story:
                    log("IG: Story requiere URL publica. Omite Story o pega una URL.")
            # Cerrar tunnel si fue iniciado desde el selector
            _stop_tunnel(log)
        
        threading.Thread(target=_run, daemon=True).start()

    def process_batch():
        config = _load_config()
        share_feed = bool(chk_feed.get())
        chunk_size_mb = _get_chunk_size_mb()
        _persist_chunk_size(chunk_size_mb)
        if not config.get("account_id") or not config.get("access_token"):
            log("Error: Faltan credenciales en la pestana Configuracion.")
            return
        files = batch_state.get("paths") or []
        if not files:
            log("❌ No hay videos en el lote.")
            return

        def _update_tokens(data: dict):
            fresh = _load_config()
            fresh["access_token"] = data.get("access_token", fresh.get("access_token"))
            if data.get("expires_at"):
                fresh["token_expires_at"] = data.get("expires_at")
            _save_config(fresh)

        def _run():
            uploader = InstagramUploader(
                config["access_token"],
                config["account_id"],
                app_id=config.get("app_id"),
                app_secret=config.get("app_secret"),
                token_expires_at=config.get("token_expires_at"),
                on_token_update=_update_tokens,
            )
            total = len(files)
            for idx, path in enumerate(files, start=1):
                if not os.path.exists(path):
                    log(f"❌ [{idx}/{total}] Archivo no encontrado: {path}")
                    continue
                try:
                    log(f"[{idx}/{total}] Generando descripción IA...")
                    ai = generar_descripcion_instagram(
                        path,
                        hashtags=_get_hashtags_count(),
                        logs=log,
                    )
                    caption = _build_caption(ai, entry_mentions.get().strip())
                except Exception as e:
                    log(f"❌ [{idx}/{total}] Error IA: {e}")
                    continue
                log(f"[{idx}/{total}] Subiendo a Instagram...")
                uploader.upload_reel_resumable(
                    path,
                    caption,
                    share_feed,
                    log_fn=log,
                    chunk_size_mb=chunk_size_mb,
                )
            log("✅ Lote finalizado.")

        threading.Thread(target=_run, daemon=True).start()

    ctk.CTkButton(parent, text="🚀 Publicar en Instagram", command=process_upload, fg_color="#E1306C", hover_color="#C13584").pack(pady=(10, 8))
    ctk.CTkButton(parent, text="📦 Subir lote con IA", command=process_batch).pack(pady=(0, 20))


def _setup_post_links_tab(parent, context):
    log = context.get("log", print)
    config = _load_config()

    ctk.CTkLabel(parent, text="Publicar Post (links)", font=("Arial", 16, "bold")).pack(pady=15)
    ctk.CTkLabel(
        parent,
        text="Pega una URL por linea. 1 URL = post simple. 2+ URLs = carousel (max 10).",
        text_color="gray",
    ).pack(pady=(0, 10))

    txt_urls = ctk.CTkTextbox(parent, height=160)
    txt_urls.pack(fill="x", padx=20, pady=(0, 10))
    btn_row = ctk.CTkFrame(parent, fg_color="transparent")
    btn_row.pack(fill="x", padx=20, pady=(0, 10))
    def _add_post_files():
        files = filedialog.askopenfilenames(filetypes=[("Media", "*.mp4;*.mov;*.m4v;*.webm;*.png;*.jpg;*.jpeg;*.webp")])
        if not files:
            return
        urls = _add_files_via_tunnel(list(files), log)
        if not urls:
            return
        current = txt_urls.get("1.0", "end").strip()
        new_text = ("\n".join(urls) if not current else current + "\n" + "\n".join(urls))
        txt_urls.delete("1.0", "end")
        txt_urls.insert("1.0", new_text)
        log("IG: URLs agregadas desde archivos locales.")
    ctk.CTkButton(btn_row, text="Agregar archivos", command=_add_post_files).pack(side="left")

    ctk.CTkLabel(parent, text="Descripcion (Caption):").pack(anchor="w", padx=20, pady=(10, 0))
    txt_caption = ctk.CTkTextbox(parent, height=100)
    txt_caption.pack(fill="x", padx=20, pady=(5, 10))

    def _parse_urls():
        raw = txt_urls.get("1.0", "end").strip()
        if not raw:
            return []
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        urls = [u for u in lines if u.lower().startswith("http")]
        return urls

    chk_story = ctk.CTkCheckBox(parent, text="Publicar tambien en Stories")
    chk_story.pack(anchor="w", padx=20, pady=(0, 8))

    story_tag_row = ctk.CTkFrame(parent, fg_color="transparent")
    story_tag_row.pack(fill="x", padx=20, pady=(0, 8))
    ctk.CTkLabel(story_tag_row, text="Story tag @ (opcional):", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_tag = ctk.CTkEntry(story_tag_row, width=200, placeholder_text="usuario")
    entry_story_tag.pack(side="left", padx=(8, 8))
    if config.get("story_tag_username"):
        entry_story_tag.insert(0, config.get("story_tag_username"))
    ctk.CTkLabel(story_tag_row, text="x", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_x = ctk.CTkEntry(story_tag_row, width=60)
    entry_story_x.pack(side="left", padx=(6, 8))
    entry_story_x.insert(0, str(config.get("story_tag_x", 0.5)))
    ctk.CTkLabel(story_tag_row, text="y", font=ctk.CTkFont(size=12)).pack(side="left")
    entry_story_y = ctk.CTkEntry(story_tag_row, width=60)
    entry_story_y.pack(side="left", padx=(6, 0))
    entry_story_y.insert(0, str(config.get("story_tag_y", 0.85)))

    def _build_story_tags():
        username = entry_story_tag.get().strip().lstrip("@")
        if not username:
            return None
        try:
            x = float(entry_story_x.get().strip().replace(",", "."))
        except Exception:
            x = 0.5
        try:
            y = float(entry_story_y.get().strip().replace(",", "."))
        except Exception:
            y = 0.85
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        data = _load_config()
        data["story_tag_username"] = username
        data["story_tag_x"] = x
        data["story_tag_y"] = y
        _save_config(data)
        return [{"username": username, "x": x, "y": y}]

    def _is_video_url(url: str) -> bool:
        low = url.lower()
        return low.endswith(".mp4") or low.endswith(".mov") or low.endswith(".m4v") or low.endswith(".webm")

    def publish_post():
        urls = _parse_urls()
        caption = txt_caption.get("1.0", "end").strip()
        if not config.get("account_id") or not config.get("access_token"):
            log("Error: Faltan credenciales en la pestana Configuracion.")
            return
        if not urls:
            log("Error: Debes pegar al menos una URL valida.")
            return

        def _update_tokens(data: dict):
            fresh = _load_config()
            fresh["access_token"] = data.get("access_token", fresh.get("access_token"))
            if data.get("expires_at"):
                fresh["token_expires_at"] = data.get("expires_at")
            _save_config(fresh)

        def _run():
            uploader = InstagramUploader(
                config["access_token"],
                config["account_id"],
                app_id=config.get("app_id"),
                app_secret=config.get("app_secret"),
                token_expires_at=config.get("token_expires_at"),
                on_token_update=_update_tokens,
            )
            if len(urls) == 1:
                log("IG: Publicando imagen (post simple)...")
                media_id = uploader.upload_image_post(urls[0], caption, log_fn=log)
                if chk_story.get() and media_id:
                    if _is_video_url(urls[0]):
                        uploader.upload_story_video_auto(urls[0], log_fn=log, user_tags=_build_story_tags())
                    else:
                        uploader.upload_story_image(urls[0], log_fn=log, user_tags=_build_story_tags())
            else:
                log(f"IG: Publicando carousel ({len(urls)} items)...")
                media_id = uploader.upload_carousel_from_urls(urls, caption, log_fn=log)
                if chk_story.get() and media_id:
                    first = urls[0]
                    if _is_video_url(first):
                        uploader.upload_story_video_auto(first, log_fn=log, user_tags=_build_story_tags())
                    else:
                        uploader.upload_story_image(first, log_fn=log, user_tags=_build_story_tags())
            _stop_tunnel(log)

        threading.Thread(target=_run, daemon=True).start()

    ctk.CTkButton(parent, text="Publicar Post", command=publish_post, fg_color="#E1306C", hover_color="#C13584").pack(pady=(6, 20))
