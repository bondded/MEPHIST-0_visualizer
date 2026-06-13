import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import h5py

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

        lbl_token = tk.Label(main_form, text="Token", font=self.app.fuente_negrita, bg="white", fg="black")
        lbl_token.grid(row=1, column=0, sticky="e", pady=5, padx=5)
        ent_token = tk.Entry(main_form, textvariable=self.input_folder_var, width=60, font=self.app.fuente_ui, show="•")
        ent_token.grid(row=1, column=1, padx=5, pady=5)

        btn_test = tk.Button(main_form, text="Prueba de conexión", font=self.app.fuente_ui, command=self.probar_conexion,
                           bg="#e0e0e0", relief="flat", padx=10, width=20)
        btn_test.grid(row=1, column=2, padx=5, pady=5)

        self.status_label = tk.Label(main_form, text="Estado: Conexión establecida ✅", font=self.app.fuente_ui, bg="white", fg="green")
        self.status_label.grid(row=2, column=1, columnspan=3, sticky="w")

        lbl_download = tk.Label(main_form, text="Shots", font=self.app.fuente_negrita, bg="white", fg="black")
        lbl_download.grid(row=3, column=0, sticky="e", pady=5)
        ent_download = tk.Entry(main_form, textvariable=self.output_file_var, width=60, font=self.app.fuente_ui)
        ent_download.grid(row=3, column=1, padx=5, pady=5)
        btn_download  = tk.Button(main_form, text="Descargar", font=self.app.fuente_ui, command=self.descargar_shots,
                            bg="#e0e0e0", relief="flat", padx=10, width=20)
        btn_download.grid(row=3, column=2, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(main_form, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=4, column=1, columnspan=1, sticky="ew", pady=(20, 5))
        self.status_label = tk.Label(main_form, text="Estado: Listo para descargar", font=self.app.fuente_ui, bg="white", fg="gray")
        self.status_label.grid(row=5, column=1, columnspan=3, sticky="w")

        db_title = tk.Label(main_form, text="🗂️ Base de datos MEPHIST-0", 
                         font=self.app.fuente_negrita, bg="white", fg="black")
        db_title.grid(row=7, column=0, columnspan=3, sticky="nesw", pady=(0, 20))

        tabla_frame = tk.Frame(main_form)
        tabla_frame.grid(row=8, column=0, columnspan=3, pady=20, sticky="nsew")
        scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")
        columnas = ("id_shot", "fecha", "working_gas", "pressure", "discharge", "plasma_duration" ,"Ip_max", "Bt_max")
        tabla = ttk.Treeview(
            tabla_frame, 
            columns=columnas, 
            show="headings", 
            yscrollcommand=scroll_y.set,  
            height=30 
        )
        tabla.pack(side="left", fill="both", expand=True)
        scroll_y.config(command=tabla.yview)

        tabla.heading("id_shot", text="shot number")
        tabla.heading("fecha", text="date")
        tabla.heading("working_gas", text="working gas")
        tabla.heading("pressure", text="pressure")
        tabla.heading("discharge", text="discharge")
        tabla.heading("plasma_duration", text="plasma duration")
        tabla.heading("Ip_max", text="Ip max")
        tabla.heading("Bt_max", text="Bt_max")
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
        for fila in datos_prueba:
            tabla.insert("", tk.END, values=fila)

        btn_inspector = tk.Button(
        main_form, 
        text=" Inspeccionar archivo .nxs", 
        font=self.app.fuente_ui,
        command=self.abrir_inspector_nexus, 
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


    def probar_conexion(self):
        print("Hola")

    def descargar_shots(self):
        print("Hola")
        
        