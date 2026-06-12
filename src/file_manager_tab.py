import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import h5py

import os
import cv2
import threading

class FileManagerTab:
    """
    Gestiona la pestaña de manejo de datos de la aplicación. Permite entre otras cosas
    obtener descargas usando un token, probar la conexión, descarga local de archivos,
    inspección de archivos .nxs y (futuro) detección de diagnosticos y capacidades
    esperadas de la información del shot.
    """
    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance 

        self.input_folder_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.original_fps_var = tk.StringVar(value="10000")
        self.playback_fps_var = tk.StringVar(value="10")

        self.setup_ui_file_manager()

    def setup_ui_file_manager(self):
        """
        Diseña el panel de control 
        """
        # Contenedor central centrado para los inputs
        main_form = tk.Frame(self.master_frame, bg="white", padx=30, pady=30)
        main_form.pack(anchor="center")

        title = tk.Label(main_form, text="📶Cliente de conexión para MEPHIST-0", 
                         font=self.app.fuente_negrita, bg="white", fg="black")
        title.grid(row=0, column=0, columnspan=3, sticky="nesw", pady=(0, 20))

        # --- Fila 1: Carpeta de origen de imágenes (.jpg) ---
        lbl_token = tk.Label(main_form, text="Token", font=self.app.fuente_negrita, bg="white", fg="black")
        lbl_token.grid(row=1, column=0, sticky="e", pady=5, padx=5)
        
        ent_token = tk.Entry(main_form, textvariable=self.input_folder_var, width=60, font=self.app.fuente_ui, show="•")
        ent_token.grid(row=1, column=1, padx=5, pady=5)

        btn_test = tk.Button(main_form, text="Prueba de conexión", font=self.app.fuente_ui, command=self.seleccionar_carpeta,
                           bg="#e0e0e0", relief="flat", padx=10, width=20)
        btn_test.grid(row=1, column=2, padx=5, pady=5)

        self.status_label = tk.Label(main_form, text="Estado: Conexión establecida ✅", font=self.app.fuente_ui, bg="white", fg="green")
        self.status_label.grid(row=2, column=1, columnspan=3, sticky="w")

        # --- Fila 2: Archivo de salida (.avi) ---
        lbl_download = tk.Label(main_form, text="Shots", font=self.app.fuente_negrita, bg="white", fg="black")
        lbl_download.grid(row=3, column=0, sticky="e", pady=5)
        
        ent_download = tk.Entry(main_form, textvariable=self.output_file_var, width=60, font=self.app.fuente_ui)
        ent_download.grid(row=3, column=1, padx=5, pady=5)
        
        btn_download  = tk.Button(main_form, text="Descargar", font=self.app.fuente_ui, command=self.definir_salida,
                            bg="#e0e0e0", relief="flat", padx=10, width=20)
        btn_download.grid(row=3, column=2, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(main_form, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=4, column=1, columnspan=1, sticky="ew", pady=(20, 5))

        self.status_label = tk.Label(main_form, text="Estado: Listo para descargar", font=self.app.fuente_ui, bg="white", fg="gray")
        self.status_label.grid(row=5, column=1, columnspan=3, sticky="w")

        db_title = tk.Label(main_form, text="🗂️ Base de datos MEPHIST-0", 
                         font=self.app.fuente_negrita, bg="white", fg="black")
        db_title.grid(row=7, column=0, columnspan=3, sticky="nesw", pady=(0, 20))

        # 1. Crear un contenedor específico para la tabla y el scroll
        tabla_frame = tk.Frame(main_form)
        # Lo ubicamos, por ejemplo, en la fila 7, abarcando 3 columnas
        tabla_frame.grid(row=8, column=0, columnspan=3, pady=20, sticky="nsew")

        # 2. Definir la barra de desplazamiento vertical
        scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        # 3. Definir las columnas de la tabla
        columnas = ("id_shot", "fecha", "working_gas", "pressure", "discharge", "plasma_duration" ,"Ip_max", "Bt_max")

        # 4. Crear el Treeview (La Tabla)
        # show="headings" es CLAVE: oculta la columna de árbol y la deja como tabla plana
        tabla = ttk.Treeview(
            tabla_frame, 
            columns=columnas, 
            show="headings", 
            yscrollcommand=scroll_y.set,  # Conectamos la tabla a la barra
            height=30  # Muestra 10 filas visibles
        )
        tabla.pack(side="left", fill="both", expand=True)

        # 5. Conectar la barra a la tabla (viaje de vuelta)
        scroll_y.config(command=tabla.yview)

        # 6. Configurar las cabeceras (Lo que lee el usuario)
 # [ ... Todo tu código anterior hasta el paso 6 ... ]
        tabla.heading("id_shot", text="shot number")
        tabla.heading("fecha", text="date")
        tabla.heading("working_gas", text="working gas")
        tabla.heading("pressure", text="pressure")
        tabla.heading("discharge", text="discharge")
        tabla.heading("plasma_duration", text="plasma duration")
        tabla.heading("Ip_max", text="Ip max")
        tabla.heading("Bt_max", text="Bt_max")

        # 7. Configurar el ancho y alineación de las columnas experimentales
        # width está en píxeles. Ajusta estos valores según cómo se vea en tu pantalla.
        tabla.column("id_shot", width=100, anchor="center")
        tabla.column("fecha", width=100, anchor="center")
        tabla.column("working_gas", width=90, anchor="center")
        tabla.column("pressure", width=100, anchor="center")
        tabla.column("discharge", width=120, anchor="w")
        tabla.column("plasma_duration", width=120, anchor="center")
        tabla.column("Ip_max", width=90, anchor="center")
        tabla.column("Bt_max", width=90, anchor="center")

        # --- Agregar datos de prueba (Simulación de catálogo del MephiST-0) ---
        datos_prueba = [
            ("1024", "2026-06-10", "H2", "5.2e-4 mbar", "Ohmic", "45 ms", "2.5 kA", "0.8 T"),
            ("1025", "2026-06-10", "He", "6.1e-4 mbar", "Ohmic", "42 ms", "2.4 kA", "0.8 T"),
            ("1026", "2026-06-11", "H2", "4.8e-4 mbar", "Disrupted", "12 ms", "1.8 kA", "0.8 T"),
            ("1027", "2026-06-11", "H2", "5.0e-4 mbar", "Ohmic", "50 ms", "2.6 kA", "0.8 T")
        ]

        # Insertar los datos mediante un bucle
        for fila in datos_prueba:
            tabla.insert("", tk.END, values=fila)

        btn_inspector = tk.Button(
        main_form, 
        text=" Inspeccionar archivo .nxs", 
        font=self.app.fuente_ui,
        command=self.abrir_inspector_nexus, # Vinculas la función aquí
        bg="#e0e0e0", 
        fg="black",
        relief="flat", 
        padx=10, 
        width=20
        )

        btn_inspector.grid(row=4, column=2, columnspan=2, pady=5, padx=5)

    def abrir_inspector_nexus(self):
        """Abre un pop-up para explorar la estructura interna de un archivo .nxs"""
        # 1. Pedirle al usuario que seleccione el archivo
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccionar archivo NeXus",
            filetypes=[("NeXus Files", "*.nxs"), ("HDF5 Files", "*.h5"), ("Todos los archivos", "*.*")]
        )
        if not ruta_archivo:
            return  # El usuario canceló

        # 2. Crear la ventana emergente (Toplevel)
        visor = tk.Toplevel() # Si estás en una pestaña, pásale el contenedor principal si es necesario
        visor.title(f"Inspeccionando: {ruta_archivo.split('/')[-1]}")
        visor.geometry("700x500")
        visor.configure(bg="white")

        # 3. Crear el Treeview (Esta vez con la columna de árbol activada)
        # Omitimos el parámetro 'show="headings"' para que aparezcan los íconos de despliegue [+]
        tree = ttk.Treeview(visor)
        tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Barra de desplazamiento
        scroll = ttk.Scrollbar(tree, orient="vertical", command=tree.yview)
        scroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scroll.set)

        tree.heading("#0", text="Estructura Interna del Archivo NeXus", anchor="w")

        # 4. Leer el archivo con h5py y construir el árbol
        try:
            with h5py.File(ruta_archivo, 'r') as h5_file:
                # Creamos el nodo raíz principal (el nombre del archivo)
                nombre_base = ruta_archivo.split("/")[-1]
                root_node = tree.insert("", "end", text=f"📦 {nombre_base}", open=True)
                
                # Llamamos a nuestra función recursiva para que haga el trabajo sucio
                self._poblar_arbol_hdf5(tree, root_node, h5_file)
                
        except Exception as e:
            messagebox.showerror("Error de Lectura", f"No se pudo leer el archivo NeXus.\nDetalle: {str(e)}")

    def _poblar_arbol_hdf5(self, tree, parent_node, h5_obj):
        """
        Viaja recursivamente por los Grupos (carpetas) y Datasets (archivos) de un HDF5.
        """
        for key in h5_obj.keys():
            item = h5_obj[key]
            
            if isinstance(item, h5py.Group):
                # Si es un grupo, es el equivalente a una CARPETA
                # open=False hace que las carpetas aparezcan cerradas por defecto
                node = tree.insert(parent_node, "end", text=f"📁 {key}", open=False)
                # Volvemos a llamar a la función para ver qué hay dentro de esta carpeta
                self._poblar_arbol_hdf5(tree, node, item)
                
            elif isinstance(item, h5py.Dataset):
                # Si es un Dataset, es el equivalente a los DATOS DEL DIAGNÓSTICO
                # Extraemos el tamaño (shape) y el tipo de dato (float64, int, etc.)
                shape = item.shape
                tipo = item.dtype
                texto_datos = f"📄 {key}  -->  [Formato: {shape} | Tipo: {tipo}]"
                tree.insert(parent_node, "end", text=texto_datos)


    def seleccionar_carpeta(self):
        folder = filedialog.askdirectory(title="Seleccionar carpeta de imágenes FastCamera")
        if folder:
            self.input_folder_var.set(folder)
            # Auto-sugerir nombre de video de salida basado en la carpeta seleccionada
            nombre_carpeta = os.path.basename(folder)
            self.output_file_var.set(os.path.join(os.path.dirname(folder), f"{nombre_carpeta}_slow_motion.avi"))

    def definir_salida(self):
        archivo = filedialog.asksaveasfilename(
            title="Guardar Video",
            defaultextension=".avi",
            filetypes=[("Video de avi", "*.avi")]
        )
        if archivo:
            self.output_file_var.set(archivo)

    def iniciar_procesamiento_hilo(self):
        """ Lanza el proceso OpenCV en un hilo secundario para evitar congelar la ventana """
        if not self.input_folder_var.get() or not self.output_file_var.get():
            messagebox.showwarning("Faltan datos", "Por favor especifique la carpeta de entrada y el archivo de salida.")
            return

        self.process_btn.configure(state="disabled", bg="#85c785")
        self.status_label.configure(text="Estado: Procesando fotogramas...", fg="#2ca02c")
        
        # Iniciar hilo de procesamiento
        hilo = threading.Thread(target=self.procesar_video_opencv, daemon=True)
        hilo.start()

    def procesar_video_opencv(self):
        try:
            input_folder = self.input_folder_var.get()
            output_file = self.output_file_var.get()
            original_fps = int(self.original_fps_var.get())
            playback_fps = int(self.playback_fps_var.get())
            
            image_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.jpg')],
                                 key=lambda x: int(x.split('S0001')[-1].split('.')[0]))
            
            if not image_files:
                self.app.after(0, lambda: messagebox.showerror("Error", f"No se encontraron imágenes JPG en {input_folder}"))
                self.restablecer_ui()
                return

            first_image = cv2.imread(os.path.join(input_folder, image_files[0]))
            if first_image is None:
                self.app.after(0, lambda: messagebox.showerror("Error", f"Error al leer la primera imagen {image_files[0]}"))
                self.restablecer_ui()
                return
            
            height, width = first_image.shape[:2]
            discharge_num = image_files[0].split('_')[0] if '_' in image_files[0] else "Desconocida"

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(output_file, fourcc, playback_fps, (width, height))
            
            total_frames = len(image_files)
            self.app.after(0, lambda: self.progress_bar.configure(maximum=total_frames, value=0))

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.8
            font_color = (255, 255, 255)  # Blanco
            thickness = 2

            for frame_num, file_name in enumerate(image_files):
                img_path = os.path.join(input_folder, file_name)
                img = cv2.imread(img_path)
                
                if img is None: continue

                # Calcular estampa física de tiempo exacta
                actual_time_ms = (frame_num / original_fps) * 1000
                y_pos = height - 30
                
                # Quemar etiquetas en el frame con OpenCV
                cv2.putText(img, f"Discharge: {discharge_num}", (20, y_pos), 
                            font, font_scale, font_color, thickness, cv2.LINE_AA)
                cv2.putText(img, f"Time: {actual_time_ms:.2f} ms", (20, y_pos - 50), 
                            font, font_scale, font_color, thickness, cv2.LINE_AA)
                
                video_writer.write(img)

                # Actualizar barra de progreso de forma segura en la UI cada 10 fotogramas
                if frame_num % 10 == 0:
                    self.app.after(0, lambda v=frame_num: self.progress_bar.configure(value=v))

            video_writer.release()
            self.app.after(0, lambda: messagebox.showinfo("Proceso Completo", f"Video guardado con éxito en:\n{output_file}"))

        except Exception as e:
            self.app.after(0, lambda: messagebox.showerror("Error Crítico", f"Ocurrió un error: {str(e)}"))
        finally:
            self.restablecer_ui()

    def restablecer_ui(self):
        """ Restablece los widgets de la interfaz al estado original """
        self.app.after(0, lambda: self.process_btn.configure(state="normal", bg="#2ca02c"))
        self.app.after(0, lambda: self.status_label.configure(text="Estado: Trabajo completado / Listo", fg="gray"))
        self.app.after(0, lambda: self.progress_bar.configure(value=0))