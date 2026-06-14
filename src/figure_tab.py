import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

class FigureTab:
    """
    pestaña para visualización dinámica y sincronizada
    de multiples diagnosticos
    """

    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance

        self.diagnosticos_disponibles = {
            "plasma current" : "Ip (kA)",
            "toroidal field" : "Bt (T)",
            "H-alpha emission": "H-alpha (a.u.)",
            "Voltage loops": "(VL2 + VL7)/2 (V)",
            "electron density": "ne (m-3)",
            "electron temperature": "Te (keV)",
            "r = a safety factor": "q(a)",
            "emission spectrum": "Intensity",
        }

        self.setup_ui_figure()

    def setup_ui_figure(self):
        # 1. Configurar la proporción 3/4 (Gráficos) y 1/4 (Controles)
        self.master_frame.columnconfigure(0, weight=3)
        self.master_frame.columnconfigure(1, weight=1)
        self.master_frame.rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: ÁREA DE GRÁFICOS (3/4) ---
        self.plot_frame = tk.Frame(self.master_frame, bg="white")
        self.plot_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Inicializar la figura de Matplotlib vacía
        self.figura = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Barra de herramientas nativa de Matplotlib (Zoom, Guardar, Mover)
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        ent_shot = tk.Entry(self.master_frame, textvariable="", width=30, font=self.app.fuente_ui)
        #ent_shot.grid(row=0, column=1, sticky="w", relief="flat")
        # --- PANEL DERECHO: SELECTOR DE DIAGNÓSTICOS (1/4) ---
        self.control_frame = tk.Frame(self.master_frame, bg="#f8f9fa", relief="ridge", bd=1)
        self.control_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        lbl_titulo = tk.Label(self.control_frame, text="Available diagnostics", 
                              font=self.app.fuente_negrita, bg="#f8f9fa", fg="black")
        lbl_titulo.pack(pady=(20, 10))

        # Listbox configurado para permitir selección múltiple
        self.listbox = tk.Listbox(
            self.control_frame, 
            selectmode=tk.MULTIPLE, # Permite seleccionar varios haciendo clic
            font=self.app.fuente_ui,
            activestyle="none",
            exportselection=False
        )
        self.listbox.pack(fill="both", expand=True, padx=15, pady=5)

        # Poblar la lista con las opciones
        for diag in self.diagnosticos_disponibles:
            self.listbox.insert(tk.END, diag)

        # Botón para detonar el renderizado
        btn_graficar = tk.Button(
            self.control_frame, 
            text="Draw", 
            font=self.app.fuente_negrita,
            bg="black", fg="white", relief="flat", pady=10,
            command=self.actualizar_graficos
        )
        btn_graficar.pack(fill="x", padx=15, pady=20)
        btn_exportar = tk.Button(
            self.control_frame, 
            text="Export", 
            font=self.app.fuente_negrita,
            bg="#e0e0e0", fg="black", relief="flat", pady=10,
            command=self.actualizar_graficos
        )
        btn_exportar.pack(fill="x", padx=15, pady=20)


    def actualizar_graficos(self, id_shot=1500):
        """Lee los diagnósticos seleccionados y redibuja la figura apilada."""
        # Obtener los índices y luego los textos (llaves) seleccionados en la Listbox
        indices = self.listbox.curselection()
        seleccion = [self.listbox.get(i) for i in indices]

        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)
        #time_ip, data_ip = self.app.modelo.obtener_corriente_plasma(id_shot)

        if not seleccion:
            # Si el usuario deseleccionó todo, limpiamos la pantalla
            self.figura.clf()
            self.canvas.draw()
            return 

        # 1. Limpiar el lienzo de cualquier trazado anterior
        self.figura.clf()

        # 2. Crear los nuevos subplots dinámicamente
        num_plots = len(seleccion)
        
        # sharex=True es el comando clave para sincronizar el tiempo
        axs = self.figura.subplots(nrows=num_plots, ncols=1, sharex=True)
        
        # Si solo se selecciona 1 gráfico, Matplotlib no devuelve una lista. 
        # Lo forzamos a ser una lista para no romper el bucle 'for' que viene abajo.
        if num_plots == 1:
            axs = [axs]

        # 3. Dibujar la señal en cada subplot correspondiente
        for i, nombre_llave in enumerate(seleccion):
            ax = axs[i]
            
            # --- LA MAGIA DEL DICCIONARIO ---
            # Buscamos el valor técnico (ej: "Ip (kA)") usando la llave (ej: "plasma current")
            etiqueta_eje_y = self.diagnosticos_disponibles[nombre_llave]
            
            # --- AQUÍ CONECTARÍAS CON TU DATA ENGINE ---
            # Por ahora, generamos una curva de prueba simulada
            import numpy as np
            t = np.linspace(0, 100, 1000) # Simula tiempo de 0 a 100 ms
            señal_simulada = np.sin(t / (i + 1)) * np.exp(-t / 50)
            # -------------------------------------------
            
            ax.plot(t, señal_simulada, color="black", linewidth=1.2)
            
            # Inyectamos el VALOR del diccionario en el eje Y
            ax.set_ylabel(etiqueta_eje_y, fontsize=10, fontweight="bold")
            ax.grid(True, linestyle="--", alpha=0.5)
            
            # Quitar marcas del eje X en los gráficos de arriba para que se vea más limpio
            if i < num_plots - 1:
                ax.tick_params(labelbottom=False)

        # 4. Configurar el eje X solo en el último gráfico de abajo
        axs[-1].set_xlabel("time [ms]", fontsize=10, fontweight="bold")
        
        # Ajustar los márgenes para que nada quede cortado
        self.figura.tight_layout()
        
        # Enviar la orden a Tkinter para que muestre el nuevo dibujo
        self.canvas.draw()
