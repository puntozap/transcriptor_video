
import os
import time
import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
from PIL import Image, ImageTk

from core.image_composer import compose_image
from core.openai_image_gen import generar_background_openai
from ui.shared import helpers




def _get_font_files():
    fonts_dir = os.path.join(os.environ.get("WINDIR", r"C:\\Windows"), "Fonts")
    if not os.path.isdir(fonts_dir):
        return []
    files = []
    for name in os.listdir(fonts_dir):
        lower = name.lower()
        if lower.endswith(".ttf") or lower.endswith(".otf"):
            files.append(os.path.join(fonts_dir, name))
    return sorted(files)


PRESETS = [
    {
        "name": "Rojo Clasico",
        "top_bg_color": "#E53935",
        "top_text_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "name_color": "#FFFFFF",
    },
    {
        "name": "Amarillo",
        "top_bg_color": "#F8BA11",
        "top_text_color": "#000000",
        "title_color": "#FFFFFF",
        "name_color": "#FFFFFF",
    },
    {
        "name": "Azul",
        "top_bg_color": "#1565C0",
        "top_text_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "name_color": "#E3F2FD",
    },
    {
        "name": "Negro",
        "top_bg_color": "#111111",
        "top_text_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "name_color": "#FFFFFF",
    },
]


def create_tab(parent, context):
    log = context.get("log", print)
    state = context.get("image_creator_state")
    if not state:
        state = {"vertical": {}, "horizontal": {}}

    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    tabview = ctk.CTkTabview(parent)
    tabview.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    tab_vert = tabview.add("Imagen vertical")
    tab_horz = tabview.add("Imagen horizontal")
    tab_ai = tabview.add("ImagenIA")

    vert_api = _build_creator(tab_vert, state["vertical"], (1080, 1920), "vertical", log)
    horz_api = _build_creator(tab_horz, state["horizontal"], (1280, 720), "horizontal", log)
    _build_ai_tab(tab_ai, state, log, state["vertical"], state["horizontal"])

    def _ensure_fonts_loaded():
        for api in (vert_api, horz_api):
            if api and "ensure_fonts_loaded" in api:
                api["ensure_fonts_loaded"]()

    return {
        "ensure_fonts_loaded": _ensure_fonts_loaded,
    }


