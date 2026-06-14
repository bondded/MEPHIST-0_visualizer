import h5py
import yaml
from pathlib import Path
import numpy as np
import os
import glob
import csv
from mephistdatakit.client import Client
import warnings
import numpy as np
from scipy import signal

# Funciones para analisis de datos
#-----------------------------------------------------------------------------
def set_zero(sig):
    """
    Provides subtraction of baseline / Вычитает базовую линию.
    Args:
        sig (numpy.ndarray): одномерный массив / 1D array

    Returns:
        numpy.ndarray
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            subtracted = sig-np.average(sig[1:180])
            return subtracted
    except:
        print("Failed to subtract baseline")
        return sig


def integrate(time,sig):
    """
    Provides signal integration / Интегрирует сигнал.

    Args:
        time,sig (numpy.ndarray, numpy.ndarray): 2 одномерных массива / Two 1D arrays

    Returns:
        numpy.ndarray
    """
    out_sig = np.zeros_like(sig)
    for i in range(1, len(sig)):
        dt = time[i] - time[i - 1]
        out_sig[i] = out_sig[i - 1] + (sig[i] + sig[i - 1]) * dt / 2
    return out_sig


def derive(time,sig):
    """
    Provides signal differentiation / Дифференцирует сигнал.

    Args:
        time,sig (numpy.ndarray, numpy.ndarray): 2 одномерных массива / Two 1D arrays

    Returns:
        numpy.ndarray
    """
    dt = (time[-1]-time[0])/(len(time)-1)
    out_sig = np.zeros_like(sig)
    for i in range(1,len(sig)-1):
        out_sig[i] = (sig[i+1]-sig[i-1])/(2*dt)
    return out_sig

def fft_filter(time,sig,fc):
    """
        Provides smoothing with lowpass filter / Сглаживание сигналов с помощью фильтра нижних частот.
    fc - cutoff frequency / частота отсечки
    Args:
        time,sig, fc (numpy.ndarray, numpy.ndarray, int): 2 одномерных массива и число / Two 1D arrays and a number

    Returns:
        numpy.ndarray
    """
    # Define the sampling frequency and the cutoff frequency
    dt = (time[-1]-time[0])/(len(time)-1)
    fs = 1/dt # Hz
    #   fc = 100 # Hz
    # Calculate the normalized cutoff frequency
    wn = fc / (fs / 2)
    # Design a Butterworth low pass filter with order 4
    b, a = signal.butter(4, wn, 'low')
    # Apply the filter to the signal
    y = signal.lfilter(b, a, sig)
    return y

def preprocess(sig):
    """
    Removes spikes from raw signal. / Удаляет выбросы из сырого сигнала.
        Was relevant for old ADCs, may not be needed with LTR. / Было актуально для старых АЦП, с LTR можно не использовать.
    Args:
        sig (numpy.ndarray): 1D array / одномерный массив

    Returns:
        numpy.ndarray
    """
    d2y_max = 1
    sig2 =sig
    sig2[np.isnan(sig2)] = 0
    for i in range(len(sig2)-1):
        if abs(sig2[i+1] -  sig2[i] )>d2y_max:
            sig2[i+1] =  sig2[i]
    return sig2

def RC_transform(time,sig,R,C):
    """
    Accounts for HF noise on the measurement line? / Учитывает ВЧ наводки на линию измерения?
        TODO verify with I. Pashkov / уточнить у И.Пашкова

    Args:
        time,sig, R,C (numpy.ndarray, numpy.ndarray, float, float)

    Returns:
        numpy.ndarray
    """
    dt = (time[-1]-time[0])/(len(time)-1)
    out_sig = np.zeros_like(sig)
    for i in range(len(sig)-1):
        out_sig[i+1] = out_sig[i]+dt*((sig[i]/R)-(out_sig[i]/(R*C)))
    out_sig = out_sig/C
    return out_sig

def chamber_delay(time, signal, tau):
    # provides signal delay for chamber response
    # Args:
    #     time (ms), signal (numpy.ndarray, numpy.ndarray): 2 1D arrays / 2 одномерных массива
    #     tau (float): delay time in ms

    # Returns:
    #     numpy.ndarray
    time = time - time[0]
    delay = np.zeros_like(signal)
    delay = (1/tau)*np.exp(-time/tau) * ((integrate(time, (signal*np.exp(time/tau)))))
    return delay

#-----------------------------------------------------------------------------
class DataEngine:
    def __init__(self):
        try:
            self.client = Client()
        except Exception as e:
            print(f"Error crítico al iniciar el motor: {e}")

        raiz_dir = Path(__file__).parent.parent
        self.ruta_yaml = raiz_dir / "MephistDataKit" / "config.yaml"

    def test_conexion(self):
        try:
            self.client.test_connection()
            return True, "✅ Conexión exitosa"
        except Exception as e:
            return False, "❌ No se puede conectar al servidor."

    def actualizar_token_yaml(self, nuevo_token):
        """Lee el config.yaml, actualiza el token y lo vuelve a guardar."""
        
        try:
            with open(self.ruta_yaml, 'r', encoding='utf-8') as archivo:
                configuracion = yaml.safe_load(archivo)
            
            configuracion['auth']['api_token'] = str(nuevo_token)
            
            with open(self.ruta_yaml, 'w', encoding='utf-8') as archivo:
                yaml.dump(configuracion, archivo, default_flow_style=False, allow_unicode=True) 
            return True
            
        except Exception as e:
            print(f"Error al modificar el YAML: {e}")
            return False

    def descargar_datos(self, id_shot: int):
        """
        Descarga de datos desde el servidor u obtención desde la carpeta caché
        """
        print(f"Intentando descargar el shot con ID: {id_shot}...")
        try:
            archivo_hdf5 = self.client.get_shot(id_shot)
            if archivo_hdf5 is not None:
                return True, "Descarga exitosa."
            else:
                return False, "El archivo no se encontró."
                
        except Exception as e:
            return False, f"Error: {e}"

    def actualizar_base_datos(self):
        carpeta_descargas =  "./MephistDataKit/.cache"
        archivo_permanente = "catalogo_mephist0.csv" 
        metadatos_totales = []
        lista_de_shots = range(1500, 4228)

        # 1. VERIFICAR SI EL ARCHIVO YA EXISTE ANTES DE ABRIRLO
        archivo_ya_existe = os.path.exists(archivo_permanente)

        # 2. ABRIR EN MODO APPEND ('a')
        with open(archivo_permanente, mode='a', newline='', encoding='utf-8') as archivo_csv:
            escritor = csv.writer(archivo_csv)
            
            # Solo escribimos la cabecera si el archivo es nuevo
            if not archivo_ya_existe:
                escritor.writerow(["id_shot", "fecha", "peso_MB", "pressure", "working_gas", "Ip_max"])

            for shot_id in lista_de_shots:
                self.descargar_datos(shot_id)
                ruta_temporal = f"{carpeta_descargas}/{shot_id}MD.nxs"

                if not os.path.exists(ruta_temporal):
                    print(f"  -> Shot {shot_id} no encontrado. Saltando...")
                    continue
                
                peso = round(os.path.getsize(ruta_temporal) / (1024 * 1024), 2)

                f = self.cargar_shot(shot_id)
                
                # ... (Aquí va tu código de extracción de datos del HDF5) ...
                date = f['META']['Main']['Shot_time'][()].decode('utf-8')
                presion  = round(float(f['Vacuum']['Pressure']['total_pressure'][()]) * 10**5, 2)
                gas  = f['Vacuum']['Pressure']['working_gas'][()].decode('utf-8')
                ip_max = round(float(self.obtener_corriente_maxima(shot_id)),2)
                
                fila_datos = [shot_id, date, peso, presion, gas, ip_max]
                
                escritor.writerow(fila_datos)
                metadatos_totales.append(tuple(fila_datos))


        return metadatos_totales

    def cargar_shot(self, id_shot: int):
        """Carga el shot actual en la base de datos"""
        carpeta = Path("./MephistDataKit/.cache")
        nombre_archivo = f"{id_shot}MD.nxs"
        archivo_encontrado = next(carpeta.rglob(nombre_archivo), None)
        path = archivo_encontrado
        f = h5py.File(path, 'r')
        return f

    def obtener_gas(self, id_shot) -> str:
        """
        Obtiene el tipo de gas utilizado.
        """
        f = self.cargar_shot(id_shot)
        try:
            if id_shot<=3807: 
                return f['Vacuum']['Pressure']['working_gas'][()].decode('utf-8')
            else: 
                return f['Vacuum']['Pressure_fastValve']['working_gas'][()].decode('utf-8')
                
        except:
            return ''

    def get_pressure(self) -> float:
        """
        Obtiene la presión total del shot
        """
        try:
            return f['Vacuum']['Pressure']['total_pressure'][()]
        except:
            return ''

    def obtener_corriente_plasma(self, id_shot) -> tuple[np.ndarray,np.ndarray]:
        """
        Obtiene la corriente del plasma en kA y el tiempo en ms.
        """
        Time = np.linspace(0,21e-3,1000)
        Ip = None
        f = self.cargar_shot(id_shot)
        shot_id = id_shot
        
        try:
            if shot_id<2658: 
                Time_original = f['rogowski_coils']['rog_tor_coils']['time'][:]/1000
                Time_internal_rog = f['rogowski_coils']['rog_internal']['time'][:]/1000
                
                U_rog_TF = set_zero(f['rogowski_coils']['rog_tor_coils']['data'][:])
                U_rog_CS = set_zero(f['rogowski_coils']['rog_inductor']['data'][:])
                U_rog_PF1 = set_zero(f['rogowski_coils']['rog_pol_coils1']['data'][:])
                U_rog_PF2 = set_zero(f['rogowski_coils']['rog_pol_coils2']['data'][:])
                U_rog_PF2 = preprocess(U_rog_PF2)
                U_rog_PF3 = set_zero(f['rogowski_coils']['rog_pol_coils3']['data'][:])
                U_rog_int =f['rogowski_coils']['rog_internal']['data'][:]                        

                U_rog_TF = np.interp(Time,Time_original,U_rog_TF)
                U_rog_CS = np.interp(Time,Time_original,U_rog_CS)
                U_rog_PF1 = np.interp(Time,Time_original,U_rog_PF1)
                U_rog_PF2 = np.interp(Time,Time_original,U_rog_PF2)
                U_rog_PF3 = np.interp(Time,Time_original,U_rog_PF3)
                U_rog_int = np.interp(Time,Time_internal_rog,U_rog_int)
                
                synt_sig = -RC_transform(Time,U_rog_TF,1,1.8e-4)*0.665
                synt_sig = synt_sig - 0.515*(RC_transform(Time,U_rog_CS,1,8.6e-5)*3 - RC_transform(Time,U_rog_CS,1,4.4e-4)*1.67 )
                synt_sig = synt_sig + 0.5*1.1*(RC_transform(Time,U_rog_PF1,1,5.5e-4)*3.8 + RC_transform(Time,U_rog_PF1,1,5e-5)*0.65)
                synt_sig = synt_sig + RC_transform(Time,U_rog_PF2,1,4.5e-4)*3.2 + RC_transform(Time,U_rog_PF2,1,15e-4)*0.45
                synt_sig = synt_sig + 1.05*( RC_transform(Time,U_rog_PF3,1,60e-4)*0.4 + RC_transform(Time,U_rog_PF3,1,6e-4)*2.4)

                # Subtract parasitic from the internal Rogowski coil
                U_rog_int_filt = U_rog_int - synt_sig
                # Calculate plasma current (in Amperes)
                Ip = integrate(Time,U_rog_int_filt)*1.48e7*0.87 
                Ip = Ip-Ip[300]
                return Time*1000, Ip/1000
            
            elif shot_id<2976: 
                Time_original = f['rogowski_coils']['rog_TF']['time'][:]/1000
                Time_internal_rog = f['rogowski_coils']['rog_internal']['time'][:]/1000

                U_rog_TF = set_zero(f['rogowski_coils']['rog_TF']['data'][:])
                U_rog_CS = set_zero(f['rogowski_coils']['rog_CS']['data'][:])
                U_rog_PF1 = set_zero(f['rogowski_coils']['rog_PF1']['data'][:])
                U_rog_PF2 = set_zero(f['rogowski_coils']['rog_PF2']['data'][:])
                U_rog_PF2 = preprocess(U_rog_PF2)
                U_rog_PF3 = set_zero(f['rogowski_coils']['rog_PF3']['data'][:])
                U_rog_PF5 = set_zero(f['rogowski_coils']['rog_PF5']['data'][:])
                U_rog_int = set_zero(f['rogowski_coils']['rog_internal']['data'][:])/10
            
                U_rog_TF = np.interp(Time,Time_original,U_rog_TF)
                U_rog_CS = np.interp(Time,Time_original,U_rog_CS)
                U_rog_PF1 = np.interp(Time,Time_original,U_rog_PF1)
                U_rog_PF2 = np.interp(Time,Time_original,U_rog_PF2)
                U_rog_PF3 = np.interp(Time,Time_original,U_rog_PF3)
                U_rog_int = np.interp(Time,Time_internal_rog,U_rog_int)

                
                U_rog_PF5 = np.interp(Time,Time_original,U_rog_PF5)
                
                synt_sig = 0.985*(RC_transform(Time,U_rog_TF,1,5e-5)*0.04 +  RC_transform(Time,U_rog_TF,1,2e-4)*0.395)
                synt_sig = synt_sig + 0.49*(RC_transform(Time,U_rog_CS,1,0.8e-4)*3.15 - RC_transform(Time,U_rog_CS,1,4.8e-4)*1.78)
                synt_sig = synt_sig - 0.27*(RC_transform(Time,U_rog_PF1,1,5.5e-4)*2.7 + RC_transform(Time,U_rog_PF1,1,5e-5)*1.35)
                synt_sig = synt_sig - (RC_transform(Time,U_rog_PF3,1,4.5e-4)*3.2 + RC_transform(Time,U_rog_PF3,1,15e-4)*0.45)*0.066
                synt_sig = synt_sig - 0.06*( RC_transform(Time,U_rog_PF5,1,60e-4)*0.5 + RC_transform(Time,U_rog_PF5,1,6e-4)*2.4)
                # Subtract parasitic from the internal Rogowski coil
                U_rog_int_filt = U_rog_int - synt_sig
                # Calculate plasma current (in Amperes)
                Ip = integrate(Time,U_rog_int_filt)*1.48e7*0.87 
                return Time*1000, Ip/1000
          
            elif shot_id<3355:
                
                Time_LTR = f['rogowski_coils']['rog_TF']['time'][0:5000]/1000
                U_rog_TF = set_zero(f['rogowski_coils']['rog_TF']['data'][0:5000])/4.89
                U_rog_CS = set_zero(f['rogowski_coils']['rog_CS']['data'][0:5000])/10.48
                U_rog_PF1 = set_zero(f['rogowski_coils']['rog_PF1']['data'][0:5000])/19.05
                U_rog_PF2 = set_zero(f['rogowski_coils']['rog_PF2']['data'][0:5000])/19.05
                U_rog_PF3 = set_zero(f['rogowski_coils']['rog_PF3']['data'][0:5000])/42.86
                U_rog_PF4 = set_zero(f['rogowski_coils']['rog_PF4']['data'][0:5000])/42.86
                U_rog_PF5 = set_zero(f['rogowski_coils']['rog_PF5']['data'][0:5000])/32.14
                U_rog_PF6 = set_zero(f['rogowski_coils']['rog_PF6']['data'][0:5000])/32.14
                U_rog_int = set_zero(f['rogowski_coils']['rog_internal']['data'][0:5000])/10

                U_rog_TF = np.interp(Time,Time_LTR,U_rog_TF)
                U_rog_CS = np.interp(Time,Time_LTR,U_rog_CS)
                U_rog_PF1 = np.interp(Time,Time_LTR,U_rog_PF1)
                U_rog_PF2 = np.interp(Time,Time_LTR,U_rog_PF2)
                U_rog_PF3 = np.interp(Time,Time_LTR,U_rog_PF3)
                U_rog_PF4 = np.interp(Time,Time_LTR,U_rog_PF4)
                U_rog_PF5 = np.interp(Time,Time_LTR,U_rog_PF5)
                U_rog_PF6 = np.interp(Time,Time_LTR,U_rog_PF6)
                U_rog_int = np.interp(Time,Time_LTR,U_rog_int)
                
                
                synt_sig = 1.4*(RC_transform(Time,U_rog_TF,1,6e-5)*0.07 +  RC_transform(Time,U_rog_TF,1,1.7e-4)*0.285)
                synt_sig = synt_sig + 0.46*(RC_transform(Time,U_rog_CS,1,0.8e-4)*3.14- RC_transform(Time,U_rog_CS,1,4.8e-4)*2.45 
                                        - RC_transform(Time,U_rog_CS,1,4e-3)*0.08)
                synt_sig = synt_sig - 4.3*RC_transform(Time,U_rog_PF1,1,3.5e-4)
                synt_sig = synt_sig + 0.6*RC_transform(Time,U_rog_PF2,1,2.5e-4)
                synt_sig = synt_sig - 1.35*(2.8*RC_transform(Time,U_rog_PF3,1,3.1e-4) + 1.2*RC_transform(Time,U_rog_PF3,1,1e-3))
                synt_sig = synt_sig + 0.8*RC_transform(Time,U_rog_PF4,1,2.1e-4) - 0.22*RC_transform(Time,U_rog_PF4,1,8e-4)
                synt_sig = synt_sig - 1.44*(RC_transform(Time,U_rog_PF5,1,3.2e-4)+0.9*RC_transform(Time,U_rog_PF5,1,9e-4))
                synt_sig = synt_sig + 1.3*(0.37*RC_transform(Time,U_rog_PF6,1,1.5e-4) - 0.4*RC_transform(Time,U_rog_PF6,1,7e-4))
                
                U_rog_int_filt = U_rog_int - synt_sig
                
                Ip = integrate(Time,U_rog_int_filt)*1.48e7*0.91
                Ip = Ip-Ip[300]
                return Time*1000, Ip/1000
            
            else:
                Time_LTR = f['rogowski_coils']['rog_TF']['time'][0:5000]/1000
                U_rog_int = -set_zero(f['rogowski_coils']['rog_internal']['data'][0:5000])
                U_rog_int = np.interp(Time,Time_LTR,U_rog_int)
                Ip=integrate(Time, U_rog_int)*2.8e3
                return Time*1000, Ip

        except Exception as e:
            print(e)
            return np.array([]), np.array([])

    def obtener_corriente_maxima(self, id_shot):
        tiempo, corriente_plasma = self.obtener_corriente_plasma(id_shot)
        try:
            return np.max(corriente_plasma)
        except:
            return 0

    def obtener_tiempos_plasma(self, id_shot) -> tuple[np.float64,np.float64]:
        """
        Entrega el tiempo de inicio del plasma y el final basado en la
        emisión Ha
        """
        f = self.cargar_shot(id_shot)
        t = f['spectroscopy']['visible_emission']['time'][0:200000]*1e-3
        Ha = f['spectroscopy']['visible_emission']['data'][0:200000]
        
        Ha = set_zero(Ha) 
        Ha = -sigproc.medfilt(Ha,501)

        i = 0
        while (i < len(t)):
            
            if (Ha[i] > 0.04): 
                t_pl_start = t[i] - 3e-4 
                break
            i+=1  
        j =  len(t) -1
        while (j > i):
            if (Ha[j] > 0.04): 
                t_pl_end = t[j] + 2e-4 
                break
            j-=1  
        return t_pl_start*1000, t_pl_end*1000

    def obtener_duracion_plasma(self, id_shot, level_percent: float = 6.0, start_time: float = 4.0, stop_time: float = 18.0) -> np.float64:
        """
        Returns the discharge duration in ms based on Ha emission data / Возвращает длительность разряда в мс на основе данных Ha эмиссии

        Algorithm:
        1. Read time (s) and signal.
        2. Time cropping from 5 to 16 ms.
        3. Absolute signal value (abs).
        4. Subtract the linear oscillation along the boundaries of the cropped interval.
        5. Smoothing (Savitsky-Golay filter: window 300, polyorder 3).
        6. Find the intersection of levels (level_percent) from the maximum.

        Args:
            level_percent: float, level for duration determination
            start_time, stop_time: times to cut halpha array, in ms 
        Returns:
            np.float64: plasma duration in ms 
        """
        f = self.cargar_shot(id_shot)
        t = f['spectroscopy']['visible_emission']['time'][0:200000] * 1e-3  # секунды
        Ha = f['spectroscopy']['visible_emission']['data'][0:200000].astype(float)

        # to ms
        t_ms = t * 1000

        # cut signal
        mask = (t_ms >= start_time) & (t_ms <= stop_time)
        t_cut = t[mask]
        Ha_cut = Ha[mask]
        Ha_abs = np.abs(Ha_cut)
        if len(Ha_cut) == 0:
            return 0.0

        # remove background linearly
        val_start = Ha_abs[0]
        val_end   = Ha_abs[-1]
        t_start_sec = t_cut[0]
        t_end_sec   = t_cut[-1]

        a = (val_end - val_start) / (t_end_sec - t_start_sec)
        b = val_start - a * t_start_sec
        Ha_detrend = Ha_abs - (a * t_cut + b)

        # smooth
        window = min(200, len(Ha_detrend) - 1)
        if window % 2 == 0:
            window -= 1   # окно должно быть нечётным
        if window >= 5:
            Ha_smooth = savgol_filter(Ha_detrend, window_length=window, polyorder=3)

        # max
        peak = np.max(Ha_smooth)
        if peak <= 0:
            return 0.0

        threshold = (level_percent / 100.0) * peak

        # start
        start_idx = None
        for i in range(len(t_cut)-1):
            if Ha_smooth[i] <= threshold and Ha_smooth[i+1] > threshold:
                t_start = t_cut[i] + (threshold - Ha_smooth[i]) / (Ha_smooth[i+1] - Ha_smooth[i]) * (t_cut[i+1] - t_cut[i])
                start_idx = i
                break
        if start_idx is None:
            return 0.0

        # stop
        end_idx = None
        for i in range(len(t_cut)-1, start_idx, -1):
            if Ha_smooth[i-1] > threshold and Ha_smooth[i] <= threshold:
                t_end = t_cut[i-1] + (threshold - Ha_smooth[i-1]) / (Ha_smooth[i] - Ha_smooth[i-1]) * (t_cut[i] - t_cut[i-1])
                end_idx = i
                break
        if end_idx is None:
            t_end = t_cut[-1]
        return (t_end - t_start) * 1000.0

    def get_plasma_density(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Linearized electron density N_e*l calculation / Расчёт линейной концентрации электронов N_e*l.
        Args:
            None
        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, плотность N_e*l в m^-2 / time in ms, density N_e*l in m^-2
        """
        try:
            Time = np.linspace(0,1e-6*(50000-1),50000)

            interferometry = MW_interferometry()
            Divider = 1
            DiscFreq = 1e7 / Divider
            IntermFreq = 1e6
            REF = self.hdf5_file['interferometry']['interf_detector2']['data'][:]
            RF = self.hdf5_file['interferometry']['interf_detector1']['data'][:]

            # Apply bandisth filters
            REF_F = interferometry.FourierCut(REF, DiscFreq, 10*1e3, IntermFreq)          #10*1e3 - filter FWHM
            RF_F = interferometry.FourierCut(RF, DiscFreq, 10*1e3, IntermFreq)
            time_density = self.hdf5_file['interferometry']['interf_detector2']['time'][:]

            # Get phase and other parameters
            ph_RF, Freq, Amp = interferometry.ProcHilbert(RF_F, DiscFreq)
            ph_REF, REF_freq, REF_amp = interferometry.ProcHilbert(REF_F, DiscFreq)

            # Calculate density
            phase = -(ph_RF - ph_REF)
            phase = phase - np.mean(phase[0:100]) # Remove initial phase
            density = abs(interferometry.PhaseToDensity(phase))
            n_el = np.interp(Time,time_density*1000,density)
            return time_density, abs(density)
            
        except:
            self.logger.warning(f"Cannot get density. Part of signals missing in shot {self.get_shot_id()} / Плотность не получить. Отсутствует часть сигналов в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])


    def get_emission(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Returns the plasma emission dynamics over time, measured by a fast photodiode
        (primarily visible range) / Возвращает динамику излучения плазмы во времени, измеренную быстрым фотодиодом
        (преимущественно видимый диапазон)

        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: time in ms, signal in arbitrary units / время в мс, сигнал в условных единицах
        """
        try:
            time = self.hdf5_file['spectroscopy']['visible_emission']['time'][:]
            inten = self.hdf5_file['spectroscopy']['visible_emission']['data'][:]
            return time, abs(inten)

        except:
            self.logger.warning(f"Cannot get photodiode. Its signal not recorded for shot {self.get_shot_id()} / Фотодиод не получить. Его Сигнал не записан для {self.get_shot_id()}")
            return np.array([]), np.array([])

    def get_emission_spectrum(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Returns the time-integrated overview spectrum from the OceanFX spectrometer / Возвращает интегрированный по времени обзорный спектр с спектрометра OceanFX

        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: wavelength in nm, number of samples per spectrometer channel / длина волны в нм, количество отсчётов на канале спектрометра
        """
        try:
            wavelengths_OceanFX = self.hdf5_file['spectroscopy']['Oceanfx']['Wavelength'][:]
            intensities_OceanFX = self.hdf5_file['spectroscopy']['Oceanfx']['CleanI'][:]
            return wavelengths_OceanFX, intensities_OceanFX

        except:
            self.logger.warning(f"Cannot get spectrum. Spectrometer did not trigger on shot {self.get_shot_id()} / Спектр не получить. Спектрометр не сработал на {self.get_shot_id()}")
            return np.array([]), np.array([])

    def get_torfield(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Returns the toroidal field in mT / Возвращает тороидальное поле в мТл

        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: time in ms, toroidal field at radius ??? in mT / время в мс, тороидальное поле на радиусе ??? в мТл
        """
        try:
            Time = self.hdf5_file['rogowski_coils']['rog_TF']['time'][:][0:5000]/1000
            U_rog_TF = set_zero(self.hdf5_file['rogowski_coils']['rog_TF']['data'][:][0:5000])/4.89
            B_phi = 9.6e-3*integrate(Time,U_rog_TF)*3.92e6
            return Time*1000, B_phi

        except:
            self.logger.warning(f"Cannot get toroidal field. Signal missing in shot {self.get_shot_id()} / Тор.поле не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])

    def get_pol_coils_current(self, coil_num : int = 1):
        """
        Returns the current in the poloidal coil / Возвращает ток в полоидальной катушке

        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: time in ms, current in kA / время в мс, ток в кА
        """
        try:
            
            if not isinstance(coil_num, int) or coil_num<1 or coil_num>6:
                self.logger.error(f"Invalid poloidal coil number specified: {coil_num}. Should be int from 1 to 6 / Указан некорректный номер пол. катушки: {coil_num}. Должно быть int от 1 до 6")
                return np.array([]), np.array([])
                
            amplifier_coeffs = [19.05, 19.05, 42.86, 42.86, 32.14, 32.14]
            
            Time = self.hdf5_file['rogowski_coils'][f'rog_PF{coil_num}']['time'][:][0:5000]/1000
            U_rog_PF = set_zero(self.hdf5_file['rogowski_coils'][f'rog_PF{coil_num}']['data'][:][0:5000])/(amplifier_coeffs[coil_num-1])
            I_PF = integrate(Time,U_rog_PF)*6.23e6
            
            return Time*1000, I_PF/1000

        except:
            self.logger.warning(f"Cannot get poloidal coil current. Signal missing in shot {self.get_shot_id()} / Ток пол. катушки не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])  

    def get_inductor_current(self):
        """
        Returns the current in the central solenoid / Возвращает ток в центральном соленоиде

        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: time in ms, current in kA / время в мс, ток в кА
        """
        try:
            Time = self.hdf5_file['rogowski_coils']['rog_CS']['time'][:][0:5000]/1000
            U_rog_CS = set_zero(self.hdf5_file['rogowski_coils']['rog_CS']['data'][:][0:5000])/10.48
            I_CS = 6.3e6*integrate(Time,U_rog_CS)
            return Time*1000, I_CS/1000

        except:
            self.logger.warning(f"Cannot get inductor current. Signal missing in shot {self.get_shot_id()} / Ток индуктора не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])   

    def get_voltage_loop(self, loop_num:int=1) -> tuple[np.ndarray,np.ndarray]:
        """
        Returns the signal from the voltage loop on the pass, where loop_num is the loop number (1 to 15) / Возвращает Сигнал с петли напряжения на обходе, где loop_num - номер петли (от 1 до 15)

        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: time in ms, voltage on the pass in Volts / время в мс, напряжение на обходе в Вольтах
        """
        
        if not isinstance(loop_num, int) or loop_num<1 or loop_num>15:
            self.logger.error(f"Invalid voltage loop number specified: {loop_num}. Should be int from 1 to 15 / Указан некорректный номер петли напряжения на обходе: {loop_num}. Должно быть int от 1 до 15")
            return np.array([]), np.array([])
        
        try:
            Time_LTR = self.hdf5_file['voltage_loops'][f'VL{loop_num}']['time'][:]
            VL = set_zero(self.hdf5_file['voltage_loops'][f'VL{loop_num}']['data'][:])
            return Time_LTR, VL

        except:
            self.logger.warning(f"Loop {loop_num} signal not recorded for shot {self.get_shot_id()} / Сигнал петли {loop_num} не записан для выстрела {self.get_shot_id()}")
            return np.array([]), np.array([])

#    def obtener_voltaje_loop(self, loop=1):
#        if self.shot_actual == None:
#            return "No se ha cargado ningún shot"        
#
#        tiempo, voltaje_loop = self.shot_actual.get_voltage_loop(loop)
#
#        return tiempo, voltaje_loop
#
#    def obtener_corriente_inductor(self):
#        tiempo, corriente_inductor = self.shot_actual.get_inductor_current()
#
#        return tiempo, corriente_inductor
#
#    def obtener_corriente_pol_coil(self, coil_num=1):
#        tiempo, corriente_bobina_poloidal = self.shot_actual.get_pol_coils_current(coil_num)
#        return tiempo, corriente_bobina_poloidal
#
#    # Puede tener problemas, aveces no accede a los archivos
#    def obtener_torfield(self):
#        try:
#            tiempo = self.shot_h5py["Postprocess"]["tor_field"]["time"][:]
#            data   = self.shot_h5py["Postprocess"]["tor_field"]["data"][:]
#
#            return tiempo, data
#
#        except:
#            return np.array([]), np.array([])
#
#
#    def obtener_Ha(self):
#        tiempo, intensidad = self.shot_actual.get_emission()
#
#        # Corrección de datos: OFFSET
#        mask = tiempo < 2.0
#        base = np.mean(intensidad[mask])
#        intensidad_corregida = intensidad - base
#
#        # Corrección de datos: orientación
#        if abs(np.min(intensidad_corregida)) > np.max(intensidad_corregida):
#            intensidad_corregida *= -1
#
#        intensidad = np.where(intensidad_corregida < 0, 0, intensidad_corregida)
#
#        return tiempo, intensidad
#
#    def obtener_espectro_emision(self):
#
#        longitud_onda, intensidad = self.shot_actual.get_emission_spectrum()
#        return longitud_onda, intensidad
# 
#    def obtener_densidad_plasma(self):
#
#        tiempo, densidad_electronica = self.shot_actual.get_plasma_density()
#        return tiempo, densidad_electronica
#
#    def obtener_mirnov(self, mirnov_num):
#        try:
#            tiempo = self.shot_h5py["magnetic_probes"][f"MP{mirnov_num}"]["time"][:]
#            data = self.shot_h5py["magnetic_probes"][f"MP{mirnov_num}"]["data"][:]
#            return tiempo, data
#        except:
#            return np.array(), np.array()
