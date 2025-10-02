import threading
import customtkinter as ctk
from tkinter.scrolledtext import ScrolledText
from ui.dialogs import seleccionar_video, mostrar_info, mostrar_error
from core.extractor import extraer_audio
from core.transcriber import transcribir
from core.utils import limpiar_temp, asegurar_dir, nombre_salida_por_video, dividir_audio_ffmpeg

def iniciar_app():
    # Configuración global
    ctk.set_appearance_mode("dark")   # "light" | "dark" | "system"
    ctk.set_default_color_theme("blue")

    def log(msg):
        txt_logs.config(state="normal")
        txt_logs.insert("end", msg + "\n")
        txt_logs.see("end")
        txt_logs.config(state="disabled")

    def deshabilitar_ui(flag=True):
        if flag:
            btn_seleccionar.configure(state="disabled")
        else:
            btn_seleccionar.configure(state="normal")

    def procesar_en_thread(video_path):
        try:
            log(f"📁 Video seleccionado: {video_path}")
            log("🎧 Extrayendo audio...")
            audio_path = extraer_audio(video_path)
            log(f"✔ Audio temporal: {audio_path}")

            # 🔥 Dividir en 5 fragmentos
            log("✂️ Dividiendo audio en 5 partes con ffmpeg...")
            partes = dividir_audio_ffmpeg(audio_path, partes=5, log_fn=log)
            log(f"✔ Audio dividido en {len(partes)} fragmentos")

            asegurar_dir("output/transcripciones")

            # 🔄 Procesar cada fragmento
            for idx, parte in enumerate(partes, start=1):
                log(f"🔊 Procesando audio {idx}/{len(partes)}: {parte}")
                texto = transcribir(parte)

                out_file = nombre_salida_por_video(
                    video_path,
                    base_dir="output/transcripciones"
                ).replace(".txt", f"_parte{idx}.txt")

                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(texto)

                log(f"✅ Parte {idx}/{len(partes)} guardada en: {out_file}")

            mostrar_info(f"Transcripción completada en {len(partes)} archivos separados.")

        except Exception as e:
            mostrar_error(str(e))
            log(f"❌ Error: {e}")
        finally:
            try:
                limpiar_temp("temp_audio.wav")
            except Exception:
                pass
            deshabilitar_ui(False)

    def on_click():
        video = seleccionar_video()
        if not video:
            return
        deshabilitar_ui(True)
        txt_logs.config(state="normal")
        txt_logs.delete("1.0", "end")
        txt_logs.config(state="disabled")
        hilo = threading.Thread(target=procesar_en_thread, args=(video,), daemon=True)
        hilo.start()

    def cambiar_tema():
        modo = ctk.get_appearance_mode()
        if modo == "Dark":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")

    # Ventana principal
    ventana = ctk.CTk()
    ventana.title("🎬 Transcriptor de Video a Texto")
    ventana.geometry("650x450")

    frame = ctk.CTkFrame(master=ventana, corner_radius=15)
    frame.pack(pady=20, padx=20, fill="both", expand=True)

    lbl = ctk.CTkLabel(
        master=frame,
        text="Selecciona un video para transcribir a texto",
        font=("Segoe UI", 16, "bold")
    )
    lbl.pack(pady=10)

    btn_seleccionar = ctk.CTkButton(
        master=frame,
        text="📂 Seleccionar Video",
        command=on_click,
        height=40,
        width=220,
        font=("Segoe UI", 14, "bold"),
        fg_color="#4CAF50",
        hover_color="#45a049"
    )
    btn_seleccionar.pack(pady=10)

    # Área de logs con ScrolledText (seguimos usando Tk, se integra bien con CTk)
    txt_logs = ScrolledText(frame, wrap="word", height=14, state="disabled", font=("Consolas", 10))
    txt_logs.pack(fill="both", expand=True, padx=10, pady=10)

    # Switch modo claro/oscuro
    switch = ctk.CTkSwitch(master=frame, text="🌙/☀️ Modo oscuro", command=cambiar_tema)
    switch.pack(pady=5)

    ventana.mainloop()
