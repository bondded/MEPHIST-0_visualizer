import tkinter as tk
from tkinter import messagebox

from model import DataEngine
from shot_comparison_tab import ShotComparisonTab
from fast_camera_tab import FastCameraTab
from file_manager_tab import FileManagerTab
from preferences_tab import PreferencesTab
from figure_tab import FigureTab


class App(tk.Tk):
    """Clase principal del Visualizador MEPHIST-0."""

    def __init__(self):
        super().__init__()
        self.title("MEPHIST-0 diagnostic visualizer v1.0")
        try:
            icono_app = tk.PhotoImage(file="./src/atom_emoji.png")
            self.iconphoto(True, icono_app)
        except tk.TclError:
            print("No se encontró el archivo del ícono, cargando el predeterminado...")
        self.configure(bg="white")
        try:
            self.state("zoomed")  
        except tk.TclError:
            self.attributes('-zoomed', True)
        self.fuente_ui = ("Roboto", 11)
        self.fuente_negrita = ("Roboto", 11, "bold")

        self.modelo = DataEngine()

        self.tab_bar_frame = tk.Frame(self, bg="#e0e0e0", height=35)
        self.tab_bar_frame.pack(side="top", fill="x")
        self.contenedor_vistas = tk.Frame(self, bg="white")
        self.contenedor_vistas.pack(side="top", fill="both", expand=True)
        
        self.pestañas = {}
        self.pestaña_activa = None
        
        self.crear_mecanismo_pestaña(
            "principal", "Home", self.setup_pantalla_comparativa
        )
        self.crear_mecanismo_pestaña(
            "camara", "Fast camera", self.setup_pantalla_camara
        )
        self.crear_mecanismo_pestaña(
            "mhd", "MHD analysis", self.setup_pantalla_mhd
        )
        self.crear_mecanismo_pestaña(
            "preferences", "Preferences", self.setup_pantalla_configuracion
        )
        self.crear_mecanismo_pestaña(
            "download", "File manager", self.setup_pantalla_descarga
        )
        self.crear_mecanismo_pestaña(
            "figure", "Figure", self.setup_pantalla_figura
        )
        self.mostrar_pantalla("principal")
        self.after(100, self.forzar_redibujo)

        ruta_actualizaciones = "./src/actualizaciones.txt"
        mostrar_actualizaciones = False
        if mostrar_actualizaciones:
            try:
                with open(ruta_actualizaciones, "r", encoding="utf-8") as archivo:
                    contenido = archivo.read()
                messagebox.showinfo("Actualizaciones! ₍^. .^₎Ⳋ", contenido)
            except FileNotFoundError:
                messagebox.showerror("ups", "el archivo de actualizaciones se murió")

    def forzar_redibujo(self):
        """
        Fuerza el redibujado para tener las pantallas centradas
        """
        try:
            self.state("normal")
            self.update_idletasks()
            self.state("zoomed")
        except tk.TclError:
            pass

    def crear_mecanismo_pestaña(self, id_pestaña, titulo_pestaña, setup_funcion):
        """Crea el mecanismo para activar las pestañas y sus funcionalidades."""
        frame_contenido = tk.Frame(self.contenedor_vistas, bg="white")
        boton_pestaña = tk.Button(
            self.tab_bar_frame,
            text=titulo_pestaña,
            font=self.fuente_ui,
            command=lambda: self.mostrar_pantalla(id_pestaña),
            bg="#d0d0d0",
            fg="black",
            activebackground="white",
            activeforeground="black",
            relief="flat",
            bd=0,
            padx=15,
            pady=5
        )
        if id_pestaña in ["download", "preferences"]:
            boton_pestaña.pack(side="right", padx=2, pady=(4, 0))
        else:
            boton_pestaña.pack(side="left", padx=2, pady=(4, 0))

        self.pestañas[id_pestaña] = {
            "frame": frame_contenido,
            "boton": boton_pestaña,
            "titulo": f"MEPHIST-0 diagnostic visualizer v1.0 | {titulo_pestaña}",
        }

        pestañas = ["principal", "camara", "mhd", "download", "figure", "preferences"] 
        if id_pestaña in pestañas:
            setup_funcion(frame_contenido)
        else:
            setup_funcion()

    def mostrar_pantalla(self, nombre_pantalla):
        """Muestra la pantalla seleccionada en la pestaña."""
        if self.pestaña_activa:
            self.pestañas[self.pestaña_activa]["frame"].pack_forget()
            self.pestañas[self.pestaña_activa]["boton"].configure(
                bg="#d0d0d0", fg="black"
            )

        self.pestañas[nombre_pantalla]["frame"].pack(fill="both", expand=True)
        self.pestañas[nombre_pantalla]["boton"].configure(
            bg="white", fg="black"
        )
        self.title(self.pestañas[nombre_pantalla]["titulo"])
        self.pestaña_activa = nombre_pantalla

        if self.pestaña_activa in ["mhd", "figure", "camara", "download", "preferences"]:
            messagebox.showinfo(
                "En desarrollo... ₍^. .^₎Ⳋ",
                "Esta pestaña está siendo actualizada."
            )

    def setup_pantalla_comparativa(self, container_frame):
        """Instancia el panel de pantalla principal."""
        self.comp_tab = ShotComparisonTab(container_frame, self)

    def setup_pantalla_camara(self, container_frame):
        """Instancia el panel de conversión de video para la cámara rápida."""
        self.camara_tab = FastCameraTab(container_frame, self)

    def setup_pantalla_magrec(self, container_frame):
        """Instancia el panel modular para las reconstrucciones de equilibrio."""
        # self.eqrec_tab = EqRecTab(container_frame, self)

    def setup_pantalla_mhd(self, container_frame):
        """Instancia el panel de análisis MHD."""

    def setup_pantalla_descarga(self, container_frame):
        """Instancia el panel de descarga e inspección."""
        self.descarga_tab = FileManagerTab(container_frame, self)


    def setup_pantalla_figura(self, container_frame):
        """Instancia el panel de analisis de figura."""
        self.figura_tab = FigureTab(container_frame, self)

    def setup_pantalla_configuracion(self, container_frame):
        """Instancia el panel de analisis de figura."""
        self.config_tab = PreferencesTab(container_frame, self)

        

