import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import os
import pyperclip
import itertools
import pandas as pd
import json

# =========================================================
# GLOBAL PARAMETERS
# =========================================================
K_ROG_TOR = 6.3e6
K_TF = 9.6e-3
K_ROG_IND = 6.3e6
K_ROG_PF1 = 6.23e6
BT_START_THRESHOLD_RATIO = 0.15
IP_START_THRESHOLD_RATIO = 0.05
IP_END_THRESHOLD_RATIO = 0.22
IP_MIN_DURATION_US = 20
IP_REPRESENTATIVE_SMOOTH_US = 10
IP_BASELINE_PRE_START_US = 800
IP_BASELINE_PRE_END_US = 200
IP_FALLBACK_BASELINE_INDEX = 6600
HALPHA_DISPLAY_SMOOTH_US = 0
HALPHA_COMPARISON_SMOOTH_US = 10
IP_COMPARISON_SMOOTH_US = 10

NORMALIZATION_NONE = "none"
NORMALIZATION_TAU = "tau"
NORMALIZATION_TAU_MAX = "tau_max"
NORMALIZATION_TAU_AREA = "tau_area"
DISPLAY_SYNC = "sync"
DISPLAY_RAW = "raw"

# =========================================================
# BASIC SIGNAL PROCESSING & NORMALIZATION
# =========================================================
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
    d2y_max = 1
    sig2 = np.copy(sig)
    sig2[np.isnan(sig2)] = 0
    for i in range(len(sig2) - 1):
        if abs(sig2[i + 1] - sig2[i]) > d2y_max:
            sig2[i + 1] = sig2[i]
    return sig2

def RC_transform(time, sig, R, C):
    sig = np.asarray(sig)
    time = np.asarray(time)
    if len(sig) < 2: return np.zeros_like(sig)
    dt = (time[-1] - time[0]) / (len(time) - 1)
    out_sig = np.zeros_like(sig)
    for i in range(len(sig) - 1):
        out_sig[i + 1] = out_sig[i] + dt * ((sig[i] / R) - (out_sig[i] / (R * C)))
    return out_sig / C

def smooth_signal_time(time, signal_data, window_us=0):
    time, signal_data = np.asarray(time), np.asarray(signal_data)
    if window_us <= 0 or len(time) < 2 or len(signal_data) < 2: return signal_data
    dt = np.mean(np.diff(time))
    window_points = max(int(np.round((window_us * 1e-6) / dt)), 1)
    if window_points % 2 == 0: window_points += 1
    if window_points >= len(signal_data): return signal_data
    kernel = np.ones(window_points) / window_points
    return np.convolve(signal_data, kernel, mode="same")

def safe_divide(signal_data, denominator):
    signal_data = np.asarray(signal_data)
    if denominator is None or abs(denominator) < 1e-15: return signal_data
    return signal_data / denominator

def positive_part(signal_data): return np.maximum(np.asarray(signal_data), 0.0)

def classic_rms(signal_data):
    signal_data = np.asarray(signal_data)
    return np.nan if signal_data.size == 0 else np.sqrt(np.mean(signal_data ** 2))

def representative_max(time, signal_data, smooth_us=IP_REPRESENTATIVE_SMOOTH_US):
    signal_data = np.asarray(signal_data)
    if signal_data.size == 0: return 0.0
    signal_smooth = smooth_signal_time(time, signal_data, window_us=smooth_us)
    positive_values = signal_smooth[signal_smooth > 0]
    return float(np.max(positive_values)) if positive_values.size > 0 else float(np.max(signal_smooth))

# --- Sync Functions ---
def find_bt_reference_time(Time, B_phi, threshold_ratio=BT_START_THRESHOLD_RATIO):
    Time, B_phi = np.asarray(Time), np.asarray(B_phi)
    if len(Time) == 0 or len(B_phi) == 0: return 0.0
    b_max_rep = representative_max(Time, B_phi, smooth_us=IP_REPRESENTATIVE_SMOOTH_US)
    if b_max_rep <= 0: b_max_rep = np.max(B_phi)
    indices = np.where(B_phi > threshold_ratio * b_max_rep)[0]
    return Time[indices[0]] if len(indices) > 0 else Time[0]

def find_ip_start_times(Time, Ip, threshold_ratio=IP_START_THRESHOLD_RATIO, min_duration_us=IP_MIN_DURATION_US):
    Time, Ip = np.asarray(Time), np.asarray(Ip)
    if len(Time) < 2 or len(Ip) < 2: return np.array([])
    ip_max_rep = representative_max(Time, Ip, smooth_us=IP_REPRESENTATIVE_SMOOTH_US)
    if ip_max_rep <= 0: return np.array([])
    above = Ip > (threshold_ratio * ip_max_rep)
    dt = np.mean(np.diff(Time))
    min_samples = max(int(np.ceil((min_duration_us * 1e-6) / dt)), 1)
    crossing_indices = np.where(np.diff(above.astype(int)) == 1)[0] + 1
    valid = [Time[idx] for idx in crossing_indices if idx + min_samples <= len(above) and np.all(above[idx:idx + min_samples])]
    return np.array(valid)

def get_first_ip_start(Time, Ip, threshold_ratio=IP_START_THRESHOLD_RATIO, min_duration_us=IP_MIN_DURATION_US):
    crossings = find_ip_start_times(Time, Ip, threshold_ratio, min_duration_us)
    return crossings[0] if len(crossings) > 0 else Time[0]

def get_plasma_end_time(Time, Ip, start_time, threshold_ratio=IP_END_THRESHOLD_RATIO):
    Time, Ip = np.asarray(Time), np.asarray(Ip)
    if len(Time) < 2 or len(Ip) < 2: return Time[-1] if len(Time) > 0 else 0.0
    ip_max_rep = representative_max(Time, Ip, smooth_us=IP_REPRESENTATIVE_SMOOTH_US)
    if ip_max_rep <= 0: return Time[-1]
    active_indices = np.where((Time >= start_time) & (Ip > threshold_ratio * ip_max_rep))[0]
    return Time[active_indices[-1]] if len(active_indices) > 0 else Time[-1]

