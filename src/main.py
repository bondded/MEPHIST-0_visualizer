from model import DataEngine
import customtkinter 
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.widgets import MultiCursor
from matplotlib.gridspec import GridSpec
import numpy as np
from scipy import signal



def hacer_espectrograma(tiempo, señal, nperseg=512, noverlap=256, fmin_contraste=2):
    """
        Recibe una señal y entrega su espectrograma
    """
    dt = np.mean(np.diff(tiempo))
    fs = 1 / dt

    f, t_rel, Sxx = signal.spectrogram(
                        señal, fs, 
                        nperseg=nperseg, 
                        noverlap=noverlap, 
                        window='hann'
    )

    t_real = t_rel + tiempo[0]
    f_mask = f > fmin_contraste
    if np.any(f_mask):
        vmax = np.max(Sxx[f_mask, :]) * 0.1
    else:
        vmax = np.max(Sxx) * 0.2

    return t_real, f, Sxx, vmax


def hacer_espectro(tiempo, señal, hanning=True):
    """
        Recibe una señal y entrega su espectro
    """
    n = len(señal)
    dt = np.mean(np.diff(tiempo))
    f_muestreo = 1 / dt
    ys = señal - np.mean(señal)
    if hanning:
        ys *= np.hanning(n)

    hs = np.fft.rfft(ys)
    fs = np.fft.rfftfreq(n, dt)
    amps = np.abs(hs) * (2.0 / n)

    return fs, amps


        
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # Parámetros del dibujado
        customtkinter.set_widget_scaling(2)  
        customtkinter.set_window_scaling(1)

        # Parámetros de los datos
        self.tmin = 6.5                               # Tiempo minimo (ms)
        self.tmax = 10                                # Tiempo máximo (ms)
        self.mirnov = 1                               # Bobina mirnov
        self.spectrogram_max = 75                     # Frecuencia máxima (kHz)
        self.nperseg = 36                             # nperseg 
        self.noverlap = self.nperseg * 0.9            # overlap
        self.q_max = 10                               # Límite fractor de seguridad

        # Configuraciones de la aplicacion
        self.fuente_ui = customtkinter.CTkFont(
            family="Roboto", 
            size=100
        )
        self.fuente_negrita = customtkinter.CTkFont(
            family="Roboto",
            size=100,
            weight="bold"
        )
        self.modelo = DataEngine()
        self.title("visualizador MEPHIST-0")
        self.geometry("1920x1080")
        self.color_fondo = "white" 
        self.configure(fg_color=self.color_fondo)
        self.grid_columnconfigure((0, 1), weight=1)

        # Frame barra superior
        self.toolbar_frame = customtkinter.CTkFrame(
            self,
            fg_color="white",
            height=60,
            corner_radius=0
        )
        self.toolbar_frame.grid(
            row=0, 
            column=0, 
            sticky="ew", 
            columnspan=2
        )

        # Botón cargar shot
        self.load_shot_btn = customtkinter.CTkButton(
            self.toolbar_frame,
            text="Cargar shot",
            font=self.fuente_negrita,
            command=self.load_shot,
            corner_radius=1,
            fg_color="gray20",
            hover_color='gray50',
            text_color='white'
        )
        self.load_shot_btn.pack(
            side="left", 
            padx=10, 
            pady=10
        )

        # Botón limpiar
        self.clear_btn = customtkinter.CTkButton(
            self.toolbar_frame, 
            text="Limpiar",
            font=self.fuente_negrita, 
            command=self.limpiar,
            corner_radius=1,
            fg_color="gray20",
            hover_color="gray50",
            text_color="white",
        )
        self.clear_btn.pack(
            side="left", 
            padx=5, 
            pady=5
        )

        # Configuracion del límite de tiempo
        self.label_tmin = customtkinter.CTkLabel(
            self.toolbar_frame,
            text="t min:",
            font=self.fuente_negrita,
            text_color="black"
        )
        self.label_tmin.pack(side="left", padx=(20, 5)) 
        self.entry_tmin = customtkinter.CTkEntry(
            self.toolbar_frame,
            width=60,
            corner_radius=2
        )
        self.entry_tmin.insert(0, str(self.tmin)) 
        self.entry_tmin.pack(
            side="left", 
            padx=5
        )

        self.label_tmax = customtkinter.CTkLabel(
            self.toolbar_frame,
            text="t max:",
            font=self.fuente_negrita,
            text_color="black"
        )
        self.label_tmax.pack(
            side="left", 
            padx=(10, 5)
        )
        self.entry_tmax = customtkinter.CTkEntry(
            self.toolbar_frame,
            width=60,
            corner_radius=2
        )
        self.entry_tmax.insert(0, str(self.tmax)) 
        self.entry_tmax.pack(
            side="left",
            padx=5
        )

        # Bindeo de la tecla Enter
        self.entry_tmin.bind(
            "<Return>", 
            lambda event: self.actualizar_rango_tiempo()
        )
        self.entry_tmax.bind(
            "<Return>", 
            lambda event: self.actualizar_rango_tiempo()
        )

        # Botón para aplicar rango de tiempo
        self.apply_time_btn = customtkinter.CTkButton(
            self.toolbar_frame, 
            text="Aplicar",
            font=self.fuente_negrita, 
            width=100,
            command=self.actualizar_rango_tiempo,
            fg_color="gray20",
            hover_color="gray50",
            text_color="white",
            corner_radius=1
        )
        self.apply_time_btn.pack(
            side="left", 
            padx=15
        )

        # Botón de pantalla 2
        self.pantalla2_btn = customtkinter.CTkButton(
            self.toolbar_frame, 
            text="Mirnov",
            font=self.fuente_negrita, 
            command=lambda: self.mostrar_pantalla("mirnov"),
            corner_radius=1,
            fg_color="gray20",
            hover_color="gray50",
            text_color="white",
        )
        self.pantalla2_btn.pack(
            side="right", 
            padx=10, 
            pady=10
        )

        # Botón de pantalla 1
        self.pantalla1_btn = customtkinter.CTkButton(
            self.toolbar_frame, 
            text="Principal",
            font=self.fuente_negrita, 
            command=lambda: self.mostrar_pantalla("principal"),
            corner_radius=1,
            fg_color="gray20",
            hover_color="gray50",
            text_color="white",
        )
        self.pantalla1_btn.pack(
            side="right", 
            padx=10, 
            pady=10
        )
        
        # Contenedor pantallas
        self.contenedor_vistas = customtkinter.CTkFrame(
            self, 
            fg_color="white"
        )
        self.contenedor_vistas.grid(
            row=1, 
            column=0, 
            sticky="nsew", 
            padx=10, 
            pady=10, 
            columnspan=2
        )
        self.grid_rowconfigure(1, weight=1) 
        self.pantalla_1= customtkinter.CTkFrame(
            self.contenedor_vistas,                      # Pantalla 1
            fg_color="white"
        ) 
        self.pantalla_mirnov = customtkinter.CTkFrame(
            self.contenedor_vistas,                      # Pantalla 2
            fg_color="white"
        )

        # Aplicar placeholders
        self.setup_graficos() 
        self.setup_graficos_mirnov() 
        self.mostrar_pantalla("principal")


    def actualizar_rango_tiempo(self):
        """
            Esta función actualiza el rango de tiempo en los ejes en 
            común

                - por ahora funciona solamente para la pantalla 
                  principal.
        """
        try:
            nuevo_tmin = float(self.entry_tmin.get())
            nuevo_tmax = float(self.entry_tmax.get())

            if nuevo_tmin < nuevo_tmax:
                self.tmin = nuevo_tmin
                self.tmax = nuevo_tmax
                

                for ax in self.axes.flat:
                    if ax == self.axes[3,1]: 
                        continue
                    ax.set_xlim([self.tmin, self.tmax])
                
                self.canvas.draw()
                # self.canvas_mirnov.draw()

                print(f"Rango actualizado: {self.tmin} - {self.tmax}")
            else:
                print("Error: tmin debe ser menor que tmax")
        except ValueError:
            print("Error: Ingrese valores numéricos válidos")


    def load_shot(self):
        """
            Carga los shots al apretar el botón "cargar shot" 
            además imprime la estructura del archivo seleccionado
        """
        dialog = customtkinter.CTkInputDialog(
            text="Ingrese número de Shot:", 
            title="Cargar Shot"
        )
        shot_num = dialog.get_input()
        try:
            self.modelo.cargar_shot(shot_num)
            print(f"El shot {shot_num} ha sido cargado con éxito")
            mensaje = self.modelo.obtener_estructura_archivo(shot_num)
            print(mensaje)

            self.actualizar_gráficos()
            self.actualizar_gráficos_mirnov()
            return
        except Exception as e:
            print(e)
            print("No se ha podido cargar el shot")
            return


    def limpiar(self):
        """
            Limpia los datos en las pantallas antes de cargar otro shot. 
            Al menos funciona para la pantalla principal
        """
        for widget in self.pantalla_1.winfo_children():
            widget.destroy()
            
        self.setup_graficos()
        print("Visualizador reiniciado.")


    def mostrar_pantalla(self, nombre_pantalla):
        """
            Configura los botones de "pestaña" para moverse entre panta-
            llas principal y mirnov
        """

        self.pantalla_1.pack_forget()
        self.pantalla_mirnov.pack_forget()

        if nombre_pantalla == "principal":
            self.pantalla_1.pack(
                fill="both", 
                expand=True
            )
            self.title("Visualizador MEPHIST-0 - Señales Principales")
        elif nombre_pantalla == "mirnov":
            self.pantalla_mirnov.pack(
                fill="both", 
                expand=False
            )
            self.title("Visualizador MEPHIST-0 - Análisis de Mirnov")


    def setup_graficos(self):
        """
            Genera automáticamente placeholders para los gráficos de la 
            primera pantalla
        """
        self.fig = Figure(figsize=(14, 6))
        self.axes = self.fig.subplots(4, 2)
        self.axes[1, 0].sharex(self.axes[0, 0])
        self.axes[2, 0].sharex(self.axes[0, 0])
        self.axes[3, 0].sharex(self.axes[0, 0])
        self.axes[0, 1].sharex(self.axes[0, 0])
        self.axes[1, 1].sharex(self.axes[0, 0])
        self.axes[2, 1].sharex(self.axes[0, 0])

        ejes_sincronizados = [
            self.axes[0, 0], self.axes[1, 0], self.axes[2, 0],
            self.axes[3, 0], self.axes[0, 1], self.axes[1, 1],
            self.axes[2, 1]
        ]




        self.fig.tight_layout()
        self.canvas = FigureCanvasTkAgg(
            self.fig, 
            master=self.pantalla_1
        )
        
        self.canvas.get_tk_widget().pack(
            fill="both", 
            expand=True
        )
        self.cursor = MultiCursor(
            self.canvas,
            ejes_sincronizados,
            color='red',
            linestyle='--',
            lw=1,
            horizOn=False,
            vertOn=True,
            useblit=True
        )

        self.canvas.draw()


    def setup_graficos_mirnov(self):
        """
            Genera automáticamente placeholders para los gráficos de la 
            segunda pantalla
        """
        
        self.fig_mirnov = Figure(
            figsize=(8, 8), 
            facecolor='white'
        )
        
        gs = GridSpec(4, 2, figure=self.fig_mirnov)
        self.axes_mirnov = []
        ax0 = self.fig_mirnov.add_subplot(gs[0, 0])
        ax1 = self.fig_mirnov.add_subplot(gs[1, 0])
        ax2 = self.fig_mirnov.add_subplot(gs[2, 0])
        ax3 = self.fig_mirnov.add_subplot(gs[3, 0])
        ax4 = self.fig_mirnov.add_subplot(gs[0:2, 1]) 
        ax5 = self.fig_mirnov.add_subplot(gs[2:4, 1]) 

        self.axes_mirnov = [ax0, ax1, ax2, ax3, ax4, ax5]

        for i, ax in enumerate(self.axes_mirnov):
            ax.set_facecolor('white')
            ax.set_title(f"Mirnov {i}", fontsize=9)
            if i < 5: 
                ax.sharex(self.axes_mirnov[0])

        self.fig_mirnov.tight_layout()
        self.canvas_mirnov = FigureCanvasTkAgg(
            self.fig_mirnov, 
            master=self.pantalla_mirnov
        )
        self.canvas_mirnov.get_tk_widget().pack(
            fill="both", 
            expand=True
        )



    def actualizar_gráficos(self):
        """
            Carga los datos para la segunda pantalla
        """
        tiempo_Ip, corriente_Ip = self.modelo.obtener_corriente_plasma()
        tiempo_VL2, VL2 = self.modelo.obtener_voltaje_loop(2)
        tiempo_VL7, VL7 = self.modelo.obtener_voltaje_loop(7)
        tiempo_CS, corriente_CS = self.modelo.obtener_corriente_inductor()
        tiempo_PF1, corriente_PF1  = self.modelo.obtener_corriente_pol_coil(1)
        tiempo_PF3, corriente_PF3  = self.modelo.obtener_corriente_pol_coil(1)
        tiempo_TF, campo_TF = self.modelo.obtener_torfield()
        tiempo_Ha, Ha = self.modelo.obtener_Ha()
        tiempo_densidad, densidad = self.modelo.obtener_densidad_plasma()
        longitud_onda, intensidad = self.modelo.obtener_espectro_emision()

        # Gráfico 1
        ax1 = self.axes[0,0]
        ax1.clear()
        ax1.plot(
            tiempo_Ip, 
            corriente_Ip,
            color='black'
        )
        ax1.set_ylabel("Ip (kA)")
        ax1.set_xlim([self.tmin, self.tmax])
        ax1.grid()
        ax1a = ax1.twinx()
        ax1a.set_xlim([self.tmin, self.tmax])
        ax1a.plot(tiempo_VL2, (VL2 + VL7)/2, 'r', label='(VL2 + VL7)/2')
        ax1a.plot([], [], 'k', label='Ip')
        ax1a.legend()
        ax1a.set_ylabel("U loop (V)", color='r')

        # Gráfico 2
        ax2 = self.axes[1,0]
        ax2.clear()
        ax2.plot(tiempo_CS, corriente_CS,'k',  label='CS')
        ax2.set_ylabel('I CS (kA)',color='k')
        ax2.set_yticks(range(0,12,2))
        ax2.grid()
        ax2a = ax2.twinx()
        ax2a.set_xlim([self.tmin,self.tmax])
        ax2a.set_ylabel('I PF (kA)',color='r')
        ax2a.plot(tiempo_PF1, corriente_PF1,'r',label='PF1/2')
        ax2a.plot(tiempo_PF3, corriente_PF3,'g',label='PF3/4')
        ax2a.plot([], [], 'k', label = 'CS')
        ax2a.legend()

        # Gráfico 3
        ax3 = self.axes[2,0]
        ax3.clear()
        ax3.plot(tiempo_TF, campo_TF,
                color='black',
                label='campo toroidal')
        ax3.set_ylabel("Bt (mT)")
        ax3.grid()
        ax3.legend()

        # Gráfico 4
        ax4 = self.axes[3,0]
        ax4.clear()
        ax4.plot(np.array([]), np.array([]),
                color='black',
                label='tiempo de confinamiento')
        ax4.set_ylabel(r"$\tau$ (ms)")
        ax4.grid()
        ax4.legend()

        # Gráfico 5
        ax5 = self.axes[0,1]
        ax5.clear()
        ax5.plot(tiempo_Ha, Ha,
                color='magenta',
                label='emision H-alpha')
        ax5.set_ylabel("Ha (Int. rel.)")
        ax5.grid()
        ax5.legend()

        # Gráfico 6
        ax6 = self.axes[1,1]
        ax6.clear()
        ax6.plot(tiempo_densidad, densidad,
                color='black',
                label='densidad electronica')
        ax6.set_ylabel("ne (m-3)")
        ax6.grid()
        ax6.legend()

        # Gráfico 7
        ax7 = self.axes[2,1]
        ax7.clear()
        ax7.plot(np.array([]), np.array([]),
                color='black',
                label='temperatura')
        ax7.set_ylabel("Te (KeV)")
        ax7.grid()
        ax7.legend()

        # Gráfico 8
        ax8 = self.axes[3,1]
        ax8.clear()
        ax8.plot(longitud_onda, intensidad,
                color='black',
                label='espectro de emision')
        ax8.set_ylabel("u. a.")
        ax8.grid()
        ax8.legend()
        self.fig.tight_layout()
        self.canvas.draw()


    def actualizar_gráficos_mirnov(self):
        """
            Carga los datos en la segunda pantalla
        """

        # Figura 1: corriente y voltaje loop
        tiempo_Ip, corriente_Ip = self.modelo.obtener_corriente_plasma()
        tiempo_VL2, VL2 = self.modelo.obtener_voltaje_loop(2)
        tiempo_VL7, VL7 = self.modelo.obtener_voltaje_loop(7)

        ax1 = self.axes_mirnov[0]
        ax1.clear()
        ax1.plot(tiempo_Ip, corriente_Ip,
                color='black')
        ax1.set_ylabel("Ip (kA)")
        ax1.set_xlim([self.tmin, self.tmax])
        ax1.grid()
        ax1a = ax1.twinx()
        ax1a.set_xlim([self.tmin, self.tmax])
        ax1a.plot(tiempo_VL2, (VL2 + VL7)/2, 'r', label='(VL2 + VL7)/2')
        ax1a.plot([], [], 'k', label='Ip')
        ax1a.legend()
        ax1a.set_ylabel("U loop (V)", color='r')

        # Figura 2: emisión Ha
        tiempo_Ha, Ha = self.modelo.obtener_Ha()
        ax2 = self.axes_mirnov[1]
        ax2.clear()
        ax2.plot(tiempo_Ha, Ha,
                color='magenta',
                label='emision H-alpha')
        ax2.set_ylabel("Ha (Int. rel.)")
        ax2.grid()
        ax2.legend()

        # Figura 3: factor de seguridad
        a = 0.13
        R = 0.25

        time_B_phi, data_B_phi = self.modelo.obtener_torfield()
        B_phi_sinc = np.interp(tiempo_Ip, time_B_phi, data_B_phi)
        threshold = 0.1
        safe_Ip = np.where(corriente_Ip > threshold, corriente_Ip, np.nan)
        q_a = (5 * a**2 * B_phi_sinc ) / (R * safe_Ip / 1000)

        ax3 = self.axes_mirnov[2]
        ax3.plot(tiempo_Ip, q_a
                    , color='blue'
                    , label='factor de seguridad')
        ax3.set_ylabel(r'qa')
        ax3.set_xlim([self.tmin, self.tmax])
        ax3.set_ylim([0, self.q_max])
        ax3.grid()
        ax3.legend()

        # Figura 4: bobinas mirnov
        self.axes_mirnov[3].clear()
        for i in range(1, 17):
            try:
                time, data = self.modelo.obtener_mirnov(i)
                self.axes_mirnov[3].plot(time, data, label=f'MP{i}')
            except:
                print(f"Mirnov {i} no encontrada")
                continue
        self.axes_mirnov[3].grid()


        # Figura 5: espectrograma
        time_mp, data_mp = self.modelo.obtener_mirnov(self.mirnov) 
        t_esp, f_esp, Sxx_esp, v_max = hacer_espectrograma(
            time_mp,
            data_mp,
            self.nperseg, 
            self.noverlap
        )
        mesh = self.axes_mirnov[4].pcolormesh(
            t_esp,
            f_esp, 
            Sxx_esp, 
            shading='gouraud', 
            cmap='turbo',
            vmin=0, 
            vmax=v_max
        ) 
        self.axes_mirnov[4].plot([], [], ' ', label=f'Mirnov {self.mirnov}')
        self.axes_mirnov[4].set_ylabel('f (kHz)')
        self.axes_mirnov[4].set_xlabel('tiempo (ms)')
        self.axes_mirnov[4].set_ylim([0, self.spectrogram_max])
        self.axes_mirnov[4].set_xlim([self.tmin, self.tmax])
        self.axes_mirnov[4].legend()

        # Figura 6: espectro de bobina mirnov
        self.axes_mirnov[5].clear()
        fs, amps = hacer_espectro(time_mp, data_mp, False)
        self.axes_mirnov[5].plot(fs, amps)
        self.axes_mirnov[5].set_ylabel('amp (V)')
        self.axes_mirnov[5].set_xlabel('frecuencia (kHz)')
        self.axes_mirnov[5].grid()
        self.fig_mirnov.tight_layout()
        self.canvas_mirnov.draw()


app = App()
app.mainloop()