"""
shot.py
========================

Получения параметров плазмы из hdf5 файла
"""

import numpy as np
import h5py, os
from .config import Config
from .mw_interferometry import MW_interferometry
from .common import *

# minor and major radius of MEPhIST-0
a = 0.13 #m
R_0=0.25 #m

#coordinates of loop Voltages VL1-VL8,mm
r=[210.0,385.0,385.0,210.0,115.0,115.0,110.0,110.0]
z=[295.0,95.0,-95.0,-295.0,-230.0,230.0,0.0,0.0]

class Shot:
    """
    Класс для получения данных из одного HDF5 файла
    
    """
    
    def __init__(self, hdf5_file: h5py.File):
        """
        Инициализация класса Shot.
        
        Args:
            self.hdf5_file (h5py.File): hdf5 файл библиотеки h5py
        """
        self.hdf5_file = hdf5_file
        self.logger = Config().get_logger('shot')
        
    def get_shot_id(self) -> int:
        """
        Возвращает номер импульса как int
        
        Args:

        Returns:
            int: номер импульса
        """
        try:
            shot_id = int(self.hdf5_file['META']['Main']['ID'][()].decode('utf-8').replace("M",""))
            return shot_id
        except Exception as e:
            #self.logger.warning(e)
            self.logger.warning(f"Файл  {self.hdf5_file.filename.split(os.sep)[-1][:-3]} повреждён")
            return None    
        
    def get_comment(self) -> str:
        """
        Возвращает комментарий оператора
        
        Args:

        Returns:
            str: комментарий
        """
        try:
            comment = self.hdf5_file['META']['Main']['Description'][()][:-1].decode('utf-8')
            return comment
        except:
            self.logger.warning(f"Файл  {self.get_shot_id()} повреждён")
            return None       
    def get_hdf5(self) -> h5py.File:
        """
        Возвращает hdf5 файл
        
        Args:

        Returns:
            h5py.File: файл разряда
        """
        return self.hdf5_file
    
    def get_shot_time(self) -> str:
        """
        Возвращает время импульса в виде str  в формате 2025-12-03 14:53
        
        Args:

        Returns:
            str: время импульса
        """
        try:
            shot_time = self.hdf5_file['META']['Main']['Shot_time'][()][:-1].decode("utf-8")[:-2]
            return shot_time
        except:
            self.logger.warning(f"Файл  {self.get_shot_id()} повреждён")
            return None        

    def get_gas(self) -> str:
        """
        Возвращает тип газав формате: H2, Ar, He, ArH (и другие комбинации)
        
        Args:

        Returns:
            str: тип газа
        """
        try:
            return self.hdf5_file['Vacuum']['Pressure']['working_gas'][()].decode('utf-8')
        except:
            self.logger.warning(f"Файл  {self.get_shot_id()} не содержит данных о типе газа или он повреждён")
            return None

    def get_pressure(self) -> float:
        """
        Возвращает абсолютное давление газа по ёмкостному датчику
        
        Args:

        Returns:
            float: давление газа
        """
        try:
            return self.hdf5_file['Vacuum']['Pressure']['total_pressure'][()]
        except:
            self.logger.warning(f"Файл  {self.get_shot_id()}  не содержит данных о давлении  или он повреждён")
            return None
        
    def get_voltage_loop(self, loop_num:int=1) -> tuple[np.ndarray,np.ndarray]:
        """
        Возвращает Сигнал с петли напряжения на обходе, где loop_num - номер петли (от 1 до 15)
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, напряжение на обходе в Вольтах
        """
        
        if not isinstance(loop_num, int) or loop_num<1 or loop_num>15:
            self.logger.error(f"Указан некорректный номер петли напряжения на обходе: {loop_num}. Должно быть int от 1 до 15")
            return np.array([]), np.array([])
        
        try:
            Time_LTR = self.hdf5_file['voltage_loops'][f'VL{loop_num}']['time'][:]
            VL = set_zero(self.hdf5_file['voltage_loops'][f'VL{loop_num}']['data'][:])
            return Time_LTR, VL

        except:
            self.logger.warning(f"Сигнал петли {loop_num} не записан для выстрела {self.get_shot_id()}")
            return np.array([]), np.array([])

    def get_inductor_current(self):
        """
        Возвращает ток в центральном соленоиде
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, ток в кА
        """
        try:
            Time = self.hdf5_file['rogowski_coils']['rog_CS']['time'][:][0:5000]/1000
            U_rog_CS = set_zero(self.hdf5_file['rogowski_coils']['rog_CS']['data'][:][0:5000])/10.48
            I_CS = 6.3e6*integrate(Time,U_rog_CS)
            return Time*1000, I_CS/1000

        except:
            self.logger.warning(f"Ток индуктора не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])    


    def get_pol_coils_current(self, coil_num : int = 1):
        """
        Возвращает ток в полоидальной катушке
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, ток в кА
        """
        try:
            
            if not isinstance(coil_num, int) or coil_num<1 or coil_num>6:
                self.logger.error(f"Указан некорректный номер пол. катушки: {coil_num}. Должно быть int от 1 до 6")
                return np.array([]), np.array([])
                
            amplifier_coeffs = [19.05, 19.05, 42.86, 42.86, 32.14, 32.14]
            
            Time = self.hdf5_file['rogowski_coils'][f'rog_PF{coil_num}']['time'][:][0:5000]/1000
            U_rog_PF = set_zero(self.hdf5_file['rogowski_coils'][f'rog_PF{coil_num}']['data'][:][0:5000])/(amplifier_coeffs[coil_num-1])
            I_PF = integrate(Time,U_rog_PF)*6.23e6
            
            return Time*1000, I_PF/1000

        except:
            self.logger.warning(f"Ток пол. катушки не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])   

    def get_torfield(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Возвращает тороидальное поле в мТл
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, тороидальное поле на радиусе ??? в мТл
        """
        try:
            Time = self.hdf5_file['rogowski_coils']['rog_TF']['time'][:][0:5000]/1000
            U_rog_TF = set_zero(self.hdf5_file['rogowski_coils']['rog_TF']['data'][:][0:5000])/4.89
            B_phi = 9.6e-3*integrate(Time,U_rog_TF)*3.92e6
            return Time*1000, B_phi

        except:
            self.logger.warning(f"Тор.поле не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])
        
    def get_U_loop(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Возвращает напряжение на обходе в В
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, Напряжение на обходе на радиусе R0 в В
        """
        try:
            Time = self.hdf5_file['rogowski_coils']['rog_TF']['time'][:][0:5000]/1000            
            time_Vl2, Vl2 = self.get_voltage_loop(2)
            time_Vl3, Vl3 = self.get_voltage_loop(3)
            time_Vl7, Vl7 = self.get_voltage_loop(7)
            U_loop = 0.5*(Vl7+0.5*(Vl2+Vl3))
            time_loop = time_Vl2
            U_loop=np.interp(Time*1000,time_loop,U_loop)
            return Time*1000, U_loop

        except:
            self.logger.warning(f"Тор.поле не получить. Отсутствует сигнал в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])

    def get_emission_spectrum(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Возвращает интегрированный по времени обзорный спектр с спектрометра OceanFX
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: длина волны в нм, количество отсчётов на канале спектрометра
        """
        try:
            wavelengths_OceanFX = self.hdf5_file['spectroscopy']['Oceanfx']['Wavelength'][:]
            intensities_OceanFX = self.hdf5_file['spectroscopy']['Oceanfx']['CleanI'][:]
            return wavelengths_OceanFX, intensities_OceanFX

        except:
            self.logger.warning(f"Спектр не получить. Спектрометр не сработал на {self.get_shot_id()}")
            return np.array([]), np.array([])


    def get_emission(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Возвращает динамику излучения плазмы во времени, измеренную быстрым фотодиодом 
        (преимущественно видимый диапазон)
        
        Args:

        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, сигнал в условных единицах
        """
        try:
            time = self.hdf5_file['spectroscopy']['visible_emission']['time'][:]
            inten = self.hdf5_file['spectroscopy']['visible_emission']['data'][:]
            return time, abs(inten)

        except:
            self.logger.warning(f"Фотодиод не получить. Его Сигнал не записан для {self.get_shot_id()}")
            return np.array([]), np.array([])

    def get_plasma_density(self) -> tuple[np.ndarray,np.ndarray]:
        """
        # linearized electron density  N_e*l calculation 
        Args:
            None
        Returns:
            tuple[np.ndarray,np.ndarray]: время в мс, плотность N_e*l в m^-2
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
            self.logger.warning(f"Плотность не получить. Отсутствует часть сигналов в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])
    
    def get_plasma_current(self) -> tuple[np.ndarray,np.ndarray]:
        """
        Возвращает массив времени в мс и массив тока плазмы в кА. 
        Так как коэффициенты пересчёт постоянно и рандомно меняются,
        то метод расчёта зависит от номера импульса. При этом раньше была 
        попытка оптимизировать его, чтобы не копировать одни и те же куски кода,
        но в долгосрочной перспективе оказалось проще копировать полностью,
        так как нейминги переменных тоже иногда меняются и следить за этим невозможно
        
        Args:
            None
        Returns:
            tuple[np.ndarray,np.ndarray]:: массив времени в мс и массив тока плазмы в кА
        """
        Time = np.linspace(0,21e-3,1000)
        Ip = None
        shot_id = self.get_shot_id()
        
        try:
            if shot_id<2658: # before 250910
                Time_original = self.hdf5_file['rogowski_coils']['rog_tor_coils']['time'][:]/1000
                Time_internal_rog = self.hdf5_file['rogowski_coils']['rog_internal']['time'][:]/1000
                
                U_rog_TF = set_zero(self.hdf5_file['rogowski_coils']['rog_tor_coils']['data'][:])
                U_rog_CS = set_zero(self.hdf5_file['rogowski_coils']['rog_inductor']['data'][:])
                U_rog_PF1 = set_zero(self.hdf5_file['rogowski_coils']['rog_pol_coils1']['data'][:])
                U_rog_PF2 = set_zero(self.hdf5_file['rogowski_coils']['rog_pol_coils2']['data'][:])
                U_rog_PF2 = preprocess(U_rog_PF2)
                U_rog_PF3 = set_zero(self.hdf5_file['rogowski_coils']['rog_pol_coils3']['data'][:])
                U_rog_int =self.hdf5_file['rogowski_coils']['rog_internal']['data'][:]                        

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
            
            elif shot_id<2976: # цифра выбрана не очень аккуратно
                Time_original = self.hdf5_file['rogowski_coils']['rog_TF']['time'][:]/1000
                Time_internal_rog = self.hdf5_file['rogowski_coils']['rog_internal']['time'][:]/1000

                U_rog_TF = set_zero(self.hdf5_file['rogowski_coils']['rog_TF']['data'][:])
                U_rog_CS = set_zero(self.hdf5_file['rogowski_coils']['rog_CS']['data'][:])
                U_rog_PF1 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF1']['data'][:])
                U_rog_PF2 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF2']['data'][:])
                U_rog_PF2 = preprocess(U_rog_PF2)
                U_rog_PF3 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF3']['data'][:])
                U_rog_PF5 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF5']['data'][:])
                U_rog_int = set_zero(self.hdf5_file['rogowski_coils']['rog_internal']['data'][:])/10
            
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
                
                Time_LTR = self.hdf5_file['rogowski_coils']['rog_TF']['time'][0:5000]/1000
                U_rog_TF = set_zero(self.hdf5_file['rogowski_coils']['rog_TF']['data'][0:5000])/4.89
                U_rog_CS = set_zero(self.hdf5_file['rogowski_coils']['rog_CS']['data'][0:5000])/10.48
                U_rog_PF1 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF1']['data'][0:5000])/19.05
                U_rog_PF2 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF2']['data'][0:5000])/19.05
                U_rog_PF3 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF3']['data'][0:5000])/42.86
                U_rog_PF4 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF4']['data'][0:5000])/42.86
                U_rog_PF5 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF5']['data'][0:5000])/32.14
                U_rog_PF6 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF6']['data'][0:5000])/32.14
                U_rog_int = set_zero(self.hdf5_file['rogowski_coils']['rog_internal']['data'][0:5000])/10

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
                
                # Dont know where it came from ...
                """
                # Calculating Plasma current. Here some "magic" occurs.
                # Сalculate syntetic signal,induced by tokamak's electromagnetic system on the internal Rogowski coil
                synt_sig = 1.155*(RC_transform(Time,U_rog_TF,1,3e-5)*0.057 +  RC_transform(Time,U_rog_TF,1,2e-4)*0.39)
                synt_sig = synt_sig + 0.472*(RC_transform(Time,U_rog_CS,1,0.85e-4)*3.15 - RC_transform(Time,U_rog_CS,1,5.5e-4)*1.73)
                synt_sig = synt_sig - 3.0*RC_transform(Time,U_rog_PF1,1,3.5e-4)
                synt_sig = synt_sig + 0.42*RC_transform(Time,U_rog_PF2,1,2.5e-4)
                synt_sig = synt_sig - 1.3*(2.8*RC_transform(Time,U_rog_PF3,1,3.1e-4) + 1.2*RC_transform(Time,U_rog_PF3,1,1e-3))
                synt_sig = synt_sig + 0.8*RC_transform(Time,U_rog_PF4,1,2.1e-4) - 0.22*RC_transform(Time,U_rog_PF4,1,8e-4)
                synt_sig = synt_sig - 1.55*(RC_transform(Time,U_rog_PF5,1,3.2e-4)+0.8*RC_transform(Time,U_rog_PF5,1,9e-4))
                synt_sig = synt_sig + 1.3*(0.37*RC_transform(Time,U_rog_PF6,1,1.5e-4) - 0.4*RC_transform(Time,U_rog_PF6,1,7e-4))
                """
                U_rog_int_filt = U_rog_int - synt_sig
                
                Ip = integrate(Time,U_rog_int_filt)*1.48e7*0.91
                Ip = Ip-Ip[300]
                return Time*1000, Ip/1000
            
            else:
                # We added new Rogowski coil with continuous winding, which significantly reduced induced noise signal.Feb 2026
                # Now the signal looks more physical and comes to zero. 
                Time_LTR = self.hdf5_file['rogowski_coils']['rog_TF']['time'][0:5000]/1000
                
                # U_rog_TF = set_zero(self.hdf5_file['rogowski_coils']['rog_TF']['data'][0:5000])/4.89
                # U_rog_CS= set_zero(self.hdf5_file['rogowski_coils']['rog_CS']['data'][0:5000])/10.48
                # U_rog_PF1 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF1']['data'][0:5000])/19.05
                # U_rog_PF2 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF2']['data'][0:5000])/19.05
                # U_rog_PF3 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF3']['data'][0:5000])/42.86
                # U_rog_PF4 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF4']['data'][0:5000])/42.86
                # U_rog_PF5 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF5']['data'][0:5000])/32.14
                # U_rog_PF6 = set_zero(self.hdf5_file['rogowski_coils']['rog_PF6']['data'][0:5000])/32.14
                # U_rog_int = -set_zero(self.hdf5_file['rogowski_coils']['rog_internal']['data'][0:5000])/2.11
                
                U_rog_int = -set_zero(self.hdf5_file['rogowski_coils']['rog_internal']['data'][0:5000])

                # U_rog_TF = np.interp(Time,Time_LTR,U_rog_TF)
                # U_rog_CS = np.interp(Time,Time_LTR,U_rog_CS)
                # U_rog_PF1 = np.interp(Time,Time_LTR,U_rog_PF1)
                # U_rog_PF2 = np.interp(Time,Time_LTR,U_rog_PF2)
                # U_rog_PF3 = np.interp(Time,Time_LTR,U_rog_PF3)
                # U_rog_PF4 = np.interp(Time,Time_LTR,U_rog_PF4)
                # U_rog_PF5 = np.interp(Time,Time_LTR,U_rog_PF5)
                # U_rog_PF6 = np.interp(Time,Time_LTR,U_rog_PF6)
                U_rog_int = np.interp(Time,Time_LTR,U_rog_int)
                
                # synt_sig = 0.13*(-RC_transform(Time,U_rog_TF,1,3e-5)*0.2 +  RC_transform(Time,U_rog_TF,1,2.4e-4)*0.60)
                # synt_sig = synt_sig + 0.02*(RC_transform(Time,U_rog_CS,1,0.8e-4)*3.14 
                #                             - RC_transform(Time,U_rog_CS,1,6e-4)*3.2 )    
                # synt_sig = synt_sig + 0.04*RC_transform(Time,U_rog_PF2,1,8e-5)
                # synt_sig = synt_sig - 0.08*RC_transform(Time,U_rog_PF4,1,8e-5) -0.3*RC_transform(Time,U_rog_PF4,1,1e-3) 
                # synt_sig = synt_sig - 0.35*RC_transform(Time,U_rog_PF6,1,5.5e-4) 

                # U_rog_int_filt = U_rog_int - synt_sig
                # Ip = integrate(Time,U_rog_int_filt)*5.8e6
                # Ip = Ip-Ip[300]
                Ip=integrate(Time, U_rog_int)*2.8e3
                #Ip_crop = np.zeros_like(Ip)
                #Ip_crop[t0:t1] = Ip[t0:t1]
                #time_pl = np.linspace(0,5e-5*(400-1),400)
                #Ip_out = np.interp(time_pl,Time,Ip_crop)
                return Time*1000, Ip
            
        except Exception as e:
            self.logger.warning(f"Ток плазмы не получить. Отсутствует часть сигналов в импульсе {self.get_shot_id()}")
            return np.array([]), np.array([])
    

    def get_hdf5_structure(self) -> str:
        """
        Возвращает строку с древовидной структурой HDF5 файла.
        
        Args:

        Returns:
            str: Строка с древовидной структурой файла
        """
        
        def _traverse(hdf_obj, prefix=""):
            """Рекурсивно обходит HDF5 объекты и строит дерево."""
            lines = []
            
            names = list(hdf_obj.keys())
            
            for i, name in enumerate(names):
                is_last = (i == len(names) - 1)
                current_prefix = "└── " if is_last else "├── "
                lines.append(prefix + current_prefix + name)
    
                if isinstance(hdf_obj[name], h5py.Group):
                    next_prefix = prefix + ("    " if is_last else "│   ")
                    lines.extend(_traverse(hdf_obj[name], next_prefix))
            
            return lines
        try:
            structure_lines = _traverse(self.hdf5_file)
            return "\n".join(structure_lines)
        except OSError as e:
            return f"Ошибка при чтении HDF5 файла: {str(e)}"