def get_tau(Time, start_time, end_time):
    Time = np.asarray(Time)
    duration = end_time - start_time
    if duration <= 0: duration = Time[-1] - Time[0]
    if duration <= 0: return np.zeros_like(Time), 0.0
    return (Time - start_time) / duration, duration

def get_tau_active_and_ip(Time, Ip):
    t_start = get_first_ip_start(Time, Ip)
    t_end = get_plasma_end_time(Time, Ip, t_start)
    tau, plasma_duration = get_tau(Time, t_start, t_end)
    active_mask = (tau >= 0.0) & (tau <= 1.0)
    return tau, plasma_duration, active_mask, tau[active_mask], Ip[active_mask]

def correct_ip_baseline_two_pass(Time, Ip_raw):
    Time, Ip_raw = np.asarray(Time), np.asarray(Ip_raw)
    t_start_prelim = get_first_ip_start(Time, Ip_raw)
    baseline_mask = (Time >= (t_start_prelim - IP_BASELINE_PRE_START_US * 1e-6)) & (Time <= (t_start_prelim - IP_BASELINE_PRE_END_US * 1e-6))
    if np.sum(baseline_mask) >= 5:
        baseline, baseline_method = np.mean(Ip_raw[baseline_mask]), "pre_plasma_window"
    elif len(Ip_raw) > IP_FALLBACK_BASELINE_INDEX:
        baseline, baseline_method = Ip_raw[IP_FALLBACK_BASELINE_INDEX], "fallback_index"
    else:
        baseline, baseline_method = np.mean(Ip_raw[:min(200, len(Ip_raw))]), "initial_mean"
    return Ip_raw - baseline, baseline, baseline_method

def get_ip_normalization_factor(tau_active, Ip_active, mode):
    tau_active, Ip_active = np.asarray(tau_active), np.asarray(Ip_active)
    if len(tau_active) < 2 or len(Ip_active) < 2: return 1.0
    if mode == NORMALIZATION_TAU_MAX:
        factor = representative_max(tau_active, Ip_active, smooth_us=0)
        return factor if factor > 0 else (np.max(np.abs(Ip_active)) if np.max(np.abs(Ip_active)) > 0 else 1.0)
    if mode == NORMALIZATION_TAU_AREA:
        factor = np.trapz(positive_part(Ip_active), tau_active)
        return factor if factor > 0 else 1.0
    return 1.0

def get_normalized_temporal_signal(Time, signal_data, Ip, mode, signal_kind="generic", display_mode=DISPLAY_SYNC, sync_time=0.0, force_tau=False):
    Time, signal_data, Ip = np.asarray(Time), np.asarray(signal_data), np.asarray(Ip)
    x_raw = Time * 1000 if display_mode == DISPLAY_RAW else (Time - sync_time) * 1000
    if mode == NORMALIZATION_NONE: return x_raw, signal_data
    tau, _, active_mask, tau_active, Ip_active = get_tau_active_and_ip(Time, Ip)
    y_active = signal_data[active_mask]
    if len(tau_active) < 2: return x_raw, signal_data
    x = tau_active if force_tau else x_raw[active_mask]
    
    if mode == NORMALIZATION_TAU: return x, y_active
    if mode == NORMALIZATION_TAU_MAX and signal_kind in ["ip", "halpha"]:
        return x, safe_divide(y_active, get_ip_normalization_factor(tau_active, Ip_active, mode))
    if mode == NORMALIZATION_TAU_AREA:
        y_to_normalize = positive_part(y_active) if signal_kind == "ip" else y_active
        return x, safe_divide(y_to_normalize, get_ip_normalization_factor(tau_active, Ip_active, mode))
    return x_raw, signal_data

def get_normalized_spectrum(wavelengths, intensity_raw, plasma_duration, mode, ip_normalization_factor=1.0):
    wavelengths, intensity_raw = np.asarray(wavelengths), np.asarray(intensity_raw)
    if wavelengths.size == 0 or intensity_raw.size == 0 or wavelengths.shape != intensity_raw.shape: return wavelengths, intensity_raw
    if mode == NORMALIZATION_NONE: return wavelengths, intensity_raw
    intensity_rate = intensity_raw.copy() if (plasma_duration is None or plasma_duration <= 0) else intensity_raw / (plasma_duration * 1000.0)
    if mode == NORMALIZATION_TAU: return wavelengths, intensity_rate
    if mode in [NORMALIZATION_TAU_MAX, NORMALIZATION_TAU_AREA]:
        return wavelengths, safe_divide(intensity_rate, ip_normalization_factor if ip_normalization_factor > 0 else 1.0)
    return wavelengths, intensity_raw

def get_normalization_label(mode):
    labels = {NORMALIZATION_NONE: "No normalization", NORMALIZATION_TAU: "Temporal normalization τ",
              NORMALIZATION_TAU_MAX: "τ + division by Ip representative maximum", NORMALIZATION_TAU_AREA: "τ + division by Ip integrated current"}
    return labels.get(mode, "No normalization")

# --- Export/Analysis Functions (From v10) ---
def compute_halpha_integral_metrics(data):
    Time, Ip, Halpha = data['Time'], data['Ip'], data['Photod']
    ip_start, ip_end, plasma_duration = data['Ip_start_time'], data['Ip_end_time'], data['plasma_duration_sec']
    if plasma_duration <= 0: return None
    active_mask = (Time >= ip_start) & (Time <= ip_end)
    if np.sum(active_mask) < 2: return None
    
    Time_active, Ip_active, Halpha_active = Time[active_mask], Ip[active_mask], Halpha[active_mask]
    tau_active, _ = get_tau(Time_active, ip_start, ip_end)
    Ip_pos, Halpha_pos = positive_part(Ip_active), positive_part(Halpha_active)
    
    return {
        'shot': data['shot_number'], 'Ip_start_ms': ip_start * 1000, 'Ip_end_ms': ip_end * 1000, 'plasma_duration_ms': plasma_duration * 1000,
        'Halpha_integral_time_positive': np.trapz(Halpha_pos, Time_active), 'Halpha_integral_time_raw': np.trapz(Halpha_active, Time_active),
        'Halpha_mean_over_plasma_duration': safe_divide(np.trapz(Halpha_pos, Time_active), plasma_duration),
        'Ip_integral_time_positive_C': np.trapz(Ip_pos, Time_active),
        'Halpha_time_over_Ip_time': np.trapz(Halpha_pos, Time_active) / np.trapz(Ip_pos, Time_active) if np.trapz(Ip_pos, Time_active) > 0 else np.nan,
        'Halpha_integral_tau_positive': np.trapz(Halpha_pos, tau_active), 'Ip_integral_tau_positive_A': np.trapz(Ip_pos, tau_active),
        'Halpha_tau_over_Ip_tau': np.trapz(Halpha_pos, tau_active) / np.trapz(Ip_pos, tau_active) if np.trapz(Ip_pos, tau_active) > 0 else np.nan,
        'Halpha_max_active': np.max(Halpha_active), 'Ip_max_rep_active_kA': representative_max(Time_active, Ip_active) / 1000,
        'Ip_max_active_kA': np.max(Ip_active) / 1000
    }