if __name__ == "__main__":
    app = App()
    app.mainloop()


# @ Código para reutilización en el futuro.
# ----------------------------------------------------------------------------
# Parámetros por defecto de visualización
#        self.tmin = 6.5  
#        self.tmax = 10  
#        self.mhd = 1  
#        self.spectrogram_max = 75  
#        self.nperseg = 36  
#        self.noverlap = self.nperseg * 0.9  
#        self.q_max = 10  
# ----------------------------------------------------------------------------
# Funciones dedicadas al procesamiento de datos importantes para señales la 
# primera función se encarga de la creación de espectrogramas y la segunda 
# de la creación de espectros de frecuencias. Ambas funciones deben salir de
# este módulo.
# def hacer_espectrograma(tiempo, señal, nperseg=512, noverlap=256, fmin_contraste=2):
#     dt = np.mean(np.diff(tiempo))
#     fs = 1 / dt
#     f, t_rel, Sxx = signal.spectrogram(
#         señal, fs, nperseg=nperseg, noverlap=noverlap, window="hann"
#     )
#     t_real = t_rel + tiempo[0]
#     f_mask = f > fmin_contraste
#     if np.any(f_mask):
#         vmax = np.max(Sxx[f_mask, :]) * 0.1
#     else:
#         vmax = np.max(Sxx) * 0.2
#     return t_real, f, Sxx, vmax
# 
# 
# def hacer_espectro(tiempo, señal, hanning=True):
#     n = len(señal)
#     dt = np.mean(np.diff(tiempo))
#     ys = señal - np.mean(señal)
#     if hanning:
#         ys *= np.hanning(n)
#     hs = np.fft.rfft(ys)
#     fs = np.fft.rfftfreq(n, dt)
#     amps = np.abs(hs) * (2.0 / n)
#     return fs, amps
# ----------------------------------------------------------------------------
# @ Reutilizar
#    def actualizar_rango_tiempo(self):
#        try:
#            nuevo_tmin = float(self.entry_tmin.get())
#            nuevo_tmax = float(self.entry_tmax.get())
#
#            if nuevo_tmin < nuevo_tmax:
#                self.tmin = nuevo_tmin
#                self.tmax = nuevo_tmax
#
#                if self.pestaña_activa == "principal" and hasattr(self, "axes"):
#                    for ax in self.axes.flat:
#                        if ax == self.axes[3, 1]: continue
#                        ax.set_xlim([self.tmin, self.tmax])
#                    self.canvas.draw()
#                    
#                elif self.pestaña_activa == "principal":
#                    # La pestaña de comparación gestiona sus propios rangos y normalizaciones avanzadas (tau, sync).
#                    # Dejamos que use sus controles internos.
#                    pass
#                    
#                print(f"Rango de tiempo sincronizado: {self.tmin} - {self.tmax} ms")
#            else:
#                print("Error: tmin debe ser menor que tmax")
#        except ValueError:
#            print("Error: Ingrese valores numéricos válidos")
#
#    def load_shot(self):
#        # Ignorar acción si estamos en la pestaña de comparación, cámara o eqrec
#        if self.pestaña_activa in ["camara", "eqrec", "principal"]:
#            print("Para esta pestaña, use los controles internos del panel que aparecen abajo.")
#            messagebox.showinfo("Aviso", "Utiliza el botón 'Load Shots' dentro de la barra de esta pestaña.")
#        else:
#            # Flujo estándar para Principal/mhd
#            shot_num = simpledialog.askstring("Cargar Shot", "Ingrese número de Shot:")
#            if not shot_num: return
#            try:
#                self.modelo.cargar_shot(shot_num)
#                self.actualizar_gráficos()
#                self.actualizar_gráficos_mhd()
#            except Exception as e:
#                messagebox.showerror("Error", f"No se pudo cargar el shot: {str(e)}")
#
#    def limpiar(self):
#        if self.pestaña_activa == "camara":
#            self.camara_tab.input_folder_var.set("")
#            self.camara_tab.output_file_var.set("")
#        elif self.pestaña_activa == "eqrec":
#            self.eqrec_tab.input_folder_var.set("")
#            self.eqrec_tab.output_file_var.set("")
#        elif self.pestaña_activa == "principal":
#            # La limpieza se hace con el botón 'Clear Shots' de su propio toolbar
#            messagebox.showinfo("Aviso", "Utiliza el botón 'Clear Shots' dentro de la barra de esta pestaña.")
#        else:
#            frame_actual = self.pestañas[self.pestaña_activa]["frame"]
#            for widget in frame_actual.winfo_children():
#                widget.destroy()
#            if self.pestaña_activa == "principal":
#                self.setup_graficos()
#            elif self.pestaña_activa == "mhd":
#                self.setup_graficos_mhd()
# ----------------------------------------------------------------------------
# @ Reutilizar
#    def actualizar_gráficos(self):
#        if not hasattr(self, "axes"): return
#        tiempo_Ip, corriente_Ip = self.modelo.obtener_corriente_plasma()
#        tiempo_VL2, VL2 = self.modelo.obtener_voltaje_loop(2)
#        tiempo_VL7, VL7 = self.modelo.obtener_voltaje_loop(7)
#        tiempo_CS, corriente_CS = self.modelo.obtener_corriente_inductor()
#        tiempo_PF1, corriente_PF1 = self.modelo.obtener_corriente_pol_coil(1)
#        tiempo_PF3, corriente_PF3 = self.modelo.obtener_corriente_pol_coil(1)
#        tiempo_TF, campo_TF = self.modelo.obtener_torfield()
#        tiempo_Ha, Ha = self.modelo.obtener_Ha()
#        tiempo_densidad, densidad = self.modelo.obtener_densidad_plasma()
#        longitud_onda, intensidad = self.modelo.obtener_espectro_emision()
#
#        # Panel (0,0) - Ip & U_loop
#        ax1 = self.axes[0, 0]
#        ax1.clear()
#        ax1.plot(tiempo_Ip, corriente_Ip, color="black")
#        ax1.set_ylabel("Ip (kA)")
#        ax1.set_xlim([self.tmin, self.tmax])
#        ax1.grid()
#
#        if hasattr(self, "ax1a"): self.ax1a.remove()
#        self.ax1a = ax1.twinx()
#        self.ax1a.set_xlim([self.tmin, self.tmax])
#        self.ax1a.plot(tiempo_VL2, (VL2 + VL7) / 2, "r", label="(VL2 + VL7)/2")
#        self.ax1a.set_ylabel("U loop (V)", color="r")
#
#        # Panel (1,0)
#        ax2 = self.axes[1, 0]
#        ax2.clear()
#        ax2.plot(tiempo_CS, corriente_CS, "k", label="CS")
#        ax2.set_ylabel("I CS (kA)")
#        ax2.grid()
#
#        if hasattr(self, "ax2a"): self.ax2a.remove()
#        self.ax2a = ax2.twinx()
#        self.ax2a.set_xlim([self.tmin, self.tmax])
#        self.ax2a.plot(tiempo_PF1, corriente_PF1, "r", label="PF1/2")
#        self.ax2a.plot(tiempo_PF3, corriente_PF3, "g", label="PF3/4")
#        self.ax2a.set_ylabel("I PF (kA)", color="r")
#
#        # Panel (2,0)
#        ax3 = self.axes[2, 0]
#        ax3.clear()
#        ax3.plot(tiempo_TF, campo_TF, color="black", label="Bt")
#        ax3.set_ylabel("Bt (mT)")
#        ax3.grid()
#
#        # Panel (3,0)
#        ax4 = self.axes[3, 0]
#        ax4.clear()
#        ax4.set_ylabel(r"$\tau$ (ms)")
#        ax4.grid()
#
#        # Panel (0,1)
#        ax5 = self.axes[0, 1]
#        ax5.clear()
#        ax5.plot(tiempo_Ha, Ha, color="magenta", label="H-alpha")
#        ax5.set_ylabel("Ha (Int. rel.)")
#        ax5.grid()
#
#        # Panel (1,1)
#        ax6 = self.axes[1, 1]
#        ax6.clear()
#        ax6.plot(tiempo_densidad, densidad, color="black", label="ne")
#        ax6.set_ylabel("ne (m-3)")
#        ax6.grid()
#
#        # Panel (2,1)
#        ax7 = self.axes[2, 1]
#        ax7.clear()
#        ax7.set_ylabel("Te (KeV)")
#        ax7.grid()
#
#        # Panel (3,1)
#        ax8 = self.axes[3, 1]
#        ax8.clear()
#        ax8.plot(longitud_onda, intensidad, color="black")
#        ax8.set_ylabel("u. a.")
#        ax8.grid()
#
#        self.fig.tight_layout()
#        self.canvas.draw()
# ----------------------------------------------------------------------------
# @ Reutilizar     
#    def setup_graficos(self):
#        master_frame = self.pestañas["principal"]["frame"]
#        self.fig = Figure(figsize=(14, 6))
#        self.axes = self.fig.subplots(4, 2)
#        
#        for row in range(4):
#            for col in range(2):
#                if row == 3 and col == 1: continue
#                self.axes[row, col].sharex(self.axes[0, 0])
#
#        ejes_sincronizados = [self.axes[r, c] for r in range(4) for c in range(2) if not (r == 3 and c == 1)]
#        self.fig.tight_layout()
#        self.canvas = FigureCanvasTkAgg(self.fig, master=master_frame)
#        self.canvas.get_tk_widget().pack(fill="both", expand=True)
#
#        self.cursor = MultiCursor(
#            self.canvas, ejes_sincronizados, color="red", linestyle="--", lw=1,
#            horizOn=False, vertOn=True, useblit=True
#        )
#        self.canvas.draw()
# ----------------------------------------------------------------------------
# @ Reutilizar
#    def setup_graficos_mhd(self):
#        master_frame = self.pestañas["mhd"]["frame"]
#        self.fig_mhd = Figure(figsize=(8, 8), facecolor="white")
#        gs = GridSpec(4, 2, figure=self.fig_mhd)
#        
#        self.axes_mhd = [
#            self.fig_mhd.add_subplot(gs[0, 0]),
#            self.fig_mhd.add_subplot(gs[1, 0]),
#            self.fig_mhd.add_subplot(gs[2, 0]),
#            self.fig_mhd.add_subplot(gs[3, 0]),
#            self.fig_mhd.add_subplot(gs[0:2, 1]),
#            self.fig_mhd.add_subplot(gs[2:4, 1])
#        ]
#
#        for i, ax in enumerate(self.axes_mhd):
#            ax.set_facecolor("white")
#            ax.set_title(f"Mirnov {i}", fontsize=9)
#            if i < 5: ax.sharex(self.axes_mhd[0])
#
#        self.fig_mhd.tight_layout()
#        self.canvas_mhd = FigureCanvasTkAgg(self.fig_mhd, master=master_frame)
#        self.canvas_mhd.get_tk_widget().pack(fill="both", expand=True)
#        self.canvas_mhd.draw()
#
#    def actualizar_gráficos_mhd(self):
#        if not hasattr(self, "axes_mhd"): return
#        tiempo_Ip, corriente_Ip = self.modelo.obtener_corriente_plasma()
#        tiempo_VL2, VL2 = self.modelo.obtener_voltaje_loop(2)
#        tiempo_VL7, VL7 = self.modelo.obtener_voltaje_loop(7)
#
#        ax1 = self.axes_mhd[0]
#        ax1.clear()
#        ax1.plot(tiempo_Ip, corriente_Ip, color="black")
#        ax1.set_ylabel("Ip (kA)")
#        ax1.set_xlim([self.tmin, self.tmax])
#        ax1.grid()
#
#        if hasattr(self, "ax1_mhd_twin"): self.ax1_mhd_twin.remove()
#        self.ax1_mhd_twin = ax1.twinx()
#        self.ax1_mhd_twin.set_xlim([self.tmin, self.tmax])
#        self.ax1_mhd_twin.plot(tiempo_VL2, (VL2 + VL7) / 2, "r")
#
#        tiempo_Ha, Ha = self.modelo.obtener_Ha()
#        ax2 = self.axes_mhd[1]
#        ax2.clear()
#        ax2.plot(tiempo_Ha, Ha, color="magenta")
#        ax2.set_ylabel("Ha")
#        ax2.grid()
#
#        a, R = 0.13, 0.25
#        time_B_phi, data_B_phi = self.modelo.obtener_torfield()
#        B_phi_sinc = np.interp(tiempo_Ip, time_B_phi, data_B_phi)
#        safe_Ip = np.where(corriente_Ip > 0.1, corriente_Ip, np.nan)
#        q_a = (5 * (a**2) * B_phi_sinc) / (R * safe_Ip / 1000)
#
#        ax3 = self.axes_mhd[2]
#        ax3.clear()
#        ax3.plot(tiempo_Ip, q_a, color="blue")
#        ax3.set_ylabel("qa")
#        ax3.set_ylim([0, self.q_max])
#        ax3.grid()
#
#        self.axes_mhd[3].clear()
#        for i in range(1, 17):
#            try:
#                time, data = self.modelo.obtener_mhd(i)
#                self.axes_mhd[3].plot(time, data)
#            except Exception: continue
#        self.axes_mhd[3].grid()
#
#        time_mp, data_mp = self.modelo.obtener_mhd(self.mhd)
#        t_esp, f_esp, Sxx_esp, v_max = hacer_espectrograma(time_mp, data_mp, self.nperseg, self.noverlap)
#        
#        ax4 = self.axes_mhd[4]
#        ax4.clear()
#        ax4.pcolormesh(t_esp, f_esp, Sxx_esp, shading="gouraud", cmap="turbo", vmin=0, vmax=v_max)
#        ax4.set_ylabel("f (kHz)")
#        ax4.set_ylim([0, self.spectrogram_max])
#        ax4.set_xlim([self.tmin, self.tmax])
#
#        ax5 = self.axes_mhd[5]
#        ax5.clear()
#        fs, amps = hacer_espectro(time_mp, data_mp, False)
#        ax5.plot(fs, amps)
#        ax5.set_xlabel("f (kHz)")
#        ax5.grid()
#
#        self.fig_mhd.tight_layout()
#        self.canvas_mhd.draw()