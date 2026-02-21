import os
import threading
import customtkinter as ctk
import tkinter as tk

from core.workflow import procesar_corte_zoom
from core.config_corte_zoom import get_corte_zoom_defaults
from core.utils import obtener_duracion_segundos

def create_tab(parent, context):
    estado = context["estado"]
    log = context["log"]
    log_seccion = context["log_seccion"]
    alerta_busy = context["alerta_busy"]
    stop_control = context["stop_control"]
    beep_fin = context["beep_fin"]

    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=1)

    scroll = ctk.CTkScrollableFrame(container, corner_radius=0)
    scroll.grid(row=0, column=0, sticky="nsew")
    scroll.grid_columnconfigure(0, weight=1)

    card = ctk.CTkFrame(scroll, corner_radius=12)
    card.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    card.grid_columnconfigure(0, weight=1)

    defaults = get_corte_zoom_defaults()

    lbl_title = ctk.CTkLabel(card, text="Corte + Zoom", font=ctk.CTkFont(size=18, weight="bold"))
    lbl_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))

    lbl_hint = ctk.CTkLabel(
        card,
        text="Recorta por porcentajes, centra y aplica zoom. Opcional: fondo video loop.",
        font=ctk.CTkFont(size=12),
        text_color="#9aa4b2",
    )
    lbl_hint.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

    dur_state = {"dur": 0.0}

    def _format_time(seconds: float) -> str:
        seconds = max(0.0, float(seconds))
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def _parse_time(text: str) -> float | None:
        raw = (text or "").strip()
        if not raw:
            return None
        parts = raw.split(":")
        try:
            nums = [float(p) for p in parts]
        except Exception:
            return None
        if len(nums) == 1:
            return nums[0]
        if len(nums) == 2:
            return nums[0] * 60 + nums[1]
        if len(nums) == 3:
            return nums[0] * 3600 + nums[1] * 60 + nums[2]
        return None

    row_select = ctk.CTkFrame(card, fg_color="transparent")
    row_select.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
    row_select.grid_columnconfigure(1, weight=1)

    def seleccionar_video():
        from ui.dialogs import seleccionar_video
        video = seleccionar_video()
        if video:
            estado["path"] = video
            estado["es_audio"] = False
            try:
                dur_state["dur"] = float(obtener_duracion_segundos(video))
            except Exception:
                dur_state["dur"] = 0.0
            slider_max = max(1.0, dur_state["dur"])
            slider_steps = max(1, int(slider_max))
            slider_inicio.configure(to=slider_max, number_of_steps=slider_steps)
            slider_fin.configure(to=slider_max, number_of_steps=slider_steps)
            slider_fin.set(dur_state["dur"])
            entry_inicio.delete(0, "end")
            entry_inicio.insert(0, _format_time(0.0))
            entry_fin.delete(0, "end")
            entry_fin.insert(0, _format_time(dur_state["dur"]))
            lbl_inicio_val.configure(text=_format_time(0.0))
            lbl_fin_val.configure(text=_format_time(dur_state["dur"]))
            lbl_duracion_val.configure(text=_format_time(dur_state["dur"]))
            log(f"Video seleccionado: {video}")

    btn_video = ctk.CTkButton(row_select, text="Seleccionar video", command=seleccionar_video, height=36)
    btn_video.grid(row=0, column=0, sticky="w")

    lbl_video = ctk.CTkLabel(row_select, text="(usa el video actual)", font=ctk.CTkFont(size=12))
    lbl_video.grid(row=0, column=1, sticky="w", padx=(12, 0))

    range_card = ctk.CTkFrame(card, corner_radius=10)
    range_card.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
    range_card.grid_columnconfigure(1, weight=1)
    range_card.grid_columnconfigure(3, weight=1)

    lbl_range = ctk.CTkLabel(range_card, text="Rango (inicio / fin):", font=ctk.CTkFont(size=12))
    lbl_range.grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))
    lbl_duracion_val = ctk.CTkLabel(range_card, text=_format_time(0.0), font=ctk.CTkFont(size=12))
    lbl_duracion_val.grid(row=0, column=1, sticky="e", padx=12, pady=(10, 6))

    entry_inicio = ctk.CTkEntry(range_card, width=90)
    entry_inicio.insert(0, _format_time(0.0))
    entry_inicio.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))
    entry_fin = ctk.CTkEntry(range_card, width=90)
    entry_fin.insert(0, _format_time(0.0))
    entry_fin.grid(row=1, column=1, sticky="e", padx=12, pady=(0, 6))

    lbl_inicio_val = ctk.CTkLabel(range_card, text=_format_time(0.0), font=ctk.CTkFont(size=12))
    lbl_inicio_val.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 6))
    lbl_fin_val = ctk.CTkLabel(range_card, text=_format_time(0.0), font=ctk.CTkFont(size=12))
    lbl_fin_val.grid(row=2, column=1, sticky="e", padx=12, pady=(0, 6))

    inicio_var = tk.DoubleVar(value=0.0)
    fin_var = tk.DoubleVar(value=0.0)

    def _sync_labels():
        lbl_inicio_val.configure(text=_format_time(inicio_var.get()))
        lbl_fin_val.configure(text=_format_time(fin_var.get()))

    def on_inicio_change(value):
        if value > fin_var.get():
            fin_var.set(value)
            slider_fin.set(value)
        _sync_labels()

    def on_fin_change(value):
        if value < inicio_var.get():
            inicio_var.set(value)
            slider_inicio.set(value)
        _sync_labels()

    slider_inicio = ctk.CTkSlider(
        range_card,
        from_=0,
        to=1,
        number_of_steps=1,
        variable=inicio_var,
        command=on_inicio_change,
        width=260,
    )
    slider_inicio.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 6))

    slider_fin = ctk.CTkSlider(
        range_card,
        from_=0,
        to=1,
        number_of_steps=1,
        variable=fin_var,
        command=on_fin_change,
        width=260,
    )
    slider_fin.grid(row=4, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))

    crop_card = ctk.CTkFrame(card, corner_radius=10)
    crop_card.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 12))
    crop_card.grid_columnconfigure(1, weight=1)
    crop_card.grid_columnconfigure(3, weight=1)

    c_top = ctk.CTkEntry(crop_card, width=70)
    c_top.insert(0, f"{estado.get('zoom_crop_top_pct', defaults.get('crop_top_pct', 25.0)):.1f}")
    c_bottom = ctk.CTkEntry(crop_card, width=70)
    c_bottom.insert(0, f"{estado.get('zoom_crop_bottom_pct', defaults.get('crop_bottom_pct', 25.0)):.1f}")
    c_left = ctk.CTkEntry(crop_card, width=70)
    c_left.insert(0, f"{estado.get('zoom_crop_left_pct', defaults.get('crop_left_pct', 0.0)):.1f}")
    c_right = ctk.CTkEntry(crop_card, width=70)
    c_right.insert(0, f"{estado.get('zoom_crop_right_pct', defaults.get('crop_right_pct', 0.0)):.1f}")

    ctk.CTkLabel(crop_card, text="Top %", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(12, 6), pady=(10, 6))
    c_top.grid(row=0, column=1, sticky="w", pady=(10, 6))
    ctk.CTkLabel(crop_card, text="Bottom %", font=ctk.CTkFont(size=12)).grid(row=0, column=2, sticky="w", padx=(12, 6), pady=(10, 6))
    c_bottom.grid(row=0, column=3, sticky="w", pady=(10, 6))

    ctk.CTkLabel(crop_card, text="Left %", font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=(0, 12))
    c_left.grid(row=1, column=1, sticky="w", pady=(0, 12))
    ctk.CTkLabel(crop_card, text="Right %", font=ctk.CTkFont(size=12)).grid(row=1, column=2, sticky="w", padx=(12, 6), pady=(0, 12))
    c_right.grid(row=1, column=3, sticky="w", pady=(0, 12))

    zoom_var = tk.DoubleVar(value=float(estado.get("zoom_factor", defaults.get("zoom_factor", 1.0)) or 1.0))
    lbl_zoom = ctk.CTkLabel(card, text="Zoom", font=ctk.CTkFont(size=12))
    lbl_zoom.grid(row=5, column=0, sticky="w", padx=16, pady=(0, 4))
    lbl_zoom_val = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12))
    lbl_zoom_val.grid(row=5, column=0, sticky="e", padx=16, pady=(0, 4))

    def _update_zoom(val=None):
        v = float(val if val is not None else zoom_var.get())
        lbl_zoom_val.configure(text=f"{v:.2f}x")

    slider_zoom = ctk.CTkSlider(
        card,
        from_=1.0,
        to=2.0,
        number_of_steps=20,
        variable=zoom_var,
        command=lambda v: _update_zoom(v),
        width=260,
    )
    slider_zoom.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 12))
    _update_zoom()

    bg_var = ctk.BooleanVar(value=bool(estado.get("zoom_bg_enabled", defaults.get("bg_enabled", False))))
    chk_bg = ctk.CTkCheckBox(card, text="Usar video de fondo (loop)", variable=bg_var)
    chk_bg.grid(row=7, column=0, sticky="w", padx=16, pady=(0, 6))

    row_bg = ctk.CTkFrame(card, fg_color="transparent")
    row_bg.grid(row=8, column=0, sticky="ew", padx=16, pady=(0, 12))
    row_bg.grid_columnconfigure(1, weight=1)

    def seleccionar_bg():
        from ui.dialogs import seleccionar_video
        video = seleccionar_video()
        if video:
            estado["zoom_bg_video_path"] = video
            lbl_bg.configure(text=os.path.basename(video))

    btn_bg = ctk.CTkButton(row_bg, text="Seleccionar fondo", command=seleccionar_bg, height=28, width=160)
    btn_bg.grid(row=0, column=0, sticky="w")

    lbl_bg = ctk.CTkLabel(row_bg, text="(sin fondo)", font=ctk.CTkFont(size=12))
    lbl_bg.grid(row=0, column=1, sticky="w", padx=(10, 0))
    if estado.get("zoom_bg_video_path"):
        lbl_bg.configure(text=os.path.basename(estado["zoom_bg_video_path"]))

    def _run():
        if not estado.get("path"):
            log("Selecciona un video primero.")
            return
        if stop_control.is_busy():
            alerta_busy()
            return
        stop_control.clear_stop()
        stop_control.set_busy(True)
        log_seccion("Corte + Zoom")

        try:
            top = float(c_top.get().strip().replace(",", "."))
        except Exception:
            top = 25.0
        try:
            bottom = float(c_bottom.get().strip().replace(",", "."))
        except Exception:
            bottom = 25.0
        try:
            left = float(c_left.get().strip().replace(",", "."))
        except Exception:
            left = 0.0
        try:
            right = float(c_right.get().strip().replace(",", "."))
        except Exception:
            right = 0.0
        zoom = float(zoom_var.get())

        start_sec = _parse_time(entry_inicio.get())
        end_sec = _parse_time(entry_fin.get())
        if start_sec is None:
            start_sec = inicio_var.get()
        if end_sec is None:
            end_sec = fin_var.get()
        if dur_state["dur"] > 0 and end_sec > dur_state["dur"]:
            end_sec = dur_state["dur"]
        if end_sec is not None and start_sec is not None and end_sec <= start_sec:
            log("Rango inválido: el final debe ser mayor al inicio.")
            stop_control.set_busy(False)
            return

        bg_path = None
        if bg_var.get():
            bg_path = estado.get("zoom_bg_video_path")
            if bg_path and not os.path.exists(bg_path):
                bg_path = None

        cinta = None
        if cinta_var.get():
            try:
                cinta = {
                    "left_pct": float(entry_left.get().strip().replace(",", ".")),
                    "top_pct": float(entry_top.get().strip().replace(",", ".")),
                    "width_pct": float(entry_width.get().strip().replace(",", ".")),
                    "height_pct": float(entry_height.get().strip().replace(",", ".")),
                    "bg_color": entry_bg.get().strip(),
                    "border_color": entry_border.get().strip(),
                    "text_color": entry_text.get().strip(),
                    "nombre": entry_nombre.get().strip(),
                    "rol": entry_rol.get().strip(),
                    "text_scale": float(entry_text_scale.get().strip().replace(",", ".")),
                    "name_scale": float(entry_name_scale.get().strip().replace(",", ".")),
                    "role_scale": float(entry_role_scale.get().strip().replace(",", ".")),
                    "fontfile_name": estado.get("zoom_cinta_fontfile_name", defaults.get("cinta_fontfile_name", "")),
                    "fontfile_role": estado.get("zoom_cinta_fontfile_role", defaults.get("cinta_fontfile_role", "")),
                }
            except Exception:
                cinta = None

        estado["zoom_crop_top_pct"] = top
        estado["zoom_crop_bottom_pct"] = bottom
        estado["zoom_crop_left_pct"] = left
        estado["zoom_crop_right_pct"] = right
        estado["zoom_factor"] = zoom
        estado["zoom_bg_enabled"] = bool(bg_var.get())
        estado["zoom_cinta_enabled"] = bool(cinta_var.get())
        estado["zoom_cinta_left_pct"] = float(entry_left.get().strip().replace(",", ".") or 0.0)
        estado["zoom_cinta_top_pct"] = float(entry_top.get().strip().replace(",", ".") or 0.0)
        estado["zoom_cinta_width_pct"] = float(entry_width.get().strip().replace(",", ".") or 0.0)
        estado["zoom_cinta_height_pct"] = float(entry_height.get().strip().replace(",", ".") or 0.0)
        estado["zoom_cinta_bg_color"] = entry_bg.get().strip()
        estado["zoom_cinta_border_color"] = entry_border.get().strip()
        estado["zoom_cinta_text_color"] = entry_text.get().strip()
        estado["zoom_cinta_nombre"] = entry_nombre.get().strip()
        estado["zoom_cinta_rol"] = entry_rol.get().strip()
        try:
            estado["zoom_cinta_text_scale"] = float(entry_text_scale.get().strip().replace(",", "."))
        except Exception:
            estado["zoom_cinta_text_scale"] = 1.0
        try:
            estado["zoom_cinta_name_scale"] = float(entry_name_scale.get().strip().replace(",", "."))
        except Exception:
            estado["zoom_cinta_name_scale"] = defaults.get("cinta_name_scale", 0.50)
        try:
            estado["zoom_cinta_role_scale"] = float(entry_role_scale.get().strip().replace(",", "."))
        except Exception:
            estado["zoom_cinta_role_scale"] = defaults.get("cinta_role_scale", 0.40)

        def worker():
            try:
                procesar_corte_zoom(
                    estado["path"],
                    crop_top_pct=top,
                    crop_bottom_pct=bottom,
                    crop_left_pct=left,
                    crop_right_pct=right,
                    zoom=zoom,
                    bg_video_path=bg_path,
                    cinta=cinta,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    logs=log,
                )
                log("Finalizado corte + zoom.")
                beep_fin()
            except Exception as exc:
                log(f"Error en corte + zoom: {exc}")
            finally:
                stop_control.set_busy(False)

        threading.Thread(target=worker, daemon=True).start()

    cinta_card = ctk.CTkFrame(card, corner_radius=10)
    cinta_card.grid(row=9, column=0, sticky="ew", padx=16, pady=(0, 12))
    cinta_card.grid_columnconfigure(1, weight=1)
    cinta_card.grid_columnconfigure(3, weight=1)

    cinta_var = tk.BooleanVar(value=bool(estado.get("zoom_cinta_enabled", defaults.get("cinta_enabled", False))))
    chk_cinta = ctk.CTkCheckBox(cinta_card, text="Agregar cinta (nombre y rol)", variable=cinta_var)
    chk_cinta.grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(10, 6))

    entry_nombre = ctk.CTkEntry(cinta_card, width=180)
    entry_nombre.insert(0, estado.get("zoom_cinta_nombre", defaults.get("cinta_nombre", "Invitado")))
    entry_rol = ctk.CTkEntry(cinta_card, width=180)
    entry_rol.insert(0, estado.get("zoom_cinta_rol", defaults.get("cinta_rol", "Rol / Profesión")))
    entry_nombre.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))
    entry_rol.grid(row=1, column=2, columnspan=2, sticky="w", padx=12, pady=(0, 6))

    entry_bg = ctk.CTkEntry(cinta_card, width=90)
    entry_bg.insert(0, estado.get("zoom_cinta_bg_color", defaults.get("cinta_bg_color", "#000000")))
    entry_border = ctk.CTkEntry(cinta_card, width=90)
    entry_border.insert(0, estado.get("zoom_cinta_border_color", defaults.get("cinta_border_color", "#F8BA11")))
    entry_text = ctk.CTkEntry(cinta_card, width=90)
    entry_text.insert(0, estado.get("zoom_cinta_text_color", defaults.get("cinta_text_color", "#FFFFFF")))
    entry_bg.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 6))
    entry_border.grid(row=2, column=1, sticky="w", padx=12, pady=(0, 6))
    entry_text.grid(row=2, column=2, sticky="w", padx=12, pady=(0, 6))

    entry_left = ctk.CTkEntry(cinta_card, width=70)
    entry_left.insert(0, f"{estado.get('zoom_cinta_left_pct', defaults.get('cinta_left_pct', 29.0)):.1f}")
    entry_top = ctk.CTkEntry(cinta_card, width=70)
    entry_top.insert(0, f"{estado.get('zoom_cinta_top_pct', defaults.get('cinta_top_pct', 70.0)):.1f}")
    entry_width = ctk.CTkEntry(cinta_card, width=70)
    entry_width.insert(0, f"{estado.get('zoom_cinta_width_pct', defaults.get('cinta_width_pct', 42.0)):.1f}")
    entry_height = ctk.CTkEntry(cinta_card, width=70)
    entry_height.insert(0, f"{estado.get('zoom_cinta_height_pct', defaults.get('cinta_height_pct', 10.0)):.1f}")
    entry_left.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 6))
    entry_top.grid(row=3, column=1, sticky="w", padx=12, pady=(0, 6))
    entry_width.grid(row=3, column=2, sticky="w", padx=12, pady=(0, 6))
    entry_height.grid(row=3, column=3, sticky="w", padx=12, pady=(0, 6))

    entry_text_scale = ctk.CTkEntry(cinta_card, width=70)
    entry_text_scale.insert(0, f"{estado.get('zoom_cinta_text_scale', defaults.get('cinta_text_scale', 1.0)):.2f}")
    ctk.CTkLabel(cinta_card, text="Texto x", font=ctk.CTkFont(size=12)).grid(row=4, column=0, sticky="w", padx=12, pady=(0, 10))
    entry_text_scale.grid(row=4, column=1, sticky="w", padx=12, pady=(0, 10))

    entry_name_scale = ctk.CTkEntry(cinta_card, width=70)
    entry_name_scale.insert(0, f"{estado.get('zoom_cinta_name_scale', defaults.get('cinta_name_scale', 0.50)):.2f}")
    ctk.CTkLabel(cinta_card, text="Nombre x", font=ctk.CTkFont(size=12)).grid(row=4, column=2, sticky="w", padx=12, pady=(0, 10))
    entry_name_scale.grid(row=4, column=3, sticky="w", padx=12, pady=(0, 10))

    entry_role_scale = ctk.CTkEntry(cinta_card, width=70)
    entry_role_scale.insert(0, f"{estado.get('zoom_cinta_role_scale', defaults.get('cinta_role_scale', 0.40)):.2f}")
    ctk.CTkLabel(cinta_card, text="Rol x", font=ctk.CTkFont(size=12)).grid(row=5, column=0, sticky="w", padx=12, pady=(0, 10))
    entry_role_scale.grid(row=5, column=1, sticky="w", padx=12, pady=(0, 10))

    btn_apply = ctk.CTkButton(card, text="Aplicar corte + zoom", command=_run, height=42)
    btn_apply.grid(row=10, column=0, sticky="ew", padx=16, pady=(4, 16))

    return {"scroll": scroll}
