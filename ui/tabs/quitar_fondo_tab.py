import customtkinter as ctk

from ui.tabs.quitar_fondo.video import tab as video_tab
from ui.tabs.quitar_fondo.imagen import tab as imagen_tab


def create_tab(parent, context):
    parent.grid_columnconfigure(0, weight=1)
    parent.grid_rowconfigure(0, weight=1)

    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(1, weight=1)

    title = ctk.CTkLabel(container, text="Transparentar", font=ctk.CTkFont(size=16, weight="bold"))
    title.grid(row=0, column=0, sticky="w", padx=6, pady=(0, 8))

    tabview = ctk.CTkTabview(container)
    tabview.grid(row=1, column=0, sticky="nsew")
    tabview.add("Video")
    tabview.add("Imagen")

    video_tab.create_tab(tabview.tab("Video"), context)
    imagen_tab.create_tab(tabview.tab("Imagen"), context)