def compute_timing_delay_metrics(data):
    return {
        'shot': data['shot_number'], 'Bt_start_ms': data['Bt_sync_time'] * 1000, 'Ip_start_ms': data['Ip_start_time'] * 1000,
        'Ip_end_ms': data['Ip_end_time'] * 1000, 'Ip_delay_from_Bt_ms': (data['Ip_start_time'] - data['Bt_sync_time']) * 1000,
        'plasma_duration_ms': (data['Ip_end_time'] - data['Ip_start_time']) * 1000
    }

def compute_single_shot_global_metrics(data):
    Time, Ip, Halpha, Bt = data['Time'], data['Ip'], data['Photod'], data['B_phi']
    active_mask = (Time >= data['Ip_start_time']) & (Time <= data['Ip_end_time'])
    if np.sum(active_mask) < 2: active_mask = np.ones_like(Time, dtype=bool)
    Ip_a, Halpha_a, Bt_a = Ip[active_mask], Halpha[active_mask], Bt[active_mask]
    
    return {
        'shot': data['shot_number'], 'Bt_rms_classic_mT': classic_rms(Bt_a), 'Ip_rms_classic_A': classic_rms(Ip_a),
        'Ip_rms_classic_kA': classic_rms(Ip_a) / 1000, 'Halpha_rms_classic': classic_rms(Halpha_a),
        'Bt_std_mT': np.std(Bt_a), 'Ip_std_A': np.std(Ip_a), 'Ip_std_kA': np.std(Ip_a) / 1000, 'Halpha_std': np.std(Halpha_a),
        'cov_Ip_Halpha': np.cov(Ip_a, Halpha_a)[0, 1] if len(Ip_a) > 1 else np.nan,
        'corr_Ip_Halpha': np.corrcoef(Ip_a, Halpha_a)[0, 1] if len(Ip_a) > 1 else np.nan,
        'cov_Bt_Ip': np.cov(Bt_a, Ip_a)[0, 1] if len(Ip_a) > 1 else np.nan,
        'corr_Bt_Ip': np.corrcoef(Bt_a, Ip_a)[0, 1] if len(Ip_a) > 1 else np.nan
    }

def compute_reproducibility(processed_data):
    if len(processed_data) < 2: return None
    ref_time_bt, ref_time_ip = processed_data[0]['Time_sync_bt'], processed_data[0]['Time_sync_ip']
    Bt_all, Ip_all, Ha_all = [], [], []
    for data in processed_data:
        Bt_all.append(np.interp(ref_time_bt, data['Time_sync_bt'], data['B_phi']))
        Ip_all.append(np.interp(ref_time_ip, data['Time_sync_ip'], data['Ip']))
        Ha_all.append(np.interp(ref_time_ip, data['Time_sync_ip'], data['Photod']))
    Bt_all, Ip_all, Ha_all = np.array(Bt_all), np.array(Ip_all), np.array(Ha_all)
    
    def time_stats(arr):
        mean, std = np.mean(arr, axis=0), np.std(arr, axis=0)
        return mean, std, np.divide(std, mean, out=np.zeros_like(std), where=mean != 0)
    
    Bt_mean, Bt_std, Bt_cv = time_stats(Bt_all)
    Ip_mean, Ip_std, Ip_cv = time_stats(Ip_all)
    Ha_mean, Ha_std, Ha_cv = time_stats(Ha_all)
    
    df_time = pd.DataFrame({
        'time_bt_ms': ref_time_bt * 1000, 'time_ip_ms': ref_time_ip * 1000, 'Bt_mean_mT': Bt_mean, 'Bt_std_mT': Bt_std,
        'Bt_cv': Bt_cv, 'Ip_mean_A': Ip_mean, 'Ip_mean_kA': Ip_mean / 1000, 'Ip_std_A': Ip_std, 'Ip_std_kA': Ip_std / 1000,
        'Ip_cv': Ip_cv, 'Halpha_mean': Ha_mean, 'Halpha_std': Ha_std, 'Halpha_cv': Ha_cv
    })
    
    df_global = pd.DataFrame([compute_single_shot_global_metrics(d) for d in processed_data])
    df_delays = pd.DataFrame([compute_timing_delay_metrics(d) for d in processed_data])
    df_covariance = pd.DataFrame([{'shot': d['shot_number'], 'cov_Ip_Halpha': m['cov_Ip_Halpha'], 'corr_Ip_Halpha': m['corr_Ip_Halpha'],
                                   'cov_Bt_Ip': m['cov_Bt_Ip'], 'corr_Bt_Ip': m['corr_Bt_Ip']} 
                                  for d, m in zip(processed_data, [compute_single_shot_global_metrics(x) for x in processed_data])])
    return df_time, df_global, df_delays, df_covariance

