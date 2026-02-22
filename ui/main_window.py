import os
import tkinter as tk
import customtkinter as ctk
import winsound
from core.drive_config import get_drive_folder_id
from ui.shared import helpers
from ui.shared.state import create_state
from ui.shared.preview import create_subtitle_preview
from core.workflow import generar_visualizador_solo
from ui.tabs import (
    actividad_tab,
    audio_tab,
    cortar_visualizador_tab,
    corte_individual_tab,
    overlay_imagenes_tab,
    musica_fondo_tab,
    corte_tab,
    corte_zoom_tab,
    corte_visualizer_tab,
    drive_config_tab,
    ia_clips_tab,
    ia_tiktok_tab,
    pegar_visualizador_tab,
    srt_tab,
    subtitular_tab,
    whatsapp_tab,
    youtube_mp3_tab,
    youtube_mp4_tab,
    youtube_upload_tab,
    youtube_analytics_tab,
    instagram_tab,
    image_creator_tab,
)


def iniciar_app(procesar_video_fn, root=None):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    ventana = root or ctk.CTk()
    if root is not None:
        try:
            for child in ventana.winfo_children():
                child.destroy()
        except Exception:
            pass
    ventana.title("Transcriptor de Video")
    ventana.geometry("980x680")
    ventana.minsize(820, 600)

    root = ctk.CTkFrame(master=ventana, corner_radius=14)
    root.pack(fill="both", expand=True, padx=24, pady=24)
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)

    shared_state = create_state()
    log_state = {"widget": None}
    estado = shared_state["estado"]
    rango = shared_state["rango"]
    rango_ind = shared_state["rango_ind"]
    srt_state = shared_state["srt_state"]
    sub_state = shared_state["sub_state"]
    ai_state = shared_state["ai_state"]
    youtube_state = shared_state["youtube_state"]
    whatsapp_state = shared_state["whatsapp_state"]
    drive_state = shared_state["drive_state"]
    stop_control = shared_state["stop_control"]
    folder_initial = get_drive_folder_id() or drive_state.get("folder_id", "")
    drive_folder_var = tk.StringVar(value=folder_initial.strip())
    drive_state["folder_id"] = drive_folder_var.get().strip()

    def _sync_drive_folder(*_):
        drive_state["folder_id"] = drive_folder_var.get().strip()

    drive_folder_var.trace_add("write", _sync_drive_folder)

    def log(msg):
        helpers.log_to_widget(log_state["widget"], msg)

    def beep_fin():
        try:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        except Exception:
            pass

    def alerta_busy():
        helpers.alerta_busy(ventana)

    def renombrar_si_largo(path: str):
        return helpers.renombrar_si_largo(path, log)

    def log_seccion(titulo):
        helpers.log_seccion(log, tabs, titulo)

    def limpiar_entry(entry):
        helpers.limpiar_entry(entry)

    abrir_transcripciones = helpers.abrir_transcripciones
    abrir_subtitulos = helpers.abrir_subtitulos
    abrir_videos = helpers.abrir_videos
    abrir_audios = helpers.abrir_audios
    abrir_descargas = helpers.abrir_descargas

    def eliminar_audios(log_fn=None):
        output_root = os.path.abspath("output")
        if not os.path.exists(output_root):
            return
        count = 0
        for root_dir, _dirs, files in os.walk(output_root):
            if os.path.basename(root_dir).lower() != "audios":
                continue
            for f in files:
                if f.lower().endswith((".mp3", ".wav", ".webm", ".mp4")):
                    try:
                        os.remove(os.path.join(root_dir, f))
                        count += 1
                    except Exception as e:
                        if log_fn:
                            log_fn(f"No se pudo borrar {f}: {e}")
        if log_fn:
            log_fn(f"{count} audios eliminados de output/")

    header = ctk.CTkFrame(root, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
    header.grid_columnconfigure(0, weight=1)

    title = ctk.CTkLabel(
        header,
        text="Transcriptor de Video",
        font=ctk.CTkFont(size=26, weight="bold")
    )
    title.grid(row=0, column=0, sticky="w")

    subtitle = ctk.CTkLabel(
        header,
        text="Divide por minutos y marca el rango con sliders.",
        font=ctk.CTkFont(size=13)
    )
    subtitle.grid(row=1, column=0, sticky="w", pady=(2, 0))

    tabs = ctk.CTkTabview(root, corner_radius=12)
    tabs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(6, 10))
    tabs.add("Corte")
    tabs.add("Cortar visualizador")
    tabs.add("Subtitulos")
    tabs.add("IA generadores")
    tabs.add("Descargas")
    tabs.add("Creador de Imagenes")
    tabs.add("Drive")
    tabs.add("YouTube")
    tabs.add("Analítica")
    tabs.add("Instagram")
    tabs.add("WhatsApp")
    tabs.add("Actividad")

    tab_corte_main = tabs.tab("Corte")
    tab_cortar_visual = tabs.tab("Cortar visualizador")
    tab_sub_main = tabs.tab("Subtitulos")
    tab_ia_main = tabs.tab("IA generadores")
    tab_desc_main = tabs.tab("Descargas")
    tab_image_creator = tabs.tab("Creador de Imagenes")
    tab_drive_main = tabs.tab("Drive")
    tab_youtube_main = tabs.tab("YouTube")
    tab_instagram_main = tabs.tab("Instagram")
    tab_whatsapp_main = tabs.tab("WhatsApp")
    tab_act = tabs.tab("Actividad")
    tab_analytics = tabs.tab("Analítica")

    corte_tabs = ctk.CTkTabview(tab_corte_main, corner_radius=10)
    corte_tabs.pack(fill="both", expand=True, padx=6, pady=6)
    corte_tabs.add("Corte editado")
    corte_tabs.add("Corte individual")
    corte_tabs.add("Corte sin bordes")
    corte_tabs.add("Corte + Zoom")
    corte_tabs.add("Música")
    corte_tabs.add("Imágenes")
    corte_tabs.add("Visualizador")
    corte_tabs.add("Pegar visualizador")

    sub_tabs = ctk.CTkTabview(tab_sub_main, corner_radius=10)
    sub_tabs.pack(fill="both", expand=True, padx=6, pady=6)
    sub_tabs.add("Generar subtitulos")
    sub_tabs.add("Subtitular video")

    ia_tabs = ctk.CTkTabview(tab_ia_main, corner_radius=10)
    ia_tabs.pack(fill="both", expand=True, padx=6, pady=6)
    ia_tabs.add("IA Clips")
    ia_tabs.add("IA TikTok")

    desc_tabs = ctk.CTkTabview(tab_desc_main, corner_radius=10)
    desc_tabs.pack(fill="both", expand=True, padx=6, pady=6)
    desc_tabs.add("Audio MP3")
    desc_tabs.add("YouTube MP3")
    desc_tabs.add("YouTube MP4")

    tab_corte = corte_tabs.tab("Corte editado")
    tab_ind = corte_tabs.tab("Corte individual")
    tab_sin_bordes = corte_tabs.tab("Corte sin bordes")
    tab_zoom = corte_tabs.tab("Corte + Zoom")
    tab_musica = corte_tabs.tab("Música")
    tab_imagenes = corte_tabs.tab("Imágenes")
    tab_srt = sub_tabs.tab("Generar subtitulos")
    tab_sub = sub_tabs.tab("Subtitular video")
    tab_clips = ia_tabs.tab("IA Clips")
    tab_ai = ia_tabs.tab("IA TikTok")
    tab_audio = desc_tabs.tab("Audio MP3")
    tab_youtube = desc_tabs.tab("YouTube MP3")
    tab_youtube_mp4 = desc_tabs.tab("YouTube MP4")

    image_creator_tab.create_tab(tab_image_creator, {
        "log": log,
        "image_creator_state": shared_state.get("image_creator_state"),
    })

    loaded_tabs = set()
    corte_api = {"value": None}
    ind_api = {"value": None}
    srt_api = {"value": None}
    sub_api = {"value": None}
    clips_api = {"value": None}
    ai_api = {"value": None}

    def ensure_corte_api():
        if corte_api["value"] is None:
            corte_api["value"] = corte_tab.create_tab(tab_corte, {
                "estado": estado,
                "rango": rango,
                "log": log,
                "log_global": log,
                "log_seccion": log_seccion,
                "limpiar_entry": limpiar_entry,
                "alerta_busy": alerta_busy,
                "abrir_videos": abrir_videos,
                "stop_control": stop_control,
                "procesar_video_fn": procesar_video_fn,
                "beep_fin": beep_fin,
            })
            set_preview_enabled = corte_api["value"]["set_preview_enabled"]
            actualizar_etiquetas_rango = corte_api["value"]["actualizar_etiquetas_rango"]
            set_preview_enabled(True)
            actualizar_etiquetas_rango()
            corte_scroll = corte_api["value"]["scroll"]
            ventana.after(150, lambda: getattr(corte_scroll, "_parent_canvas", None) and corte_scroll._parent_canvas.yview_moveto(0))
        return corte_api["value"]

    def ensure_individual():
        if ind_api["value"] is None:
            corte_api_val = ensure_corte_api()
            ind_api["value"] = corte_individual_tab.create_tab(tab_ind, {
                "estado": estado,
                "rango_ind": rango_ind,
                "log": log,
                "log_global": log,
                "log_seccion": log_seccion,
                "limpiar_entry": limpiar_entry,
                "alerta_busy": alerta_busy,
                "abrir_videos": abrir_videos,
                "stop_control": stop_control,
                "beep_fin": beep_fin,
                "renombrar_si_largo": renombrar_si_largo,
                "set_preview_enabled": corte_api_val["set_preview_enabled"],
                "cargar_video_preview": corte_api_val["cargar_video_preview"],
            })
            actualizar_etiquetas_rango_ind = ind_api["value"]["actualizar_etiquetas_rango_ind"]
            actualizar_etiquetas_rango_ind()
        return ind_api["value"]

    def ensure_corte_sin_bordes():
        if "corte_sin_bordes" in loaded_tabs:
            return
        ensure_corte_api()
        corte_tab.create_tab(tab_sin_bordes, {
            "estado": estado,
            "rango": rango,
            "log": log,
            "log_global": log,
            "log_seccion": log_seccion,
            "limpiar_entry": limpiar_entry,
            "alerta_busy": alerta_busy,
            "abrir_videos": abrir_videos,
            "stop_control": stop_control,
            "procesar_video_fn": procesar_video_fn,
            "beep_fin": beep_fin,
            "modo_sin_bordes": True,
            "titulo_seccion": "Corte sin bordes",
        })
        loaded_tabs.add("corte_sin_bordes")

    def ensure_corte_zoom():
        if "corte_zoom" in loaded_tabs:
            return
        corte_zoom_tab.create_tab(tab_zoom, {
            "estado": estado,
            "log": log,
            "log_seccion": log_seccion,
            "alerta_busy": alerta_busy,
            "stop_control": stop_control,
            "beep_fin": beep_fin,
        })
        loaded_tabs.add("corte_zoom")

    def ensure_musica():
        if "musica" in loaded_tabs:
            return
        musica_fondo_tab.create_tab(tab_musica, {
            "estado": estado,
            "log": log,
            "log_global": log,
        })
        loaded_tabs.add("musica")

    def ensure_imagenes():
        if "imagenes" in loaded_tabs:
            return
        overlay_imagenes_tab.create_tab(tab_imagenes, {
            "estado": estado,
            "log": log,
            "log_global": log,
        })
        loaded_tabs.add("imagenes")

    def ensure_visualizador():
        if "visualizador" in loaded_tabs:
            return
        tab_visual = corte_tabs.tab("Visualizador")
        corte_visualizer_tab.create_tab(tab_visual, {
            "estado": estado,
        })
        loaded_tabs.add("visualizador")

    def ensure_pegar_visualizador():
        if "pegar_visualizador" in loaded_tabs:
            return
        tab_pegar_visual = corte_tabs.tab("Pegar visualizador")
        pegar_visualizador_tab.create_tab(tab_pegar_visual, {
            "estado": estado,
            "log": log,
            "stop_control": stop_control,
            "alerta_busy": alerta_busy,
            "beep_fin": beep_fin,
        })
        loaded_tabs.add("pegar_visualizador")

    def ensure_cortar_visualizador():
        if "cortar_visualizador" in loaded_tabs:
            return
        cortar_visualizador_tab.create_tab(tab_cortar_visual, {
            "estado": estado,
            "log": log,
            "log_seccion": log_seccion,
            "alerta_busy": alerta_busy,
            "stop_control": stop_control,
            "generar_visualizador_fn": generar_visualizador_solo,
        })
        loaded_tabs.add("cortar_visualizador")

    def ensure_srt():
        if srt_api["value"] is None:
            srt_api["value"] = srt_tab.create_tab(tab_srt, {
                "srt_state": srt_state,
                "log": log,
                "log_global": log,
                "log_seccion": log_seccion,
                "limpiar_entry": limpiar_entry,
                "alerta_busy": alerta_busy,
                "abrir_subtitulos": abrir_subtitulos,
                "stop_control": stop_control,
                "beep_fin": beep_fin,
                "renombrar_si_largo": renombrar_si_largo,
            })
        return srt_api["value"]

    def ensure_subtitulados():
        if sub_api["value"] is None:
            sub_api["value"] = subtitular_tab.create_tab(tab_sub, {
                "sub_state": sub_state,
                "log": log,
                "log_global": log,
                "log_seccion": log_seccion,
                "limpiar_entry": limpiar_entry,
                "alerta_busy": alerta_busy,
                "stop_control": stop_control,
                "beep_fin": beep_fin,
                "renombrar_si_largo": renombrar_si_largo,
            })
        return sub_api["value"]

    def ensure_ia_clips():
        if clips_api["value"] is None:
            clips_api["value"] = ia_clips_tab.create_tab(tab_clips, {
                "log": log,
                "log_global": log,
                "log_seccion": log_seccion,
                "alerta_busy": alerta_busy,
                "stop_control": stop_control,
                "beep_fin": beep_fin,
                "renombrar_si_largo": renombrar_si_largo,
            })
        return clips_api["value"]

    def ensure_ia_tiktok():
        if ai_api["value"] is None:
            ai_api["value"] = ia_tiktok_tab.create_tab(tab_ai, {
                "ventana": ventana,
                "ai_state": ai_state,
                "log": log,
                "log_global": log,
                "log_seccion": log_seccion,
                "alerta_busy": alerta_busy,
                "stop_control": stop_control,
                "beep_fin": beep_fin,
            })
        return ai_api["value"]

    def ensure_audio_mp3():
        if "audio_mp3" in loaded_tabs:
            return
        audio_tab.create_tab(tab_audio, {
            "log": log,
            "log_global": log,
            "log_seccion": log_seccion,
            "alerta_busy": alerta_busy,
            "stop_control": stop_control,
            "beep_fin": beep_fin,
            "renombrar_si_largo": renombrar_si_largo,
            "abrir_audios": abrir_audios,
        })
        loaded_tabs.add("audio_mp3")

    def ensure_youtube_mp3():
        if "youtube_mp3" in loaded_tabs:
            return
        youtube_mp3_tab.create_tab(tab_youtube, {
            "log": log,
            "log_global": log,
            "log_seccion": log_seccion,
            "limpiar_entry": limpiar_entry,
            "alerta_busy": alerta_busy,
            "stop_control": stop_control,
            "beep_fin": beep_fin,
            "abrir_descargas": abrir_descargas,
        })
        loaded_tabs.add("youtube_mp3")

    def ensure_youtube_mp4():
        if "youtube_mp4" in loaded_tabs:
            return
        youtube_mp4_tab.create_tab(tab_youtube_mp4, {
            "log": log,
            "log_global": log,
            "log_seccion": log_seccion,
            "limpiar_entry": limpiar_entry,
            "alerta_busy": alerta_busy,
            "stop_control": stop_control,
            "beep_fin": beep_fin,
            "abrir_descargas": abrir_descargas,
        })
        loaded_tabs.add("youtube_mp4")

    def ensure_youtube_upload():
        if "youtube_upload" in loaded_tabs:
            return
        youtube_upload_tab.create_tab(tab_youtube_main, {
            "log": log,
            "log_global": log,
            "stop_control": stop_control,
            "youtube_state": youtube_state,
        })
        loaded_tabs.add("youtube_upload")

    def ensure_drive():
        if "drive" in loaded_tabs:
            return
        drive_config_tab.create_tab(tab_drive_main, {
            "log_global": log,
            "stop_control": stop_control,
            "drive_state": drive_state,
            "drive_folder_var": drive_folder_var,
        })
        loaded_tabs.add("drive")

    def ensure_whatsapp():
        if "whatsapp" in loaded_tabs:
            return
        whatsapp_tab.create_tab(tab_whatsapp_main, {
            "log": log,
            "log_global": log,
            "stop_control": stop_control,
            "whatsapp_state": whatsapp_state,
            "drive_folder_var": drive_folder_var,
        })
        loaded_tabs.add("whatsapp")

    def ensure_analytics():
        if "analytics" in loaded_tabs:
            return
        youtube_analytics_tab.create_tab(tab_analytics, {
            "log": log,
            "log_global": log,
            "stop_control": stop_control,
        })
        loaded_tabs.add("analytics")

    def ensure_instagram():
        if "instagram" in loaded_tabs:
            return
        instagram_tab.create_instagram_tab(tab_instagram_main, {
            "log": log,
            "stop_control": stop_control,
        })
        loaded_tabs.add("instagram")

    def ensure_activity():
        if "activity" in loaded_tabs:
            return
        actividad_tab.create_tab(tab_act, {
            "log_state": log_state,
            "log": log,
            "abrir_transcripciones": abrir_transcripciones,
            "eliminar_audios": lambda: eliminar_audios(log),
            "stop_control": stop_control,
        })
        loaded_tabs.add("activity")

    def ensure_image_creator():
        if "image_creator" in loaded_tabs:
            return
        image_creator_tab.create_tab(tab_image_creator, {
            "log": log,
            "image_creator_state": shared_state.get("image_creator_state"),
        })
        loaded_tabs.add("image_creator")

    def on_main_tab_change(tab_name: str):
        if tab_name == "Corte":
            on_corte_tab_change(corte_tabs.get())
            return
        if tab_name == "Cortar visualizador":
            ensure_cortar_visualizador()
        elif tab_name == "Subtitulos":
            on_sub_tab_change(sub_tabs.get())
        elif tab_name == "IA generadores":
            on_ia_tab_change(ia_tabs.get())
        elif tab_name == "Descargas":
            on_desc_tab_change(desc_tabs.get())
        elif tab_name == "Creador de Imagenes":
            ensure_image_creator()
        elif tab_name == "Drive":
            ensure_drive()
        elif tab_name == "YouTube":
            ensure_youtube_upload()
        elif tab_name == "Anal?tica":
            ensure_analytics()
        elif tab_name == "Instagram":
            ensure_instagram()
        elif tab_name == "WhatsApp":
            ensure_whatsapp()
        elif tab_name == "Actividad":
            ensure_activity()

    def on_corte_tab_change(tab_name: str):
        if tab_name == "Corte editado":
            ensure_corte_api()
        elif tab_name == "Corte individual":
            ensure_individual()
        elif tab_name == "Corte sin bordes":
            ensure_corte_sin_bordes()
        elif tab_name == "Corte + Zoom":
            ensure_corte_zoom()
        elif tab_name == "M?sica":
            ensure_musica()
        elif tab_name == "Im?genes":
            ensure_imagenes()
        elif tab_name == "Visualizador":
            ensure_visualizador()
        elif tab_name == "Pegar visualizador":
            ensure_pegar_visualizador()

    def on_sub_tab_change(tab_name: str):
        if tab_name == "Generar subtitulos":
            ensure_srt()
        elif tab_name == "Subtitular video":
            ensure_subtitulados()

    def on_ia_tab_change(tab_name: str):
        if tab_name == "IA Clips":
            ensure_ia_clips()
        elif tab_name == "IA TikTok":
            ensure_ia_tiktok()

    def on_desc_tab_change(tab_name: str):
        if tab_name == "Audio MP3":
            ensure_audio_mp3()
        elif tab_name == "YouTube MP3":
            ensure_youtube_mp3()
        elif tab_name == "YouTube MP4":
            ensure_youtube_mp4()

    tabs.configure(command=on_main_tab_change)
    corte_tabs.configure(command=on_corte_tab_change)
    sub_tabs.configure(command=on_sub_tab_change)
    ia_tabs.configure(command=on_ia_tab_change)
    desc_tabs.configure(command=on_desc_tab_change)

    try:
        on_corte_tab_change(corte_tabs.get())
    except Exception:
        ensure_corte_api()
    try:
        on_main_tab_change(tabs.get())
    except Exception:
        pass
    ventana.after_idle(lambda: ventana.state("zoomed"))

    return ventana, None, log, None
