import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import cv2
import threading

class EqRecTab:
    """
    Gestiona la pestaña de procesamiento de Reconstrucción de Equilibrio (EqRec).
    Genera videos en Slow-Motion limpios (sin texto superpuesto) indexando imágenes numéricas.
    """
    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance  

        # Variables de control de rutas y parámetros
        self.input_folder_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.original_fps_var = tk.StringVar(value="10000")
        self.playback_fps_var = tk.StringVar(value="10")

        self.setup_ui_eq_rec()

    def setup_ui_eq_rec(self):
        """
        Diseña el panel de control siguiendo fielmente la estética unificada.
        """
        main_form = tk.Frame(self.master_frame, bg="white", padx=30, pady=30)
        main_form.pack(anchor="nw")

        title = tk.Label(main_form, text="Reconstrucción de Equilibrio (EquiRecons)", 
                         font=self.app.fuente_negrita, bg="white", fg="black")
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 20))

        # --- Fila 1: Carpeta de origen ---
        lbl_in = tk.Label(main_form, text="Carpeta de imágenes:", font=self.app.fuente_ui, bg="white", fg="black")
        lbl_in.grid(row=1, column=0, sticky="w", pady=5, padx=5)
        
        ent_in = tk.Entry(main_form, textvariable=self.input_folder_var, width=60, font=self.app.fuente_ui)
        ent_in.grid(row=1, column=1, padx=5, pady=5)
        
        btn_in = tk.Button(main_form, text="Buscar...", font=self.app.fuente_ui, command=self.seleccionar_carpeta,
                           bg="#e0e0e0", relief="flat", padx=10)
        btn_in.grid(row=1, column=2, padx=5, pady=5)

        # --- Fila 2: Archivo de salida ---
        lbl_out = tk.Label(main_form, text="Guardar video como:", font=self.app.fuente_ui, bg="white", fg="black")
        lbl_out.grid(row=2, column=0, sticky="w", pady=5)
        
        ent_out = tk.Entry(main_form, textvariable=self.output_file_var, width=60, font=self.app.fuente_ui)
        ent_out.grid(row=2, column=1, padx=5, pady=5)
        
        btn_out = tk.Button(main_form, text="Definir...", font=self.app.fuente_ui, command=self.definir_salida,
                            bg="#e0e0e0", relief="flat", padx=10)
        btn_out.grid(row=2, column=2, padx=5, pady=5)

        # --- Fila 3: Parámetros de FPS ---
        fps_frame = tk.Frame(main_form, bg="white")
        fps_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=15)

        lbl_ofps = tk.Label(fps_frame, text="Original FPS:", font=self.app.fuente_ui, bg="white", fg="black")
        lbl_ofps.pack(side="left", padx=(0, 5))
        ent_ofps = tk.Entry(fps_frame, textvariable=self.original_fps_var, width=8, font=self.app.fuente_ui)
        ent_ofps.pack(side="left", padx=(0, 20))

        lbl_pfps = tk.Label(fps_frame, text="Playback FPS (Salida):", font=self.app.fuente_ui, bg="white", fg="black")
        lbl_pfps.pack(side="left", padx=(0, 5))
        ent_pfps = tk.Entry(fps_frame, textvariable=self.playback_fps_var, width=8, font=self.app.fuente_ui)
        ent_pfps.pack(side="left")

        # --- Fila 4: Barra de progreso ---
        self.progress_bar = ttk.Progressbar(main_form, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.grid(row=4, column=0, columnspan=2, sticky="w", pady=(20, 5))

        self.status_label = tk.Label(main_form, text="Estado: Listo para procesar", font=self.app.fuente_ui, bg="white", fg="gray")
        self.status_label.grid(row=5, column=0, columnspan=2, sticky="w")

        # --- Botón de Acción Principal ---
        self.process_btn = tk.Button(
            main_form, text="Generar Video EqRec", font=self.app.fuente_negrita,
            command=self.iniciar_procesamiento_hilo, bg="#2ca02c", fg="white",
            activebackground="#218021", activeforeground="white", relief="flat", padx=20, pady=8
        )
        self.process_btn.grid(row=6, column=0, columnspan=3, sticky="w", pady=(25, 0))

    def seleccionar_carpeta(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta de imágenes EquiRecons")
        if folder:
            self.input_folder_var.set(folder)
            nombre_carpeta = os.path.basename(folder)
            self.output_file_var.set(os.path.join(os.path.dirname(folder), f"{nombre_carpeta}_EqRec.avi"))

    def definir_salida(self):
        archivo = filedialog.asksaveasfilename(
            title="Guardar Video Reconstrucción",
            defaultextension=".avi",
            filetypes=[("Video de avi", "*.avi")]
        )
        if archivo:
            self.output_file_var.set(archivo)

    def iniciar_procesamiento_hilo(self):
        if not self.input_folder_var.get() or not self.output_file_var.get():
            messagebox.showwarning("Faltan datos", "Por favor especifique la carpeta de entrada y el archivo de salida.")
            return

        self.process_btn.configure(state="disabled", bg="#85c785")
        self.status_label.configure(text="Estado: Procesando reconstrucciones...", fg="#2ca02c")
        
        hilo = threading.Thread(target=self.procesar_video_opencv, daemon=True)
        hilo.start()

    def procesar_video_opencv(self):
        try:
            input_folder = self.input_folder_var.get()
            output_file = self.output_file_var.get()
            playback_fps = int(self.playback_fps_var.get())
            
            # Ordenamiento numérico estricto (1.jpg, 2.jpg, etc.) según EqRec.py
            image_files = sorted(
                [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))],
                key=lambda x: int(os.path.splitext(x)[0])
            )
            
            if not image_files:
                self.app.after(0, lambda: messagebox.showerror("Error", f"No se encontraron imágenes válidas en {input_folder}"))
                self.restablecer_ui()
                return

            first_image = cv2.imread(os.path.join(input_folder, image_files[0]))
            if first_image is None:
                self.app.after(0, lambda: messagebox.showerror("Error", f"Error al leer la primera imagen {image_files[0]}"))
                self.restablecer_ui()
                return
            
            height, width = first_image.shape[:2]

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(output_file, fourcc, playback_fps, (width, height))
            
            total_frames = len(image_files)
            self.app.after(0, lambda: self.progress_bar.configure(maximum=total_frames, value=0))

            for frame_num, file_name in enumerate(image_files):
                img_path = os.path.join(input_folder, file_name)
                img = cv2.imread(img_path)
                
                if img is None: continue
                
                # Escritura directa del frame limpio sin overlays de texto
                video_writer.write(img)

                if frame_num % 10 == 0:
                    self.app.after(0, lambda v=frame_num: self.progress_bar.configure(value=v))

            video_writer.release()
            self.app.after(0, lambda: messagebox.showinfo("Proceso Completo", f"Video EqRec guardado en:\n{output_file}"))

        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("Error Crítico", f"Ocurrió un error: {str(e)}"))
        finally:
            self.restablecer_ui()

    def restablecer_ui(self):
        self.app.after(0, lambda: self.process_btn.configure(state="normal", bg="#2ca02c"))
        self.app.after(0, lambda: self.status_label.configure(text="Estado: Trabajo completado / Listo", fg="gray"))
        self.app.after(0, lambda: self.progress_bar.configure(value=0))