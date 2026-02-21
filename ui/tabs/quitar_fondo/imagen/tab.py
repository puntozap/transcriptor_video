import os
import customtkinter as ctk
from tkinter import filedialog

from core.utils import transparentar_imagen_ffmpeg


def create_tab(parent, context):
    log = context.get("log")

    parent.grid_columnconfigure(0, weight=1)

    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
    row.grid_columnconfigure(0, weight=1)

    path_var = ctk.StringVar(value="")
    entry = ctk.CTkEntry(row, textvariable=path_var, placeholder_text="Selecciona una imagen")
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

    def _browse():
        f = filedialog.askopenfilename(filetypes=[("Imagen", "*.png;*.jpg;*.jpeg;*.webp")])
        if f:
            path_var.set(f)
            if log:
                log(f"Imagen seleccionada: {f}")

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
        text="Salida en PNG con alpha. Funciona mejor con fondo uniforme (blanco/verde).",
        text_color="#9aa4b2",
        font=ctk.CTkFont(size=11),
    )
    note.grid(row=4, column=0, sticky="w", padx=14, pady=(0, 10))

    def _run():
        src = path_var.get().strip()
        if not src or not os.path.exists(src):
            if log:
                log("Selecciona una imagen valida.")
            return
        base, _ext = os.path.splitext(src)
        out_path = f"{base}_transparent.png"
        try:
            transparentar_imagen_ffmpeg(
                src,
                out_path,
                color=color_var.get().strip(),
                similarity=float(sim_var.get()),
                blend=float(blend_var.get()),
                log_fn=log,
            )
            if log:
                log(f"OK: Imagen transparentada: {out_path}")
        except Exception as e:
            if log:
                log(f"Error transparentando imagen: {e}")

    ctk.CTkButton(parent, text="Transparentar imagen", command=_run).grid(
        row=5, column=0, sticky="w", padx=14, pady=(0, 12)
    )
