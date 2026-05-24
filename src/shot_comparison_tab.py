import tkinter as tk
from tkinter import messagebox, simpledialog
import h5py
import numpy as np
import itertools
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor

# Parámetros globales de conversión física
K_rog_tor = 6.3e6
K_TF = 9.6e-3

# --- FUNCIONES DE PROCESAMIENTO DE SEÑALES ---
def set_zero(sig):
    sig = np.asarray(sig)
    if sig.size < 200: return sig
    return sig - np.average(sig[10:200])

def integrate(time, sig):
    sig = np.asarray(sig)
    time = np.asarray(time)
    if len(sig) < 2: return np.zeros_like(sig)
    dt = (time[-1] - time[0]) / (len(time) - 1)
    return np.cumsum(sig) * dt

def preprocess(sig):
    sig = np.asarray(sig)
    if sig.size == 0: return sig
    sig2 = np.copy(sig)
    sig2[np.isnan(sig2)] = 0
    return sig2


class ShotComparisonTab:
    """
    Gestiona la pestaña de comparación de múltiples disparos en un layout 2x2.
    """
    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance  
        
        # Paleta de colores para superponer curvas
        self.colors = itertools.cycle(['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
        self.setup_graficos_comparacion()

    def setup_graficos_comparacion(self):
        """
        Crea la cuadrícula simétrica de 2x2 para las 4 señales seleccionadas.
        """
        self.fig = Figure(figsize=(12, 7), facecolor="white")
        
        # Generar matriz 2x2 de subplots
        self.axes = self.fig.subplots(2, 2)
        
        # Desempaquetar para fácil manipulación
        self.ax_ip = self.axes[0, 0]
        self.ax_bt = self.axes[0, 1]
        self.ax_ha = self.axes[1, 0]
        self.ax_esp = self.axes[1, 1]

        # Configuración inicial de títulos y etiquetas
        self.ax_ip.set_ylabel("Ip (kA)")
        self.ax_bt.set_ylabel("Bt (T)")
        self.ax_ha.set_ylabel("H-alpha (V)")
        self.ax_esp.set_ylabel("Espectro Emitido (u. a.)")
        
        self.ax_ip.set_xlabel("Tiempo (ms)")
        self.ax_bt.set_xlabel("Tiempo (ms)")
        self.ax_ha.set_xlabel("Tiempo (ms)")
        self.ax_esp.set_xlabel("Longitud de onda o Frecuencia") # Depende de tus datos de espectro

        # Formatear todos los ejes
        for ax in self.axes.flat:
            ax.set_facecolor("white")
            ax.grid(True, linestyle=":", alpha=0.6)

        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Cursor interactivo que cruza las 4 ventanas del plano 2x2
        self.cursor = MultiCursor(
            self.canvas,
            [self.ax_ip, self.ax_bt, self.ax_ha, self.ax_esp],
            color="red",
            linestyle="--",
            lw=1,
            horizOn=False,
            vertOn=True,
            useblit=True
        )
        self.canvas.draw()

    def cargar_nuevo_shot_overlay(self):
        """
        Pide un disparo y lo grafica encima de los cuadrantes existentes.
        """
        shot_num = simpledialog.askstring("Comparar Shot", "Ingrese número de Shot para superponer:")
        if not shot_num:
            return

        file_path = f"./MephistDataKit/.cache/{shot_num}MD.nxs"
        try:
            with h5py.File(file_path, 'r') as f:
                # Extraer canales crudos
                raw_time = f['discharges'][shot_num]['time'][:]
                raw_ip = f['discharges'][shot_num]['Rog_tor'][:]
                raw_bt = f['discharges'][shot_num]['TF'][:]
                raw_ha = f['discharges'][shot_num]['Photod'][:]
                
                # Para el espectro completo (ajusta las llaves según tu archivo si difieren)
                raw_wl = f['discharges'][shot_num]['wavelength'][:] if 'wavelength' in f['discharges'][shot_num] else np.array([])
                raw_intensidad = f['discharges'][shot_num]['spec_intensity'][:] if 'spec_intensity' in f['discharges'][shot_num] else np.array([])

            # Procesamiento temporal
            time_ms = raw_time * 1000
            ip_processed = integrate(time_ms, set_zero(raw_ip)) * K_rog_tor / 1000
            bt_processed = set_zero(raw_bt) * K_TF
            ha_processed = preprocess(raw_ha)

            color = next(self.colors)
            
            # Dibujar curvas superpuestas en el layout 2x2
            self.ax_ip.plot(time_ms, ip_processed, color=color, label=f"Shot {shot_num}")
            self.ax_bt.plot(time_ms, bt_processed, color=color, label=f"Shot {shot_num}")
            self.ax_ha.plot(time_ms, ha_processed, color=color, label=f"Shot {shot_num}")
            
            if raw_wl.size > 0 and raw_intensidad.size > 0:
                self.ax_esp.plot(raw_wl, raw_intensidad, color=color, label=f"Shot {shot_num}")
            else:
                # Si no hay canal de espectro en el h5, ponemos un texto de advertencia en el cuadrante
                self.ax_esp.text(0.5, 0.5, "[Espectro no disponible]", transform=self.ax_esp.transAxes, ha='center')

            # Actualizar rangos de tiempo basados en la UI general para los ejes de evolución temporal
            for ax in [self.ax_ip, self.ax_bt, self.ax_ha]:
                ax.set_xlim([self.app.tmin, self.app.tmax])

            # Refrescar leyendas en cada cuadrante
            for ax in self.axes.flat:
                ax.legend(loc="upper right", fontsize=8)

            self.canvas.draw()
            print(f"Shot {shot_num} añadido al análisis 2x2.")

        except FileNotFoundError:
            messagebox.showerror("Error", f"No se encontró el archivo del disparo en la ruta: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error procesando el disparo {shot_num}: {str(e)}")

    def limpiar_comparacion(self):
        """
        Limpia los 4 paneles y restablece las etiquetas.
        """
        for ax in self.axes.flat:
            ax.clear()
        
        self.ax_ip.set_ylabel("Ip (kA)")
        self.ax_bt.set_ylabel("Bt (T)")
        self.ax_ha.set_ylabel("H-alpha (V)")
        self.ax_esp.set_ylabel("Espectro Emitido (u. a.)")
        
        self.ax_ip.set_xlabel("Tiempo (ms)")
        self.ax_bt.set_xlabel("Tiempo (ms)")
        self.ax_ha.set_xlabel("Tiempo (ms)")
        self.ax_esp.set_xlabel("Longitud de onda o Frecuencia")

        for ax in self.axes.flat:
            ax.grid(True, linestyle=":", alpha=0.6)
            ax.set_facecolor("white")

        self.colors = itertools.cycle(['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'])
        self.canvas.draw()