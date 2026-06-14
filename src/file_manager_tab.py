import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import h5py
import os
from model import DataEngine
import csv

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

        self.input_token_var = tk.StringVar(value="C8yvwmWZ8THNjwBgaBJz43DWomyl3yNcStgwTXf3hAd3WaXNqtlI46kRaD5L")
        self.token = tk.StringVar()
        self.shots = tk.StringVar()
        self.tabla = None
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
        ent_token = tk.Entry(main_form, textvariable=self.input_token_var, width=60, font=self.app.fuente_ui, show="•")  
        ent_token.grid(row=1, column=1, padx=5, pady=5)
        self.token.set(ent_token.get())

        btn_test = tk.Button(main_form, text="Prueba de conexión", font=self.app.fuente_ui, command=self.probar_conexion,
                           bg="#e0e0e0", relief="flat", padx=10, width=20)
        btn_test.grid(row=1, column=2, padx=5, pady=5)

        self.status_conection_label = tk.Label(main_form, text="Estado: Esperando prueba...", font=self.app.fuente_ui, bg="white", fg="gray")
        self.status_conection_label.grid(row=2, column=1, columnspan=3, sticky="w")

        lbl_download = tk.Label(main_form, text="Shots", font=self.app.fuente_negrita, bg="white", fg="black")
        lbl_download.grid(row=3, column=0, sticky="e", pady=5)
        ent_download = tk.Entry(main_form,textvariable=self.shots, width=60, font=self.app.fuente_ui)
        ent_download.grid(row=3, column=1, padx=5, pady=5)
        self.shots.set(ent_download.get())

        btn_download  = tk.Button(main_form, text="Descargar", font=self.app.fuente_ui, command=self.descargar_shots,
                            bg="#e0e0e0", relief="flat", padx=10, width=20)
        btn_download.grid(row=3, column=2, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(main_form, orient="horizontal", mode="determinate")
        self.progress_bar.grid(row=4, column=1, columnspan=1, sticky="ew", pady=(20, 5))
        self.status_label = tk.Label(main_form, text="Estado: Esperando prueba...", font=self.app.fuente_ui, bg="white", fg="gray")
        self.status_label.grid(row=5, column=1, columnspan=3, sticky="w")

        db_title = tk.Label(main_form, text="🗂️ Base de datos MEPHIST-0", 
                         font=self.app.fuente_negrita, bg="white", fg="black")
        db_title.grid(row=7, column=0, columnspan=3, sticky="nesw", pady=(0, 20))

        tabla_frame = tk.Frame(main_form)
        tabla_frame.grid(row=8, column=0, columnspan=3, pady=20, sticky="nsew")
        scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical")
        scroll_y.pack(side="right", fill="y")
        columnas = ("id_shot", "fecha", "peso", "pressure", "working_gas", "Ip_max")
        tabla = ttk.Treeview(
            tabla_frame, 
            columns=columnas, 
            show="headings", 
            yscrollcommand=scroll_y.set,  
            height=30 
        )
        tabla.pack(side="left", fill="both", expand=True)
        scroll_y.config(command=tabla.yview)

        tabla.heading("id_shot", text="shot")
        tabla.heading("fecha", text="date")
        tabla.heading("peso", text="peso (mb)")
        tabla.heading("pressure", text="pressure (mPa)")
        tabla.heading("working_gas", text="working gas")
        tabla.heading("Ip_max", text="Ip max (kA)")
        tabla.column("id_shot", width=60, anchor="center")
        tabla.column("fecha", width=100, anchor="center")
        tabla.column("peso", width=90, anchor="center")
        tabla.column("pressure", width=100, anchor="center")
        tabla.column("working_gas", width=100, anchor="center")
        tabla.column("Ip_max", width=100, anchor="center")

        self.tabla = tabla
        #self.app.modelo.actualizar_base_datos()
        self.poblar_tabla_desde_csv()

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
        estado, respuesta = self.app.modelo.test_conexion()
        token = self.token.get()
        self.app.modelo.actualizar_token_yaml(token)
        if respuesta:
            self.status_conection_label.config(
                text="Estado: Conexión establecida ✅",
                fg="green"
            )
            self.status_label.config(
                text="Estado: Listo para descargar ✅",
                fg="green"
            )
        else:
            self.status_conection_label.config(
                text="Estado: No se pudo conectar al servidor ❌",
                fg="red"
            )            
            self.status_label.config(
                text="Estado: No se puede descargar ❌",
                fg="red"
            )
        self.master_frame.update_idletasks()
        
    def descargar_shots(self):
        shots_str = self.shots.get()
        shots = [int(x) for x in shots_str.split(",")]
        total_shots = len(shots)
        self.progress_bar["maximum"] = total_shots
        self.progress_bar["value"] = 0
        for i, shot in enumerate(shots):
            self.status_label.config(
                text=f"Estado: Descargando shot {shot} ({i + 1}/{total_shots})",
                fg="blue"
            )
            self.master_frame.update_idletasks()

            estado, respuesta = self.app.modelo.descargar_datos(shot)
        
            self.progress_bar["value"] = i + 1
            self.master_frame.update_idletasks()

        self.status_label.config(text="Estado: Completado!", fg="green")

    def poblar_tabla_desde_csv(self):
        archivo_permanente = "catalogo_mephist0.csv"
        
        # Si el archivo no existe, no hacemos nada
        if not os.path.exists(archivo_permanente):
            return

        # 1. Limpiar la tabla actual (para no duplicar datos visualmente si refrescas)
        for fila_existente in self.tabla.get_children():
            self.tabla.delete(fila_existente)

        # 2. Leer el archivo y agregar las filas
        with open(archivo_permanente, mode='r', encoding='utf-8') as archivo_csv:
            lector = csv.reader(archivo_csv)
            
            # Saltamos la primera línea (las cabeceras)
            next(lector, None) 
            
            # Recorremos cada línea de datos y la insertamos en el Treeview
            for fila_datos in lector:
                self.tabla.insert("", tk.END, values=fila_datos)