def _build_creator(parent, settings, size, variant, log):
    width, height = size

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack(fill="both", expand=True)
    container.grid_columnconfigure(0, weight=2)
    container.grid_columnconfigure(1, weight=3)
    container.grid_columnconfigure(2, weight=2)
    container.grid_rowconfigure(0, weight=1)

    # Left: Options (scroll)
    options = ctk.CTkScrollableFrame(container, corner_radius=10)
    options.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)
    options.grid_columnconfigure(0, weight=1)

    # Center: Preview
    preview_card = ctk.CTkFrame(container, corner_radius=10)
    preview_card.grid(row=0, column=1, sticky="nsew", padx=(0, 8), pady=0)
    preview_card.grid_rowconfigure(1, weight=1)
    preview_card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(preview_card, text="Preview", font=ctk.CTkFont(size=16, weight="bold")).grid(
        row=0, column=0, sticky="w", padx=12, pady=(10, 6)
    )
    preview_wrap = ctk.CTkFrame(preview_card, corner_radius=8)
    preview_wrap.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
    preview_wrap.grid_rowconfigure(0, weight=1)
    preview_wrap.grid_columnconfigure(0, weight=1)

    preview_canvas = tk.Canvas(preview_wrap, bg="#1a1d24", highlightthickness=0)
    preview_canvas.grid(row=0, column=0, sticky="nsew")
    preview_scroll_y = tk.Scrollbar(preview_wrap, orient="vertical", command=preview_canvas.yview)
    preview_scroll_y.grid(row=0, column=1, sticky="ns")
    preview_scroll_x = tk.Scrollbar(preview_wrap, orient="horizontal", command=preview_canvas.xview)
    preview_scroll_x.grid(row=1, column=0, sticky="ew")
    preview_canvas.configure(yscrollcommand=preview_scroll_y.set, xscrollcommand=preview_scroll_x.set)

    preview_label = tk.Label(preview_canvas, text="(sin preview)", bg="#1a1d24", fg="#cbd5e1")
    preview_window = preview_canvas.create_window((0, 0), window=preview_label, anchor="nw")

    # Right: Extra / Export
    right = ctk.CTkFrame(container, corner_radius=10)
    right.grid(row=0, column=2, sticky="nsew", padx=(0, 0), pady=0)
    right.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(right, text="Exportar", font=ctk.CTkFont(size=16, weight="bold")).grid(
        row=0, column=0, sticky="w", padx=12, pady=(10, 6)
    )

    entry_name = ctk.CTkEntry(right, placeholder_text="Nombre base (opcional)")
    entry_name.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))

    btn_preview = ctk.CTkButton(right, text="Generar preview", height=34)
    btn_preview.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

    btn_export = ctk.CTkButton(right, text="Exportar PNG + JPG", height=36)
    btn_export.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))

    log_card, _log_widget, log_local = helpers.create_log_panel(
        right,
        title="Actividad",
        height=240,
    )
    log_card.grid(row=4, column=0, sticky="nsew", padx=12, pady=(8, 12))

    preview_state = {"image": None}
    render_state = {"running": False}
    ui_ready = {"value": False}
    entry_top_text = None
    entry_top_text2 = None
    entry_title = None
    entry_name_text = None
    entry_top_color = None
    entry_top_bg = None
    entry_top2_color = None
    entry_top2_bg = None
    entry_title_color = None
    entry_name_color = None
    entry_filter = None

    def _clear_children(frame):
        for child in frame.winfo_children():
            child.destroy()


    def _apply_preset(preset_idx: int):
        preset = PRESETS[preset_idx % len(PRESETS)]
        settings["top_bg_color"] = preset["top_bg_color"]
        settings["top_text_color"] = preset["top_text_color"]
        settings["title_color"] = preset["title_color"]
        settings["name_color"] = preset["name_color"]
        settings["preset_index"] = preset_idx % len(PRESETS)
        entry_top_bg.delete(0, "end")
        entry_top_bg.insert(0, settings["top_bg_color"])
        entry_top_color.delete(0, "end")
        entry_top_color.insert(0, settings["top_text_color"])
        entry_title_color.delete(0, "end")
        entry_title_color.insert(0, settings["title_color"])
        entry_name_color.delete(0, "end")
        entry_name_color.insert(0, settings["name_color"])
        lbl_preset.configure(text=preset["name"])
        
    def _sync_all_inputs():
        if not ui_ready["value"]:
            return
        if not all([
            entry_top_text,
            entry_top_text2,
            entry_title,
            entry_name_text,
            entry_top_color,
            entry_top_bg,
            entry_top2_color,
            entry_top2_bg,
            entry_title_color,
            entry_name_color,
            entry_filter,
        ]):
            return
        settings["top_text"] = entry_top_text.get("1.0", "end").strip()
        settings["top_text_2"] = entry_top_text2.get("1.0", "end").strip()
        settings["title_text"] = entry_title.get("1.0", "end").strip()
        settings["name_text"] = entry_name_text.get("1.0", "end").strip()
        settings["top_text_color"] = entry_top_color.get().strip()
        settings["top_bg_color"] = entry_top_bg.get().strip()
        settings["top2_text_color"] = entry_top2_color.get().strip()
        settings["top2_bg_color"] = entry_top2_bg.get().strip()
        settings["title_color"] = entry_title_color.get().strip()
        settings["name_color"] = entry_name_color.get().strip()
        try:
            value = float(entry_filter.get().strip())
            value = max(0.0, min(1.0, value))
            settings["bg_filter_intensity"] = value
        except Exception:
            pass

    def _render_preview():
        if render_state["running"]:
            return
        render_state["running"] = True
        try:
            btn_preview.configure(state="disabled")
            _sync_all_inputs()
            scale = 0.35 if variant == "vertical" else 0.55
            img = compose_image(settings, (width, height), preview_scale=scale)
            preview = ImageTk.PhotoImage(img)
            preview_label.configure(image=preview, text="")
            preview_state["image"] = preview
            preview_canvas.itemconfigure(preview_window)
            preview_label.update_idletasks()
            preview_canvas.configure(scrollregion=preview_canvas.bbox("all"))
            log_local("? Preview actualizado")
        except Exception as exc:
            log_local(f"? Error preview: {exc}")
        finally:
            try:
                btn_preview.configure(state="normal")
            except Exception:
                pass
            render_state["running"] = False

    def _trigger_preview():
        if not ui_ready["value"]:
            return
        threading.Thread(target=_render_preview, daemon=True).start()

    def _export_images():
        try:
            _sync_all_inputs()
            base = entry_name.get().strip() or f"{variant}_{int(time.time())}"
            out_dir = os.path.join("output", "imagenes_creator", variant)
            os.makedirs(out_dir, exist_ok=True)
            img = compose_image(settings, (width, height), preview_scale=1.0)
            png_path = os.path.join(out_dir, f"{base}.png")
            jpg_path = os.path.join(out_dir, f"{base}.jpg")
            img.save(png_path, format="PNG")
            img.convert("RGB").save(jpg_path, format="JPEG", quality=95)
            log_local(f"? Exportado: {png_path}")
            log_local(f"? Exportado: {jpg_path}")
        except Exception as exc:
            log_local(f"? Error exportando: {exc}")

    btn_preview.configure(command=lambda: threading.Thread(target=_render_preview, daemon=True).start())
    btn_export.configure(command=lambda: threading.Thread(target=_export_images, daemon=True).start())

    # Options UI
    title = ctk.CTkLabel(options, text="Opciones", font=ctk.CTkFont(size=16, weight="bold"))
    title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

    # Presets carousel
    preset_row = ctk.CTkFrame(options, fg_color="transparent")
    preset_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
    preset_row.grid_columnconfigure(1, weight=1)
    btn_prev = ctk.CTkButton(preset_row, text="<", width=32)
    btn_prev.grid(row=0, column=0, padx=(0, 6))
    lbl_preset = ctk.CTkLabel(preset_row, text=PRESETS[0]["name"])
    lbl_preset.grid(row=0, column=1, sticky="ew")
    btn_next = ctk.CTkButton(preset_row, text=">", width=32)
    btn_next.grid(row=0, column=2, padx=(6, 0))

    def _preset_prev():
        idx = int(settings.get("preset_index", 0)) - 1
        _apply_preset(idx)

    def _preset_next():
        idx = int(settings.get("preset_index", 0)) + 1
        _apply_preset(idx)

    btn_prev.configure(command=_preset_prev)
    btn_next.configure(command=_preset_next)

    # Fondo
    ctk.CTkLabel(options, text="Fondo", font=ctk.CTkFont(size=13, weight="bold")).grid(
        row=2, column=0, sticky="w", padx=12, pady=(0, 6)
    )
    bg_row = ctk.CTkFrame(options, fg_color="transparent")
    bg_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 8))
    bg_row.grid_columnconfigure(1, weight=1)
    lbl_bg = ctk.CTkLabel(bg_row, text=os.path.basename(settings.get("background_path", "")) or "(sin fondo)")

    def _select_bg():
        from ui.dialogs import seleccionar_imagen
        path = seleccionar_imagen()
        if path:
            settings["background_path"] = path
            lbl_bg.configure(text=os.path.basename(path))
            
    ctk.CTkButton(bg_row, text="Seleccionar", width=120, command=_select_bg).grid(row=0, column=0)
    lbl_bg.grid(row=0, column=1, sticky="w", padx=(8, 0))

    # Filtro fondo
    filter_row = ctk.CTkFrame(options, fg_color="transparent")
    filter_row.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 8))
    filter_row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(filter_row, text="Filtro fondo", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
    filter_var = tk.StringVar(value=settings.get("bg_filter", "none"))
    filter_menu = ctk.CTkOptionMenu(filter_row, values=["none", "sepia", "bw", "cool", "warm"], variable=filter_var)
    filter_menu.grid(row=0, column=1, sticky="ew", padx=(8, 0))

    def _sync_filter(*_):
        settings["bg_filter"] = filter_var.get()
        
    filter_var.trace_add("write", lambda *_: _sync_filter())

    row_filter = ctk.CTkFrame(options, fg_color="transparent")
    row_filter.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 8))
    row_filter.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(row_filter, text="Intensidad", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
    slider_filter = ctk.CTkSlider(row_filter, from_=0.0, to=1.0, number_of_steps=20)
    slider_filter.grid(row=0, column=1, sticky="ew", padx=(8, 6))
    entry_filter = ctk.CTkEntry(row_filter, width=70)
    entry_filter.grid(row=0, column=2)
    slider_filter.set(float(settings.get("bg_filter_intensity", 0.7)))
    entry_filter.insert(0, f"{settings.get('bg_filter_intensity', 0.7):.2f}")

    def _sync_filter_slider(val):
        try:
            settings["bg_filter_intensity"] = float(val)
            entry_filter.delete(0, "end")
            entry_filter.insert(0, f"{float(val):.2f}")
        except Exception:
            pass

    def _sync_filter_entry(_=None):
        try:
            value = float(entry_filter.get().strip())
            value = max(0.0, min(1.0, value))
            settings["bg_filter_intensity"] = value
            slider_filter.set(value)
        except Exception:
            pass

    slider_filter.configure(command=_sync_filter_slider)
    slider_filter.bind("<ButtonRelease-1>", lambda _e: _trigger_preview())
    entry_filter.bind("<FocusOut>", _sync_filter_entry)
    entry_filter.bind("<Return>", _sync_filter_entry)

    # Imagen principal
    ctk.CTkLabel(options, text="Imagen principal (PNG)", font=ctk.CTkFont(size=13, weight="bold")).grid(
        row=6, column=0, sticky="w", padx=12, pady=(4, 6)
    )
    main_row = ctk.CTkFrame(options, fg_color="transparent")
    main_row.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 8))
    main_row.grid_columnconfigure(1, weight=1)
    lbl_main = ctk.CTkLabel(main_row, text=os.path.basename(settings.get("main_path", "")) or "(sin imagen)")

    def _select_main():
        from ui.dialogs import seleccionar_imagen
        path = seleccionar_imagen()
        if path:
            settings["main_path"] = path
            lbl_main.configure(text=os.path.basename(path))
            
    ctk.CTkButton(main_row, text="Seleccionar", width=120, command=_select_main).grid(row=0, column=0)
    lbl_main.grid(row=0, column=1, sticky="w", padx=(8, 0))

    chk_main = ctk.CTkCheckBox(options, text="Mostrar imagen principal")
    chk_main.grid(row=8, column=0, sticky="w", padx=12)
    chk_main.select() if settings.get("main_enabled", True) else chk_main.deselect()

    def _toggle_main():
        settings["main_enabled"] = bool(chk_main.get())
        
    chk_main.configure(command=_toggle_main)

    def _add_slider(row, label, key, from_, to_, step=0.01, unit=""):
        frame = ctk.CTkFrame(options, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
        frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        entry = ctk.CTkEntry(frame, width=70)
        entry.grid(row=0, column=2, padx=(6, 0))
        slider = ctk.CTkSlider(frame, from_=from_, to=to_, number_of_steps=int((to_ - from_) / step) if step else None)
        slider.grid(row=0, column=1, sticky="ew", padx=(6, 6))
        slider.set(float(settings.get(key, from_)))
        entry.insert(0, f"{settings.get(key, from_)}")

        def _sync_from_slider(val):
            try:
                settings[key] = float(val)
                entry.delete(0, "end")
                entry.insert(0, f"{float(val):.2f}{unit}")
            except Exception:
                pass

        def _sync_from_entry(_=None):
            raw = entry.get().replace(unit, "").strip()
            try:
                value = float(raw)
                settings[key] = value
                slider.set(value)
            except Exception:
                pass

        slider.configure(command=_sync_from_slider)
        entry.bind("<FocusOut>", _sync_from_entry)
        entry.bind("<Return>", _sync_from_entry)
        slider.bind("<ButtonRelease-1>", lambda _e: _trigger_preview())
        return row + 1

    row = 9
    row = _add_slider(row, "Pos X (%)", "main_x_pct", 0.0, 1.0, 0.01)
    row = _add_slider(row, "Pos Y (%)", "main_y_pct", 0.0, 1.0, 0.01)
    row = _add_slider(row, "Escala", "main_scale", 0.5, 2.0, 0.01)
    row = _add_slider(row, "Altura (%)", "main_height_pct", 0.2, 0.9, 0.01)
    row = _add_slider(row, "Rotacion imagen", "main_rotation", 0.0, 360.0, 1.0)

    # Fuentes (carga diferida)
    fonts_container = ctk.CTkFrame(options, fg_color="transparent")
    fonts_container.grid(row=row, column=0, sticky="ew", padx=12, pady=(6, 8))
    fonts_container.grid_columnconfigure(0, weight=1)
    row += 1

    fonts_state = {"loaded": False, "refreshes": 0}

    def _build_fonts_section():
        _clear_children(fonts_container)
        row_f = 0
        ctk.CTkLabel(fonts_container, text="Fuentes", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=row_f, column=0, sticky="w", pady=(0, 6)
        )
        row_f += 1

        font_files = _get_font_files()
        font_names = [os.path.basename(p) for p in font_files] if font_files else ["arial.ttf"]

        current_bold = settings.get("font_bold") or ""
        current_regular = settings.get("font_regular") or ""

        def _select_font(default_path: str, prefer_bold: bool) -> str:
            if default_path and os.path.exists(default_path):
                return os.path.basename(default_path)
            if font_names:
                for name in font_names:
                    low = name.lower()
                    if prefer_bold and ("bd" in low or "bold" in low):
                        return name
                return font_names[0]
            return "arial.ttf"

        bold_name = _select_font(current_bold, True)
        regular_name = _select_font(current_regular, False)

        search_row = ctk.CTkFrame(fonts_container, fg_color="transparent")
        search_row.grid(row=row_f, column=0, sticky="ew", pady=(0, 6))
        search_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_row, text="Buscar fuente", font=ctk.CTkFont(size=11)).grid(
            row=0, column=0, sticky="w"
        )
        entry_font_search = ctk.CTkEntry(search_row, placeholder_text="Escribe para filtrar...")
        entry_font_search.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        row_f += 1

        ctk.CTkLabel(fonts_container, text="Font Bold", font=ctk.CTkFont(size=11)).grid(
            row=row_f, column=0, sticky="w"
        )
        row_f += 1
        bold_list = ctk.CTkScrollableFrame(fonts_container, height=120)
        bold_list.grid(row=row_f, column=0, sticky="ew", pady=(0, 6))
        row_f += 1
        bold_preview = ctk.CTkLabel(fonts_container, text="Preview Bold", font=ctk.CTkFont(size=11), text_color="#9aa4b2")
        bold_preview.grid(row=row_f, column=0, sticky="w", pady=(0, 6))
        row_f += 1
        bold_preview_img = ctk.CTkLabel(fonts_container, text="")
        bold_preview_img.grid(row=row_f, column=0, sticky="w", pady=(0, 8))
        row_f += 1

        ctk.CTkLabel(fonts_container, text="Font Regular", font=ctk.CTkFont(size=11)).grid(
            row=row_f, column=0, sticky="w"
        )
        row_f += 1
        reg_list = ctk.CTkScrollableFrame(fonts_container, height=120)
        reg_list.grid(row=row_f, column=0, sticky="ew", pady=(0, 6))
        row_f += 1
        reg_preview = ctk.CTkLabel(fonts_container, text="Preview Regular", font=ctk.CTkFont(size=11), text_color="#9aa4b2")
        reg_preview.grid(row=row_f, column=0, sticky="w", pady=(0, 6))
        row_f += 1
        reg_preview_img = ctk.CTkLabel(fonts_container, text="")
        reg_preview_img.grid(row=row_f, column=0, sticky="w", pady=(0, 8))
        row_f += 1

        bold_var = tk.StringVar(value=bold_name)
        reg_var = tk.StringVar(value=regular_name)

        lbl_bold_current = ctk.CTkLabel(fonts_container, text=f"Bold actual: {bold_name}", font=ctk.CTkFont(size=11))
        lbl_bold_current.grid(row=row_f, column=0, sticky="w", pady=(0, 6))
        row_f += 1
        lbl_reg_current = ctk.CTkLabel(fonts_container, text=f"Regular actual: {regular_name}", font=ctk.CTkFont(size=11))
        lbl_reg_current.grid(row=row_f, column=0, sticky="w", pady=(0, 6))
        row_f += 1

        def _resolve_font_path(name: str) -> str:
            for p in font_files:
                if os.path.basename(p) == name:
                    return p
            return name

        def _sync_fonts(*_):
            settings["font_bold"] = _resolve_font_path(bold_var.get())
            settings["font_regular"] = _resolve_font_path(reg_var.get())
            lbl_bold_current.configure(text=f"Bold actual: {bold_var.get()}")
            lbl_reg_current.configure(text=f"Regular actual: {reg_var.get()}")
            _trigger_preview()

        def _render_font_preview(font_name: str, target_label):
            try:
                sample = "Aa Bb 123"
                font_path = _resolve_font_path(font_name)
                from PIL import Image, ImageDraw, ImageFont, ImageTk
                img = Image.new("RGBA", (320, 48), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                try:
                    font = ImageFont.truetype(font_path, size=28)
                except Exception:
                    font = ImageFont.load_default()
                draw.text((0, 6), sample, font=font, fill="#FFFFFF")
                preview = ImageTk.PhotoImage(img)
                target_label.configure(image=preview)
                target_label.image = preview
            except Exception:
                target_label.configure(image="")
                target_label.image = None

        def _fill_font_list(frame, items, var, preview_label, active_color="#1f5f99"):
            _clear_children(frame)
            for name in items:
                def _make_cmd(n=name):
                    def _set():
                        var.set(n)
                        _fill_font_list(frame, items, var, preview_label, active_color=active_color)
                    return _set
                btn = ctk.CTkButton(frame, text=name, height=26, anchor="w", command=_make_cmd())
                if var.get() == name:
                    btn.configure(fg_color=active_color)
                btn.bind("<Enter>", lambda _e, n=name: _render_font_preview(n, preview_label))
                btn.pack(fill="x", padx=6, pady=2)
            var.trace_add("write", lambda *_: _sync_fonts())

        def _apply_font_filter(*_):
            query = entry_font_search.get().strip().lower()
            if not query:
                filtered = font_names
            else:
                filtered = [n for n in font_names if query in n.lower()]
                if not filtered:
                    filtered = font_names
            _fill_font_list(bold_list, filtered, bold_var, bold_preview_img)
            _fill_font_list(reg_list, filtered, reg_var, reg_preview_img)
            if bold_var.get() not in filtered and filtered:
                bold_var.set(filtered[0])
            if reg_var.get() not in filtered and filtered:
                reg_var.set(filtered[0])

        entry_font_search.bind("<KeyRelease>", _apply_font_filter)
        _apply_font_filter()

    def _build_fonts_placeholder():
        _clear_children(fonts_container)
        ctk.CTkLabel(fonts_container, text="Fuentes", font=ctk.CTkFont(size=13, weight="bold")).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(
            fonts_container,
            text="Cargando fuentes al entrar en la pestaña...",
            font=ctk.CTkFont(size=11),
            text_color="#9aa4b2",
        ).grid(row=1, column=0, sticky="w", pady=(2, 8))
        ctk.CTkButton(fonts_container, text="Cargar ahora", height=28, command=_ensure_fonts_loaded).grid(
            row=2, column=0, sticky="w"
        )

    def _ensure_fonts_loaded():
        if not fonts_state["loaded"]:
            _build_fonts_section()
            fonts_state["loaded"] = True
            return
        if fonts_state["refreshes"] < 1:
            _build_fonts_section()
            fonts_state["refreshes"] += 1

    _build_fonts_placeholder()


    # Texto superior
    ctk.CTkLabel(options, text="Texto superior", font=ctk.CTkFont(size=13, weight="bold")).grid(
        row=row, column=0, sticky="w", padx=12, pady=(8, 6)
    )
    row += 1
    chk_top = ctk.CTkCheckBox(options, text="Mostrar texto superior")
    chk_top.grid(row=row, column=0, sticky="w", padx=12)
    chk_top.select() if settings.get("top_enabled", True) else chk_top.deselect()

    def _toggle_top():
        settings["top_enabled"] = bool(chk_top.get())

    chk_top.configure(command=_toggle_top)
    row += 1

    entry_top_text = ctk.CTkTextbox(options, height=50)
    entry_top_text.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    entry_top_text.insert("1.0", settings.get("top_text", ""))

    def _sync_top_text(_=None):
        settings["top_text"] = entry_top_text.get("1.0", "end").strip()
        _trigger_preview()

    entry_top_text.bind("<FocusOut>", _sync_top_text)
    entry_top_text.bind("<Return>", _sync_top_text)
    row += 1

    entry_top_color = ctk.CTkEntry(options, placeholder_text="#FFFFFF")
    entry_top_bg = ctk.CTkEntry(options, placeholder_text="#E53935")
    entry_top_color.insert(0, settings.get("top_text_color", "#FFFFFF"))
    entry_top_bg.insert(0, settings.get("top_bg_color", "#E53935"))
    entry_top_color.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 4))
    row += 1
    entry_top_bg.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    row += 1

    ctk.CTkLabel(options, text="Texto superior 2", font=ctk.CTkFont(size=11)).grid(
        row=row, column=0, sticky="w", padx=12, pady=(2, 4)
    )
    row += 1
    entry_top_text2 = ctk.CTkTextbox(options, height=46)
    entry_top_text2.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    entry_top_text2.insert("1.0", settings.get("top_text_2", ""))
    row += 1

    entry_top2_color = ctk.CTkEntry(options, placeholder_text="#FFE9B3")
    entry_top2_bg = ctk.CTkEntry(options, placeholder_text="#E53935")
    entry_top2_color.insert(0, settings.get("top2_text_color", "#FFE9B3"))
    entry_top2_bg.insert(0, settings.get("top2_bg_color", "#E53935"))
    entry_top2_color.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 4))
    row += 1
    entry_top2_bg.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    row += 1

    row = _add_slider(row, "Separacion badges (%)", "top_gap_pct", 0.0, 0.2, 0.005)
    row = _add_slider(row, "Rotacion badge 1", "top_rotation", 0.0, 360.0, 1.0)
    row = _add_slider(row, "Rotacion badge 2", "top2_rotation", 0.0, 360.0, 1.0)

    def _sync_top_colors(_=None):
        settings["top_text_color"] = entry_top_color.get().strip()
        settings["top_bg_color"] = entry_top_bg.get().strip()
        settings["top2_text_color"] = entry_top2_color.get().strip()
        settings["top2_bg_color"] = entry_top2_bg.get().strip()
        _trigger_preview()

    entry_top_color.bind("<FocusOut>", _sync_top_colors)
    entry_top_bg.bind("<FocusOut>", _sync_top_colors)
    entry_top2_color.bind("<FocusOut>", _sync_top_colors)
    entry_top2_bg.bind("<FocusOut>", _sync_top_colors)

    def _pick_color(entry):
        initial = entry.get().strip() or "#FFFFFF"
        try:
            _, hex_color = colorchooser.askcolor(color=initial, parent=parent)
        except Exception:
            hex_color = None
        if hex_color:
            entry.delete(0, "end")
            entry.insert(0, hex_color)
            _sync_top_colors()

    
    def _sync_top_text2(_=None):
        settings["top_text_2"] = entry_top_text2.get("1.0", "end").strip()
        _trigger_preview()

    entry_top_text2.bind("<FocusOut>", _sync_top_text2)
    entry_top_text2.bind("<Return>", _sync_top_text2)

    row = _add_slider(row, "Top font size", "top_font_size", 20, 140, 1)
    row = _add_slider(row, "Top Y (%)", "top_y_pct", 0.0, 0.3, 0.01)

    # Titulo
    ctk.CTkLabel(options, text="Titulo", font=ctk.CTkFont(size=13, weight="bold")).grid(
        row=row, column=0, sticky="w", padx=12, pady=(8, 6)
    )
    row += 1
    chk_title = ctk.CTkCheckBox(options, text="Mostrar titulo")
    chk_title.grid(row=row, column=0, sticky="w", padx=12)
    chk_title.select() if settings.get("title_enabled", True) else chk_title.deselect()

    def _toggle_title():
        settings["title_enabled"] = bool(chk_title.get())
        
    chk_title.configure(command=_toggle_title)
    row += 1

    entry_title = ctk.CTkTextbox(options, height=70)
    entry_title.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    entry_title.insert("1.0", settings.get("title_text", ""))

    def _sync_title(_=None):
        settings["title_text"] = entry_title.get("1.0", "end").strip()
        _trigger_preview()
        
    entry_title.bind("<FocusOut>", _sync_title)
    entry_title.bind("<Return>", _sync_title)
    row += 1

    entry_title_color = ctk.CTkEntry(options, placeholder_text="#FFFFFF")
    entry_title_color.insert(0, settings.get("title_color", "#FFFFFF"))
    entry_title_color.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    row += 1

    def _sync_title_color(_=None):
        settings["title_color"] = entry_title_color.get().strip()
        _trigger_preview()
        
    entry_title_color.bind("<FocusOut>", _sync_title_color)
    ctk.CTkButton(options, text="Color titulo", height=26, command=lambda: _pick_color(entry_title_color)).grid(
        row=row, column=0, sticky="w", padx=12, pady=(0, 6)
    )
    row += 1

    row = _add_slider(row, "Title font size", "title_font_size", 20, 160, 1)
    row = _add_slider(row, "Title Y (%)", "title_y_pct", 0.2, 0.9, 0.01)
    row = _add_slider(row, "Rotacion titulo", "title_rotation", 0.0, 360.0, 1.0)

    # Nombre
    ctk.CTkLabel(options, text="Nombre", font=ctk.CTkFont(size=13, weight="bold")).grid(
        row=row, column=0, sticky="w", padx=12, pady=(8, 6)
    )
    row += 1
    chk_name = ctk.CTkCheckBox(options, text="Mostrar nombre")
    chk_name.grid(row=row, column=0, sticky="w", padx=12)
    chk_name.select() if settings.get("name_enabled", True) else chk_name.deselect()

    def _toggle_name():
        settings["name_enabled"] = bool(chk_name.get())
        
    chk_name.configure(command=_toggle_name)
    row += 1

    entry_name_text = ctk.CTkTextbox(options, height=60)
    entry_name_text.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    entry_name_text.insert("1.0", settings.get("name_text", ""))

    def _sync_name(_=None):
        settings["name_text"] = entry_name_text.get("1.0", "end").strip()
        _trigger_preview()
        
    entry_name_text.bind("<FocusOut>", _sync_name)
    entry_name_text.bind("<Return>", _sync_name)
    row += 1

    entry_name_color = ctk.CTkEntry(options, placeholder_text="#FFFFFF")
    entry_name_color.insert(0, settings.get("name_color", "#FFFFFF"))
    entry_name_color.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    row += 1

    color_row = ctk.CTkFrame(options, fg_color="transparent")
    color_row.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    color_row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(color_row, text="Picker", font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")

    color_targets = [
        ("Top texto", entry_top_color),
        ("Top fondo", entry_top_bg),
        ("Top2 texto", entry_top2_color),
        ("Top2 fondo", entry_top2_bg),
        ("Titulo", entry_title_color),
        ("Nombre", entry_name_color),
    ]
    color_target_names = [name for name, _entry in color_targets]
    color_target_var = tk.StringVar(value=color_target_names[0])
    color_menu = ctk.CTkOptionMenu(color_row, values=color_target_names, variable=color_target_var)
    color_menu.grid(row=0, column=1, sticky="ew", padx=(6, 6))

    def _pick_selected_color():
        name = color_target_var.get()
        entry = next((e for n, e in color_targets if n == name), None)
        if entry is None:
            return
        _pick_color(entry)

    ctk.CTkButton(color_row, text="Elegir color", width=120, command=_pick_selected_color).grid(row=0, column=2)
    row += 1

    def _sync_name_color(_=None):
        settings["name_color"] = entry_name_color.get().strip()
        _trigger_preview()
        
    entry_name_color.bind("<FocusOut>", _sync_name_color)
    ctk.CTkButton(options, text="Color nombre", height=26, command=lambda: _pick_color(entry_name_color)).grid(
        row=row, column=0, sticky="w", padx=12, pady=(0, 6)
    )
    row += 1

    row = _add_slider(row, "Name font size", "name_font_size", 20, 120, 1)
    row = _add_slider(row, "Name Y (%)", "name_y_pct", 0.3, 0.95, 0.01)
    row = _add_slider(row, "Rotacion nombre", "name_rotation", 0.0, 360.0, 1.0)

    # Logo
    ctk.CTkLabel(options, text="Logo", font=ctk.CTkFont(size=13, weight="bold")).grid(
        row=row, column=0, sticky="w", padx=12, pady=(8, 6)
    )
    row += 1
    logo_row = ctk.CTkFrame(options, fg_color="transparent")
    logo_row.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 6))
    logo_row.grid_columnconfigure(1, weight=1)
    lbl_logo = ctk.CTkLabel(logo_row, text=os.path.basename(settings.get("logo_path", "")) or "(sin logo)")

    def _select_logo():
        from ui.dialogs import seleccionar_imagen
        path = seleccionar_imagen()
        if path:
            settings["logo_path"] = path
            lbl_logo.configure(text=os.path.basename(path))
            
    ctk.CTkButton(logo_row, text="Seleccionar", width=120, command=_select_logo).grid(row=0, column=0)
    lbl_logo.grid(row=0, column=1, sticky="w", padx=(8, 0))
    row += 1

    chk_logo = ctk.CTkCheckBox(options, text="Mostrar logo")
    chk_logo.grid(row=row, column=0, sticky="w", padx=12)
    chk_logo.select() if settings.get("logo_enabled", True) else chk_logo.deselect()

    def _toggle_logo():
        settings["logo_enabled"] = bool(chk_logo.get())
        
    chk_logo.configure(command=_toggle_logo)
    row += 1

    row = _add_slider(row, "Logo X (%)", "logo_x_pct", 0.0, 1.0, 0.01)
    row = _add_slider(row, "Logo Y (%)", "logo_y_pct", 0.0, 1.0, 0.01)
    row = _add_slider(row, "Logo escala", "logo_scale", 0.5, 2.0, 0.01)
    row = _add_slider(row, "Logo ancho (%)", "logo_width_pct", 0.05, 0.5, 0.01)
    row = _add_slider(row, "Rotacion logo", "logo_rotation", 0.0, 360.0, 1.0)

    # Inicializar preset
    _apply_preset(int(settings.get("preset_index", 0)))

    ui_ready["value"] = True

    return {
        "ensure_fonts_loaded": _ensure_fonts_loaded,
    }


