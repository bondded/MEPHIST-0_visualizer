import tkinter as tk
from tkinter import messagebox, simpledialog
import numpy as np
import itertools
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor

class ShotComparisonTab:
    """
    Gestiona la pestaña de comparación de múltiples disparos en un layout 2x2.
    Consume los datos centralizados desde el DataEngine (model.py).
    """
    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance  
        
        # Paleta de colores rotativa para distinguir las curvas superpuestas
        self.colores = itertools.cycle(["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"])
        self.shots_cargados = []  # Registro de IDs cargados

        self.setup_ui_comparativa()

    def setup_ui_comparativa(self):
        # 1. Crear la figura especificando el color de fondo para evitar transparencias
        self.fig = Figure(figsize=(10, 8), facecolor="white")
        self.axes = self.fig.subplots(2, 2)
        
        self.ax_ip = self.axes[0, 0]
        self.ax_bt = self.axes[0, 1]
        self.ax_ha = self.axes[1, 0]
        self.ax_esp = self.axes[1, 1]

        # Configuración de etiquetas iniciales
        self.ax_ip.set_ylabel("Ip (kA)", fontname="Roboto", fontsize=10)
        self.ax_bt.set_ylabel("Bt (T)", fontname="Roboto", fontsize=10)
        self.ax_ha.set_ylabel("H-alpha (V)", fontname="Roboto", fontsize=10)
        self.ax_esp.set_ylabel("Espectro Emitido (u. a.)", fontname="Roboto", fontsize=10)
        
        for ax in self.axes.flat:
            ax.set_xlabel("Tiempo (ms)", fontname="Roboto", fontsize=9)
            ax.grid(True, linestyle=":", alpha=0.6)
            ax.set_facecolor("white")

        self.fig.tight_layout()

        # 2. Enlazar al contenedor de Tkinter asegurando expansión total
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # Cursor reticular sincronizado
        self.cursor = MultiCursor(
            self.canvas, (self.ax_ip, self.ax_bt, self.ax_ha),
            color="gray", linestyle="--", lw=0.8, horizOn=False, vertOn=True, useblit=True
        )
        self.canvas.draw()

    def cargar_nuevo_shot_overlay(self):
        """
        Pide un número de shot, solicita los datos procesados al DataEngine
        y renderiza de forma síncrona las curvas en el layout 2x2.
        """
        shot_num = simpledialog.askstring("Comparar Shot", "Ingrese número de Shot a superponer:")
        if not shot_num: 
            return

        if shot_num in self.shots_cargados:
            messagebox.showinfo("Información", f"El shot {shot_num} ya se encuentra en la gráfica.")
            return

        # LLAMADA CENTRALIZADA AL MOTOR: Consume tus propios métodos encapsulados
        datos_shot = self.app.modelo.obtener_datos_especificos_shot(shot_num)

        # Control defensivo solicitado: Si retorna None saltamos el mensaje exacto
        if datos_shot is None:
            messagebox.showinfo("No encontrado", f"No se ha encontrado información para el shot pedido: {shot_num}")
            return

        print('Comprobación 1: pasamos la verificación')
        color = next(self.colores)
        label_curva = f"Shot {shot_num}"
        lineas_añadidas = False

        # --- Inyección de curvas en los paneles de Matplotlib ---
        if datos_shot["t_ip"] is not None and datos_shot["t_ip"].size > 0:
            self.ax_ip.plot(datos_shot["t_ip"], datos_shot["d_ip"], color=color, label=label_curva, lw=1.5)
            lineas_añadidas = True
            
        if datos_shot["t_bt"] is not None and datos_shot["t_bt"].size > 0:
            self.ax_bt.plot(datos_shot["t_bt"], datos_shot["d_bt"], color=color, label=label_curva, lw=1.5)
            lineas_añadidas = True
            
        if datos_shot["t_ha"] is not None and datos_shot["t_ha"].size > 0:
            self.ax_ha.plot(datos_shot["t_ha"], datos_shot["d_ha"], color=color, label=label_curva, lw=1.5)
            lineas_añadidas = True
            
        if datos_shot["w_length"] is not None and datos_shot["w_length"].size > 0:
            self.ax_esp.plot(datos_shot["w_length"], datos_shot["intensity"], color=color, label=label_curva, lw=1.2)
            lineas_añadidas = True

        if not lineas_añadidas:
            messagebox.showwarning("Advertencia", f"El shot {shot_num} no contenía canales válidos para graficar.")
            return

        self.shots_cargados.append(shot_num)
        print("Comprobación 2: cargamos el shot")

        # Ajustar límites temporales dinámicos basados en la barra superior de tu interfaz
        tmin = float(self.app.entry_tmin.get()) if hasattr(self.app, 'entry_tmin') else self.app.tmin
        tmax = float(self.app.entry_tmax.get()) if hasattr(self.app, 'entry_tmax') else self.app.tmax
        for ax in [self.ax_ip, self.ax_bt, self.ax_ha]:
            ax.set_xlim([tmin, tmax])

        # Actualizar leyendas
        for ax in self.axes.flat:
            handles, labels = ax.get_legend_handles_labels()
            if labels:
                ax.legend(loc="upper right", fontsize=8)

        # Forzar refresco geométrico en Linux Mint / Tkinter
        self.master_frame.update_idletasks()
        self.fig.tight_layout()
        self.canvas.draw()
        print(f"✅ Curvas del Shot {shot_num} superpuestas usando el procesado oficial de model.py.")   


    def limpiar_comparacion(self):
        """
        Limpia por completo los 4 paneles del layout.
        """
        for ax in self.axes.flat:
            ax.clear()
        
        self.ax_ip.set_ylabel("Ip (kA)")
        self.ax_bt.set_ylabel("Bt (T)")
        self.ax_ha.set_ylabel("H-alpha (V)")
        self.ax_esp.set_ylabel("Espectro Emitido (u. a.)")
        
        for ax in self.axes.flat:
            ax.set_xlabel("Tiempo (ms)")
            ax.grid(True, linestyle=":", alpha=0.6)

        self.shots_cargados.clear()
        self.colores = itertools.cycle(["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"])
        
        self.master_frame.update_idletasks()
        self.fig.tight_layout()
        self.canvas.draw()