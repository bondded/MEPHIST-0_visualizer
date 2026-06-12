"""
common.py
========================

Общие методы для обработки данных.
При необходимости можно реализовывать различные вариации одного метода (разные методы integrate и т.п.) 
"""
import warnings
import numpy as np
from scipy import signal

def set_zero(sig):
    """
    # provides subtraction of baseline
    Args:
        sig (numpy.ndarray): одномерный массив
        
    Returns:
        numpy.ndarray

    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            subtracted = sig-np.average(sig[10:200])
            return subtracted
    except:
        print("Failed to subtract baseline")
        return sig
     

def integrate(time,sig):
    """
    # provides signal integration

    Args:
        time,sig (numpy.ndarray, numpy.ndarray): 2 одномерных массива

    Returns:
        numpy.ndarray
    """
    dt = (time[-1]-time[0])/(len(time)-1)
    summ = np.zeros_like(sig)
    for i in range(len(sig)-1):
        summ[i+1] = summ[i]+sig[i]
    return  summ*dt


def derive(time,sig):
    """
    # provides signal differentiation

    Args:
        time,sig (numpy.ndarray, numpy.ndarray): 2 одномерных массива
        
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
    # provides smoothing with lowpass filter
    fc - нижняя частота отсечки
    Args:
        time,sig, fc (numpy.ndarray, numpy.ndarray, int): 2 одномерных массива и число
        
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
    removes spikes from raw signal. 
    Было актуально для старых АЦП, с LTR можно не использовать
    Args:
        sig (numpy.ndarray): одномерный массив
        
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
    Учитывает ВЧ наводки на линию измерения?
    TODO уточнить у И.Пашкова
    
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
    #     time (ms), signal (numpy.ndarray, numpy.ndarray): 2 одномерных массива
    #     tau (float): delay time in ms

    # Returns:
    #     numpy.ndarray
    time = time - time[0]
    delay = np.zeros_like(signal)
    delay = (1/tau)*np.exp(-time/tau) * ((integrate(time, (signal*np.exp(time/tau)))))
    return delay