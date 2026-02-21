import os
import threading
import customtkinter as ctk
from tkinter import filedialog

from core.utils import transparentar_video_ffmpeg, output_base_dir


def create_tab(parent, context):
    log = context.get("log")

    parent.grid_columnconfigure(0, weight=1)

    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
    row.grid_columnconfigure(0, weight=1)

    path_var = ctk.StringVar(value="")
    entry = ctk.CTkEntry(row, textvariable=path_var, placeholder_text="Selecciona un video")
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def _browse():
        f = filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.mov;*.mkv;*.avi;*.webm")])
        if f:
            path_var.set(f)
            if log:
                log(f"Video seleccionado: {f}")

    ctk.CTkButton(row, text="Examinar", width=110, command=_browse).grid(row=0, column=1)

    color_row = ctk.CTkFrame(parent, fg_color="transparent")
    color_row.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))
    ctk.CTkLabel(color_row, text="Color a quitar (hex):").pack(side="left")
    color_var = ctk.StringVar(value="#FFFFFF")
    ctk.CTkEntry(color_row, width=110, textvariable=color_var).pack(side="left", padx=(8, 0))

    sim_row = ctk.CTkFrame(parent, fg_color="transparent")
    sim_row.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))
    sim_row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(sim_row, text="Similarity:").grid(row=0, column=0, sticky="w")
    sim_var = ctk.DoubleVar(value=0.10)
    sim_val = ctk.CTkLabel(sim_row, text="0.10")
    sim_val.grid(row=0, column=2, sticky="e")

    def _on_sim(v):
        sim_val.configure(text=f"{float(v):.2f}")

    ctk.CTkSlider(sim_row, from_=0.0, to=1.0, number_of_steps=100, variable=sim_var, command=_on_sim).grid(
        row=0, column=1, sticky="ew", padx=10
    )

    blend_row = ctk.CTkFrame(parent, fg_color="transparent")
    blend_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
    blend_row.grid_columnconfigure(1, weight=1)
    ctk.CTkLabel(blend_row, text="Blend:").grid(row=0, column=0, sticky="w")
    blend_var = ctk.DoubleVar(value=0.0)
    blend_val = ctk.CTkLabel(blend_row, text="0.00")
    blend_val.grid(row=0, column=2, sticky="e")

    def _on_blend(v):
        blend_val.configure(text=f"{float(v):.2f}")

    ctk.CTkSlider(blend_row, from_=0.0, to=1.0, number_of_steps=100, variable=blend_var, command=_on_blend).grid(
        row=0, column=1, sticky="ew", padx=10
    )

    note = ctk.CTkLabel(
        parent,
        text="Salida en .mov con alpha. Funciona mejor con fondo uniforme (blanco/verde).",
        text_color="#9aa4b2",
        font=ctk.CTkFont(size=11),
    )
    note.grid(row=4, column=0, sticky="w", padx=14, pady=(0, 10))

    chunk_row = ctk.CTkFrame(parent, fg_color="transparent")
    chunk_row.grid(row=5, column=0, sticky="w", padx=14, pady=(0, 8))
    chunk_enabled = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(chunk_row, text="Procesar por partes", variable=chunk_enabled).pack(side="left")
    ctk.CTkLabel(chunk_row, text="Segundos por parte:", font=ctk.CTkFont(size=12)).pack(side="left", padx=(12, 4))
    chunk_var = ctk.StringVar(value="10")
    ctk.CTkEntry(chunk_row, width=70, textvariable=chunk_var).pack(side="left")

    def _run():
        src = path_var.get().strip()
        if not src or not os.path.exists(src):
            if log:
                log("Selecciona un video valido.")
            return
        base_dir = output_base_dir(src)
        os.makedirs(base_dir, exist_ok=True)
        out_path = os.path.join(base_dir, "transparentar.mov")
        chunk_seconds = None
        if chunk_enabled.get():
            try:
                chunk_seconds = float(chunk_var.get().strip())
            except Exception:
                chunk_seconds = None
        try:
            transparentar_video_ffmpeg(
                src,
                out_path,
                color=color_var.get().strip(),
                similarity=float(sim_var.get()),
                blend=float(blend_var.get()),
                chunk_seconds=chunk_seconds,
                log_fn=log,
            )
            if log:
                log(f"OK: Video transparentado: {out_path}")
        except Exception as e:
            if log:
                log(f"Error transparentando video: {e}")

    def _start():
        threading.Thread(target=_run, daemon=True).start()

    ctk.CTkButton(parent, text="Transparentar video", command=_start).grid(
        row=6, column=0, sticky="w", padx=14, pady=(0, 12)
    )