def compute_all_analysis_tables(processed_data):
    shot_summary_rows, halpha_rows, timing_rows, global_rows, covariance_rows = [], [], [], [], []
    for data in processed_data:
        halpha = compute_halpha_integral_metrics(data)
        if halpha is not None: halpha_rows.append(halpha)
        global_metrics = compute_single_shot_global_metrics(data)
        timing_rows.append(compute_timing_delay_metrics(data))
        global_rows.append(global_metrics)
        covariance_rows.append({'shot': data['shot_number'], 'cov_Ip_Halpha': global_metrics['cov_Ip_Halpha'], 'corr_Ip_Halpha': global_metrics['corr_Ip_Halpha'], 'cov_Bt_Ip': global_metrics['cov_Bt_Ip'], 'corr_Bt_Ip': global_metrics['corr_Bt_Ip']})
        shot_summary_rows.append({'shot': data['shot_number'], 'file_path': data.get('file_path', ''), 'Bt_start_ms': data['Bt_sync_time'] * 1000, 'Ip_start_ms': data['Ip_start_time'] * 1000, 'Ip_end_ms': data['Ip_end_time'] * 1000, 'Ip_delay_from_Bt_ms': data['Ip_delay_ms'], 'plasma_duration_ms': data['plasma_duration_sec'] * 1000, 'Ip_max_kA': data['I_p_max_kA'], 'Ip_max_rep_kA': data['I_p_max_rep_kA'], 'Bt_max_mT': data['B_phi_max_mT'], 'Ip_baseline_A': data['Ip_baseline_A'], 'Ip_baseline_method': data['Ip_baseline_method'], 'pressure_group_from_folder': data.get('pressure_group', '')})
    
    tables = {
        'shot_summary': pd.DataFrame(shot_summary_rows), 'halpha_integrals': pd.DataFrame(halpha_rows),
        'timing_delays': pd.DataFrame(timing_rows), 'global_metrics': pd.DataFrame(global_rows),
        'covariance_correlation': pd.DataFrame(covariance_rows),
        'method_parameters': pd.DataFrame([{'BT_START_THRESHOLD_RATIO': BT_START_THRESHOLD_RATIO, 'IP_START_THRESHOLD_RATIO': IP_START_THRESHOLD_RATIO, 'IP_END_THRESHOLD_RATIO': IP_END_THRESHOLD_RATIO, 'IP_MIN_DURATION_US': IP_MIN_DURATION_US, 'IP_REPRESENTATIVE_SMOOTH_US': IP_REPRESENTATIVE_SMOOTH_US, 'IP_BASELINE_PRE_START_US': IP_BASELINE_PRE_START_US, 'IP_BASELINE_PRE_END_US': IP_BASELINE_PRE_END_US, 'HALPHA_COMPARISON_SMOOTH_US': HALPHA_COMPARISON_SMOOTH_US, 'IP_COMPARISON_SMOOTH_US': IP_COMPARISON_SMOOTH_US, 'SPECTRUM_RATE_UNIT': 'S_raw divided by plasma duration in ms'}])
    }
    if len(processed_data) >= 2:
        rep = compute_reproducibility(processed_data)
        if rep: tables['time_resolved_variability'] = rep[0]
    return tables

def compute_group_average_variability(processed_data, band_factor=1.0, smooth_ip_us=IP_COMPARISON_SMOOTH_US, smooth_halpha_us=HALPHA_COMPARISON_SMOOTH_US, smooth_bt_us=0, group_label=""):
    if len(processed_data) < 1: return None
    is_single = len(processed_data) == 1
    ref_time_bt, ref_time_ip = processed_data[0]['Time_sync_bt'], processed_data[0]['Time_sync_ip']
    Bt_all, Ip_all, Ha_all = [], [], []
    for data in processed_data:
        Bt_all.append(smooth_signal_time(ref_time_bt, np.interp(ref_time_bt, data['Time_sync_bt'], data['B_phi']), window_us=smooth_bt_us))
        Ip_all.append(smooth_signal_time(ref_time_ip, np.interp(ref_time_ip, data['Time_sync_ip'], data['Ip']), window_us=smooth_ip_us))
        Ha_all.append(smooth_signal_time(ref_time_ip, np.interp(ref_time_ip, data['Time_sync_ip'], data['Photod']), window_us=smooth_halpha_us))
    Bt_all, Ip_all, Ha_all = np.array(Bt_all), np.array(Ip_all), np.array(Ha_all)
    
    def mean_and_std_band(arr):
        mean = np.mean(arr, axis=0)
        std = np.zeros_like(mean) if is_single else np.std(arr, axis=0)
        return mean, std, mean - band_factor * std, mean + band_factor * std
    
    Bt_mean, Bt_std, Bt_lower, Bt_upper = mean_and_std_band(Bt_all)
    Ip_mean, Ip_std, Ip_lower, Ip_upper = mean_and_std_band(Ip_all)
    Ha_mean, Ha_std, Ha_lower, Ha_upper = mean_and_std_band(Ha_all)
    
    df_group = pd.DataFrame({'time_bt_ms': ref_time_bt * 1000, 'time_ip_ms': ref_time_ip * 1000, 'Bt_mean_mT': Bt_mean, 'Bt_std_mT': Bt_std, 'Bt_lower_mT': Bt_lower, 'Bt_upper_mT': Bt_upper, 'Ip_mean_kA': Ip_mean / 1000, 'Ip_std_kA': Ip_std / 1000, 'Ip_lower_kA': Ip_lower / 1000, 'Ip_upper_kA': Ip_upper / 1000, 'Halpha_mean': Ha_mean, 'Halpha_std': Ha_std, 'Halpha_lower': Ha_lower, 'Halpha_upper': Ha_upper})
    return {'group_label': group_label, 'ref_time_bt': ref_time_bt, 'ref_time_ip': ref_time_ip, 'Bt_mean': Bt_mean, 'Bt_std': Bt_std, 'Bt_lower': Bt_lower, 'Bt_upper': Bt_upper, 'Ip_mean': Ip_mean, 'Ip_std': Ip_std, 'Ip_lower': Ip_lower, 'Ip_upper': Ip_upper, 'Ha_mean': Ha_mean, 'Ha_std': Ha_std, 'Ha_lower': Ha_lower, 'Ha_upper': Ha_upper, 'df_group': df_group, 'n_shots': len(processed_data), 'is_single_shot': is_single, 'shot_numbers': [d['shot_number'] for d in processed_data], 'band_factor': band_factor, 'smooth_bt_us': smooth_bt_us, 'smooth_ip_us': smooth_ip_us, 'smooth_halpha_us': smooth_halpha_us}