def _build_ai_tab(parent, state, log, vert_settings, horz_settings):
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    scroll = ctk.CTkScrollableFrame(parent, corner_radius=10)
    scroll.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
    scroll.grid_columnconfigure(0, weight=1)

    header = ctk.CTkFrame(scroll, fg_color="transparent")
    header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
    header.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(header, text="ImagenIA (OpenAI)", font=ctk.CTkFont(size=16, weight="bold")).grid(
        row=0, column=0, sticky="w"
    )
    ctk.CTkLabel(
        header,
        text="Genera backgrounds desde texto.",
        text_color="gray",
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    body = ctk.CTkFrame(scroll, fg_color="transparent")
    body.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
    body.grid_columnconfigure(0, weight=2)
    body.grid_columnconfigure(1, weight=3)
    body.grid_rowconfigure(2, weight=1)

    ctk.CTkLabel(body, text="Prompt:", font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w")
    txt_prompt = ctk.CTkTextbox(body, height=120)
    txt_prompt.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(6, 8))

    right = ctk.CTkFrame(body)
    right.grid(row=0, column=1, rowspan=3, sticky="nsew")
    right.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(right, text="Opciones", font=ctk.CTkFont(size=14, weight="bold")).grid(
        row=0, column=0, sticky="w", padx=12, pady=(10, 6)
    )

    size_row = ctk.CTkFrame(right, fg_color="transparent")
    size_row.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
    ctk.CTkLabel(size_row, text="Tamaño:", font=ctk.CTkFont(size=11)).pack(side="left")
    size_var = tk.StringVar(value="1024x1536")
    size_menu = ctk.CTkOptionMenu(
        size_row,
        values=["1024x1536", "1536x1024", "1024x1024"],
        variable=size_var,
        width=140,
    )
    size_menu.pack(side="left", padx=(8, 0))

    quality_row = ctk.CTkFrame(right, fg_color="transparent")
    quality_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))
    ctk.CTkLabel(quality_row, text="Calidad:", font=ctk.CTkFont(size=11)).pack(side="left")
    quality_var = tk.StringVar(value="medium")
    quality_menu = ctk.CTkOptionMenu(
        quality_row,
        values=["low", "medium", "high"],
        variable=quality_var,
        width=140,
    )
    quality_menu.pack(side="left", padx=(8, 0))

    assign_row = ctk.CTkFrame(right, fg_color="transparent")
    assign_row.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 6))
    ctk.CTkLabel(assign_row, text="Asignar fondo:", font=ctk.CTkFont(size=11)).pack(side="left")
    assign_var = tk.StringVar(value="Ninguno")
    assign_menu = ctk.CTkOptionMenu(
        assign_row,
        values=["Ninguno", "Vertical", "Horizontal", "Ambos"],
        variable=assign_var,
        width=140,
    )
    assign_menu.pack(side="left", padx=(8, 0))

    name_row = ctk.CTkFrame(right, fg_color="transparent")
    name_row.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 8))
    ctk.CTkLabel(name_row, text="Nombre (opcional):", font=ctk.CTkFont(size=11)).pack(side="left")
    entry_name = ctk.CTkEntry(name_row, width=180, placeholder_text="ai_bg")
    entry_name.pack(side="left", padx=(8, 0), fill="x", expand=True)

    preview_card = ctk.CTkFrame(right)
    preview_card.grid(row=5, column=0, sticky="nsew", padx=12, pady=(0, 8))
    preview_card.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(preview_card, text="Preview", font=ctk.CTkFont(size=12, weight="bold")).grid(
        row=0, column=0, sticky="w", padx=8, pady=(8, 4)
    )
    preview_lbl = tk.Label(preview_card, text="(sin preview)", bg="#1a1d24", fg="#cbd5e1")
    preview_lbl.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
    preview_state = {"img": None, "path": ""}

    log_card, _log_widget, log_local = helpers.create_log_panel(
        right,
        title="Actividad IA",
        height=160,
    )
    log_card.grid(row=6, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _update_preview(img_path: str):
        try:
            img = Image.open(img_path)
            img.thumbnail((360, 360))
            tk_img = ImageTk.PhotoImage(img)
            preview_lbl.configure(image=tk_img, text="")
            preview_lbl.image = tk_img
            preview_state["img"] = tk_img
            preview_state["path"] = img_path
        except Exception as exc:
            log_local(f"Error preview: {exc}")

    def _assign_background(path: str):
        opt = assign_var.get()
        if opt == "Vertical":
            vert_settings["background_path"] = path
            log_local("Fondo asignado a Imagen vertical.")
        elif opt == "Horizontal":
            horz_settings["background_path"] = path
            log_local("Fondo asignado a Imagen horizontal.")
        elif opt == "Ambos":
            vert_settings["background_path"] = path
            horz_settings["background_path"] = path
            log_local("Fondo asignado a Vertical y Horizontal.")

    def _run_generate():
        prompt = txt_prompt.get("1.0", "end").strip()
        if not prompt:
            log_local("Escribe un prompt primero.")
            return
        base = entry_name.get().strip() or f"ai_bg_{int(time.time())}"
        out_dir = os.path.join("output", "imagenes_creator", "ai")
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, f"{base}.jpg")
        try:
            generar_background_openai(
                prompt=prompt,
                output_path=output_path,
                size=size_var.get(),
                quality=quality_var.get(),
                log_fn=log_local,
            )
            _update_preview(output_path)
            _assign_background(output_path)
            state["ai_last_path"] = output_path
        except Exception as exc:
            log_local(f"Error IA: {exc}")

    btn_generate = ctk.CTkButton(right, text="Generar background", height=36)
    btn_generate.grid(row=7, column=0, sticky="ew", padx=12, pady=(0, 12))
    btn_generate.configure(command=lambda: threading.Thread(target=_run_generate, daemon=True).start())
