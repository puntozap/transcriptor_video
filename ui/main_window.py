import threading
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from ui.dialogs import seleccionar_video, mostrar_info, mostrar_error
from core.extractor import extraer_audio
from core.transcriber import transcribir
from core.utils import limpiar_temp, asegurar_dir, nombre_salida_por_video, dividir_audio_ffmpeg

def iniciar_app():
    def log(msg):
        txt_logs.config(state="normal")
        txt_logs.insert(tk.END, msg + "\n")
        txt_logs.see(tk.END)
        txt_logs.config(state="disabled")

    def deshabilitar_ui(flag=True):
        btn_seleccionar.config(state=tk.DISABLED if flag else tk.NORMAL)

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
        txt_logs.delete("1.0", tk.END)
        txt_logs.config(state="disabled")
        hilo = threading.Thread(target=procesar_en_thread, args=(video,), daemon=True)
        hilo.start()

    # UI
    ventana = tk.Tk()
    ventana.title("Transcriptor de Video")
    ventana.geometry("560x360")

    lbl = tk.Label(ventana, text="Selecciona un video para transcribir a texto", pady=8, font=("Segoe UI", 11))
    lbl.pack()

    btn_seleccionar = tk.Button(ventana, text="Seleccionar Video", command=on_click, height=2, width=24)
    btn_seleccionar.pack(pady=6)

    txt_logs = ScrolledText(ventana, wrap="word", height=14, state="disabled")
    txt_logs.pack(fill="both", expand=True, padx=10, pady=8)

    ventana.mainloop()