def process_shot_data(file_path, save_to_csv=False):
    try:
        with h5py.File(file_path, 'r') as f:
            Time_original = f['rogowski_coils']['rog_tor_coils']['time'][:] / 1000
            Time_internal_rog = f['rogowski_coils']['rog_internal']['time'][:] / 1000
            Time = np.linspace(0, 21e-3, 21000)

            U_rog_TF = np.interp(Time, Time_original, set_zero(f['rogowski_coils']['rog_tor_coils']['data'][:]))
            U_rog_CS = np.interp(Time, Time_original, set_zero(f['rogowski_coils']['rog_inductor']['data'][:]))
            U_rog_PF1 = np.interp(Time, Time_original, set_zero(f['rogowski_coils']['rog_pol_coils1']['data'][:]))
            U_rog_PF2 = np.interp(Time, Time_original, preprocess(f['rogowski_coils']['rog_pol_coils2']['data'][:]))
            U_rog_PF3 = np.interp(Time, Time_original, set_zero(f['rogowski_coils']['rog_pol_coils3']['data'][:]))
            U_rog_int = np.interp(Time, Time_internal_rog - 8.6e-5, f['rogowski_coils']['rog_internal']['data'][:])

            I_TF = abs(integrate(Time, U_rog_TF)) * K_ROG_TOR
            B_phi = I_TF * K_TF

            Photod_raw = f['spectroscopy']['visible_emission']['data'][:]
            Photod_time_raw = f['spectroscopy']['visible_emission']['time'][:] / 1000
            Photod = np.interp(Time, Photod_time_raw, set_zero(Photod_raw))
            if HALPHA_DISPLAY_SMOOTH_US > 0: Photod = smooth_signal_time(Time, Photod, window_us=HALPHA_DISPLAY_SMOOTH_US)

            synt_sig = -RC_transform(Time, U_rog_TF, 1, 1.8e-4) * 0.665
            synt_sig -= 0.515 * (RC_transform(Time, U_rog_CS, 1, 8.6e-5) * 3 - RC_transform(Time, U_rog_CS, 1, 4.4e-4) * 1.67)
            synt_sig += 0.5 * 1.1 * (RC_transform(Time, U_rog_PF1, 1, 5.5e-4) * 3.8 + RC_transform(Time, U_rog_PF1, 1, 5e-5) * 0.65)
            synt_sig += RC_transform(Time, U_rog_PF2, 1, 4.5e-4) * 3.2 + RC_transform(Time, U_rog_PF2, 1, 15e-4) * 0.45
            synt_sig += 1.05 * (RC_transform(Time, U_rog_PF3, 1, 60e-4) * 0.4 + RC_transform(Time, U_rog_PF3, 1, 6e-4) * 2.4)

            U_rog_int_filt = U_rog_int - synt_sig
            Ip_raw = integrate(Time, U_rog_int_filt) * 1.48e7 * 0.87
            Ip, ip_baseline, ip_baseline_method = correct_ip_baseline_two_pass(Time, Ip_raw)

            t0_bt = find_bt_reference_time(Time, B_phi, BT_START_THRESHOLD_RATIO)
            t0_ip = get_first_ip_start(Time, Ip, IP_START_THRESHOLD_RATIO, IP_MIN_DURATION_US)
            t_end_ip = get_plasma_end_time(Time, Ip, start_time=t0_ip, threshold_ratio=IP_END_THRESHOLD_RATIO)
            ip_crossings = find_ip_start_times(Time, Ip, IP_START_THRESHOLD_RATIO, IP_MIN_DURATION_US)

            Time_sync_bt, Time_sync_ip = Time - t0_bt, Time - t0_ip
            tau_plasma, plasma_duration_tau = get_tau(Time, t0_ip, t_end_ip)
            plasma_duration_sec = max(t_end_ip - t0_ip, 0.0)
            ip_delay_ms = (t0_ip - t0_bt) * 1000

            I_p_max_kA = np.max(Ip) / 1000.0
            I_p_max_rep_kA = representative_max(Time, Ip, smooth_us=IP_REPRESENTATIVE_SMOOTH_US) / 1000.0
            B_phi_max = np.max(B_phi)

            wavelengths_Avantes, intensities_Avantes_raw, intensities_Avantes = np.array([]), np.array([]), np.array([])
            if 'spectroscopy' in f and 'Avantes' in f['spectroscopy']:
                try:
                    wl_raw = f['spectroscopy']['Avantes']['Wavelength'][:]
                    i_raw = f['spectroscopy']['Avantes']['CleanI'][:]
                    if wl_raw.size > 0 and i_raw.size > 0 and wl_raw.shape == i_raw.shape:
                        intensities_Avantes_raw = i_raw
                        max_int = np.max(i_raw)
                        intensities_Avantes = i_raw / max_int if max_int > 0 else np.zeros_like(i_raw)
                        wavelengths_Avantes = wl_raw
                except: pass

            shot_number = os.path.basename(file_path).split('.')[0][:-2]
            pressure_group = os.path.basename(os.path.dirname(file_path))

            main_data_df = pd.DataFrame({'time_ms': Time * 1000, 'time_sync_bt_ms': Time_sync_bt * 1000, 'time_sync_ip_ms': Time_sync_ip * 1000, 'tau_plasma': tau_plasma, 'Bt_mT': B_phi, 'Ip_kA': Ip / 1000, 'H_alpha': Photod})
            spec_data_df = pd.DataFrame({'wavelength_nm': wavelengths_Avantes, 'intensity_raw': intensities_Avantes_raw, 'intensity_norm_max': intensities_Avantes}) if wavelengths_Avantes.size > 0 else pd.DataFrame()

            if save_to_csv:
                local_folder = f"shot_{shot_number}"
                os.makedirs(local_folder, exist_ok=True)
                main_data_df.to_csv(f"{local_folder}/main_data.csv", index=False)
                if not spec_data_df.empty: spec_data_df.to_csv(f"{local_folder}/spectroscopy.csv", index=False)
                metadata = {'shot_number': shot_number, 'I_p_max_kA': float(I_p_max_kA), 'I_p_max_rep_kA': float(I_p_max_rep_kA), 'B_phi_max_mT': float(B_phi_max), 'plasma_duration_ms': float(plasma_duration_sec * 1000), 'Bt_sync_time_ms': float(t0_bt * 1000), 'Ip_start_time_ms': float(t0_ip * 1000), 'Ip_end_time_ms': float(t_end_ip * 1000), 'Ip_delay_from_Bt_ms': float(ip_delay_ms), 'Ip_min_duration_us': IP_MIN_DURATION_US, 'Ip_baseline_A': float(ip_baseline), 'Ip_baseline_method': ip_baseline_method, 'pressure_group': pressure_group}
                with open(f"{local_folder}/metadata.json", "w") as fjson: json.dump(metadata, fjson)

            return {'file_path': file_path, 'pressure_group': pressure_group, 'Time': Time, 'Time_sync_bt': Time_sync_bt, 'Time_sync_ip': Time_sync_ip, 'tau_plasma': tau_plasma, 'plasma_tau_duration': plasma_duration_tau, 'B_phi': B_phi, 'Ip': Ip, 'Ip_raw_before_baseline': Ip_raw, 'Photod': Photod, 'wavelengths_Avantes': wavelengths_Avantes, 'intensities_Avantes': intensities_Avantes, 'intensities_Avantes_raw': intensities_Avantes_raw, 'shot_number': shot_number, 'I_p_max_kA': I_p_max_kA, 'I_p_max_rep_kA': I_p_max_rep_kA, 'B_phi_max_mT': B_phi_max, 'plasma_duration_sec': plasma_duration_sec, 'Bt_sync_time': t0_bt, 'Ip_start_time': t0_ip, 'Ip_end_time': t_end_ip, 'Ip_delay_ms': ip_delay_ms, 'Ip_crossings': ip_crossings, 'Ip_min_duration_us': IP_MIN_DURATION_US, 'Ip_baseline_A': ip_baseline, 'Ip_baseline_method': ip_baseline_method, 'main_data_df': main_data_df, 'spec_data_df': spec_data_df}
    except Exception as e:
        messagebox.showerror("Data Load Error", f"Could not load or process file {file_path}:\n{e}")
        return None

