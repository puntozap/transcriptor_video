from tkinter import filedialog, messagebox

def seleccionar_video():
    return filedialog.askopenfilename(
        title="Seleccionar video",
        filetypes=[
            ("Videos", "*.mp4;*.mkv;*.mov;*.avi;*.flv;*.webm"),
            ("Todos", "*.*"),
        ],
    )

def mostrar_info(msg: str):
    messagebox.showinfo("Información", msg)

def mostrar_error(msg: str):
    messagebox.showerror("Error", msg)
