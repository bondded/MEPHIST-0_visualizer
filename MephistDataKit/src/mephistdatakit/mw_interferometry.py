"""
mw_interferometry.py
========================

Методы для обработки сигналов СВЧ интерферометрии
Код создал А. Дрозд
"""
import numpy as np
from scipy import signal as sigproc
from scipy.fft import fft, fftfreq, ifft
import math

from .config import Config
from .common import *

class MW_interferometry:
    """
    Класс для получения данных из одного HDF5 файла
    
    """
    
    def __init__(self):
        """
        Инициализация класса Interferometry.
        
        """
    
    # Methods specific for electron density calculation
    def PhaseHilbert(self, Signal):
        AnalyticSignal = sigproc.hilbert(Signal)
        Phase = np.unwrap(np.angle(AnalyticSignal))*(180 / math.pi)
        return Phase

    def FreqHilbert(self, Signal, FreqDisc):
        T = np.arange(Signal.size)*(1.0 / FreqDisc)
        AnalyticSignal = sigproc.hilbert(Signal)
        Phase = np.unwrap(np.angle(AnalyticSignal))
        Freq = np.gradient(Phase, T)/(2 * math.pi)
        return Freq

    def AmpHilbert(self, Signal):
        AnalyticSignal = sigproc.hilbert(Signal)
        Amp = np.abs(AnalyticSignal)
        return Amp

    def ProcHilbert(self, Signal, FreqDisc):
        T = np.arange(Signal.size)*(1.0/FreqDisc)
        AnalyticSignal = sigproc.hilbert(Signal)
        Phase = np.unwrap(np.angle(AnalyticSignal))*(180 / math.pi)
        Freq = np.gradient(Phase, T)/(360)
        Amp = np.abs(AnalyticSignal)
        return Phase, Freq, Amp

    def PhaseToDensity(self, Signal, Lamb = 3.16e-3):
        data = Signal / (2 * 360 * 4.49e-16 * Lamb)           
        return data

    def FourierCut(self, Signal, FreqDisc, FreqCutoff, FreqSignal = 'None'):
        N = Signal.size
        T = 1.0/FreqDisc     
        yf = fft(Signal)
        xf = fftfreq(N, T)
        if (FreqSignal == 'None'):
            FreqSignal = abs(xf[np.argmax(yf)])
        for i in range(len(xf)):
                if (abs(FreqSignal - xf[i]) > FreqCutoff) and (abs(-FreqSignal - xf[i]) > FreqCutoff):          #поскольку у спектра по частотам 2 симметричные части
                    yf[i] = 0.0
        FilteredSignal = ifft(yf).real
        return FilteredSignal
