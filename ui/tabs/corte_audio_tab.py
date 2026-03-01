import os
import threading
import customtkinter as ctk
import tkinter as tk

from core.utils import obtener_duracion_segundos, dividir_audio_ffmpeg, output_base_dir, next_correlative_dir


def create_tab(parent, context):
    estado = context["estado"]
    log = context["log"]
    log_seccion = context["log_seccion"]
    alerta_busy = context["alerta_busy"]
    stop_control = context["stop_control"]
    beep_fin = context.get("beep_fin")

    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    scroll = ctk.CTkScrollableFrame(parent, corner_radius=0)
    scroll.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
    scroll.grid_columnconfigure(0, weight=1)

    card = ctk.CTkFrame(scroll, corner_radius=12)
    card.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
    card.grid_columnconfigure(0, weight=1)

    lbl_title = ctk.CTkLabel(card, text="Corte de audio", font=ctk.CTkFont(size=18, weight="bold"))
    lbl_title.grid(row=0, column=0, sticky="w", padx=14, pady=(12, 4))
    lbl_sub = ctk.CTkLabel(
        card,
        text="Sube un audio, corta por rango y/o divide en partes iguales.",
        font=ctk.CTkFont(size=12),
    )
    lbl_sub.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 10))

    audio_path_var = tk.StringVar(value=estado.get("audio_corte_path", ""))
    duracion_var = tk.StringVar(value="00:00")
    inicio_var = tk.StringVar(value=estado.get("audio_corte_inicio", "00:00"))
    fin_var = tk.StringVar(value=estado.get("audio_corte_fin", ""))
    partes_var = tk.StringVar(value=str(estado.get("audio_corte_partes", "5")))
    por_parte_var = tk.StringVar(value="00:00")
    duration_state = {"value": 0.0}
    slider_programmatic = {"value": False}

    def format_mmss(seconds: float) -> str:
        seconds = max(0.0, float(seconds))
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def parse_mmss(value: str, allow_empty: bool = False):
        text = (value or "").strip()
        if not text:
            return None if allow_empty else 0.0
        if ":" not in text:
            raise ValueError("Formato mm:ss")
        parts = text.split(":")
        if len(parts) != 2:
            raise ValueError("Formato mm:ss")
        min_part, sec_part = parts
        minutes = int(min_part.strip())
        seconds = float(sec_part.strip().replace(",", "."))
        if minutes < 0 or seconds < 0 or seconds >= 60:
            raise ValueError("Tiempo invalido")
        return minutes * 60 + seconds

    def _update_duracion():
        path = audio_path_var.get().strip()
        if not path or not os.path.exists(path):
            duracion_var.set("00:00")
            por_parte_var.set("00:00")
            duration_state["value"] = 0.0
            return
        try:
            dur = float(obtener_duracion_segundos(path))
        except Exception:
            duracion_var.set("00:00")
            por_parte_var.set("00:00")
            duration_state["value"] = 0.0
            return
        duration_state["value"] = dur
        duracion_var.set(format_mmss(dur))
        _set_slider_range(dur)
        _sync_sliders_from_entries()
        _update_por_parte()

    def _update_por_parte():
        path = audio_path_var.get().strip()
        if not path or not os.path.exists(path):
            por_parte_var.set("00:00")
            return
        try:
            dur = float(obtener_duracion_segundos(path))
        except Exception:
            por_parte_var.set("00:00")
            return
        try:
            start = parse_mmss(inicio_var.get(), allow_empty=True)
            end = parse_mmss(fin_var.get(), allow_empty=True)
        except Exception:
            por_parte_var.set("00:00")
            return
        if start is None:
            start = 0.0
        if end is None or end <= 0:
            end = dur
        start = max(0.0, min(start, dur))
        end = max(0.0, min(end, dur))
        if end <= start:
            por_parte_var.set("00:00")
            return
        try:
            partes = int(float(partes_var.get().strip().replace(",", ".")))
        except Exception:
            partes = 0
        if partes <= 0:
            por_parte_var.set("00:00")
            return
        por_parte_var.set(format_mmss((end - start) / partes))

    def _set_slider_range(dur: float):
        slider_inicio.configure(from_=0, to=dur)
        slider_fin.configure(from_=0, to=dur)

    def _set_slider_values(start: float, end: float):
        slider_programmatic["value"] = True
        try:
            slider_inicio.set(start)
            slider_fin.set(end)
            lbl_inicio_val.configure(text=format_mmss(start))
            lbl_fin_val.configure(text=format_mmss(end))
        finally:
            slider_programmatic["value"] = False

    def _sync_sliders_from_entries():
        if slider_programmatic["value"]:
            return
        dur = duration_state["value"]
        if dur <= 0:
            return
        try:
            start = parse_mmss(inicio_var.get(), allow_empty=True)
            end = parse_mmss(fin_var.get(), allow_empty=True)
        except Exception:
            return
        if start is None:
            start = 0.0
        if end is None or end <= 0:
            end = dur
        start = max(0.0, min(start, dur))
        end = max(0.0, min(end, dur))
        if end <= start:
            return
        _set_slider_values(start, end)

    def _seleccionar_audio():
        from ui.dialogs import seleccionar_archivo
        path = seleccionar_archivo("Seleccionar audio", [("Audio", "*.mp3;*.wav;*.m4a;*.aac;*.ogg")])
        if not path:
            return
        audio_path_var.set(path)
        estado["audio_corte_path"] = path
        log(f"Audio seleccionado: {path}")
        _update_duracion()

    def _get_range_seconds():
        path = audio_path_var.get().strip()
        if not path or not os.path.exists(path):
            raise ValueError("Selecciona un audio primero.")
        dur = float(obtener_duracion_segundos(path))
        start = parse_mmss(inicio_var.get(), allow_empty=True)
        end = parse_mmss(fin_var.get(), allow_empty=True)
        if start is None:
            start = 0.0
        if end is None or end <= 0:
            end = dur
        start = max(0.0, min(start, dur))
        end = max(0.0, min(end, dur))
        if end <= start:
            raise ValueError("Rango invalido: fin debe ser mayor a inicio.")
        return start, end, dur

    def _cortar_rango():
        if stop_control.is_busy():
            alerta_busy()
            return
        stop_control.clear_stop()
        stop_control.set_busy(True)

        def _run():
            try:
                log_seccion("Corte de audio")
                start, end, _dur = _get_range_seconds()
                path = audio_path_var.get().strip()
                out_dir = next_correlative_dir(output_base_dir(path), "audios", "audio-corte")
                log(f"Rango: {format_mmss(start)} - {format_mmss(end)}")
                partes_audio = dividir_audio_ffmpeg(
                    path,
                    segundos_por_parte=(end - start),
                    out_dir=out_dir,
                    total_partes=1,
                    start_sec=start,
                    end_sec=end,
                    log_fn=log,
                )
                if partes_audio:
                    log(f"Corte listo: {partes_audio[0]}")
                log(f"Carpeta: {out_dir}")
                if beep_fin:
                    beep_fin()
            except Exception as exc:
                log(f"Error al cortar audio: {exc}")
            finally:
                stop_control.set_busy(False)

        threading.Thread(target=_run, daemon=True).start()

    def _dividir_partes():
        if stop_control.is_busy():
            alerta_busy()
            return
        stop_control.clear_stop()
        stop_control.set_busy(True)

        def _run():
            try:
                log_seccion("Corte de audio")
                start, end, _dur = _get_range_seconds()
                try:
                    partes = int(float(partes_var.get().strip().replace(",", ".")))
                except Exception:
                    partes = 0
                if partes <= 0:
                    log("Partes invalidas. Usa un numero mayor a 0.")
                    return
                path = audio_path_var.get().strip()
                out_dir = next_correlative_dir(output_base_dir(path), "audios", "audio-partes")
                log(f"Rango: {format_mmss(start)} - {format_mmss(end)}")
                log(f"Dividiendo en {partes} partes...")
                partes_audio = dividir_audio_ffmpeg(
                    path,
                    segundos_por_parte=((end - start) / partes),
                    out_dir=out_dir,
                    total_partes=partes,
                    start_sec=start,
                    end_sec=end,
                    log_fn=log,
                )
                log(f"Partes generadas: {len(partes_audio)}")
                log(f"Carpeta: {out_dir}")
                if beep_fin:
                    beep_fin()
            except Exception as exc:
                log(f"Error al dividir audio: {exc}")
            finally:
                stop_control.set_busy(False)

        threading.Thread(target=_run, daemon=True).start()

    file_row = ctk.CTkFrame(card, fg_color="transparent")
    file_row.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
    file_row.grid_columnconfigure(1, weight=1)

    btn_audio = ctk.CTkButton(file_row, text="Seleccionar audio", command=_seleccionar_audio, height=32, width=160)
    btn_audio.grid(row=0, column=0, sticky="w")

    lbl_audio = ctk.CTkLabel(
        file_row,
        text=os.path.basename(audio_path_var.get()) if audio_path_var.get() else "(sin audio)",
        font=ctk.CTkFont(size=12),
    )
    lbl_audio.grid(row=0, column=1, sticky="w", padx=(8, 0))

    def _refresh_audio_label(*_):
        lbl_audio.configure(text=os.path.basename(audio_path_var.get()) if audio_path_var.get() else "(sin audio)")
        _update_duracion()

    audio_path_var.trace_add("write", _refresh_audio_label)

    dur_row = ctk.CTkFrame(card, fg_color="transparent")
    dur_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
    dur_row.grid_columnconfigure(1, weight=1)

    lbl_dur = ctk.CTkLabel(dur_row, text="Duracion total", font=ctk.CTkFont(size=12))
    lbl_dur.grid(row=0, column=0, sticky="w")
    lbl_dur_val = ctk.CTkLabel(dur_row, textvariable=duracion_var, font=ctk.CTkFont(size=12))
    lbl_dur_val.grid(row=0, column=1, sticky="e")

    rango_card = ctk.CTkFrame(card, corner_radius=10)
    rango_card.grid(row=4, column=0, sticky="ew", padx=14, pady=(0, 12))
    rango_card.grid_columnconfigure(1, weight=1)
    rango_card.grid_columnconfigure(3, weight=1)

    lbl_rango = ctk.CTkLabel(rango_card, text="Rango (mm:ss)", font=ctk.CTkFont(size=12, weight="bold"))
    lbl_rango.grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(8, 4))

    lbl_inicio = ctk.CTkLabel(rango_card, text="Inicio", font=ctk.CTkFont(size=12))
    lbl_inicio.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
    entry_inicio = ctk.CTkEntry(rango_card, width=120, textvariable=inicio_var, placeholder_text="mm:ss")
    entry_inicio.grid(row=1, column=1, sticky="w", pady=(0, 8))

    lbl_fin = ctk.CTkLabel(rango_card, text="Fin", font=ctk.CTkFont(size=12))
    lbl_fin.grid(row=1, column=2, sticky="w", padx=(16, 0), pady=(0, 8))
    entry_fin = ctk.CTkEntry(rango_card, width=120, textvariable=fin_var, placeholder_text="mm:ss (opcional)")
    entry_fin.grid(row=1, column=3, sticky="w", pady=(0, 8))

    lbl_inicio_val = ctk.CTkLabel(rango_card, text="00:00", font=ctk.CTkFont(size=11))
    lbl_inicio_val.grid(row=2, column=1, sticky="w", pady=(0, 6))
    lbl_fin_val = ctk.CTkLabel(rango_card, text="00:00", font=ctk.CTkFont(size=11))
    lbl_fin_val.grid(row=2, column=3, sticky="w", pady=(0, 6))

    slider_inicio = ctk.CTkSlider(
        rango_card,
        from_=0,
        to=1,
        command=lambda value: _on_slider_change("inicio", value),
    )
    slider_inicio.grid(row=3, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 6))

    slider_fin = ctk.CTkSlider(
        rango_card,
        from_=0,
        to=1,
        command=lambda value: _on_slider_change("fin", value),
    )
    slider_fin.grid(row=4, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 6))

    hint = ctk.CTkLabel(
        rango_card,
        text="Si no colocas fin, se usa la duracion completa.",
        font=ctk.CTkFont(size=11),
        text_color="#9aa4b2",
    )
    hint.grid(row=5, column=0, columnspan=4, sticky="w", padx=10, pady=(0, 8))

    parts_card = ctk.CTkFrame(card, corner_radius=10)
    parts_card.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 12))
    parts_card.grid_columnconfigure(1, weight=1)

    lbl_parts = ctk.CTkLabel(parts_card, text="Dividir en partes", font=ctk.CTkFont(size=12, weight="bold"))
    lbl_parts.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(8, 4))

    row_parts = ctk.CTkFrame(parts_card, fg_color="transparent")
    row_parts.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
    row_parts.grid_columnconfigure(1, weight=1)

    lbl_partes = ctk.CTkLabel(row_parts, text="Partes", font=ctk.CTkFont(size=12))
    lbl_partes.grid(row=0, column=0, sticky="w")
    entry_partes = ctk.CTkEntry(row_parts, width=80, textvariable=partes_var)
    entry_partes.grid(row=0, column=1, sticky="w", padx=(6, 0))

    row_pp = ctk.CTkFrame(parts_card, fg_color="transparent")
    row_pp.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 8))
    row_pp.grid_columnconfigure(1, weight=1)

    lbl_pp = ctk.CTkLabel(row_pp, text="Duracion por parte", font=ctk.CTkFont(size=11))
    lbl_pp.grid(row=0, column=0, sticky="w")
    lbl_pp_val = ctk.CTkLabel(row_pp, textvariable=por_parte_var, font=ctk.CTkFont(size=11))
    lbl_pp_val.grid(row=0, column=1, sticky="e")

    btn_row = ctk.CTkFrame(card, fg_color="transparent")
    btn_row.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 12))
    btn_row.grid_columnconfigure(0, weight=1)
    btn_row.grid_columnconfigure(1, weight=1)

    btn_cortar = ctk.CTkButton(btn_row, text="Cortar rango", command=_cortar_rango, height=40)
    btn_cortar.grid(row=0, column=0, sticky="ew", padx=(0, 6))

    btn_dividir = ctk.CTkButton(btn_row, text="Dividir en partes", command=_dividir_partes, height=40)
    btn_dividir.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _on_slider_change(which: str, value: float):
        if slider_programmatic["value"]:
            return
        dur = duration_state["value"]
        if dur <= 0:
            return
        value = max(0.0, min(float(value), dur))
        if which == "inicio":
            if value > slider_fin.get():
                slider_fin.set(value)
            inicio_var.set(format_mmss(value))
        else:
            if value < slider_inicio.get():
                slider_inicio.set(value)
            fin_var.set(format_mmss(value))
        _set_slider_values(slider_inicio.get(), slider_fin.get())
        _update_por_parte()

    def _on_entry_change(*_):
        _sync_sliders_from_entries()
        _update_por_parte()

    inicio_var.trace_add("write", _on_entry_change)
    fin_var.trace_add("write", _on_entry_change)
    partes_var.trace_add("write", lambda *_: _update_por_parte())

    _refresh_audio_label()
    _set_slider_values(0.0, 0.0)

    return {}