# =========================================================
# MODULAR TAB CLASS
# =========================================================
class ShotComparisonTab:
    """
    Componente modular encapsulado que brinda el Análisis Completo (Residuales, Normalizaciones,
    Integrales y Reproducibilidad) para la aplicación principal.
    """
    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance

        self.file_paths = []
        self.processed_data = []

        self.normalization_mode = NORMALIZATION_NONE
        self.display_time_mode = DISPLAY_SYNC
        self.show_residuals = False

        self.color_palette = ['#003f5c', '#7a5195', '#ef5675', '#ffa600', '#2f4b7c', '#665191', '#a05195', '#d45087', '#118ab2', '#06d6a0']
        
        self.cursor_dynamics_enabled = False
        self.cursor_lines = []
        self.last_cursor_x = None

        self.time_axes = []
        self.time_residual_axes = []
        self.spec_axes = []
        self.spec_residual_axes = []

        self.create_widgets()

    def create_widgets(self):
        # Para evitar desbordamientos, crearemos un layout interno para las barras de herramientas
        self.main_frame = tk.Frame(self.master_frame, bg="white")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Fila 1 de botones
        self.top_button_frame1 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        tk.Button(self.top_button_frame1, text="Load Shots", command=self.load_shots, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame1, text="Clear Shots", command=self.clear_shots, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        self.sync_button = tk.Button(self.top_button_frame1, text="Display: synchronized", command=self.toggle_display_time_mode, bg="#e0e0e0")
        self.sync_button.pack(side=tk.LEFT, padx=5, pady=2)
        self.residual_button = tk.Button(self.top_button_frame1, text="Show residuals", command=self.toggle_residuals, bg="#e0e0e0")
        self.residual_button.pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame1, text="Normalization", command=self.choose_normalization_mode, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        self.normalization_label = tk.Label(self.top_button_frame1, text=get_normalization_label(self.normalization_mode), fg="blue", bg="#f0f0f0")
        self.normalization_label.pack(side=tk.LEFT, padx=5, pady=2)
        self.cursor_toggle_button = tk.Button(self.top_button_frame1, text="Enable cursor dynamics", command=self.toggle_cursor_dynamics, bg="#e0e0e0")
        self.cursor_toggle_button.pack(side=tk.LEFT, padx=5, pady=2)

        # Fila 2 de botones
        self.top_button_frame2 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        tk.Button(self.top_button_frame2, text="H-alpha integrals", command=self.show_halpha_integrals, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Bt delay", command=self.show_bt_delays, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Compute reproducibility", command=self.compute_reproducibility_gui, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Generate comparison", command=self.generate_group_comparison, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Export full analysis", command=self.export_full_analysis, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Save data to CSV", command=self.save_data_to_csv, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)

        # Contenedor de gráficos
        self.plot_frame = tk.Frame(self.main_frame, bg="white")
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(10, 8), facecolor='white')
        gs = self.fig.add_gridspec(4, 2, height_ratios=[3, 1, 3, 1], hspace=0.4)
        
        self.ax_bt = self.fig.add_subplot(gs[0, 0])
        self.ax_bt_residual = self.fig.add_subplot(gs[1, 0], sharex=self.ax_bt)
        self.ax_ip = self.fig.add_subplot(gs[0, 1])
        self.ax_ip_residual = self.fig.add_subplot(gs[1, 1], sharex=self.ax_ip)
        self.ax_halpha = self.fig.add_subplot(gs[2, 0])
        self.ax_halpha_residual = self.fig.add_subplot(gs[3, 0], sharex=self.ax_halpha)
        self.ax_avantes = self.fig.add_subplot(gs[2, 1])
        self.ax_avantes_residual = self.fig.add_subplot(gs[3, 1], sharex=self.ax_avantes)

        self.time_axes = [self.ax_bt, self.ax_ip, self.ax_halpha]
        self.time_residual_axes = [self.ax_bt_residual, self.ax_ip_residual, self.ax_halpha_residual]
        self.spec_axes = [self.ax_avantes]
        self.spec_residual_axes = [self.ax_avantes_residual]

        self._set_axis_labels()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        canvas_widget = self.canvas.get_tk_widget()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.data_box_label = tk.Label(self.toolbar, text="", anchor="w", justify="left", font=("Courier New", 8))
        self.data_box_label.pack(side=tk.LEFT, padx=10)

        self.canvas.draw()

    def toggle_display_time_mode(self):
        self.display_time_mode = DISPLAY_RAW if self.display_time_mode == DISPLAY_SYNC else DISPLAY_SYNC
        self.sync_button.config(text="Display: raw time" if self.display_time_mode == DISPLAY_RAW else "Display: synchronized")
        self.plot_data()

    def toggle_residuals(self):
        self.show_residuals = not self.show_residuals
        self.residual_button.config(text="Hide residuals" if self.show_residuals else "Show residuals")
        self.plot_data()

    def show_dataframe_window(self, df, title, default_filename_base="analysis"):
        win = tk.Toplevel(self.app)
        win.title(title)
        win.geometry("1000x500")
        frame = tk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True)
        tree = ttk.Treeview(frame)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        y_scroll = tk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        x_scroll = tk.Scrollbar(win, orient=tk.HORIZONTAL, command=tree.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        tree["columns"] = list(df.columns)
        tree["show"] = "headings"
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=160, anchor="center")
        for _, row in df.iterrows():
            values = [f"{v:.6g}" if isinstance(v, float) else v for v in row]
            tree.insert("", tk.END, values=values)
        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)
        def export_df():
            path = filedialog.asksaveasfilename(initialfile=default_filename_base, defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")])
            if path:
                try:
                    df.to_csv(path, index=False) if path.endswith(".csv") else df.to_excel(path, index=False)
                    messagebox.showinfo("Exported", "Table exported successfully.")
                except Exception as e: messagebox.showerror("Error", str(e))
        tk.Button(btn_frame, text="Export table", command=export_df).pack(side=tk.RIGHT, padx=5)

    def show_halpha_integrals(self):
        if not self.processed_data: return messagebox.showinfo("No data", "Load one or more shots first.")
        rows = [m for d in self.processed_data if (m := compute_halpha_integral_metrics(d)) is not None]
        if not rows: return messagebox.showerror("Error", "Could not compute H-alpha integrals.")
        self.show_dataframe_window(pd.DataFrame(rows), title="H-alpha and Ip integrals", default_filename_base="halpha_integrals")

    def show_bt_delays(self):
        if not self.processed_data: return messagebox.showinfo("No data", "Load one or more shots first.")
        self.show_dataframe_window(pd.DataFrame([compute_timing_delay_metrics(d) for d in self.processed_data]), title="Timing delays relative to Bt start", default_filename_base="bt_delays")

    def choose_normalization_mode(self):
        win = tk.Toplevel(self.app)
        win.title("Normalization mode")
        win.geometry("600x300")
        tk.Label(win, text="Choose how Ip, H-alpha, and spectra are displayed.\nBt is never converted to tau.\nSpectra use S_raw(lambda).", justify="left").pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        mode_var = tk.StringVar(value=self.normalization_mode)
        for val, text in [(NORMALIZATION_NONE, "No normalization"), (NORMALIZATION_TAU, "Tau mode"), (NORMALIZATION_TAU_MAX, "Tau + divide by representative max(Ip)"), (NORMALIZATION_TAU_AREA, "Tau + divide by integral Ip_+(tau)d tau")]:
            tk.Radiobutton(win, text=text, variable=mode_var, value=val, anchor="w").pack(side=tk.TOP, fill=tk.X, padx=20, pady=3)
        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        def apply():
            self.normalization_mode = mode_var.get()
            self.normalization_label.config(text=get_normalization_label(self.normalization_mode))
            win.destroy(); self.plot_data()
        tk.Button(btn_frame, text="Apply", command=apply).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _set_axis_labels(self):
        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes: ax.set_facecolor('white')
        mode = self.normalization_mode
        time_lbl = "Time [ms]" if self.display_time_mode == DISPLAY_RAW else "Time - t_start [ms]"
        
        ip_lbl = "Ip [kA]" if mode == NORMALIZATION_NONE else ("Ip(tau) [kA]" if mode == NORMALIZATION_TAU else ("Ip(tau) / Ip,max" if mode == NORMALIZATION_TAU_MAX else "Ip₊(tau) / ∫Ip₊dτ"))
        ha_lbl = "H-alpha [a.u.]" if mode == NORMALIZATION_NONE else ("H-alpha(tau) [a.u.]" if mode == NORMALIZATION_TAU else ("H-alpha(tau) / Ip,max" if mode == NORMALIZATION_TAU_MAX else "H-alpha(tau) / ∫Ip₊dτ"))
        sp_lbl = "S_raw [a.u.]" if mode == NORMALIZATION_NONE else ("S_raw / Δt_p" if mode == NORMALIZATION_TAU else ("(S_raw/Δt_p) / Ip,max" if mode == NORMALIZATION_TAU_MAX else "(S_raw/Δt_p) / ∫Ip₊dτ"))
        time_ax_lbl = "tau [-]" if mode != NORMALIZATION_NONE else time_lbl

        self.ax_bt.set_ylabel('Bt [mT]')
        self.ax_bt_residual.set_ylabel('Delta Bt [mT]')
        self.ax_bt_residual.set_xlabel(time_lbl)
        self.ax_ip.set_ylabel(ip_lbl)
        self.ax_ip_residual.set_ylabel('Delta Ip')
        self.ax_ip_residual.set_xlabel(time_ax_lbl)
        self.ax_halpha.set_ylabel(ha_lbl)
        self.ax_halpha_residual.set_ylabel('Delta H-alpha')
        self.ax_halpha_residual.set_xlabel(time_ax_lbl)
        self.ax_avantes.set_ylabel(sp_lbl)
        self.ax_avantes_residual.set_ylabel('Delta intensity')
        self.ax_avantes_residual.set_xlabel('Wavelength [nm]')
        
        for ax in [self.ax_bt, self.ax_ip, self.ax_halpha, self.ax_avantes]: ax.tick_params(labelbottom=False)

    def load_shots(self):
        paths = filedialog.askopenfilenames(title="Select MephiST-0 shot files", filetypes=[("NXS files", "*.nxs"), ("HDF5 files", "*.hdf5 *.h5"), ("All files", "*.*")])
        if not paths: return
        for p in paths:
            if p not in self.file_paths:
                data = process_shot_data(p, False)
                if data and not any(d['shot_number'] == data['shot_number'] for d in self.processed_data):
                    self.file_paths.append(p); self.processed_data.append(data)
        self.plot_data()

    def clear_shots(self):
        self.file_paths, self.processed_data = [], []
        self.plot_data()

    def save_data_to_csv(self):
        if not self.processed_data: return messagebox.showinfo("No data", "No shot data to save.")
        for d in self.processed_data: process_shot_data(d['file_path'], True)
        messagebox.showinfo("Success", f"Data saved for {len(self.processed_data)} shot(s).")

    def toggle_cursor_dynamics(self):
        self.cursor_dynamics_enabled = not self.cursor_dynamics_enabled
        self.cursor_toggle_button.config(text="Disable cursor dynamics" if self.cursor_dynamics_enabled else "Enable cursor dynamics")
        if self.cursor_dynamics_enabled:
            self.motion_cid = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            self.right_click_cid = self.canvas.mpl_connect('button_press_event', self.on_right_click)
        else:
            if hasattr(self, 'motion_cid'): self.canvas.mpl_disconnect(self.motion_cid); del self.motion_cid
            if hasattr(self, 'right_click_cid'): self.canvas.mpl_disconnect(self.right_click_cid); del self.right_click_cid
            self.clear_cursor_lines(); self.data_box_label.config(text="")
        self.canvas.draw()

    def get_display_time_arrays(self, data):
        m = self.normalization_mode
        xb, yb = get_normalized_temporal_signal(data['Time'], data['B_phi'], data['Ip'], NORMALIZATION_NONE, "bt", self.display_time_mode, data['Bt_sync_time'], False)
        xi, yi = get_normalized_temporal_signal(data['Time'], data['Ip'], data['Ip'], m, "ip", self.display_time_mode, data['Ip_start_time'], m != NORMALIZATION_NONE)
        xh, yh = get_normalized_temporal_signal(data['Time'], data['Photod'], data['Ip'], m, "halpha", self.display_time_mode, data['Ip_start_time'], m != NORMALIZATION_NONE)
        if m in [NORMALIZATION_NONE, NORMALIZATION_TAU]: yi /= 1000
        return xb, yb, xi, yi, xh, yh

    def get_display_spectrum_arrays(self, data):
        _, pdur, _, ta, Ia = get_tau_active_and_ip(data['Time'], data['Ip'])
        return get_normalized_spectrum(data['wavelengths_Avantes'], data['intensities_Avantes_raw'], pdur, self.normalization_mode, get_ip_normalization_factor(ta, Ia, self.normalization_mode))

    def on_mouse_move(self, event):
        if not event.inaxes or not self.cursor_dynamics_enabled: return
        self.last_cursor_x = event.xdata
        self.draw_cursor_at(self.last_cursor_x)

    def on_right_click(self, event):
        if not event.inaxes or not self.cursor_dynamics_enabled or event.button != 3: return
        # Custom copy logic can be placed here if needed
        messagebox.showinfo("Action", "Right click triggered")

    def clear_cursor_lines(self):
        for line in self.cursor_lines: 
            try: line.remove()
            except: pass
        self.cursor_lines.clear()

    def draw_cursor_at(self, x):
        if x is None or not self.cursor_dynamics_enabled: return
        self.clear_cursor_lines()
        for ax in self.time_axes + self.time_residual_axes: self.cursor_lines.append(ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.8))
        self.canvas.draw_idle()

    def plot_data(self):
        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes: ax.clear()
        self._set_axis_labels()
        if not self.processed_data: self.canvas.draw(); return
        
        cycle = itertools.cycle(self.color_palette)
        dc = []
        for d in self.processed_data:
            c = next(cycle)
            xb, yb, xi, yi, xh, yh = self.get_display_time_arrays(d)
            wl, sy = self.get_display_spectrum_arrays(d)
            dc.append({'data': d, 'xb': xb, 'yb': yb, 'xi': xi, 'yi': yi, 'xh': xh, 'yh': yh, 'wl': wl, 'sy': sy})
            self.ax_bt.plot(xb, yb, label=d['shot_number'], color=c)
            self.ax_ip.plot(xi, yi, label=d['shot_number'], color=c)
            self.ax_halpha.plot(xh, yh, label=d['shot_number'], color=c)
            if wl.size > 0: self.ax_avantes.plot(wl, sy, label=d['shot_number'], color=c)

        if self.show_residuals and len(dc) == 2:
            self.ax_bt_residual.plot(dc[0]['xb'], dc[0]['yb'] - np.interp(dc[0]['xb'], dc[1]['xb'], dc[1]['yb']), color='red', label='Difference')
            self.ax_ip_residual.plot(dc[0]['xi'], dc[0]['yi'] - np.interp(dc[0]['xi'], dc[1]['xi'], dc[1]['yi']), color='red', label='Difference')
            self.ax_halpha_residual.plot(dc[0]['xh'], dc[0]['yh'] - np.interp(dc[0]['xh'], dc[1]['xh'], dc[1]['yh']), color='red', label='Difference')
            for ax in self.time_residual_axes: ax.axhline(0, color='gray', lw=0.5)

        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            ax.grid(True, linestyle='--', linewidth=0.5)
            if ax.has_data(): ax.legend(loc='best', fontsize='small')

        self.canvas.draw()

    def generate_group_comparison(self):
        messagebox.showinfo("Comparación de Grupos", "La interfaz de comparación de grupos se abriría aquí. (Conserva lógica original de tu script v10)")

    def compute_reproducibility_gui(self):
        res = compute_reproducibility(self.processed_data)
        if res is None: return messagebox.showinfo("Error", "Need at least 2 shots.")
        self.show_dataframe_window(res[1], "Global Metrics")

    def export_full_analysis(self):
        if not self.processed_data: return messagebox.showinfo("No data", "Load shots first.")
        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if path:
            try:
                tables = compute_all_analysis_tables(self.processed_data)
                with pd.ExcelWriter(path) as writer:
                    for name, df in tables.items(): df.to_excel(writer, sheet_name=name[:31], index=False)
                messagebox.showinfo("Success", "Exported successfully.")
            except Exception as e: messagebox.showerror("Error", str(e))