import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import os
import pyperclip
import itertools
import colorsys
import pandas as pd
import json
import re
from pathlib import Path

# =========================================================
# NUMPY COMPATIBILITY
# =========================================================
def trapz_compat(y, x=None):
    """Compatibility wrapper for trapezoidal integration.

    NumPy 2.x removed np.trapz; np.trapezoid is the replacement.
    This wrapper keeps the code working in both NumPy 1.x and 2.x.
    """
    if hasattr(np, "trapezoid"):
        return np.trapezoid(y, x)
    return np.trapz(y, x)
import traceback

# =========================================================
# EXPORT HELPERS
# =========================================================
def save_dataframe_with_openpyxl_fallback(df, path, index=False):
    """
    Save one DataFrame as CSV or Excel.

    If the user chooses .xlsx but openpyxl is not installed, the code saves
    a .csv file with the same base name instead of failing.
    """
    p = Path(path)

    if p.suffix.lower() == ".csv":
        df.to_csv(p, index=index)
        return p, "csv"

    try:
        import openpyxl  # noqa: F401
        df.to_excel(p, index=index, engine="openpyxl")
        return p, "xlsx"
    except ImportError:
        fallback = p.with_suffix(".csv")
        df.to_csv(fallback, index=index)
        return fallback, "csv_fallback"


def save_workbook_with_openpyxl_fallback(path, tables):
    """
    Save several DataFrames as an Excel workbook.

    tables can be either:
        dict[str, DataFrame]
        list[tuple[str, DataFrame]]

    If openpyxl is not installed, creates a folder with one CSV per sheet.
    """
    p = Path(path)

    if isinstance(tables, dict):
        items = list(tables.items())
    else:
        items = list(tables)

    try:
        import openpyxl  # noqa: F401
        with pd.ExcelWriter(p, engine="openpyxl") as writer:
            for sheet_name, df in items:
                clean_name = str(sheet_name).replace("/", "_").replace("\\", "_").replace(":", "_")[:31]
                df.to_excel(writer, sheet_name=clean_name, index=False)
        return p, "xlsx"
    except ImportError:
        out_dir = p.with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)

        for sheet_name, df in items:
            clean_name = str(sheet_name).replace("/", "_").replace("\\", "_").replace(":", "_")
            clean_name = re.sub(r"[^A-Za-z0-9_. -]+", "_", clean_name).strip() or "sheet"
            df.to_csv(out_dir / f"{clean_name}.csv", index=False)

        return out_dir, "csv_folder"


# =========================================================
# GLOBAL PARAMETERS
# =========================================================
K_ROG_TOR = 6.3e6
K_TF = 9.6e-3
K_ROG_IND = 6.3e6
K_ROG_PF1 = 6.23e6
BT_START_THRESHOLD_RATIO = 0.15
IP_START_THRESHOLD_RATIO = 0.05

# Ip start detector:
# The official Ip start is obtained by finding Ip,max and then searching
# backward for the last upward crossing of IP_START_THRESHOLD_RATIO * Ip_max_ref
# before that maximum. This keeps the 5% criterion, but avoids selecting an
# early low-current precursor when the main Ip rise occurs later.
IP_START_BACKWARD_FROM_PEAK_SMOOTH_US = 10

# Fallback Ip end detector:
# If no plateau is found, the plasma end is taken as the first time after Ip,max
# where Ip stays below IP_END_THRESHOLD_RATIO * Ip_max_ref for IP_END_AFTER_MAX_GAP_US.
IP_END_THRESHOLD_RATIO = 0.05
IP_END_AFTER_MAX_SMOOTH_US = 10
IP_END_AFTER_MAX_GAP_US = 80

# =========================================================
# Ip plateau end detector
# =========================================================
# Official plasma end is determined from Ip, not from H-alpha:
#   1) first valid low-slope Ip plateau/knee after Ip,max,
#   2) fallback threshold after Ip,max if no plateau is found.
#
# A plateau is accepted only when BOTH conditions are true for a sustained time:
#   A) Ip <= IP_PLATEAU_MAX_CURRENT_RATIO * Ip_max_ref
#   B) |dIp/dt| <= IP_PLATEAU_FIXED_SLOPE_LIMIT_KA_PER_MS
#
# There is no lead/advance correction anymore: the code cuts exactly at the
# first sample where the sustained plateau begins.
IP_PLATEAU_DETECTION_ENABLED = True

# Single amplitude restriction used by both plateau detectors.
# Example: 0.30 means a plateau is accepted only when Ip <= 0.30 * Ip_max_ref.
IP_PLATEAU_MAX_CURRENT_RATIO = 0.30

# Fixed slope threshold, independent of Ip_max. Units: kA/ms.
# Larger values detect the plateau earlier; smaller values require a flatter tail.
IP_PLATEAU_FIXED_SLOPE_LIMIT_KA_PER_MS = 0.9

# The low-slope + low-current condition must persist for this duration.
IP_PLATEAU_MIN_DURATION_US = 60

# Wait this long after Ip,max before searching for a plateau.
IP_PLATEAU_MIN_AFTER_PEAK_US = 80

# Targeted detector for abrupt drops into a low-current residual plateau.
# It uses the same IP_PLATEAU_MAX_CURRENT_RATIO and does not cut before the
# detected step. It is meant only for shots where the smooth-knee detector fails.
IP_STEP_PLATEAU_DETECTION_ENABLED = True
IP_STEP_PLATEAU_MIN_AFTER_PEAK_US = 150
IP_STEP_PLATEAU_PRE_WINDOW_US = 70
IP_STEP_PLATEAU_POST_WINDOW_US = 100
IP_STEP_PLATEAU_DROP_RATIO = 0.05
IP_STEP_PLATEAU_POST_ABSOLUTE_SLOPE_KA_PER_MS = 0.90

IP_MIN_DURATION_US = 20
IP_REPRESENTATIVE_SMOOTH_US = 10
IP_BASELINE_PRE_START_US = 800
IP_BASELINE_PRE_END_US = 200
IP_FALLBACK_BASELINE_INDEX = 6600
HALPHA_DISPLAY_SMOOTH_US = 0
HALPHA_COMPARISON_SMOOTH_US = 10
IP_COMPARISON_SMOOTH_US = 10

# H-alpha end detection is auxiliary.
# The official plasma end used for tau/plasma duration is determined from Ip.
# H-alpha end is only stored for optical-emission diagnostics and H-alpha integrals.
HALPHA_END_THRESHOLD_RATIO = 0.3
HALPHA_END_SMOOTH_US = 10
HALPHA_END_MIN_ACTIVE_US = 20
HALPHA_END_GAP_US = 120
HALPHA_END_MAX_SEARCH_MS = 8.0


NORMALIZATION_NONE = "none"
NORMALIZATION_TAU = "tau"
NORMALIZATION_TAU_MAX = "tau_max"
NORMALIZATION_TAU_AREA = "tau_area"
DISPLAY_SYNC = "sync"
DISPLAY_RAW = "raw"

# =========================================================
# SPECTROSCOPY INTENSITY NORMALIZATION
# =========================================================
# For the NIST matched-line table, the experimental Avantes intensity is not
# ranked from the raw/CleanI array. It is ranked from the RW spectrum normalized
# by:
#
#     S_rw_norm(lambda) = S_rw(lambda) / (Delta t_plasma * integral_0^1 Ip_+(tau)d tau)
#
# where Delta t_plasma = Ip_end - Ip_start and the Ip integral is computed over
# the Ip-defined plasma window. This makes line intensities more comparable
# between shots with different plasma duration and different integrated current.
AVANTES_RW_DATASET_CANDIDATES = (
    "rw", "RW", "Rw", "rW",
    "S_rw", "s_rw",
    "Spectrum_rw", "spectrum_rw",
    "CleanI", "cleanI", "clean_i",
)


def read_first_existing_dataset(h5_group, candidates):
    """Return (array, key) for the first dataset found in an HDF5 group."""
    for key in candidates:
        if key in h5_group:
            try:
                return np.asarray(h5_group[key][:]), key
            except Exception:
                pass
    return np.array([]), ""


def get_spectroscopy_plasma_normalization_factor(Time, Ip, ip_start, ip_end):
    """
    Return (factor, duration_s, Ip_integral_tau_A, Ip_integral_time_C).

    For the spectroscopy filter and the tau-area display mode, the intended
    normalization is:

        S_rw_norm(lambda) = S_rw(lambda) /
                            (Delta t_plasma * integral_0^1 Ip_+(tau) d tau)

    Since:
        dt = Delta t_plasma * d tau

    then:
        Delta t_plasma * integral_0^1 Ip_+(tau) d tau
        =
        integral Ip_+(t) dt

    This avoids dividing by the plasma duration twice, while keeping the visual
    Ip normalization meaningful in tau space.
    """
    Time = np.asarray(Time)
    Ip = np.asarray(Ip)

    if Time.size < 2 or Ip.size < 2 or Time.shape != Ip.shape:
        return 1.0, np.nan, np.nan, np.nan

    if ip_start is None or ip_end is None or not np.isfinite(ip_start) or not np.isfinite(ip_end):
        return 1.0, np.nan, np.nan, np.nan

    duration_s = float(ip_end - ip_start)
    if not np.isfinite(duration_s) or duration_s <= 0:
        return 1.0, duration_s, np.nan, np.nan

    tau, _ = get_tau(Time, ip_start, ip_end)
    active_mask = (tau >= 0.0) & (tau <= 1.0)

    if np.sum(active_mask) < 2:
        return 1.0, duration_s, np.nan, np.nan

    tau_active = tau[active_mask]
    t_active = Time[active_mask]
    ip_active = Ip[active_mask]
    ip_pos = positive_part(ip_active)

    ip_integral_tau_A = float(trapz_compat(ip_pos, tau_active))
    ip_integral_time_C = float(trapz_compat(ip_pos, t_active))

    if not np.isfinite(ip_integral_tau_A) or ip_integral_tau_A <= 0:
        return 1.0, duration_s, ip_integral_tau_A, ip_integral_time_C

    factor = duration_s * ip_integral_tau_A

    if not np.isfinite(factor) or factor <= 0:
        return 1.0, duration_s, ip_integral_tau_A, ip_integral_time_C

    return factor, duration_s, ip_integral_tau_A, ip_integral_time_C


def get_spectroscopy_rw_normalized_arrays(data):
    """
    Return wavelength and normalized Avantes RW intensity arrays for matched-line
    analysis.

    The returned intensity is:
        S_rw(lambda) / (Delta t_plasma * integral_0^1 Ip_+(tau)d tau)
    """
    wl = np.asarray(data.get("wavelengths_Avantes", np.array([])), dtype=float)
    rw = np.asarray(data.get("intensities_Avantes_rw", np.array([])), dtype=float)

    if rw.size == 0:
        # Backward-compatible fallback for older loaded shots/files that do not
        # yet have the RW key. Prefer not to fail silently, but keep the tool usable.
        rw = np.asarray(data.get("intensities_Avantes_raw", np.array([])), dtype=float)

    if wl.size == 0 or rw.size == 0 or wl.shape != rw.shape:
        return wl, rw, {
            "spectrum_source": data.get("Avantes_intensity_source", "missing"),
            "spectrum_normalization_factor": np.nan,
            "plasma_duration_s_for_spectrum": np.nan,
            "Ip_integral_plasma_tau_positive_A_for_spectrum": np.nan,
            "Ip_integral_plasma_time_positive_C_for_spectrum": np.nan,
        }

    factor, duration_s, ip_integral_tau_A, ip_integral_time_C = get_spectroscopy_plasma_normalization_factor(
        data.get("Time", np.array([])),
        data.get("Ip", np.array([])),
        data.get("Ip_start_time", np.nan),
        data.get("Ip_end_time", np.nan),
    )

    rw_norm = rw / factor if factor > 0 else rw

    meta = {
        "spectrum_source": data.get("Avantes_intensity_source", "rw_or_fallback"),
        "spectrum_normalization_factor": factor,
        "plasma_duration_s_for_spectrum": duration_s,
        "Ip_integral_plasma_tau_positive_A_for_spectrum": ip_integral_tau_A,
        "Ip_integral_plasma_time_positive_C_for_spectrum": ip_integral_time_C,
    }

    return wl, rw_norm, meta


# =========================================================
# LOCAL NIST EMISSION-LINE DATABASE
# =========================================================
# Keep this path relative to the repository so the code works on GitHub/clones.
# Recommended repository layout:
#   MEPHIST-0_visualizer/
#       src/shot_comparison_tab.py
#       Lineas de emisión/*.csv
#
# You can override it with the environment variable:
#   MEPHIST_EMISSION_LINES_DIR=C:/path/to/Lineas de emisión
EMISSION_LINES_FOLDER_NAME = "Líneas de emisión"
EMISSION_LINE_FILE_EXTENSIONS = (".csv", ".txt", ".tsv")

# NIST-to-experiment matching parameters.
# MATCH_TOLERANCE_NM should be comparable to the Avantes/Ocean-FX resolution
# reported for MEPhIST-0 (~0.5 nm). Here 1.0 nm is used to absorb
# wavelength calibration offsets such as H-alpha 656.28 nm measured near 657.0 nm.
NIST_MATCH_TOLERANCE_NM = 1.00
NIST_MIN_RELATIVE_PEAK_HEIGHT = 0.03
NIST_NOISE_SIGMA_FACTOR = 5.0
NIST_LOCAL_BACKGROUND_WINDOW_NM = 2.0
NIST_MIN_PROMINENCE_RELATIVE = 0.01


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


def safe_area(x, y):
    """Robust trapezoidal area. Returns 0 when there are not enough points."""
    x = np.asarray(x)
    y = np.asarray(y)
    if len(x) < 2 or len(y) < 2 or len(x) != len(y):
        return 0.0
    area = float(trapz_compat(y, x))
    return area if np.isfinite(area) else 0.0

def get_ip_tau_area_factor(tau_active, Ip_active):
    """
    Factor used by the DISPLAY normalization τ / ∫Ip.

    It uses the same x-axis that is plotted in this mode: tau. Therefore,
    after normalization, ∫ Ip_norm(tau) d tau = 1 for the positive Ip signal.
    This makes the effect visible and mathematically testable in the display.
    """
    factor = safe_area(tau_active, positive_part(Ip_active))
    return factor if factor > 1e-15 else 1.0

def get_ip_time_area_factor(time_active, Ip_active):
    """Physical current integral in real time, useful for exported charge-like metrics."""
    factor = safe_area(time_active, positive_part(Ip_active))
    return factor if factor > 1e-15 else 1.0

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

def get_ip_start_backward_from_peak_info(
    Time,
    Ip,
    threshold_ratio=IP_START_THRESHOLD_RATIO,
    min_duration_us=IP_MIN_DURATION_US,
    smooth_us=IP_START_BACKWARD_FROM_PEAK_SMOOTH_US
):
    """
    Official Ip-start detector based on a backward search from Ip,max.

    Logic:
      1) Smooth Ip slightly and keep its positive part.
      2) Find Ip,max_ref and the time/index of the maximum.
      3) Define the start threshold as threshold_ratio * Ip,max_ref.
      4) Search only before Ip,max and select the LAST upward crossing of that
         threshold before the maximum.

    This keeps the same physical 5% criterion, but avoids taking an early
    low-current precursor as the plasma start when the main rise occurs later.
    """
    Time = np.asarray(Time)
    Ip = np.asarray(Ip)

    if len(Time) < 3 or len(Ip) < 3:
        fallback_time = Time[0] if len(Time) > 0 else 0.0
        return {
            'start_time': fallback_time,
            'method': 'Ip_start_invalid_signal',
            'threshold_start_time': fallback_time,
            'ip_peak_time': np.nan,
            'ip_start_threshold_A': np.nan,
            'ip_start_ip_max_ref_A': np.nan,
            'ip_start_peak_idx': np.nan,
        }

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return {
            'start_time': Time[0],
            'method': 'Ip_start_invalid_dt',
            'threshold_start_time': Time[0],
            'ip_peak_time': np.nan,
            'ip_start_threshold_A': np.nan,
            'ip_start_ip_max_ref_A': np.nan,
            'ip_start_peak_idx': np.nan,
        }

    Ip_smooth = smooth_signal_time(Time, Ip, window_us=smooth_us)
    Ip_pos = positive_part(Ip_smooth)

    ip_max_ref = representative_max(
        Time,
        Ip_smooth,
        smooth_us=IP_REPRESENTATIVE_SMOOTH_US
    )

    if not np.isfinite(ip_max_ref) or ip_max_ref <= 0:
        return {
            'start_time': Time[0],
            'method': 'Ip_start_bad_ipmax',
            'threshold_start_time': Time[0],
            'ip_peak_time': np.nan,
            'ip_start_threshold_A': np.nan,
            'ip_start_ip_max_ref_A': ip_max_ref,
            'ip_start_peak_idx': np.nan,
        }

    # Use the smoothed positive signal to locate the main maximum.
    peak_idx = int(np.nanargmax(Ip_pos))
    threshold = threshold_ratio * ip_max_ref
    above = Ip_pos > threshold

    min_samples = max(
        int(np.ceil((min_duration_us * 1e-6) / dt)),
        1
    )

    # Rising crossings before the peak. The selected start is the last valid
    # crossing before Ip,max, i.e. what is found when going backward from Ip,max.
    crossing_indices = np.where(np.diff(above.astype(int)) == 1)[0] + 1
    crossing_indices = crossing_indices[crossing_indices <= peak_idx]

    valid_crossings = []
    for idx in crossing_indices:
        if idx + min_samples <= len(above) and np.all(above[idx:idx + min_samples]):
            valid_crossings.append(idx)

    if valid_crossings:
        start_idx = int(valid_crossings[-1])
        start_time = Time[start_idx]
        method = 'Ip_start_backward_from_peak_5pct'
    else:
        # If the signal is already above threshold at the beginning of the record
        # and remains connected to the peak, use the first valid above-threshold
        # sample before the peak.
        above_before_peak = np.where(above[:peak_idx + 1])[0]
        if len(above_before_peak) > 0:
            start_idx = int(above_before_peak[0])
            start_time = Time[start_idx]
            method = 'Ip_start_backward_from_peak_already_above'
        else:
            start_idx = 0
            start_time = Time[0]
            method = 'Ip_start_backward_from_peak_not_found'

    return {
        'start_time': start_time,
        'method': method,
        'threshold_start_time': start_time,
        'ip_peak_time': Time[peak_idx],
        'ip_start_threshold_A': threshold,
        'ip_start_ip_max_ref_A': ip_max_ref,
        'ip_start_peak_idx': peak_idx,
    }

def find_ip_start_times(Time, Ip, threshold_ratio=IP_START_THRESHOLD_RATIO, min_duration_us=IP_MIN_DURATION_US):
    """
    Backward-from-Ipmax start detector.

    The function keeps the old public name for compatibility, but now returns
    the official start obtained as the last 5% upward crossing before Ip,max.
    """
    info = get_ip_start_backward_from_peak_info(
        Time,
        Ip,
        threshold_ratio=threshold_ratio,
        min_duration_us=min_duration_us
    )
    start_time = info.get('start_time', np.nan)
    if start_time is None or not np.isfinite(start_time):
        return np.array([])
    return np.array([start_time])

def get_first_ip_start(Time, Ip, threshold_ratio=IP_START_THRESHOLD_RATIO, min_duration_us=IP_MIN_DURATION_US):
    info = get_ip_start_backward_from_peak_info(
        Time,
        Ip,
        threshold_ratio=threshold_ratio,
        min_duration_us=min_duration_us
    )
    return info['start_time']

def get_ip_after_max_threshold_end_time(
    Time,
    Ip,
    start_time,
    threshold_ratio=IP_END_THRESHOLD_RATIO,
    smooth_us=IP_END_AFTER_MAX_SMOOTH_US,
    gap_us=IP_END_AFTER_MAX_GAP_US
):
    """
    Fallback Ip end detector.

    It defines the end as the first time AFTER the Ip maximum where Ip stays
    below threshold_ratio * Ip_max for a continuous gap.
    """
    Time = np.asarray(Time)
    Ip = np.asarray(Ip)

    if len(Time) < 2 or len(Ip) < 2:
        return Time[-1] if len(Time) > 0 else 0.0, None, 0.0

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return Time[-1], None, 0.0

    after_start = Time >= start_time
    if np.sum(after_start) < 2:
        return Time[-1], None, 0.0

    Ip_smooth = smooth_signal_time(Time, Ip, window_us=smooth_us)
    Ip_pos = positive_part(Ip_smooth)

    after_indices = np.where(after_start)[0]
    ip_after = Ip_pos[after_indices]
    if ip_after.size < 2 or np.nanmax(ip_after) <= 0:
        return Time[-1], None, 0.0

    local_peak_pos = int(np.nanargmax(ip_after))
    peak_idx = int(after_indices[local_peak_pos])
    ip_max_ref = float(ip_after[local_peak_pos])

    if ip_max_ref <= 0:
        return Time[-1], peak_idx, ip_max_ref

    threshold = threshold_ratio * ip_max_ref
    below = Ip_pos < threshold
    gap_samples = max(int(np.ceil((gap_us * 1e-6) / dt)), 1)

    below_run = 0
    for idx in range(peak_idx, len(Time)):
        if below[idx]:
            below_run += 1
            if below_run >= gap_samples:
                end_idx = max(idx - gap_samples + 1, peak_idx)
                return Time[end_idx], peak_idx, ip_max_ref
        else:
            below_run = 0

    return Time[-1], peak_idx, ip_max_ref


def detect_ip_plateau_start_time(
    Time,
    Ip,
    start_time,
    peak_idx=None,
    ip_max_ref=None,
    smooth_us=IP_END_AFTER_MAX_SMOOTH_US,
    max_current_ratio=IP_PLATEAU_MAX_CURRENT_RATIO,
    fixed_slope_limit_kA_per_ms=IP_PLATEAU_FIXED_SLOPE_LIMIT_KA_PER_MS,
    min_duration_us=IP_PLATEAU_MIN_DURATION_US,
    min_after_peak_us=IP_PLATEAU_MIN_AFTER_PEAK_US
):
    """
    Detect the first sustained low-current, low-slope Ip plateau after Ip,max.

    This detector intentionally uses a single amplitude restriction:
        Ip <= max_current_ratio * Ip_max_ref

    and a fixed slope threshold independent of Ip,max:
        |dIp/dt| <= fixed_slope_limit_kA_per_ms

    There is no lead/advance correction. The returned time is exactly the first
    sample of the sustained plateau condition.
    """
    Time = np.asarray(Time)
    Ip = np.asarray(Ip)

    if not IP_PLATEAU_DETECTION_ENABLED:
        return None, "plateau_disabled"

    if len(Time) < 3 or len(Ip) < 3:
        return None, "plateau_invalid_signal"

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return None, "plateau_invalid_dt"

    Ip_smooth = smooth_signal_time(Time, Ip, window_us=smooth_us)
    Ip_pos = positive_part(Ip_smooth)

    if peak_idx is None or peak_idx < 0 or peak_idx >= len(Time):
        after_indices = np.where(Time >= start_time)[0]
        if len(after_indices) < 2:
            return None, "plateau_no_after_start"
        local_peak_pos = int(np.nanargmax(Ip_pos[after_indices]))
        peak_idx = int(after_indices[local_peak_pos])

    if ip_max_ref is None or ip_max_ref <= 0:
        ip_max_ref = float(Ip_pos[peak_idx])

    if ip_max_ref <= 0:
        return None, "plateau_bad_ipmax"

    min_samples = max(int(np.ceil((min_duration_us * 1e-6) / dt)), 1)
    min_after_peak_samples = max(int(np.ceil((min_after_peak_us * 1e-6) / dt)), 1)
    start_search_idx = min(peak_idx + min_after_peak_samples, len(Time) - 1)

    dIp_dt = np.gradient(Ip_smooth, Time)

    level_limit = max_current_ratio * ip_max_ref
    slope_limit = fixed_slope_limit_kA_per_ms * 1e6  # kA/ms -> A/s

    candidate = (
        (np.arange(len(Time)) >= start_search_idx) &
        (Ip_pos <= level_limit) &
        (np.abs(dIp_dt) <= slope_limit)
    )

    run = 0
    for idx in range(start_search_idx, len(Time)):
        if candidate[idx]:
            run += 1
            if run >= min_samples:
                plateau_first_idx = idx - run + 1
                return Time[plateau_first_idx], "Ip_plateau_fixed_slope_no_lead"
        else:
            run = 0

    return None, "plateau_not_found"



def detect_ip_step_to_plateau_time(
    Time,
    Ip,
    start_time,
    peak_idx=None,
    ip_max_ref=None,
    smooth_us=IP_END_AFTER_MAX_SMOOTH_US
):
    """
    Detector for the beginning of the final residual-current plateau.

    This version does not require a perfectly abrupt step. Instead, it searches
    for the first time after Ip,max where Ip has already entered a low-current
    region and remains low/stable over a short forward window.

    Conditions:
      1) Ip at idx is below IP_PLATEAU_MAX_CURRENT_RATIO * Ip_max_ref.
      2) The forward window remains below that same current level.
      3) The forward window has small variation, so it behaves like a residual plateau.
      4) The local slope is not too large.

    It returns the first valid point, not the best-scored point.
    """

    if not IP_STEP_PLATEAU_DETECTION_ENABLED:
        return None, "step_plateau_disabled"

    Time = np.asarray(Time)
    Ip = np.asarray(Ip)

    if len(Time) < 5 or len(Ip) < 5:
        return None, "step_plateau_invalid_signal"

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return None, "step_plateau_invalid_dt"

    Ip_smooth = smooth_signal_time(
        Time,
        Ip,
        window_us=smooth_us
    )

    Ip_pos = positive_part(Ip_smooth)

    if peak_idx is None or peak_idx < 0 or peak_idx >= len(Time):
        after_indices = np.where(Time >= start_time)[0]
        if len(after_indices) < 2:
            return None, "step_plateau_no_after_start"

        peak_idx = int(
            after_indices[
                int(np.nanargmax(Ip_pos[after_indices]))
            ]
        )

    if ip_max_ref is None or ip_max_ref <= 0:
        ip_max_ref = float(Ip_pos[peak_idx])

    if ip_max_ref <= 0:
        return None, "step_plateau_bad_ipmax"

    min_after_samples = max(
        int(np.ceil((IP_STEP_PLATEAU_MIN_AFTER_PEAK_US * 1e-6) / dt)),
        1
    )

    post_samples = max(
        int(np.ceil((IP_STEP_PLATEAU_POST_WINDOW_US * 1e-6) / dt)),
        2
    )

    start_idx = peak_idx + min_after_samples
    stop_idx = len(Time) - post_samples - 1

    if start_idx >= stop_idx:
        return None, "step_plateau_no_room"

    dIp_dt = np.gradient(Ip_smooth, Time)

    level_limit = IP_PLATEAU_MAX_CURRENT_RATIO * ip_max_ref

    slope_limit = (
        IP_STEP_PLATEAU_POST_ABSOLUTE_SLOPE_KA_PER_MS
        * 1e6
    )

    # This controls how stable the future window must be.
    # Example: 0.08 means the peak-to-peak variation in the post-window
    # must be less than 8% of Ip_max_ref.
    plateau_variation_limit = 0.08 * ip_max_ref

    for idx in range(start_idx, stop_idx):

        # Current at the candidate point must already be low.
        if Ip_pos[idx] > level_limit:
            continue

        post = Ip_pos[idx:idx + post_samples]
        post_slope = np.abs(dIp_dt[idx:idx + post_samples])

        if len(post) < 2:
            continue

        post_mean = float(np.nanmean(post))
        post_max = float(np.nanmax(post))
        post_min = float(np.nanmin(post))
        post_range = post_max - post_min
        post_slope_mean = float(np.nanmean(post_slope))

        # The future window must remain in the low-current region.
        if post_mean > level_limit:
            continue

        # Avoid accepting a point where the current briefly dips but rises again.
        if post_max > 1.10 * level_limit:
            continue

        # The future window must look like a residual plateau, not like a
        # continuing strong decay.
        if post_range > plateau_variation_limit:
            continue

        # The average future slope must be low enough.
        if post_slope_mean > slope_limit:
            continue

        return Time[idx], "Ip_step_residual_plateau_first_valid"

    return None, "step_plateau_not_found"


def get_plasma_end_time(
    Time,
    Ip,
    start_time,
    threshold_ratio=IP_END_THRESHOLD_RATIO,
    smooth_us=IP_END_AFTER_MAX_SMOOTH_US,
    gap_us=IP_END_AFTER_MAX_GAP_US,
    return_details=False
):
    """
    Official plasma-end detector based on Ip.

    Priority:
      1) If a residual Ip plateau is detected after Ip,max, use the first
         sample of that sustained plateau.
      2) Otherwise use the fallback threshold criterion: after Ip,max, when Ip
         stays below IP_END_THRESHOLD_RATIO * Ip,max for IP_END_AFTER_MAX_GAP_US.

    This keeps the rising and falling effective Ip phase, but excludes the
    low-current residual plateau from tau.
    """
    threshold_end, peak_idx, ip_max_ref = get_ip_after_max_threshold_end_time(
        Time,
        Ip,
        start_time,
        threshold_ratio=threshold_ratio,
        smooth_us=smooth_us,
        gap_us=gap_us
    )

    plateau_end = None
    plateau_method = "plateau_not_checked"
    if IP_PLATEAU_DETECTION_ENABLED:
        plateau_end, plateau_method = detect_ip_plateau_start_time(
            Time,
            Ip,
            start_time=start_time,
            peak_idx=peak_idx,
            ip_max_ref=ip_max_ref,
            smooth_us=smooth_us
        )

    step_end = None
    step_method = "step_plateau_not_checked"
    if IP_STEP_PLATEAU_DETECTION_ENABLED:
        step_end, step_method = detect_ip_step_to_plateau_time(
            Time,
            Ip,
            start_time=start_time,
            peak_idx=peak_idx,
            ip_max_ref=ip_max_ref,
            smooth_us=smooth_us
        )

    end_time = threshold_end
    method = "Ip_after_max_threshold"

    # Use only local/shot-specific plateau candidates that occur earlier than
    # the threshold fallback. This prevents problematic step-like plateaus from
    # being included, without globally shortening well-behaved shots.
    candidates = []
    if plateau_end is not None and np.isfinite(plateau_end) and plateau_end > start_time and plateau_end <= threshold_end:
        candidates.append((plateau_end, plateau_method))
    if step_end is not None and np.isfinite(step_end) and step_end > start_time and step_end <= threshold_end:
        candidates.append((step_end, step_method))

    if candidates:
        end_time, method = min(candidates, key=lambda x: x[0])

    if return_details:
        return {
            "end_time": end_time,
            "method": method,
            "threshold_end_time": threshold_end,
            "plateau_end_time": plateau_end,
            "plateau_method": plateau_method,
            "step_plateau_end_time": step_end,
            "step_plateau_method": step_method,
            "peak_time": Time[peak_idx] if peak_idx is not None and 0 <= peak_idx < len(Time) else np.nan,
            "ip_max_ref_A": ip_max_ref,
        }

    return end_time

def find_signal_end_time(
    Time,
    signal_data,
    start_time,
    threshold_ratio=0.04,
    smooth_us=10,
    min_active_us=HALPHA_END_MIN_ACTIVE_US,
    end_gap_us=HALPHA_END_GAP_US,
    max_search_ms=HALPHA_END_MAX_SEARCH_MS
):
    """
    Robust H-alpha plasma-end detector.

    Previous versions used the last H-alpha point above threshold after Ip start.
    That made the plasma duration too long when a later isolated H-alpha spike
    appeared after the actual discharge. This version detects the first sustained
    H-alpha burst after Ip start and ends the plasma when the signal has stayed
    below threshold for a continuous gap.

    Returned end time is therefore the end of the first H-alpha emission burst,
    not the last late spike in the record.
    """
    Time = np.asarray(Time)
    signal_data = np.asarray(signal_data)

    if len(Time) < 2 or len(signal_data) < 2:
        return Time[-1] if len(Time) > 0 else 0.0, "invalid_signal"

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return Time[-1], "invalid_dt"

    # Work only in a physical window after Ip start. This prevents unrelated
    # late H-alpha peaks from extending the plasma duration.
    search_end_time = start_time + max_search_ms * 1e-3
    search_mask = (Time >= start_time) & (Time <= search_end_time)
    if np.sum(search_mask) < 2:
        search_mask = Time >= start_time

    sig_smooth = smooth_signal_time(Time, signal_data, window_us=smooth_us)

    # Estimate and remove local pre-plasma baseline if available.
    baseline_mask = (Time >= start_time - 0.6e-3) & (Time <= start_time - 0.05e-3)
    if np.sum(baseline_mask) >= 5:
        baseline = float(np.median(sig_smooth[baseline_mask]))
    else:
        baseline = float(np.median(sig_smooth[:min(200, len(sig_smooth))]))

    sig_pos = positive_part(sig_smooth - baseline)
    sig_search = sig_pos[search_mask]
    if sig_search.size < 2 or np.nanmax(sig_search) <= 0:
        return Time[-1], "no_positive_signal"

    # Use a robust high percentile instead of the absolute maximum, because the
    # maximum can be an isolated late spike.
    amp_ref = float(np.nanpercentile(sig_search, 95))
    if amp_ref <= 0:
        amp_ref = float(np.nanmax(sig_search))
    if amp_ref <= 0:
        return Time[-1], "no_positive_signal"

    threshold = threshold_ratio * amp_ref
    above = sig_pos > threshold
    search_indices = np.where(search_mask)[0]
    if len(search_indices) == 0:
        return Time[-1], "no_search_indices"

    min_active_samples = max(int(np.ceil((min_active_us * 1e-6) / dt)), 1)
    gap_samples = max(int(np.ceil((end_gap_us * 1e-6) / dt)), 1)

    # Find the first sustained active region after Ip start.
    active_start = None
    for idx in search_indices:
        if idx + min_active_samples <= len(above) and np.all(above[idx:idx + min_active_samples]):
            active_start = idx
            break

    if active_start is None:
        return Time[-1], "no_sustained_crossing"

    last_above = active_start
    below_run = 0
    for idx in range(active_start, search_indices[-1] + 1):
        if above[idx]:
            last_above = idx
            below_run = 0
        else:
            below_run += 1
            if below_run >= gap_samples:
                return Time[last_above], "Halpha_first_burst"

    return Time[last_above], "Halpha_first_burst"

def get_plasma_end_time_from_halpha(
    Time,
    Halpha,
    Ip,
    start_time,
    threshold_ratio=HALPHA_END_THRESHOLD_RATIO,
    smooth_us=HALPHA_END_SMOOTH_US
):
    """
    H-alpha end detector.

    This no longer defines the plasma end used for tau. It is kept as a
    separate optical-emission end time so H-alpha can be integrated over
    its own emission window.
    """
    t_end_halpha, method = find_signal_end_time(
        Time,
        Halpha,
        start_time=start_time,
        threshold_ratio=threshold_ratio,
        smooth_us=smooth_us
    )

    if str(method).startswith("Halpha") and t_end_halpha > start_time:
        return t_end_halpha, method

    t_end_ip = get_plasma_end_time(
        Time,
        Ip,
        start_time=start_time,
        threshold_ratio=IP_END_THRESHOLD_RATIO
    )

    return t_end_ip, "Ip_fallback"

def get_tau(Time, start_time, end_time):
    Time = np.asarray(Time)
    duration = end_time - start_time
    if duration <= 0: duration = Time[-1] - Time[0]
    if duration <= 0: return np.zeros_like(Time), 0.0
    return (Time - start_time) / duration, duration

def get_tau_active_and_ip(Time, Ip, start_time=None, end_time=None):
    """
    Returns tau and active Ip.

    If start_time/end_time are provided, it uses them directly.
    This is important because the final plasma end is now defined from H-alpha.
    If not provided, it falls back to Ip-based start/end for backward compatibility.
    """
    Time = np.asarray(Time)
    Ip = np.asarray(Ip)

    if start_time is None:
        start_time = get_first_ip_start(Time, Ip)

    if end_time is None:
        end_time = get_plasma_end_time(Time, Ip, start_time)

    tau, plasma_duration = get_tau(Time, start_time, end_time)
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

def get_ip_normalization_factor(tau_active, Ip_active, mode, time_active=None):
    """
    Normalization factor for display normalizations.

    tau_max:
        representative maximum of Ip over the active region.

    tau_area:
        The visual normalization is now performed in normalized time tau:

            Ip_norm(tau) = Ip_+(tau) / integral_0^1 Ip_+(tau) d tau

        Therefore:

            integral_0^1 Ip_norm(tau) d tau = 1

        This is what makes all shots have the same area in the Ip panel when
        using the tau / integral(Ip) normalization.

        For spectroscopy, the equivalent physical factor is:
            Delta t_plasma * integral_0^1 Ip_+(tau)d tau
        which is equal to:
            integral Ip_+(t)dt
    """
    tau_active = np.asarray(tau_active)
    Ip_active = np.asarray(Ip_active)

    if len(tau_active) < 2 or len(Ip_active) < 2:
        return 1.0

    if mode == NORMALIZATION_TAU_MAX:
        factor = representative_max(tau_active, Ip_active, smooth_us=0)
        if factor > 0:
            return factor
        abs_max = np.max(np.abs(Ip_active))
        return abs_max if abs_max > 0 else 1.0

    if mode == NORMALIZATION_TAU_AREA:
        return get_ip_tau_area_factor(tau_active, Ip_active)

    return 1.0

def get_normalized_temporal_signal(
    Time,
    signal_data,
    Ip,
    mode,
    signal_kind="generic",
    display_mode=DISPLAY_SYNC,
    sync_time=0.0,
    force_tau=False,
    start_time=None,
    end_time=None
):
    Time = np.asarray(Time)
    signal_data = np.asarray(signal_data)
    Ip = np.asarray(Ip)

    x_raw = Time * 1000 if display_mode == DISPLAY_RAW else (Time - sync_time) * 1000

    if mode == NORMALIZATION_NONE:
        return x_raw, signal_data

    tau, _, active_mask, tau_active, Ip_active = get_tau_active_and_ip(
        Time,
        Ip,
        start_time=start_time,
        end_time=end_time
    )

    y_active = signal_data[active_mask]
    time_active = Time[active_mask]

    if len(tau_active) < 2:
        return x_raw, signal_data

    x = tau_active if force_tau else x_raw[active_mask]

    if mode == NORMALIZATION_TAU:
        return x, y_active

    if mode == NORMALIZATION_TAU_MAX and signal_kind in ["ip", "halpha"]:
        factor = get_ip_normalization_factor(
            tau_active,
            Ip_active,
            mode,
            time_active=time_active
        )
        return x, safe_divide(y_active, factor)

    if mode == NORMALIZATION_TAU_AREA:
        # Ip is forced positive for the physical-time integral normalization.
        # H-alpha is kept as measured, but divided by the same ∫Ip_+(t)dt factor.
        y_to_normalize = positive_part(y_active) if signal_kind == "ip" else y_active

        factor = get_ip_normalization_factor(
            tau_active,
            Ip_active,
            mode,
            time_active=time_active
        )

        return x, safe_divide(y_to_normalize, factor)

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
              NORMALIZATION_TAU_MAX: "τ + division by Ip representative maximum", NORMALIZATION_TAU_AREA: "tau + division by int(Ip_+(tau)dtau)"}
    return labels.get(mode, "No normalization")

# --- Export/Analysis Functions (From v10) ---
def get_halpha_start_5pct_time(
    Time,
    Halpha,
    ip_start,
    halpha_end,
    threshold_ratio=0.05,
    smooth_us=HALPHA_END_SMOOTH_US,
    min_active_us=HALPHA_END_MIN_ACTIVE_US
):
    """
    Detect the H-alpha emission start as the first sustained crossing of
    threshold_ratio * Halpha_ref after Ip start.

    Halpha_ref is computed from the positive, baseline-corrected H-alpha signal
    in the interval [Ip_start, Halpha_end]. This intentionally ignores possible
    pre-plasma sparks before Ip start.
    """
    Time = np.asarray(Time)
    Halpha = np.asarray(Halpha)

    if len(Time) < 2 or len(Halpha) < 2:
        return np.nan, np.nan, "Halpha_start_invalid_signal"

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return np.nan, np.nan, "Halpha_start_invalid_dt"

    if halpha_end is None or not np.isfinite(halpha_end) or halpha_end <= ip_start:
        halpha_end = Time[-1]

    H_smooth = smooth_signal_time(Time, Halpha, window_us=smooth_us)

    # Local pre-plasma baseline. Same spirit as the H-alpha end detector.
    baseline_mask = (Time >= ip_start - 0.6e-3) & (Time <= ip_start - 0.05e-3)
    if np.sum(baseline_mask) >= 5:
        baseline = float(np.nanmedian(H_smooth[baseline_mask]))
    else:
        baseline = float(np.nanmedian(H_smooth[:min(200, len(H_smooth))]))

    H_pos = positive_part(H_smooth - baseline)

    search_mask = (Time >= ip_start) & (Time <= halpha_end)
    if np.sum(search_mask) < 2:
        search_mask = Time >= ip_start

    H_search = H_pos[search_mask]
    if H_search.size < 2 or np.nanmax(H_search) <= 0:
        return np.nan, np.nan, "Halpha_start_no_positive_signal"

    # Use the maximum within the valid H-alpha window for the requested 5%.
    h_ref = float(np.nanmax(H_search))
    threshold = threshold_ratio * h_ref

    above = H_pos > threshold
    min_samples = max(int(np.ceil((min_active_us * 1e-6) / dt)), 1)
    search_indices = np.where(search_mask)[0]

    for idx in search_indices:
        if idx + min_samples <= len(above) and np.all(above[idx:idx + min_samples]):
            return Time[idx], threshold, "Halpha_start_5pct_after_Ip_start"

    return np.nan, threshold, "Halpha_start_5pct_not_found"

def compute_halpha_integral_metrics(data):
    """
    Computes H-alpha and Ip integrals over three windows:

    1) Plasma window:
        Ip_start_time -> Ip_end_time

    2) Old H-alpha window:
        Ip_start_time -> Halpha_end_time
       This is kept for backward compatibility.

    3) Real H-alpha window:
        Halpha_start_5pct_time -> Halpha_end_time

       This is the preferred window when the goal is to measure the optical
       H-alpha emission itself, because it does not count the time between
       Ip_start and the actual rise of H-alpha.
    """
    Time, Ip, Halpha = data['Time'], data['Ip'], data['Photod']
    ip_start = data['Ip_start_time']
    plasma_end = data['Ip_end_time']
    halpha_end = data.get('Halpha_end_time', plasma_end)

    halpha_start_5pct, halpha_start_5pct_threshold, halpha_start_5pct_method = get_halpha_start_5pct_time(
        Time,
        Halpha,
        ip_start,
        halpha_end,
        threshold_ratio=0.05,
        smooth_us=HALPHA_END_SMOOTH_US,
        min_active_us=HALPHA_END_MIN_ACTIVE_US
    )

    plasma_duration = max(plasma_end - ip_start, 0.0)
    halpha_duration = max(halpha_end - ip_start, 0.0)
    halpha_real_duration = (
        max(halpha_end - halpha_start_5pct, 0.0)
        if np.isfinite(halpha_start_5pct)
        else np.nan
    )
    halpha_start_delay_from_Ip = (
        halpha_start_5pct - ip_start
        if np.isfinite(halpha_start_5pct)
        else np.nan
    )

    if plasma_duration <= 0 and halpha_duration <= 0:
        return None

    def window_integrals(t_start, t_end):
        """
        Compute integrals in an arbitrary time window.

        This helper is intentionally start/end agnostic so it can be used for:
          - plasma window: Ip_start -> Ip_end
          - old H-alpha window: Ip_start -> Halpha_end
          - real H-alpha window: Halpha_start_5pct -> Halpha_end
        """
        if t_start is None or t_end is None:
            return None
        if not np.isfinite(t_start) or not np.isfinite(t_end) or t_end <= t_start:
            return None

        mask = (Time >= t_start) & (Time <= t_end)
        if np.sum(mask) < 2:
            return None

        t = Time[mask]
        ip_a = Ip[mask]
        ha_a = Halpha[mask]
        tau_a, duration = get_tau(t, t_start, t_end)

        ip_pos = positive_part(ip_a)
        ha_pos = positive_part(ha_a)

        ip_int_t = trapz_compat(ip_pos, t)
        ha_int_t_pos = trapz_compat(ha_pos, t)
        ha_int_t_raw = trapz_compat(ha_a, t)
        ip_int_tau = trapz_compat(ip_pos, tau_a)
        ha_int_tau_pos = trapz_compat(ha_pos, tau_a)

        return {
            't': t,
            'ip': ip_a,
            'ha': ha_a,
            'ip_pos': ip_pos,
            'ha_pos': ha_pos,
            'duration_s': duration,
            'ip_integral_time_positive_C': ip_int_t,
            'Halpha_integral_time_positive': ha_int_t_pos,
            'Halpha_integral_time_raw': ha_int_t_raw,
            'Ip_integral_tau_positive_A': ip_int_tau,
            'Halpha_integral_tau_positive': ha_int_tau_pos,
            'Halpha_mean_over_window': safe_divide(ha_int_t_pos, duration),
            'Halpha_over_Ip_time': ha_int_t_pos / ip_int_t if ip_int_t > 0 else np.nan,
            'Halpha_over_Ip_tau': ha_int_tau_pos / ip_int_tau if ip_int_tau > 0 else np.nan,
            'Halpha_max': np.max(ha_a) if len(ha_a) else np.nan,
            'Ip_max_rep_kA': representative_max(t, ip_a) / 1000 if len(t) > 1 else np.nan,
            'Ip_max_kA': np.max(ip_a) / 1000 if len(ip_a) else np.nan,
        }

    plasma = window_integrals(ip_start, plasma_end)
    halpha_window = window_integrals(ip_start, halpha_end)
    halpha_real_window = window_integrals(halpha_start_5pct, halpha_end)

    if plasma is None and halpha_window is None and halpha_real_window is None:
        return None

    # Use empty dictionaries so keys below remain defined even if one window fails.
    plasma = plasma or {}
    halpha_window = halpha_window or {}
    halpha_real_window = halpha_real_window or {}

    ip_integral_plasma = plasma.get('ip_integral_time_positive_C', np.nan)
    ip_integral_real_halpha = halpha_real_window.get('ip_integral_time_positive_C', np.nan)
    halpha_real_integral = halpha_real_window.get('Halpha_integral_time_positive', np.nan)
    halpha_real_mean = safe_divide(halpha_real_integral, halpha_real_duration)

    return {
        'shot': data['shot_number'],
        'Ip_start_ms': ip_start * 1000,
        'Ip_end_ms_plasma': plasma_end * 1000,
        'Halpha_end_ms': halpha_end * 1000,
        'Halpha_start_5pct_ms': halpha_start_5pct * 1000 if np.isfinite(halpha_start_5pct) else np.nan,
        'Halpha_start_5pct_threshold': halpha_start_5pct_threshold,
        'Halpha_real_duration_ms_5pct_to_end': halpha_real_duration * 1000 if np.isfinite(halpha_real_duration) else np.nan,
        'Halpha_start_delay_from_Ip_ms': halpha_start_delay_from_Ip * 1000 if np.isfinite(halpha_start_delay_from_Ip) else np.nan,
        'plasma_duration_ms_Ip': plasma_duration * 1000,
        'Halpha_duration_ms': halpha_duration * 1000,
        'plasma_end_method': data.get('plasma_end_method', ''),
        'Halpha_end_method': data.get('Halpha_end_method', ''),
        'Halpha_start_5pct_method': halpha_start_5pct_method,

        # Window 1: Ip start -> plasma end from Ip.
        'Halpha_integral_plasma_time_positive': plasma.get('Halpha_integral_time_positive', np.nan),
        'Halpha_integral_plasma_time_raw': plasma.get('Halpha_integral_time_raw', np.nan),
        'Halpha_mean_over_plasma_duration': safe_divide(plasma.get('Halpha_integral_time_positive', np.nan), plasma_duration),
        'Ip_integral_plasma_time_positive_C': ip_integral_plasma,
        'Halpha_plasma_time_over_Ip_time': plasma.get('Halpha_over_Ip_time', np.nan),
        'Halpha_integral_plasma_tau_positive': plasma.get('Halpha_integral_tau_positive', np.nan),
        'Ip_integral_plasma_tau_positive_A': plasma.get('Ip_integral_tau_positive_A', np.nan),
        'Halpha_plasma_tau_over_Ip_tau': plasma.get('Halpha_over_Ip_tau', np.nan),
        'Halpha_max_plasma_window': plasma.get('Halpha_max', np.nan),

        # Window 2: Ip start -> H-alpha end.
        # Kept for comparison with previous versions.
        'Halpha_integral_halpha_time_positive': halpha_window.get('Halpha_integral_time_positive', np.nan),
        'Halpha_integral_halpha_time_raw': halpha_window.get('Halpha_integral_time_raw', np.nan),
        'Halpha_mean_over_Halpha_duration': safe_divide(halpha_window.get('Halpha_integral_time_positive', np.nan), halpha_duration),
        'Ip_integral_halpha_time_positive_C': halpha_window.get('ip_integral_time_positive_C', np.nan),
        'Halpha_halpha_time_over_Ip_time': halpha_window.get('Halpha_over_Ip_time', np.nan),
        'Halpha_integral_halpha_tau_positive': halpha_window.get('Halpha_integral_tau_positive', np.nan),
        'Ip_integral_halpha_tau_positive_A': halpha_window.get('Ip_integral_tau_positive_A', np.nan),
        'Halpha_halpha_tau_over_Ip_tau': halpha_window.get('Halpha_over_Ip_tau', np.nan),
        'Halpha_max_halpha_window': halpha_window.get('Halpha_max', np.nan),

        # Window 3: H-alpha start at 5% -> H-alpha end.
        # These are the new preferred metrics for the optical emission itself.
        'Halpha_integral_real_time_positive': halpha_real_integral,
        'Halpha_integral_real_time_raw': halpha_real_window.get('Halpha_integral_time_raw', np.nan),
        'Halpha_mean_over_real_Halpha_duration': halpha_real_mean,
        'Ip_integral_real_Halpha_time_positive_C': ip_integral_real_halpha,
        'Halpha_real_time_over_Ip_real_time': (
            halpha_real_integral / ip_integral_real_halpha
            if ip_integral_real_halpha is not None and ip_integral_real_halpha > 0
            else np.nan
        ),
        'Halpha_real_time_over_Ip_plasma_time': (
            halpha_real_integral / ip_integral_plasma
            if ip_integral_plasma is not None and ip_integral_plasma > 0
            else np.nan
        ),
        'Halpha_mean_real_over_Ip_plasma_time': (
            halpha_real_mean / ip_integral_plasma
            if ip_integral_plasma is not None and ip_integral_plasma > 0
            else np.nan
        ),
        'Halpha_integral_real_tau_positive': halpha_real_window.get('Halpha_integral_tau_positive', np.nan),
        'Ip_integral_real_Halpha_tau_positive_A': halpha_real_window.get('Ip_integral_tau_positive_A', np.nan),
        'Halpha_real_tau_over_Ip_real_tau': halpha_real_window.get('Halpha_over_Ip_tau', np.nan),
        'Halpha_max_real_Halpha_window': halpha_real_window.get('Halpha_max', np.nan),

        # Backward-compatible aliases: keep old column names as the plasma-window values.
        'Halpha_integral_time_positive': plasma.get('Halpha_integral_time_positive', np.nan),
        'Halpha_integral_time_raw': plasma.get('Halpha_integral_time_raw', np.nan),
        'Ip_integral_time_positive_C': plasma.get('ip_integral_time_positive_C', np.nan),
        'Halpha_time_over_Ip_time': plasma.get('Halpha_over_Ip_time', np.nan),
        'Halpha_integral_tau_positive': plasma.get('Halpha_integral_tau_positive', np.nan),
        'Ip_integral_tau_positive_A': plasma.get('Ip_integral_tau_positive_A', np.nan),
        'Halpha_tau_over_Ip_tau': plasma.get('Halpha_over_Ip_tau', np.nan),
        'Halpha_max_active': plasma.get('Halpha_max', np.nan),
        'Ip_max_rep_active_kA': plasma.get('Ip_max_rep_kA', np.nan),
        'Ip_max_active_kA': plasma.get('Ip_max_kA', np.nan),
    }


def compute_halpha_real_window_table(data):
    """
    Compact table focused on the new real H-alpha integration window:
        Halpha_start_5pct -> Halpha_end

    It reuses compute_halpha_integral_metrics so the values remain consistent
    with the full H-alpha integral table.
    """
    m = compute_halpha_integral_metrics(data)
    if m is None:
        return None

    return {
        'shot': m.get('shot', ''),
        'Halpha_start_5pct_ms': m.get('Halpha_start_5pct_ms', np.nan),
        'Halpha_end_ms': m.get('Halpha_end_ms', np.nan),
        'Halpha_real_duration_ms_5pct_to_end': m.get('Halpha_real_duration_ms_5pct_to_end', np.nan),
        'Halpha_start_delay_from_Ip_ms': m.get('Halpha_start_delay_from_Ip_ms', np.nan),
        'Halpha_integral_real_time_positive': m.get('Halpha_integral_real_time_positive', np.nan),
        'Halpha_integral_real_time_raw': m.get('Halpha_integral_real_time_raw', np.nan),
        'Halpha_mean_over_real_Halpha_duration': m.get('Halpha_mean_over_real_Halpha_duration', np.nan),
        'Halpha_max_real_Halpha_window': m.get('Halpha_max_real_Halpha_window', np.nan),
        'Ip_integral_plasma_time_positive_C': m.get('Ip_integral_plasma_time_positive_C', np.nan),
        'Ip_integral_real_Halpha_time_positive_C': m.get('Ip_integral_real_Halpha_time_positive_C', np.nan),
        'Halpha_real_time_over_Ip_plasma_time': m.get('Halpha_real_time_over_Ip_plasma_time', np.nan),
        'Halpha_real_time_over_Ip_real_time': m.get('Halpha_real_time_over_Ip_real_time', np.nan),
        'Halpha_mean_real_over_Ip_plasma_time': m.get('Halpha_mean_real_over_Ip_plasma_time', np.nan),
        'Halpha_integral_real_tau_positive': m.get('Halpha_integral_real_tau_positive', np.nan),
        'Ip_integral_real_Halpha_tau_positive_A': m.get('Ip_integral_real_Halpha_tau_positive_A', np.nan),
        'Halpha_real_tau_over_Ip_real_tau': m.get('Halpha_real_tau_over_Ip_real_tau', np.nan),
        'Halpha_start_5pct_threshold': m.get('Halpha_start_5pct_threshold', np.nan),
        'Halpha_start_5pct_method': m.get('Halpha_start_5pct_method', ''),
        'Halpha_end_method': m.get('Halpha_end_method', ''),
    }

def compute_timing_delay_metrics(data):
    halpha_end = data.get('Halpha_end_time', data['Ip_end_time'])
    return {
        'shot': data['shot_number'],
        'Bt_start_ms': data['Bt_sync_time'] * 1000,
        'Ip_start_ms': data['Ip_start_time'] * 1000,
        'Ip_start_method': data.get('Ip_start_method', ''),
        'Ip_start_threshold_ms': data.get('Ip_start_threshold_time', np.nan) * 1000,
        'Ip_start_peak_ms': data.get('Ip_start_peak_time', np.nan) * 1000,
        'Ip_start_threshold_A': data.get('Ip_start_threshold_A', np.nan),
        'Ip_start_ip_max_ref_A': data.get('Ip_start_ip_max_ref_A', np.nan),
        'Plasma_end_ms_Ip': data['Ip_end_time'] * 1000,
        'Halpha_end_ms': halpha_end * 1000,
        'Ip_delay_from_Bt_ms': (data['Ip_start_time'] - data['Bt_sync_time']) * 1000,
        'plasma_duration_ms_Ip': (data['Ip_end_time'] - data['Ip_start_time']) * 1000,
        'Halpha_duration_ms': (halpha_end - data['Ip_start_time']) * 1000,
        'plasma_end_method': data.get('plasma_end_method', ''),
        'Halpha_end_method': data.get('Halpha_end_method', '')
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
    shot_summary_rows, halpha_rows, halpha_real_rows, timing_rows, global_rows, covariance_rows = [], [], [], [], [], []
    for data in processed_data:
        halpha = compute_halpha_integral_metrics(data)
        if halpha is not None:
            halpha_rows.append(halpha)
            real_halpha = compute_halpha_real_window_table(data)
            if real_halpha is not None:
                halpha_real_rows.append(real_halpha)
        global_metrics = compute_single_shot_global_metrics(data)
        timing_rows.append(compute_timing_delay_metrics(data))
        global_rows.append(global_metrics)
        covariance_rows.append({'shot': data['shot_number'], 'cov_Ip_Halpha': global_metrics['cov_Ip_Halpha'], 'corr_Ip_Halpha': global_metrics['corr_Ip_Halpha'], 'cov_Bt_Ip': global_metrics['cov_Bt_Ip'], 'corr_Bt_Ip': global_metrics['corr_Bt_Ip']})
        shot_summary_rows.append({'shot': data['shot_number'], 'file_path': data.get('file_path', ''), 'Bt_start_ms': data['Bt_sync_time'] * 1000, 'Ip_start_ms': data['Ip_start_time'] * 1000, 'Ip_start_method': data.get('Ip_start_method', ''), 'Ip_start_threshold_ms': data.get('Ip_start_threshold_time', np.nan) * 1000, 'Ip_start_peak_ms': data.get('Ip_start_peak_time', np.nan) * 1000, 'Ip_start_threshold_A': data.get('Ip_start_threshold_A', np.nan), 'Ip_start_ip_max_ref_A': data.get('Ip_start_ip_max_ref_A', np.nan), 'Ip_end_ms': data['Ip_end_time'] * 1000, 'Halpha_end_ms': data.get('Halpha_end_time', data['Ip_end_time']) * 1000, 'Ip_delay_from_Bt_ms': data['Ip_delay_ms'], 'plasma_duration_ms': data['plasma_duration_sec'] * 1000, 'Halpha_duration_ms': data.get('halpha_duration_sec', max(data.get('Halpha_end_time', data['Ip_end_time']) - data['Ip_start_time'], 0.0)) * 1000, 'Ip_max_kA': data['I_p_max_kA'], 'Ip_max_rep_kA': data['I_p_max_rep_kA'], 'Bt_max_mT': data['B_phi_max_mT'], 'Ip_baseline_A': data['Ip_baseline_A'], 'Ip_baseline_method': data['Ip_baseline_method'], 'pressure_group_from_folder': data.get('pressure_group', ''), 'plasma_end_method': data.get('plasma_end_method', ''), 'Halpha_end_method': data.get('Halpha_end_method', ''), 'Ip_threshold_end_ms': data.get('Ip_threshold_end_time', np.nan) * 1000, 'Ip_plateau_end_ms': data.get('Ip_plateau_end_time', np.nan) * 1000 if data.get('Ip_plateau_end_time', None) is not None else np.nan, 'Ip_peak_time_ms': data.get('Ip_peak_time', np.nan) * 1000, 'Ip_plateau_method': data.get('Ip_plateau_method', ''), 'Ip_step_plateau_end_ms': data.get('Ip_step_plateau_end_time', np.nan) * 1000 if data.get('Ip_step_plateau_end_time', None) is not None else np.nan, 'Ip_step_plateau_method': data.get('Ip_step_plateau_method', '')})
    
    tables = {
        'shot_summary': pd.DataFrame(shot_summary_rows), 'halpha_integrals': pd.DataFrame(halpha_rows),
        'halpha_real_window_integrals': pd.DataFrame(halpha_real_rows),
        'timing_delays': pd.DataFrame(timing_rows), 'global_metrics': pd.DataFrame(global_rows),
        'covariance_correlation': pd.DataFrame(covariance_rows),
        'method_parameters': pd.DataFrame([{
            'BT_START_THRESHOLD_RATIO': BT_START_THRESHOLD_RATIO,
            'IP_START_THRESHOLD_RATIO': IP_START_THRESHOLD_RATIO,
            'IP_START_BACKWARD_FROM_PEAK_SMOOTH_US': IP_START_BACKWARD_FROM_PEAK_SMOOTH_US,
            'IP_END_THRESHOLD_RATIO': IP_END_THRESHOLD_RATIO,
            'IP_END_AFTER_MAX_SMOOTH_US': IP_END_AFTER_MAX_SMOOTH_US,
            'IP_END_AFTER_MAX_GAP_US': IP_END_AFTER_MAX_GAP_US,

            'IP_PLATEAU_DETECTION_ENABLED': IP_PLATEAU_DETECTION_ENABLED,
            'IP_PLATEAU_MAX_CURRENT_RATIO': IP_PLATEAU_MAX_CURRENT_RATIO,
            'IP_PLATEAU_FIXED_SLOPE_LIMIT_KA_PER_MS': IP_PLATEAU_FIXED_SLOPE_LIMIT_KA_PER_MS,
            'IP_PLATEAU_MIN_DURATION_US': IP_PLATEAU_MIN_DURATION_US,
            'IP_PLATEAU_MIN_AFTER_PEAK_US': IP_PLATEAU_MIN_AFTER_PEAK_US,

            'IP_STEP_PLATEAU_DETECTION_ENABLED': IP_STEP_PLATEAU_DETECTION_ENABLED,
            'IP_STEP_PLATEAU_DROP_RATIO': IP_STEP_PLATEAU_DROP_RATIO,
            'IP_STEP_PLATEAU_POST_ABSOLUTE_SLOPE_KA_PER_MS': IP_STEP_PLATEAU_POST_ABSOLUTE_SLOPE_KA_PER_MS,

            'IP_MIN_DURATION_US': IP_MIN_DURATION_US,
            'IP_REPRESENTATIVE_SMOOTH_US': IP_REPRESENTATIVE_SMOOTH_US,
            'IP_BASELINE_PRE_START_US': IP_BASELINE_PRE_START_US,
            'IP_BASELINE_PRE_END_US': IP_BASELINE_PRE_END_US,
            'HALPHA_COMPARISON_SMOOTH_US': HALPHA_COMPARISON_SMOOTH_US,
            'IP_COMPARISON_SMOOTH_US': IP_COMPARISON_SMOOTH_US,
            'SPECTRUM_TAU_AREA_UNIT': 'S_raw divided by plasma duration and integral Ip_+(tau)d tau',
            'HALPHA_END_THRESHOLD_RATIO': HALPHA_END_THRESHOLD_RATIO,
            'HALPHA_END_SMOOTH_US': HALPHA_END_SMOOTH_US,
            'HALPHA_END_MIN_ACTIVE_US': HALPHA_END_MIN_ACTIVE_US,
            'HALPHA_END_GAP_US': HALPHA_END_GAP_US,
            'HALPHA_END_MAX_SEARCH_MS': HALPHA_END_MAX_SEARCH_MS,
            'PLASMA_END_DETECTOR': (
                'Ip low-current fixed-slope plateau after Ip,max, '
                'else Ip after-maximum threshold; Halpha end stored separately'
            )
        }])
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

            ip_start_info = get_ip_start_backward_from_peak_info(
                Time,
                Ip,
                threshold_ratio=IP_START_THRESHOLD_RATIO,
                min_duration_us=IP_MIN_DURATION_US
            )
            t0_ip = ip_start_info['start_time']
            ip_start_method = ip_start_info.get('method', '')

            # Plasma end is now defined from Ip. Priority:
            #   1) start of a sustained low-slope Ip plateau after Ip,max,
            #   2) fallback threshold after Ip,max.
            ip_end_info = get_plasma_end_time(
                Time,
                Ip,
                start_time=t0_ip,
                threshold_ratio=IP_END_THRESHOLD_RATIO,
                smooth_us=IP_END_AFTER_MAX_SMOOTH_US,
                gap_us=IP_END_AFTER_MAX_GAP_US,
                return_details=True
            )
            t_end_ip = ip_end_info['end_time']
            plasma_end_method = ip_end_info['method']

            # H-alpha end is still computed and stored separately. It is used
            # for H-alpha-specific integrals, but NOT for tau/plasma duration.
            t_end_halpha, halpha_end_method = get_plasma_end_time_from_halpha(
                Time,
                Photod,
                Ip,
                start_time=t0_ip
            )

            ip_crossings = find_ip_start_times(Time, Ip, IP_START_THRESHOLD_RATIO, IP_MIN_DURATION_US)

            Time_sync_bt, Time_sync_ip = Time - t0_bt, Time - t0_ip
            tau_plasma, plasma_duration_tau = get_tau(Time, t0_ip, t_end_ip)
            plasma_duration_sec = max(t_end_ip - t0_ip, 0.0)
            halpha_duration_sec = max(t_end_halpha - t0_ip, 0.0)
            ip_delay_ms = (t0_ip - t0_bt) * 1000

            I_p_max_kA = np.max(Ip) / 1000.0
            I_p_max_rep_kA = representative_max(Time, Ip, smooth_us=IP_REPRESENTATIVE_SMOOTH_US) / 1000.0
            B_phi_max = np.max(B_phi)

            wavelengths_Avantes = np.array([])
            intensities_Avantes_raw = np.array([])
            intensities_Avantes_rw = np.array([])
            intensities_Avantes = np.array([])
            Avantes_intensity_source = ""

            if 'spectroscopy' in f and 'Avantes' in f['spectroscopy']:
                try:
                    av_group = f['spectroscopy']['Avantes']
                    wl_raw = av_group['Wavelength'][:] if 'Wavelength' in av_group else np.array([])

                    # Display/backward-compatible spectrum: keep CleanI when available.
                    i_clean, clean_key = read_first_existing_dataset(
                        av_group,
                        ("CleanI", "cleanI", "clean_i", "rw", "RW")
                    )

                    # Matched-line spectroscopy table: prefer RW, then fallback to CleanI.
                    i_rw, rw_key = read_first_existing_dataset(
                        av_group,
                        AVANTES_RW_DATASET_CANDIDATES
                    )

                    if i_rw.size == 0:
                        i_rw = i_clean
                        rw_key = clean_key

                    if wl_raw.size > 0 and i_clean.size > 0 and wl_raw.shape == i_clean.shape:
                        intensities_Avantes_raw = i_clean
                        max_int = np.nanmax(i_clean)
                        intensities_Avantes = i_clean / max_int if max_int > 0 else np.zeros_like(i_clean)
                        wavelengths_Avantes = wl_raw

                    if wl_raw.size > 0 and i_rw.size > 0 and wl_raw.shape == i_rw.shape:
                        intensities_Avantes_rw = i_rw
                        Avantes_intensity_source = rw_key

                except Exception:
                    pass

            shot_number = os.path.basename(file_path).split('.')[0][:-2]
            pressure_group = os.path.basename(os.path.dirname(file_path))

            main_data_df = pd.DataFrame({'time_ms': Time * 1000, 'time_sync_bt_ms': Time_sync_bt * 1000, 'time_sync_ip_ms': Time_sync_ip * 1000, 'tau_plasma': tau_plasma, 'Bt_mT': B_phi, 'Ip_kA': Ip / 1000, 'H_alpha': Photod})
            spec_data_df = pd.DataFrame({'wavelength_nm': wavelengths_Avantes, 'intensity_raw': intensities_Avantes_raw, 'intensity_rw': intensities_Avantes_rw, 'intensity_norm_max': intensities_Avantes, 'intensity_source': Avantes_intensity_source}) if wavelengths_Avantes.size > 0 else pd.DataFrame()

            if save_to_csv:
                local_folder = f"shot_{shot_number}"
                os.makedirs(local_folder, exist_ok=True)
                main_data_df.to_csv(f"{local_folder}/main_data.csv", index=False)
                if not spec_data_df.empty: spec_data_df.to_csv(f"{local_folder}/spectroscopy.csv", index=False)
                metadata = {'shot_number': shot_number, 'I_p_max_kA': float(I_p_max_kA), 'I_p_max_rep_kA': float(I_p_max_rep_kA), 'B_phi_max_mT': float(B_phi_max), 'plasma_duration_ms': float(plasma_duration_sec * 1000), 'halpha_duration_ms': float(halpha_duration_sec * 1000), 'Bt_sync_time_ms': float(t0_bt * 1000), 'Ip_start_time_ms': float(t0_ip * 1000), 'Ip_start_method': ip_start_method, 'Ip_start_threshold_ms': float(ip_start_info.get('threshold_start_time', np.nan) * 1000), 'Ip_start_peak_ms': float(ip_start_info.get('ip_peak_time', np.nan) * 1000), 'Ip_start_threshold_A': float(ip_start_info.get('ip_start_threshold_A', np.nan)), 'Ip_start_ip_max_ref_A': float(ip_start_info.get('ip_start_ip_max_ref_A', np.nan)), 'Ip_end_time_ms': float(t_end_ip * 1000), 'Halpha_end_time_ms': float(t_end_halpha * 1000), 'Ip_delay_from_Bt_ms': float(ip_delay_ms), 'Ip_min_duration_us': IP_MIN_DURATION_US, 'Ip_baseline_A': float(ip_baseline), 'Ip_baseline_method': ip_baseline_method, 'pressure_group': pressure_group, 'plasma_end_method': plasma_end_method, 'Halpha_end_method': halpha_end_method, 'Ip_threshold_end_ms': float(ip_end_info.get('threshold_end_time', np.nan) * 1000), 'Ip_plateau_end_ms': float(ip_end_info.get('plateau_end_time', np.nan) * 1000) if ip_end_info.get('plateau_end_time', None) is not None else None, 'Ip_peak_time_ms': float(ip_end_info.get('peak_time', np.nan) * 1000), 'Ip_step_plateau_end_ms': float(ip_end_info.get('step_plateau_end_time', np.nan) * 1000) if ip_end_info.get('step_plateau_end_time', None) is not None else None}
                with open(f"{local_folder}/metadata.json", "w") as fjson: json.dump(metadata, fjson)

            return {'file_path': file_path, 'pressure_group': pressure_group, 'Time': Time, 'Time_sync_bt': Time_sync_bt, 'Time_sync_ip': Time_sync_ip, 'tau_plasma': tau_plasma, 'plasma_tau_duration': plasma_duration_tau, 'B_phi': B_phi, 'Ip': Ip, 'Ip_raw_before_baseline': Ip_raw, 'Photod': Photod, 'wavelengths_Avantes': wavelengths_Avantes, 'intensities_Avantes': intensities_Avantes, 'intensities_Avantes_raw': intensities_Avantes_raw, 'intensities_Avantes_rw': intensities_Avantes_rw, 'Avantes_intensity_source': Avantes_intensity_source, 'shot_number': shot_number, 'I_p_max_kA': I_p_max_kA, 'I_p_max_rep_kA': I_p_max_rep_kA, 'B_phi_max_mT': B_phi_max, 'plasma_duration_sec': plasma_duration_sec, 'halpha_duration_sec': halpha_duration_sec, 'Bt_sync_time': t0_bt, 'Ip_start_time': t0_ip, 'Ip_start_method': ip_start_method, 'Ip_start_threshold_time': ip_start_info.get('threshold_start_time', np.nan), 'Ip_start_peak_time': ip_start_info.get('ip_peak_time', np.nan), 'Ip_start_threshold_A': ip_start_info.get('ip_start_threshold_A', np.nan), 'Ip_start_ip_max_ref_A': ip_start_info.get('ip_start_ip_max_ref_A', np.nan), 'Ip_end_time': t_end_ip, 'Halpha_end_time': t_end_halpha, 'Ip_threshold_end_time': ip_end_info.get('threshold_end_time', np.nan), 'Ip_plateau_end_time': ip_end_info.get('plateau_end_time', np.nan), 'Ip_peak_time': ip_end_info.get('peak_time', np.nan), 'Ip_end_ip_max_ref_A': ip_end_info.get('ip_max_ref_A', np.nan), 'Ip_plateau_method': ip_end_info.get('plateau_method', ''), 'Ip_step_plateau_end_time': ip_end_info.get('step_plateau_end_time', np.nan), 'Ip_step_plateau_method': ip_end_info.get('step_plateau_method', ''), 'Halpha_end_method': halpha_end_method, 'plasma_end_method': plasma_end_method, 'Ip_delay_ms': ip_delay_ms, 'Ip_crossings': ip_crossings, 'Ip_min_duration_us': IP_MIN_DURATION_US, 'Ip_baseline_A': ip_baseline, 'Ip_baseline_method': ip_baseline_method, 'main_data_df': main_data_df, 'spec_data_df': spec_data_df}
    except Exception as e:
        messagebox.showerror("Data Load Error", f"Could not load or process file {file_path}:\n{e}")
        return None


# =========================================================
# NIST EMISSION-LINE LOCAL DATABASE HELPERS
# =========================================================
def get_emission_lines_dir():
    """
    Return the local folder that contains NIST ASD line files.

    The code intentionally avoids hard-coded user-specific paths such as
    C:/Users/... so it can be pushed to GitHub and used on another computer.

    Search priority:
      1) Environment variable MEPHIST_EMISSION_LINES_DIR.
      2) Repository root / "Lineas de emisión" when this file is inside src/.
      3) Same folder as this file / "Lineas de emisión".
      4) Current working directory / "Lineas de emisión".
    """
    env_path = os.environ.get("MEPHIST_EMISSION_LINES_DIR", "").strip()
    if env_path:
        return Path(env_path).expanduser()

    module_dir = Path(__file__).resolve().parent
    candidates = [
        module_dir.parent / EMISSION_LINES_FOLDER_NAME,
        module_dir / EMISSION_LINES_FOLDER_NAME,
        Path.cwd() / EMISSION_LINES_FOLDER_NAME,
        Path.cwd().parent / EMISSION_LINES_FOLDER_NAME,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Default for a repository where shot_comparison_tab.py lives in src/.
    return candidates[0]


def clean_nist_cell(value):
    """
    Clean NIST CSV cells.

    NIST CSV output often looks like Excel-safe formulas, for example:
        ="365.51234"
        =""
    This function removes that wrapper and returns a plain string.
    """
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.startswith('="') and text.endswith('"'):
        text = text[2:-1]
    elif text.startswith("='") and text.endswith("'"):
        text = text[2:-1]

    text = text.replace('""', '"').strip()
    return text


def nist_cell_to_float(value):
    """Convert a cleaned NIST cell into a float, returning NaN if impossible."""
    text = clean_nist_cell(value)
    if not text:
        return np.nan

    # Remove brackets used by NIST for some calculated/uncertain values.
    text = text.replace('[', '').replace(']', '')

    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
    if not match:
        return np.nan

    try:
        return float(match.group(0))
    except ValueError:
        return np.nan


def nist_intensity_to_float(value):
    """
    Convert a NIST relative-intensity cell to a float when possible.

    NIST intensity cells can contain strings such as:
        "155000", "34hbl(Fe II)", "1.2e+05", Excel-style formula-wrapped numbers

    The first numeric token is used. Blank/non-numeric values return NaN.
    This value is used only as a relative plausibility weight when multiple
    selected elements match the same experimental wavelength bin.
    """
    text = clean_nist_cell(value)
    if text is None:
        return np.nan
    text = str(text).strip()
    if text == "":
        return np.nan
    text = text.replace('[', '').replace(']', '')
    match = re.search(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text)
    if not match:
        return np.nan
    try:
        return float(match.group(0))
    except ValueError:
        return np.nan


def read_nist_line_file(file_path):
    """
    Read a local NIST ASD CSV/TXT/TSV file and normalize useful columns.

    Returned dataframe always includes:
      - lambda_nm: preferred wavelength used for plotting/matching
      - lambda_source: 'observed_air', 'ritz_air', 'observed', 'ritz', or 'unknown'
      - source_file
      - element_guess
    """
    file_path = Path(file_path)

    # NIST CSV output is comma-separated; TSV/TXT may be tab-separated.
    sep = '\t' if file_path.suffix.lower() in {'.tsv', '.txt'} else ','

    try:
        df = pd.read_csv(file_path, sep=sep, dtype=str, engine='python')
    except Exception:
        # Fallback: try automatic separator inference.
        df = pd.read_csv(file_path, sep=None, dtype=str, engine='python')

    # Normalize column names while keeping original columns available.
    df.columns = [str(c).strip() for c in df.columns]

    # Clean all object cells from Excel-formula wrappers like ="365.51234".
    for col in df.columns:
        df[col] = df[col].map(clean_nist_cell)

    lower_cols = {str(c).lower(): c for c in df.columns}

    wavelength_preferences = [
        ('obs_wl_air(nm)', 'observed_air'),
        ('ritz_wl_air(nm)', 'ritz_air'),
        ('obs_wl_vac(nm)', 'observed_vacuum'),
        ('ritz_wl_vac(nm)', 'ritz_vacuum'),
        ('obs_wl(nm)', 'observed'),
        ('ritz_wl(nm)', 'ritz'),
    ]

    lambda_values = None
    lambda_source = 'unknown'

    # Prefer observed wavelength when available; otherwise use Ritz.
    for key, source in wavelength_preferences:
        if key in lower_cols:
            candidate = df[lower_cols[key]].map(nist_cell_to_float)
            if candidate.notna().any():
                lambda_values = candidate
                lambda_source = source
                break

    if lambda_values is None:
        # Last fallback: find any nm wavelength-like column.
        for col in df.columns:
            col_l = col.lower()
            if 'wl' in col_l and '(nm)' in col_l:
                candidate = df[col].map(nist_cell_to_float)
                if candidate.notna().any():
                    lambda_values = candidate
                    lambda_source = col
                    break

    if lambda_values is None:
        df['lambda_nm'] = np.nan
    else:
        df['lambda_nm'] = lambda_values

    df['lambda_source'] = lambda_source
    df['source_file'] = file_path.name
    df['element_guess'] = guess_element_from_filename(file_path.name)

    return df.dropna(subset=['lambda_nm']).copy()


def guess_element_from_filename(filename):
    """Infer an element/spectrum label from a file name like Fe_I_II_290_1110_nm.csv."""
    stem = Path(filename).stem
    stem = re.sub(r'_?\d+(?:\.\d+)?_\d+(?:\.\d+)?_nm$', '', stem)
    return stem.replace('_', ' ')


def list_local_nist_files():
    """Return a summary dataframe of files available in the emission-lines folder."""
    folder = get_emission_lines_dir()

    if not folder.exists():
        return pd.DataFrame([{
            'available': False,
            'folder': str(folder),
            'file': '',
            'element_guess': '',
            'n_lines': 0,
            'lambda_min_nm': np.nan,
            'lambda_max_nm': np.nan,
            'message': 'Folder not found. Create it and place NIST CSV files there.'
        }])

    files = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in EMISSION_LINE_FILE_EXTENSIONS
    )

    if not files:
        return pd.DataFrame([{
            'available': False,
            'folder': str(folder),
            'file': '',
            'element_guess': '',
            'n_lines': 0,
            'lambda_min_nm': np.nan,
            'lambda_max_nm': np.nan,
            'message': 'No CSV/TXT/TSV line files found in this folder.'
        }])

    rows = []
    for path in files:
        try:
            df = read_nist_line_file(path)
            rows.append({
                'available': True,
                'folder': str(folder),
                'file': path.name,
                'element_guess': guess_element_from_filename(path.name),
                'n_lines': int(len(df)),
                'lambda_min_nm': float(df['lambda_nm'].min()) if len(df) else np.nan,
                'lambda_max_nm': float(df['lambda_nm'].max()) if len(df) else np.nan,
                'wavelength_source': str(df['lambda_source'].iloc[0]) if len(df) else '',
                'message': 'OK'
            })
        except Exception as exc:
            rows.append({
                'available': False,
                'folder': str(folder),
                'file': path.name,
                'element_guess': guess_element_from_filename(path.name),
                'n_lines': 0,
                'lambda_min_nm': np.nan,
                'lambda_max_nm': np.nan,
                'wavelength_source': '',
                'message': f'Could not read file: {exc}'
            })

    return pd.DataFrame(rows)



def get_nist_file_options():
    """Return available NIST files with absolute paths and parsed metadata."""
    folder = get_emission_lines_dir()
    summary = list_local_nist_files()

    if summary.empty or 'available' not in summary.columns:
        return pd.DataFrame()

    rows = []
    for _, row in summary.iterrows():
        if not bool(row.get('available', False)):
            continue

        file_name = str(row.get('file', '')).strip()
        if not file_name:
            continue

        rows.append({
            'element_guess': str(row.get('element_guess', '')).strip(),
            'file': file_name,
            'file_path': str((folder / file_name).resolve()),
            'n_lines': int(row.get('n_lines', 0)) if pd.notna(row.get('n_lines', np.nan)) else 0,
            'lambda_min_nm': row.get('lambda_min_nm', np.nan),
            'lambda_max_nm': row.get('lambda_max_nm', np.nan),
            'wavelength_source': row.get('wavelength_source', ''),
        })

    return pd.DataFrame(rows)


def robust_noise_level(signal_data):
    """Robust noise estimate using MAD."""
    y = np.asarray(signal_data, dtype=float)
    y = y[np.isfinite(y)]
    if y.size == 0:
        return 0.0, 0.0
    median = float(np.nanmedian(y))
    mad = float(np.nanmedian(np.abs(y - median)))
    sigma = 1.4826 * mad
    if not np.isfinite(sigma) or sigma <= 0:
        sigma = float(np.nanstd(y)) if y.size > 1 else 0.0
    return median, sigma


def is_local_peak(wavelengths, intensities, idx, half_width_points=2):
    """Return True if idx is a local maximum in a small neighborhood."""
    n = len(intensities)
    if n == 0 or idx < 0 or idx >= n:
        return False
    i0 = max(0, idx - half_width_points)
    i1 = min(n, idx + half_width_points + 1)
    local = intensities[i0:i1]
    if local.size == 0:
        return False
    return intensities[idx] >= np.nanmax(local)


def match_nist_lines_for_shot(
    wavelengths_exp,
    intensity_exp,
    nist_df,
    element_label,
    shot_number,
    tolerance_nm=NIST_MATCH_TOLERANCE_NM,
    min_relative_peak_height=NIST_MIN_RELATIVE_PEAK_HEIGHT,
    noise_sigma_factor=NIST_NOISE_SIGMA_FACTOR,
    local_background_window_nm=NIST_LOCAL_BACKGROUND_WINDOW_NM,
    min_prominence_relative=NIST_MIN_PROMINENCE_RELATIVE,
):
    """
    Match local NIST lines directly against the experimental wavelength array.

    This version does NOT require an isolated local peak. That is important for
    Avantes spectra where strong lines can be saturated, clipped, or appear as a
    plateau instead of a sharp maximum.

    For each NIST wavelength lambda_0, the code inspects the real experimental
    samples inside:

        |lambda_exp - lambda_0| <= tolerance_nm

    and accepts the line if the local experimental signal is significantly above
    the robust noise/background level.

    Accepted intensity is the maximum experimental normalized RW intensity inside
    the wavelength window. When several selected elements match the same
    experimental wavelength bin, the final table keeps only the most plausible
    candidate using only the NIST relative intensity; wavelength proximity is only a tie-breaker.
    """
    wl = np.asarray(wavelengths_exp, dtype=float)
    y = np.asarray(intensity_exp, dtype=float)

    if wl.size == 0 or y.size == 0 or wl.shape != y.shape or nist_df is None or len(nist_df) == 0:
        return pd.DataFrame()

    finite = np.isfinite(wl) & np.isfinite(y)
    wl = wl[finite]
    y = y[finite]
    if wl.size < 3:
        return pd.DataFrame()

    # Ensure increasing wavelength order.
    order = np.argsort(wl)
    wl = wl[order]
    y = y[order]

    y_max = float(np.nanmax(y))
    if not np.isfinite(y_max) or y_max <= 0:
        return pd.DataFrame()

    # Robust baseline/noise over the full spectrum. This avoids counting small
    # fluctuations as real lines. The user can tune noise_sigma_factor and
    # min_relative_peak_height in the filter panel.
    baseline, noise_sigma = robust_noise_level(y)
    absolute_threshold = max(
        baseline + noise_sigma_factor * noise_sigma,
        min_relative_peak_height * y_max,
    )

    # Local-background criterion. It is weaker than a local-peak requirement:
    # it only asks whether the signal in the NIST window is above the nearby
    # continuum/noise. This keeps plateau/saturated regions detectable.
    min_local_excess = max(
        noise_sigma_factor * noise_sigma,
        min_prominence_relative * y_max,
    )

    rows = []

    # Try to keep optional NIST columns if they exist.
    nist_intensity_col = None
    for candidate in ['intens', 'Intensity', 'Rel.', 'rel_intensity']:
        if candidate in nist_df.columns:
            nist_intensity_col = candidate
            break

    source_file = str(nist_df['source_file'].iloc[0]) if 'source_file' in nist_df.columns and len(nist_df) else ''
    lambda_source = str(nist_df['lambda_source'].iloc[0]) if 'lambda_source' in nist_df.columns and len(nist_df) else ''

    for _, line in nist_df.iterrows():
        lam_nist = float(line.get('lambda_nm', np.nan))
        if not np.isfinite(lam_nist):
            continue

        # Direct wavelength-window search in the experimental arrays.
        window_mask = np.abs(wl - lam_nist) <= tolerance_nm
        if not np.any(window_mask):
            continue

        local_indices = np.where(window_mask)[0]
        local_wl = wl[local_indices]
        local_y = y[local_indices]
        if local_y.size == 0:
            continue

        local_max_pos = int(np.nanargmax(local_y))
        best_idx = int(local_indices[local_max_pos])
        best_wl = float(wl[best_idx])
        best_intensity = float(y[best_idx])
        delta_nm = best_wl - lam_nist

        # Reject noise using global robust threshold + relative threshold.
        if best_intensity < absolute_threshold:
            continue

        rel_height = best_intensity / y_max if y_max > 0 else np.nan
        if rel_height < min_relative_peak_height:
            continue

        # Estimate nearby background from a ring around the NIST line. Exclude
        # the actual matching window to avoid subtracting the line/plateau itself.
        bg_mask = (
            (wl >= lam_nist - local_background_window_nm)
            & (wl <= lam_nist + local_background_window_nm)
            & (np.abs(wl - lam_nist) > tolerance_nm)
        )
        if np.any(bg_mask):
            local_background = float(np.nanmedian(y[bg_mask]))
        else:
            local_background = baseline

        local_excess = best_intensity - local_background
        if local_excess < min_local_excess:
            continue

        # Integrated local signal over the NIST tolerance window after subtracting
        # local background. This is not the ranking column by default, but it is
        # useful when a line appears as a broad plateau rather than a sharp peak.
        local_signal_bg_sub = positive_part(local_y - local_background)
        local_integral = safe_area(local_wl, local_signal_bg_sub)
        local_mean = float(np.nanmean(local_y)) if len(local_y) else np.nan

        nist_intensity = ''
        nist_intensity_numeric = np.nan
        if nist_intensity_col is not None:
            nist_intensity = clean_nist_cell(line.get(nist_intensity_col, ''))
            nist_intensity_numeric = nist_intensity_to_float(nist_intensity)

        rows.append({
            'shot': shot_number,
            'type of element': element_label,
            'wavelength': lam_nist,
            'intensity': best_intensity,
            'experimental_wavelength_nm': best_wl,
            'delta_nm': delta_nm,
            'relative_intensity_in_shot': rel_height,
            'local_background': local_background,
            'local_excess': local_excess,
            'local_mean_intensity': local_mean,
            'local_integrated_intensity': local_integral,
            'nist_relative_intensity': nist_intensity,
            'nist_relative_intensity_numeric': nist_intensity_numeric,
            'source_file': source_file,
            'wavelength_source': lambda_source,
            'matching_method': 'wavelength_window_normalized_rw_intensity_threshold',
        })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)

    # Avoid duplicated rows caused by several NIST lines falling inside one
    # Avantes-resolution bin for the same element. Keep the line with the
    # largest NIST relative intensity only. Wavelength proximity is kept only as
    # a tie-breaker, not as part of the score.
    bin_width = max(tolerance_nm / 2.0, 1e-9)
    out['abs_delta_nm'] = out['delta_nm'].abs()
    out['experimental_peak_bin'] = np.round(out['experimental_wavelength_nm'] / bin_width).astype(int)

    out['nist_intensity_for_score'] = pd.to_numeric(
        out.get('nist_relative_intensity_numeric', np.nan),
        errors='coerce'
    ).fillna(0.0)

    out['candidate_score'] = out['nist_intensity_for_score'].astype(float)

    out = (
        out.sort_values(
            ['shot', 'type of element', 'source_file', 'experimental_peak_bin', 'candidate_score', 'abs_delta_nm', 'intensity'],
            ascending=[True, True, True, True, False, True, False]
        )
        .drop_duplicates(
            subset=['shot', 'type of element', 'source_file', 'experimental_peak_bin'],
            keep='first'
        )
    )

    out = out.drop(columns=['experimental_peak_bin', 'nist_intensity_for_score'])
    return out

# =========================================================
# MODULAR TAB CLASS
# =========================================================
class ShotComparisonTab:
    """
    Modular shot comparison panel used by main.py.

    This class intentionally keeps all advanced comparison logic inside the tab.
    main.py only instantiates it through:
        self.comp_tab = ShotComparisonTab(container_frame, self)
    """

    def __init__(self, master_frame, app_instance):
        self.master_frame = master_frame
        self.app = app_instance

        self.file_paths = []
        self.processed_data = []

        self.normalization_mode = NORMALIZATION_NONE
        self.display_time_mode = DISPLAY_SYNC
        self.show_residuals = False

        # Local NIST spectroscopy filtering state.
        self.selected_nist_files = set()
        self.nist_match_tolerance_nm = NIST_MATCH_TOLERANCE_NM
        self.nist_min_relative_peak_height = NIST_MIN_RELATIVE_PEAK_HEIGHT
        self.nist_noise_sigma_factor = NIST_NOISE_SIGMA_FACTOR
        self.nist_last_matches = pd.DataFrame()
        # Show/export only the first N globally assigned candidate lines per shot.
        # The assignment is always computed with all local NIST files first;
        # selected files only filter the already-assigned best candidates.
        self.nist_display_max_lines = 10
        self.nist_all_matches_cache = None
        self.nist_all_matches_cache_key = None

        self.color_palette = [
            '#003f5c', '#7a5195', '#ef5675', '#ffa600', '#2f4b7c',
            '#665191', '#a05195', '#d45087', '#118ab2', '#06d6a0'
        ]

        # Folder-aware labeling and coloring. Each folder gets a base hue;
        # shots inside that folder get close, but distinguishable, colors.
        self.folder_order = []
        self.folder_color_state = {}
        self.folder_base_hues = [
            0.00, 0.08, 0.16, 0.28, 0.45,
            0.56, 0.64, 0.74, 0.83, 0.92
        ]

        self.cursor_dynamics_enabled = False
        self.cursor_lines = []
        self.last_cursor_x = None
        self.motion_cid = None
        self.right_click_cid = None

        self.time_axes = []
        self.time_residual_axes = []
        self.spec_axes = []
        self.spec_residual_axes = []
        self.xlim_callback_ids = []
        self._syncing_xlim = False

        self.create_widgets()

    # -----------------------------------------------------
    # GUI LAYOUT
    # -----------------------------------------------------
    def create_widgets(self):
        self.main_frame = tk.Frame(self.master_frame, bg="white")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_button_frame1 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame1.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        tk.Button(self.top_button_frame1, text="Load Shots", command=self.load_shots, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame1, text="Load Folder", command=self.load_shots_from_folder, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame1, text="Clear Shots", command=self.clear_shots, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)

        self.sync_button = tk.Button(
            self.top_button_frame1,
            text="Display: synchronized",
            command=self.toggle_display_time_mode,
            bg="#e0e0e0"
        )
        self.sync_button.pack(side=tk.LEFT, padx=5, pady=2)

        self.residual_button = tk.Button(
            self.top_button_frame1,
            text="Show residuals",
            command=self.toggle_residuals,
            bg="#e0e0e0"
        )
        self.residual_button.pack(side=tk.LEFT, padx=5, pady=2)

        tk.Button(self.top_button_frame1, text="Normalization", command=self.choose_normalization_mode, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame1, text="No norm", command=lambda: self.set_normalization_mode(NORMALIZATION_NONE), bg="#eeeeee").pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(self.top_button_frame1, text="τ", command=lambda: self.set_normalization_mode(NORMALIZATION_TAU), bg="#eeeeee").pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(self.top_button_frame1, text="τ / ∫Ip", command=lambda: self.set_normalization_mode(NORMALIZATION_TAU_AREA), bg="#eeeeee").pack(side=tk.LEFT, padx=2, pady=2)

        self.normalization_label = tk.Label(
            self.top_button_frame1,
            text=get_normalization_label(self.normalization_mode),
            fg="blue",
            bg="#f0f0f0"
        )
        self.normalization_label.pack(side=tk.LEFT, padx=5, pady=2)

        self.cursor_toggle_button = tk.Button(
            self.top_button_frame1,
            text="Enable cursor dynamics",
            command=self.toggle_cursor_dynamics,
            bg="#e0e0e0"
        )
        self.cursor_toggle_button.pack(side=tk.LEFT, padx=5, pady=2)

        self.top_button_frame2 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        tk.Button(self.top_button_frame2, text="H-alpha integrals", command=self.show_halpha_integrals, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="H-alpha real integrals", command=self.show_halpha_real_integrals, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Bt delay", command=self.show_bt_delays, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Compute reproducibility", command=self.compute_reproducibility_gui, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Generate comparison", command=self.generate_group_comparison, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Export full analysis", command=self.export_full_analysis, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Save data to CSV", command=self.save_data_to_csv, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Filter spectroscopy", command=self.show_spectroscopy_filter_options, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)

        self.plot_frame = tk.Frame(self.main_frame, bg="white")
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig = Figure(figsize=(10, 8), facecolor='white')
        self.rebuild_plot_axes()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        canvas_widget = self.canvas.get_tk_widget()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.data_box_label = tk.Label(
            self.toolbar,
            text="",
            anchor="w",
            justify="left",
            font=("Courier New", 8)
        )
        self.data_box_label.pack(side=tk.LEFT, padx=10)

        self.connect_xlim_sync_callbacks()
        self.canvas.draw()

    def rebuild_plot_axes(self):
        """
        Rebuild the Matplotlib axes according to the residual state.

        Residual subplots are created only when Show residuals is active. This
        keeps the normal visualizer compact and leaves more room for readable
        axes and labels.
        """
        self.disconnect_xlim_sync_callbacks()
        self.fig.clear()

        if self.show_residuals:
            gs = self.fig.add_gridspec(
                4,
                2,
                height_ratios=[3, 1, 3, 1],
                hspace=0.4
            )

            self.ax_bt = self.fig.add_subplot(gs[0, 0])
            self.ax_bt_residual = self.fig.add_subplot(gs[1, 0])
            self.ax_ip = self.fig.add_subplot(gs[0, 1])
            self.ax_ip_residual = self.fig.add_subplot(gs[1, 1])
            self.ax_halpha = self.fig.add_subplot(gs[2, 0])
            self.ax_halpha_residual = self.fig.add_subplot(gs[3, 0])
            self.ax_avantes = self.fig.add_subplot(gs[2, 1])
            self.ax_avantes_residual = self.fig.add_subplot(gs[3, 1])

            self.time_residual_axes = [
                self.ax_bt_residual,
                self.ax_ip_residual,
                self.ax_halpha_residual
            ]
            self.spec_residual_axes = [self.ax_avantes_residual]

        else:
            gs = self.fig.add_gridspec(
                2,
                2,
                height_ratios=[1, 1],
                hspace=0.32,
                wspace=0.28
            )

            self.ax_bt = self.fig.add_subplot(gs[0, 0])
            self.ax_ip = self.fig.add_subplot(gs[0, 1])
            self.ax_halpha = self.fig.add_subplot(gs[1, 0])
            self.ax_avantes = self.fig.add_subplot(gs[1, 1])

            self.ax_bt_residual = None
            self.ax_ip_residual = None
            self.ax_halpha_residual = None
            self.ax_avantes_residual = None

            self.time_residual_axes = []
            self.spec_residual_axes = []

        self.time_axes = [self.ax_bt, self.ax_ip, self.ax_halpha]
        self.spec_axes = [self.ax_avantes]

        # Leave a clean upper band for the single global legend.
        self.fig.subplots_adjust(top=0.82, right=0.82)

        self._set_axis_labels()

    def disconnect_xlim_sync_callbacks(self):
        """Disconnect x-limit synchronization callbacks."""
        if not hasattr(self, "xlim_callback_ids"):
            self.xlim_callback_ids = []

        for ax, cid in self.xlim_callback_ids:
            try:
                ax.callbacks.disconnect(cid)
            except Exception:
                pass

        self.xlim_callback_ids = []

    def connect_xlim_sync_callbacks(self):
        """Connect zoom/pan synchronization callbacks for the current axes."""
        self.disconnect_xlim_sync_callbacks()
        self._syncing_xlim = False

        axes = self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes

        for ax in axes:
            if ax is None:
                continue
            try:
                cid = ax.callbacks.connect("xlim_changed", self.on_axis_xlim_changed)
                self.xlim_callback_ids.append((ax, cid))
            except Exception:
                pass

    def get_xlim_sync_group(self, source_ax):
        """
        Return the axes that should share x-limits with source_ax.

        The temporal panels are synchronized with each other. In tau
        normalizations, Ip and H-alpha use tau while Bt keeps its own time axis,
        so Bt is kept separate from the tau axes. Spectroscopy is synchronized
        only with the spectroscopy residual axis because its x-axis is wavelength.
        """
        if source_ax in self.spec_axes or source_ax in self.spec_residual_axes:
            return [ax for ax in (self.spec_axes + self.spec_residual_axes) if ax is not None]

        if source_ax in self.time_axes or source_ax in self.time_residual_axes:
            if self.normalization_mode == NORMALIZATION_NONE:
                return [ax for ax in (self.time_axes + self.time_residual_axes) if ax is not None]

            # In tau modes, Ip/H-alpha use tau; Bt remains in ms.
            tau_axes = [
                self.ax_ip,
                self.ax_halpha,
                self.ax_ip_residual,
                self.ax_halpha_residual
            ]
            bt_axes = [
                self.ax_bt,
                self.ax_bt_residual
            ]

            if source_ax in tau_axes:
                return [ax for ax in tau_axes if ax is not None]
            return [ax for ax in bt_axes if ax is not None]

        return []

    def on_axis_xlim_changed(self, source_ax):
        """Synchronize zoom/pan x-limits across compatible axes."""
        if getattr(self, "_syncing_xlim", False):
            return

        group = self.get_xlim_sync_group(source_ax)
        if len(group) <= 1:
            return

        try:
            xlim = source_ax.get_xlim()
        except Exception:
            return

        self._syncing_xlim = True
        try:
            for ax in group:
                if ax is source_ax:
                    continue
                try:
                    ax.set_xlim(xlim, emit=False)
                except Exception:
                    pass

            if hasattr(self, "canvas"):
                self.canvas.draw_idle()
        finally:
            self._syncing_xlim = False


    def toggle_display_time_mode(self):
        self.display_time_mode = DISPLAY_RAW if self.display_time_mode == DISPLAY_SYNC else DISPLAY_SYNC
        self.sync_button.config(text="Display: raw time" if self.display_time_mode == DISPLAY_RAW else "Display: synchronized")
        self.plot_data()

    def toggle_residuals(self):
        self.show_residuals = not self.show_residuals
        self.residual_button.config(text="Hide residuals" if self.show_residuals else "Show residuals")
        self.plot_data()

    # -----------------------------------------------------
    # TABLE WINDOWS AND BASIC ANALYSIS BUTTONS
    # -----------------------------------------------------
    def show_dataframe_window(self, df, title, default_filename_base="analysis", plot_callback=None):
        win = tk.Toplevel(self.app)
        win.title(title)
        win.geometry("1150x560")

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
            values = [f"{v:.6g}" if isinstance(v, (float, np.floating)) else v for v in row]
            tree.insert("", tk.END, values=values)

        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

        def export_df():
            path = filedialog.asksaveasfilename(
                initialfile=default_filename_base,
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")]
            )
            if not path:
                return
            try:
                saved_path, mode = save_dataframe_with_openpyxl_fallback(df, path, index=False)
                if mode == "csv_fallback":
                    messagebox.showinfo(
                        "Exported as CSV",
                        "openpyxl is not installed, so the table was saved as CSV instead:\n"
                        f"{saved_path}"
                    )
                else:
                    messagebox.showinfo("Exported", f"Table exported successfully:\n{saved_path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(btn_frame, text="Export table", command=export_df).pack(side=tk.RIGHT, padx=5)

        if plot_callback is not None:
            def plot_from_table():
                try:
                    plot_callback(df.copy())
                except Exception as e:
                    messagebox.showerror(
                        "Plot error",
                        "Could not generate the plot from this table.\n\n"
                        f"{type(e).__name__}: {e}"
                    )

            tk.Button(
                btn_frame,
                text="Plot figure",
                command=plot_from_table
            ).pack(side=tk.RIGHT, padx=5)

    def show_halpha_integrals(self):
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")

        rows = []
        failed = []

        for d in self.processed_data:
            try:
                m = compute_halpha_integral_metrics(d)
                if m is not None:
                    rows.append(m)
                else:
                    failed.append(d.get('shot_number', 'unknown'))
            except Exception as e:
                failed.append(f"{d.get('shot_number', 'unknown')}: {e}")

        if not rows:
            return messagebox.showerror(
                "Error",
                "Could not compute H-alpha integrals.\n"
                "Check that shots are loaded and that the plasma end time is valid."
            )

        if failed:
            messagebox.showwarning(
                "Some shots were skipped",
                "Could not compute integrals for:\n" + "\n".join(map(str, failed))
            )

        self.show_dataframe_window(
            pd.DataFrame(rows),
            title="H-alpha and Ip integrals",
            default_filename_base="halpha_integrals"
        )

    def show_halpha_real_integrals(self):
        """
        Show a compact table where H-alpha is integrated over its own real
        emission window:
            Halpha_start_5pct -> Halpha_end

        This table is useful when H-alpha emission extends beyond the Ip-defined
        plasma duration.
        """
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")

        rows = []
        failed = []

        for d in self.processed_data:
            try:
                m = compute_halpha_real_window_table(d)
                if m is not None:
                    rows.append(m)
                else:
                    failed.append(d.get('shot_number', 'unknown'))
            except Exception as e:
                failed.append(f"{d.get('shot_number', 'unknown')}: {e}")

        if not rows:
            return messagebox.showerror(
                "Error",
                "Could not compute real H-alpha integrals.\n"
                "Check that shots are loaded and that H-alpha start/end times are valid."
            )

        if failed:
            messagebox.showwarning(
                "Some shots were skipped",
                "Could not compute real H-alpha integrals for:\n" + "\n".join(map(str, failed))
            )

        self.show_dataframe_window(
            pd.DataFrame(rows),
            title="H-alpha real-window integrals",
            default_filename_base="halpha_real_window_integrals"
        )


    def show_bt_delays(self):
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")
        self.show_dataframe_window(
            pd.DataFrame([compute_timing_delay_metrics(d) for d in self.processed_data]),
            title="Timing delays relative to Bt start",
            default_filename_base="bt_delays"
        )

    def show_spectroscopy_filter_options(self):
        """
        Open a control panel for local NIST spectroscopy filtering.

        The panel lets the user select which local element files should be
        overlaid on the Avantes spectrum and exported as a matched-line table.
        """
        options_df = get_nist_file_options()
        folder = str(get_emission_lines_dir())

        if options_df.empty:
            summary_df = list_local_nist_files()
            messagebox.showwarning(
                "Emission-line database",
                "No local NIST emission-line files are available yet.\n\n"
                f"Expected folder:\n{folder}\n\n"
                "Place your NIST CSV files there, for example Fe_I_II_290_1110_nm.csv."
            )
            self.show_dataframe_window(
                summary_df,
                title="Spectroscopy filter options - local NIST lines",
                default_filename_base="nist_emission_line_options"
            )
            return

        win = tk.Toplevel(self.app)
        win.title("Filter spectroscopy - local NIST lines")
        win.geometry("920x560")

        info = tk.Label(
            win,
            text=(
                "Select the local NIST elements/files to overlay on the Avantes spectrum.\n"
                "Only NIST lines with significant normalized RW intensity inside the wavelength tolerance are shown/exported.\n"
                f"Folder: {folder}"
            ),
            justify="left",
            anchor="w"
        )
        info.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        main = tk.Frame(win)
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ["use", "element", "file", "n_lines", "lambda_min_nm", "lambda_max_nm", "source"]
        tree = ttk.Treeview(main, columns=columns, show="headings", height=12)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(main, orient=tk.VERTICAL, command=tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=y_scroll.set)

        widths = {
            "use": 70,
            "element": 120,
            "file": 250,
            "n_lines": 90,
            "lambda_min_nm": 120,
            "lambda_max_nm": 120,
            "source": 130,
        }
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 120), anchor="center")

        option_rows = []
        for i, row in options_df.iterrows():
            file_name = str(row['file'])
            selected = file_name in self.selected_nist_files
            option_rows.append(row.to_dict())
            tree.insert(
                "",
                tk.END,
                iid=str(i),
                values=[
                    "YES" if selected else "",
                    row.get('element_guess', ''),
                    file_name,
                    row.get('n_lines', ''),
                    f"{row.get('lambda_min_nm', np.nan):.4g}" if pd.notna(row.get('lambda_min_nm', np.nan)) else "",
                    f"{row.get('lambda_max_nm', np.nan):.4g}" if pd.notna(row.get('lambda_max_nm', np.nan)) else "",
                    row.get('wavelength_source', ''),
                ]
            )

        def refresh_tree_marks():
            for i, row in options_df.iterrows():
                file_name = str(row['file'])
                values = list(tree.item(str(i), "values"))
                values[0] = "YES" if file_name in self.selected_nist_files else ""
                tree.item(str(i), values=values)

        def toggle_selected(_event=None):
            selected_items = tree.selection()
            for item in selected_items:
                try:
                    row = options_df.iloc[int(item)]
                except Exception:
                    continue
                file_name = str(row['file'])
                if file_name in self.selected_nist_files:
                    self.selected_nist_files.remove(file_name)
                else:
                    self.selected_nist_files.add(file_name)
            refresh_tree_marks()

        tree.bind("<Double-1>", toggle_selected)

        params_frame = tk.LabelFrame(win, text="Wavelength/intensity matching parameters")
        params_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=6)

        tol_var = tk.StringVar(value=str(self.nist_match_tolerance_nm))
        rel_var = tk.StringVar(value=str(self.nist_min_relative_peak_height))
        sigma_var = tk.StringVar(value=str(self.nist_noise_sigma_factor))

        tk.Label(params_frame, text="Tolerance [nm]").pack(side=tk.LEFT, padx=(8, 2), pady=6)
        tk.Entry(params_frame, textvariable=tol_var, width=8).pack(side=tk.LEFT, padx=(0, 12), pady=6)

        tk.Label(params_frame, text="Min relative intensity").pack(side=tk.LEFT, padx=(8, 2), pady=6)
        tk.Entry(params_frame, textvariable=rel_var, width=8).pack(side=tk.LEFT, padx=(0, 12), pady=6)

        tk.Label(params_frame, text="Noise sigma factor").pack(side=tk.LEFT, padx=(8, 2), pady=6)
        tk.Entry(params_frame, textvariable=sigma_var, width=8).pack(side=tk.LEFT, padx=(0, 12), pady=6)

        max_lines_var = tk.StringVar(value=str(getattr(self, "nist_display_max_lines", 10)))
        tk.Label(params_frame, text="Max lines/shot shown").pack(side=tk.LEFT, padx=(8, 2), pady=6)
        tk.Entry(params_frame, textvariable=max_lines_var, width=6).pack(side=tk.LEFT, padx=(0, 12), pady=6)

        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        def read_params():
            try:
                new_tolerance = float(tol_var.get())
                new_rel_height = float(rel_var.get())
                new_sigma = float(sigma_var.get())
                new_max_lines = int(float(max_lines_var.get()))
                if new_max_lines < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid parameters",
                    "Tolerance, relative height, sigma factor, and max lines/shot must be valid numbers.\n"
                    "Max lines/shot must be an integer >= 1."
                )
                return False

            # Changing the physical matching parameters invalidates the all-elements cache.
            if (
                new_tolerance != getattr(self, "nist_match_tolerance_nm", NIST_MATCH_TOLERANCE_NM)
                or new_rel_height != getattr(self, "nist_min_relative_peak_height", NIST_MIN_RELATIVE_PEAK_HEIGHT)
                or new_sigma != getattr(self, "nist_noise_sigma_factor", NIST_NOISE_SIGMA_FACTOR)
            ):
                self.nist_all_matches_cache = None
                self.nist_all_matches_cache_key = None

            self.nist_match_tolerance_nm = new_tolerance
            self.nist_min_relative_peak_height = new_rel_height
            self.nist_noise_sigma_factor = new_sigma
            self.nist_display_max_lines = new_max_lines
            return True

        def apply_filter():
            if not read_params():
                return
            self.plot_data()

        def clear_filter():
            self.selected_nist_files.clear()
            self.nist_last_matches = pd.DataFrame()
            refresh_tree_marks()
            self.plot_data()

        def show_available_files():
            self.show_dataframe_window(
                list_local_nist_files(),
                title="Spectroscopy filter options - local NIST lines",
                default_filename_base="nist_emission_line_options"
            )

        def show_matches():
            if not read_params():
                return
            df = self.compute_selected_spectroscopy_matches()
            if df.empty:
                messagebox.showinfo(
                    "No matched lines",
                    "No selected NIST lines had significant experimental intensity within the wavelength tolerance.\n"
                    "Try selecting an element, increasing the tolerance, or reducing the intensity threshold."
                )
                return
            self.show_dataframe_window(
                df,
                title="Matched spectroscopy lines",
                default_filename_base="matched_spectroscopy_lines",
                plot_callback=self.show_matched_spectroscopy_figure
            )

        tk.Button(btn_frame, text="Toggle selected", command=toggle_selected).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Apply filter", command=apply_filter).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear filter", command=clear_filter).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show available files", command=show_available_files).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Update max lines", command=lambda: (read_params() and self.plot_data())).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show / export matched table", command=show_matches).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def get_selected_nist_dataframes(self):
        """Return [(element_label, file_name, dataframe), ...] for selected NIST files."""
        if not self.selected_nist_files:
            return []

        folder = get_emission_lines_dir()
        loaded = []
        for file_name in sorted(self.selected_nist_files):
            path = folder / file_name
            if not path.exists():
                continue
            try:
                df = read_nist_line_file(path)
                element_label = guess_element_from_filename(file_name)
                loaded.append((element_label, file_name, df))
            except Exception as exc:
                print(f"Could not read NIST file {file_name}: {exc}")
        return loaded

    def get_all_nist_dataframes(self):
        """
        Return [(element_label, file_name, dataframe), ...] for ALL local NIST files.

        This is intentionally independent of the current GUI selection. The selected
        elements/files are applied only after the globally best candidate for each
        measured spectral bin has already been chosen. That prevents a line such as
        H-alpha from being reassigned to Fe just because only Fe was selected later.
        """
        options_df = get_nist_file_options()
        if options_df.empty:
            return []

        folder = get_emission_lines_dir()
        loaded = []
        for _, row in options_df.iterrows():
            file_name = str(row.get('file', '')).strip()
            if not file_name:
                continue
            path = folder / file_name
            if not path.exists():
                continue
            try:
                df = read_nist_line_file(path)
                element_label = guess_element_from_filename(file_name)
                loaded.append((element_label, file_name, df))
            except Exception as exc:
                print(f"Could not read NIST file {file_name}: {exc}")
        return loaded

    def _spectroscopy_cache_key(self):
        """Key for the all-elements spectroscopy match cache."""
        shots = tuple(str(d.get('shot_number', '')) for d in self.processed_data)
        files = tuple(
            sorted(
                str(x.get('file', ''))
                for _, x in get_nist_file_options().iterrows()
                if str(x.get('file', '')).strip()
            )
        )
        return (
            shots,
            files,
            float(self.nist_match_tolerance_nm),
            float(self.nist_min_relative_peak_height),
            float(self.nist_noise_sigma_factor),
        )

    def compute_all_spectroscopy_matches(self):
        """
        Compute the globally assigned matched-line table using ALL local NIST files.

        Important behavior:
          1) all local element files are matched first;
          2) for each experimental wavelength bin, only the best candidate is kept;
          3) GUI selection is NOT used here.

        This prevents recalculating assignments after Toggle selected. Selection later
        only filters the already-computed candidate table.
        """
        base_cols = [
            "shot",
            "type of element",
            "wavelength",
            "intensity",
            "rank_in_shot",
            "experimental_wavelength_nm",
            "delta_nm",
            "relative_intensity_in_shot",
            "spectrum_source",
            "spectrum_normalization",
        ]

        if not self.processed_data:
            return pd.DataFrame(columns=base_cols)

        cache_key = self._spectroscopy_cache_key()
        if (
            self.nist_all_matches_cache is not None
            and self.nist_all_matches_cache_key == cache_key
        ):
            return self.nist_all_matches_cache.copy()

        all_nist = self.get_all_nist_dataframes()
        if not all_nist:
            return pd.DataFrame(columns=base_cols)

        shot_tables = []

        for shot_order, data in enumerate(self.processed_data):
            wl, intensity_norm, spec_meta = get_spectroscopy_rw_normalized_arrays(data)
            shot = data.get('shot_number', '')

            if len(wl) == 0 or len(intensity_norm) == 0:
                continue

            rows_for_shot = []

            for element_label, file_name, nist_df in all_nist:
                matched = match_nist_lines_for_shot(
                    wl,
                    intensity_norm,
                    nist_df,
                    element_label=element_label,
                    shot_number=shot,
                    tolerance_nm=self.nist_match_tolerance_nm,
                    min_relative_peak_height=self.nist_min_relative_peak_height,
                    noise_sigma_factor=self.nist_noise_sigma_factor,
                )

                if not matched.empty:
                    matched["source_file"] = file_name
                    matched["spectrum_source"] = spec_meta.get("spectrum_source", "")
                    matched["spectrum_normalization"] = "S_rw / (plasma_duration_s * Ip_integral_plasma_tau_A)"
                    matched["spectrum_normalization_factor"] = spec_meta.get("spectrum_normalization_factor", np.nan)
                    matched["plasma_duration_s_for_spectrum"] = spec_meta.get("plasma_duration_s_for_spectrum", np.nan)
                    matched["Ip_integral_plasma_tau_positive_A_for_spectrum"] = spec_meta.get(
                        "Ip_integral_plasma_tau_positive_A_for_spectrum",
                        np.nan
                    )
                    matched["Ip_integral_plasma_time_positive_C_for_spectrum"] = spec_meta.get(
                        "Ip_integral_plasma_time_positive_C_for_spectrum",
                        np.nan
                    )
                    matched["shot_order"] = shot_order
                    rows_for_shot.append(matched)

            if not rows_for_shot:
                continue

            shot_df = pd.concat(rows_for_shot, ignore_index=True)
            shot_df["abs_delta_nm"] = shot_df["delta_nm"].abs()

            bin_width = max(self.nist_match_tolerance_nm / 2.0, 1e-9)
            shot_df["experimental_peak_bin_global"] = np.round(
                shot_df["experimental_wavelength_nm"].astype(float) / bin_width
            ).astype(int)

            shot_df["nist_intensity_for_score"] = pd.to_numeric(
                shot_df.get("nist_relative_intensity_numeric", np.nan),
                errors="coerce"
            ).fillna(0.0)

            # Choose the best candidate for each measured wavelength bin from ALL
            # elements. A selected-only Fe table cannot steal H-alpha afterwards.
            shot_df["candidate_score"] = shot_df["nist_intensity_for_score"].astype(float)
            shot_df["proximity_score"] = np.clip(
                1.0 - shot_df["abs_delta_nm"].astype(float) / max(self.nist_match_tolerance_nm, 1e-12),
                0.0,
                1.0
            )
            shot_df["nist_score_norm"] = shot_df["candidate_score"]

            shot_df = (
                shot_df
                .sort_values(
                    ["experimental_peak_bin_global", "candidate_score", "abs_delta_nm", "intensity"],
                    ascending=[True, False, True, False]
                )
                .drop_duplicates(
                    subset=["shot", "experimental_peak_bin_global"],
                    keep="first"
                )
            )

            # Rank within each shot after global assignment.
            shot_df = shot_df.sort_values("intensity", ascending=False).reset_index(drop=True)
            shot_df["rank_in_shot"] = np.arange(1, len(shot_df) + 1)
            shot_tables.append(shot_df)

        if not shot_tables:
            return pd.DataFrame(columns=base_cols)

        out = pd.concat(shot_tables, ignore_index=True)
        out = out.sort_values(
            ["rank_in_shot", "shot_order", "intensity"],
            ascending=[True, True, False]
        ).reset_index(drop=True)

        first_cols = [
            "shot",
            "type of element",
            "wavelength",
            "intensity",
            "rank_in_shot",
            "experimental_wavelength_nm",
            "delta_nm",
            "nist_relative_intensity",
            "nist_relative_intensity_numeric",
            "candidate_score",
            "proximity_score",
            "nist_score_norm",
        ]
        other_cols = [
            c for c in out.columns
            if c not in first_cols + [
                "shot_order",
                "abs_delta_nm",
                "experimental_peak_bin_global",
                "nist_intensity_for_score",
                "nist_log_for_score",
            ]
        ]

        out = out[first_cols + other_cols]
        self.nist_all_matches_cache = out.copy()
        self.nist_all_matches_cache_key = cache_key
        return out.copy()

    def compute_selected_spectroscopy_matches(self):
        """
        Return selected/visible matched lines from the all-elements assignment.

        Toggle selected only filters this precomputed global assignment. It does not
        recompute line ownership, so a line first assigned to H remains H even if the
        current display filter asks to show Fe only.
        """
        all_matches = self.compute_all_spectroscopy_matches()
        if all_matches.empty:
            return all_matches

        out = all_matches
        if self.selected_nist_files:
            out = out[out["source_file"].astype(str).isin(self.selected_nist_files)].copy()
        else:
            out = out.iloc[0:0].copy()

        max_lines = int(getattr(self, "nist_display_max_lines", 10))
        if max_lines > 0 and "rank_in_shot" in out.columns:
            out = out[out["rank_in_shot"].astype(float) <= max_lines].copy()

        out = out.sort_values(
            ["rank_in_shot", "shot", "intensity"],
            ascending=[True, True, False]
        ).reset_index(drop=True)
        return out

    def show_matched_spectroscopy_figure(self, matches_df):
        """
        Plot the matched spectroscopy table as a wavelength-intensity figure.

        The plot uses:
          - X axis: NIST/selected wavelength from the table column "wavelength".
          - Y axis: experimental intensity from the table column "intensity".
          - Marker shape: element type, e.g. H=x, Fe=triangle, W=square.
          - Color: shot number.
          - Horizontal bar: wavelength interval used by the matcher,
            wavelength +/- current NIST matching tolerance.

        A broken X axis is used by default to remove the empty region between
        525 and 625 nm when there are points on both sides of that gap.
        """
        if matches_df is None or matches_df.empty:
            messagebox.showinfo("No data", "There are no matched spectroscopy lines to plot.")
            return

        required_cols = ["shot", "type of element", "wavelength", "intensity", "rank_in_shot"]
        missing = [c for c in required_cols if c not in matches_df.columns]
        if missing:
            messagebox.showerror(
                "Missing columns",
                "The matched spectroscopy table is missing required columns:\n" + ", ".join(missing)
            )
            return

        try:
            max_available_rank = int(pd.to_numeric(matches_df["rank_in_shot"], errors="coerce").max())
        except Exception:
            max_available_rank = 10

        max_rank = simpledialog.askinteger(
            "Spectroscopy plot",
            "Maximum rank_in_shot to plot:",
            initialvalue=min(max_available_rank, 10),
            minvalue=1,
            maxvalue=max(max_available_rank, 1),
            parent=self.app
        )
        if max_rank is None:
            return

        # Default gap used to remove the visually empty central wavelength band.
        cut_min = 525.0
        cut_max = 625.0

        df = matches_df.copy()
        for col in ["shot", "wavelength", "intensity", "rank_in_shot", "experimental_wavelength_nm"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["shot", "wavelength", "intensity", "rank_in_shot"])
        df = df[df["rank_in_shot"] <= max_rank].copy()

        if df.empty:
            messagebox.showinfo("No data", "No rows remain after the selected rank filter.")
            return

        # Remove only the visually empty wavelength interval. The original table
        # remains unchanged; this affects only the figure.
        df_visible = df[(df["wavelength"] < cut_min) | (df["wavelength"] > cut_max)].copy()
        if df_visible.empty:
            df_visible = df.copy()

        marker_map = {
            "H": "x",
            "Fe": "^",
            "W": "s",
            "Ar": "o",
        }

        distinct_colors = [
            "#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
            "#17becf", "#8c564b", "#e377c2", "#bcbd22", "#000000",
            "#7f7f7f", "#005f73", "#9b2226", "#3a0ca3", "#f77f00",
            "#008000", "#00b4d8", "#6a040f", "#ff006e", "#4361ee",
        ]

        unique_shots = sorted(df_visible["shot"].dropna().astype(int).unique())
        shot_color_map = {
            shot: distinct_colors[i % len(distinct_colors)]
            for i, shot in enumerate(unique_shots)
        }

        tolerance = float(getattr(self, "nist_match_tolerance_nm", NIST_MATCH_TOLERANCE_NM))
        if not np.isfinite(tolerance) or tolerance <= 0:
            tolerance = NIST_MATCH_TOLERANCE_NM

        left_df = df_visible[df_visible["wavelength"] < cut_min].copy()
        right_df = df_visible[df_visible["wavelength"] > cut_max].copy()
        use_broken_axis = (not left_df.empty) and (not right_df.empty)

        win = tk.Toplevel(self.app)
        win.title("Matched spectroscopy lines figure")
        win.geometry("1350x760")

        if use_broken_axis:
            fig, axes = plt.subplots(
                1,
                2,
                sharey=True,
                figsize=(13.5, 6.8),
                gridspec_kw={"width_ratios": [1, 1]}
            )
            ax1, ax2 = axes
            plot_axes = [ax1, ax2]
        else:
            fig = Figure(figsize=(12.5, 6.8), facecolor="white")
            ax1 = fig.add_subplot(111)
            ax2 = None
            plot_axes = [ax1]

        def label_offset(idx):
            offsets = [
                (4, 6), (4, -10), (-18, 6), (-18, -10),
                (8, 12), (8, -16), (-24, 12), (-24, -16),
                (12, 20), (-28, 20), (12, -24), (-28, -24),
            ]
            return offsets[idx % len(offsets)]

        def interval_for_row(row):
            lam = float(row["wavelength"])
            return lam - tolerance, lam + tolerance

        def axis_for_wavelength(lam):
            if use_broken_axis:
                return ax1 if lam < cut_min else ax2
            return ax1

        def clip_interval_to_axis(ax, x0, x1):
            xmin, xmax = ax.get_xlim()
            return max(x0, xmin), min(x1, xmax)

        # Pre-set limits so bars can be clipped correctly.
        if use_broken_axis:
            left_min = float(left_df["wavelength"].min())
            left_max = float(left_df["wavelength"].max())
            right_min = float(right_df["wavelength"].min())
            right_max = float(right_df["wavelength"].max())
            left_margin = max(0.5, 0.06 * max(left_max - left_min, 1.0))
            right_margin = max(0.5, 0.06 * max(right_max - right_min, 1.0))
            ax1.set_xlim(left_min - left_margin, left_max + left_margin)
            ax2.set_xlim(right_min - right_margin, right_max + right_margin)
        else:
            x_min = float(df_visible["wavelength"].min())
            x_max = float(df_visible["wavelength"].max())
            margin = max(0.5, 0.06 * max(x_max - x_min, 1.0))
            ax1.set_xlim(x_min - margin, x_max + margin)

        for i, (_, row) in enumerate(df_visible.iterrows()):
            shot = int(row["shot"])
            wavelength = float(row["wavelength"])
            intensity = float(row["intensity"])
            element = str(row["type of element"]).strip()
            rank = int(row["rank_in_shot"])

            ax = axis_for_wavelength(wavelength)
            color = shot_color_map.get(shot, "black")
            marker = marker_map.get(element, "o")
            x0, x1 = interval_for_row(row)
            x0, x1 = clip_interval_to_axis(ax, x0, x1)

            ax.hlines(
                y=intensity,
                xmin=x0,
                xmax=x1,
                color=color,
                linewidth=2.5,
                alpha=0.85,
                zorder=2
            )

            ax.scatter(
                wavelength,
                intensity,
                color=color,
                edgecolor="black",
                linewidth=0.5,
                marker=marker,
                s=95,
                zorder=3
            )

            dx, dy = label_offset(i)
            ax.annotate(
                f"{element} r{rank}",
                (wavelength, intensity),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=8,
                clip_on=False
            )

        for ax in plot_axes:
            ax.grid(True, alpha=0.30)
            ax.set_xlabel("Wavelength [nm]")

        ax1.set_ylabel("Intensity [a.u.]")
        fig.suptitle(
            f"Matched spectroscopy lines up to rank_in_shot = {max_rank}",
            fontsize=14
        )

        if use_broken_axis:
            ax1.spines["right"].set_visible(False)
            ax2.spines["left"].set_visible(False)
            ax2.yaxis.tick_right()
            ax2.tick_params(labelright=False, right=False)

            d = 0.015
            kwargs = dict(transform=ax1.transAxes, color="k", clip_on=False)
            ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)
            ax1.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)
            kwargs.update(transform=ax2.transAxes)
            ax2.plot((-d, +d), (-d, +d), **kwargs)
            ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)

        shot_handles = [
            Line2D(
                [0], [0],
                marker="o",
                color="w",
                markerfacecolor=shot_color_map[shot],
                markeredgecolor="black",
                markersize=8,
                label=f"Shot {shot}"
            )
            for shot in unique_shots
        ]

        elements_present = sorted({str(x).strip() for x in df_visible["type of element"].dropna().unique()})
        element_handles = []
        for element in elements_present:
            element_handles.append(
                Line2D(
                    [0], [0],
                    marker=marker_map.get(element, "o"),
                    color="black",
                    linestyle="None",
                    markersize=8,
                    label=element
                )
            )

        legend_ax = ax2 if use_broken_axis else ax1
        legend1 = legend_ax.legend(
            handles=shot_handles,
            title="Shots",
            loc="upper left",
            bbox_to_anchor=(1.02, 1.0),
            fontsize=9,
            title_fontsize=10
        )
        legend_ax.add_artist(legend1)
        legend_ax.legend(
            handles=element_handles,
            title="Element markers",
            loc="upper left",
            bbox_to_anchor=(1.02, 0.62),
            fontsize=9,
            title_fontsize=10
        )

        fig.tight_layout(rect=[0, 0, 0.82, 0.94])

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.draw()

    def plot_selected_nist_lines(self):
        """Overlay selected NIST lines that match significant experimental spectral signal."""
        if not self.selected_nist_files or not self.processed_data:
            self.nist_last_matches = pd.DataFrame()
            return

        df = self.compute_selected_spectroscopy_matches()
        self.nist_last_matches = df
        if df.empty:
            return

        # Keep only the first N globally assigned lines per shot in the visualizer.
        max_lines = int(getattr(self, "nist_display_max_lines", 10))
        plot_df = df.copy()
        if max_lines > 0 and "rank_in_shot" in plot_df.columns:
            plot_df = plot_df[plot_df["rank_in_shot"].astype(float) <= max_lines]

        # Plot only unique element/wavelength combinations to keep the display readable.
        plot_df = (
            plot_df.sort_values("intensity", ascending=False)
                   .drop_duplicates(subset=["type of element", "wavelength"], keep="first")
        )

        ymax = self.ax_avantes.get_ylim()[1] if self.ax_avantes.has_data() else 1.0
        shown_labels = set()
        max_labels = 35
        label_count = 0

        for _, row in plot_df.iterrows():
            lam = float(row["wavelength"])
            element = str(row["type of element"])
            intensity = float(row["intensity"])

            self.ax_avantes.axvline(
                lam,
                linestyle="--",
                linewidth=0.8,
                alpha=0.55,
                color="black"
            )

            # Avoid unreadable label clutter for dense spectra such as Fe.
            if label_count < max_labels:
                label = f"{element} {lam:.2f}"
                if label not in shown_labels:
                    self.ax_avantes.text(
                        lam,
                        0.96,
                        label,
                        rotation=90,
                        transform=self.ax_avantes.get_xaxis_transform(),
                        fontsize=7,
                        va="top",
                        ha="center",
                        alpha=0.8,
                        color="black"
                    )
                    shown_labels.add(label)
                    label_count += 1

        # Small status note in the plot.
        self.ax_avantes.text(
            0.01,
            0.98,
            f"NIST filter: {', '.join(sorted({str(x) for x in df['type of element'].unique()}))} | top {getattr(self, 'nist_display_max_lines', 10)} lines/shot",
            transform=self.ax_avantes.transAxes,
            fontsize=8,
            va="top",
            ha="left",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none")
        )

    # -----------------------------------------------------
    # NORMALIZATION AND LABELS
    # -----------------------------------------------------
    def set_normalization_mode(self, mode):
        """Apply normalization immediately and force a complete redraw.

        Important fix: the previous version changed the text label before the plot
        was successfully redrawn. If the tau-area branch raised a Tk/Matplotlib
        callback error, the label changed but the old, unnormalized plot stayed
        on screen. Now the figure is redrawn first; if something fails, the user
        sees the full error instead of a silent no-op.
        """
        old_mode = self.normalization_mode
        try:
            self.normalization_mode = mode

            # A toolbar cursor table can overwrite the status text, so remove the
            # old cursor guides before rebuilding the plot.
            self.clear_cursor_lines()

            # Rebuild the full plot using the new mode. Do not rely on previous
            # axis state.
            self.plot_data()

            # Only update the button label after the redraw has succeeded.
            self.normalization_label.config(text=get_normalization_label(self.normalization_mode))
            self.update_normalization_status_text()
            self.canvas.draw_idle()

        except Exception:
            self.normalization_mode = old_mode
            err = traceback.format_exc()
            print(err)
            messagebox.showerror(
                "Normalization error",
                "The normalization callback failed. Full traceback:\n\n" + err
            )

    def choose_normalization_mode(self):
        win = tk.Toplevel(self.app)
        win.title("Normalization mode")
        win.geometry("710x330")

        tk.Label(
            win,
            text=(
                "Choose how Ip, H-alpha, and spectra are displayed.\n"
                "Bt is never converted to tau because tau is defined from Ip.\n"
                "Spectra use S_raw(lambda), not the max-normalized spectrum.\n"
                "In tau mode, spectra are divided by the plasma duration in milliseconds."
            ),
            justify="left"
        ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        mode_var = tk.StringVar(value=self.normalization_mode)
        options = [
            (NORMALIZATION_NONE, "No normalization: synchronized/raw time, S_raw(lambda)"),
            (NORMALIZATION_TAU, "Tau mode: Ip(tau), H-alpha(tau), S_raw(lambda)/duration [ms]"),
            (NORMALIZATION_TAU_MAX, "Tau + divide by representative max(Ip)"),
            (NORMALIZATION_TAU_AREA, "Tau + divide by physical-time integral int(Ip_+(t) dt)"),
        ]

        for val, text in options:
            tk.Radiobutton(
                win,
                text=text,
                variable=mode_var,
                value=val,
                anchor="w",
                justify="left"
            ).pack(side=tk.TOP, fill=tk.X, padx=20, pady=3)

        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        def apply():
            selected_mode = mode_var.get()
            win.destroy()
            self.set_normalization_mode(selected_mode)

        tk.Button(btn_frame, text="Apply", command=apply).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.RIGHT, padx=5)

    def _set_axis_labels(self):
        """Set axis labels safely for both compact and residual layouts."""
        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            if ax is not None:
                ax.set_facecolor('white')

        mode = self.normalization_mode

        if self.display_time_mode == DISPLAY_RAW:
            bt_time_label = "Time [ms]"
            ip_time_label = "Time [ms]"
            ha_time_label = "Time [ms]"
        else:
            bt_time_label = "Time - t_Bt,start [ms]"
            ip_time_label = "Time - t_Ip,start [ms]"
            ha_time_label = "Time - t_Ip,start [ms]"

        if mode == NORMALIZATION_NONE:
            ip_label = "Ip [kA]"
            ha_label = "H-alpha [a.u.]"
            spec_label = "S_raw [a.u.]"
        elif mode == NORMALIZATION_TAU:
            ip_time_label = "tau [-]"
            ha_time_label = "tau [-]"
            ip_label = "Ip(tau) [kA]"
            ha_label = "H-alpha(tau) [a.u.]"
            spec_label = "S_raw / Δt_p [a.u./ms]"
        elif mode == NORMALIZATION_TAU_MAX:
            ip_time_label = "tau [-]"
            ha_time_label = "tau [-]"
            ip_label = "Ip(tau) / Ip,max_rep"
            ha_label = "H-alpha(tau) / Ip,max_rep"
            spec_label = "(S_raw/Δt_p) / Ip,max_rep"
        elif mode == NORMALIZATION_TAU_AREA:
            ip_time_label = "tau [-]"
            ha_time_label = "tau [-]"
            ip_label = "Ip_pos(tau) / int(Ip_pos(tau)dtau)"
            ha_label = "H-alpha(tau) / int(Ip_pos(tau)dtau)"
            spec_label = "S_raw / (dt_p * int(Ip_pos(tau)dtau))"
        else:
            ip_label = "Ip [kA]"
            ha_label = "H-alpha [a.u.]"
            spec_label = "S_raw [a.u.]"

        self.ax_bt.set_ylabel('Bt [mT]')
        self.ax_ip.set_ylabel(ip_label)
        self.ax_halpha.set_ylabel(ha_label)
        self.ax_avantes.set_ylabel(spec_label)

        if self.show_residuals:
            if self.ax_bt_residual is not None:
                self.ax_bt_residual.set_ylabel('Delta Bt [mT]')
                self.ax_bt_residual.set_xlabel(bt_time_label)
            if self.ax_ip_residual is not None:
                self.ax_ip_residual.set_ylabel('Delta Ip')
                self.ax_ip_residual.set_xlabel(ip_time_label)
            if self.ax_halpha_residual is not None:
                self.ax_halpha_residual.set_ylabel('Delta H-alpha')
                self.ax_halpha_residual.set_xlabel(ha_time_label)
            if self.ax_avantes_residual is not None:
                self.ax_avantes_residual.set_ylabel('Delta intensity')
                self.ax_avantes_residual.set_xlabel('Wavelength [nm]')

            for ax in [self.ax_bt, self.ax_ip, self.ax_halpha, self.ax_avantes]:
                ax.tick_params(labelbottom=False)
        else:
            self.ax_bt.set_xlabel(bt_time_label)
            self.ax_ip.set_xlabel(ip_time_label)
            self.ax_halpha.set_xlabel(ha_time_label)
            self.ax_avantes.set_xlabel('Wavelength [nm]')

            for ax in [self.ax_bt, self.ax_ip, self.ax_halpha, self.ax_avantes]:
                ax.tick_params(labelbottom=True)

    # -----------------------------------------------------
    # LOADING AND SAVING
    # -----------------------------------------------------
    def _normalize_folder_label(self, folder_path):
        """Return a compact label such as '20mPa' from the parent folder name."""
        label = os.path.basename(os.path.normpath(folder_path))
        return label.replace(" ", "") if label else "folder"

    def _register_folder(self, folder_label):
        if folder_label not in self.folder_order:
            self.folder_order.append(folder_label)

    def _postprocess_loaded_data_metadata(self, data, file_path, folder_label=None):
        """Attach metadata used only for labels and colors.

        Important behavior:
        - Load Shots: keeps the old behavior, i.e. labels are only the shot number
          and colors come from the original color palette.
        - Load Folder: uses folder-aware labels/colors, e.g. "2626, 20mPa".
        """
        folder_path = os.path.dirname(file_path)
        data['folder_path'] = folder_path

        if folder_label is None:
            # Manual file selection: do NOT infer a folder label from the path.
            # This keeps the old legend/color behavior for Load Shots.
            data['loaded_from_folder'] = False
            data['folder_label'] = ''
            return data

        # Folder loading: explicitly group shots by the chosen folder label.
        folder_label = str(folder_label).strip().replace(" ", "") or self._normalize_folder_label(folder_path)
        data['loaded_from_folder'] = True
        data['folder_label'] = folder_label
        data['pressure_group'] = folder_label
        self._register_folder(folder_label)
        return data

    def load_shots(self):
        paths = filedialog.askopenfilenames(
            title="Select MephiST-0 shot files",
            filetypes=[("NXS files", "*.nxs"), ("HDF5 files", "*.hdf5 *.h5"), ("All files", "*.*")]
        )
        if not paths:
            return
        self._load_paths(paths, folder_label=None)

    def load_shots_from_folder(self):
        folder_path = filedialog.askdirectory(title="Select folder with .nxs shots")
        if not folder_path:
            return

        paths = sorted(
            os.path.join(folder_path, f)
            for f in os.listdir(folder_path)
            if f.lower().endswith((".nxs", ".h5", ".hdf5"))
        )

        if not paths:
            return messagebox.showinfo(
                "No files",
                "No .nxs/.h5/.hdf5 files were found in the selected folder."
            )

        default_label = self._normalize_folder_label(folder_path)
        folder_label = simpledialog.askstring(
            "Folder legend label",
            "Label to use in the legend for this folder (example: 20mPa):",
            initialvalue=default_label,
            parent=self.app
        )
        if folder_label is None:
            return
        folder_label = folder_label.strip().replace(" ", "") or default_label

        self._load_paths(paths, folder_label=folder_label)

    def _load_paths(self, paths, folder_label=None):
        loaded_count = 0
        skipped = []
        errors = []

        existing_paths = set(os.path.abspath(p) for p in self.file_paths)

        for p in paths:
            abs_path = os.path.abspath(p)
            if abs_path in existing_paths:
                skipped.append(os.path.basename(p))
                continue
            try:
                data = process_shot_data(p, False)
                if data:
                    data = self._postprocess_loaded_data_metadata(data, p, folder_label=folder_label)
                    self.file_paths.append(p)
                    self.processed_data.append(data)
                    existing_paths.add(abs_path)
                    loaded_count += 1
                else:
                    skipped.append(os.path.basename(p))
            except Exception as e:
                errors.append(f"{os.path.basename(p)}: {e}")

        # Rebuild color assignment whenever new folders/shots are loaded.
        self.folder_color_state = {}
        self.plot_data()

        if loaded_count:
            messagebox.showinfo("Loaded", f"Loaded {loaded_count} shot(s).")
        if skipped:
            messagebox.showinfo("Skipped", "Already loaded or duplicated shots:\n" + "\n".join(skipped))
        if errors:
            messagebox.showwarning("Load errors", "Some files could not be loaded:\n" + "\n".join(errors))

    def clear_shots(self):
        self.file_paths = []
        self.processed_data = []
        self.folder_order = []
        self.folder_color_state = {}
        self.plot_data()

    def save_data_to_csv(self):
        if not self.processed_data:
            return messagebox.showinfo("No data", "No shot data to save.")
        for d in self.processed_data:
            process_shot_data(d['file_path'], True)
        messagebox.showinfo("Success", f"Data saved for {len(self.processed_data)} shot(s).")

    # -----------------------------------------------------
    # CURSOR
    # -----------------------------------------------------
    def toggle_cursor_dynamics(self):
        self.cursor_dynamics_enabled = not self.cursor_dynamics_enabled
        self.cursor_toggle_button.config(
            text="Disable cursor dynamics" if self.cursor_dynamics_enabled else "Enable cursor dynamics"
        )

        if self.cursor_dynamics_enabled:
            self.motion_cid = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            self.right_click_cid = self.canvas.mpl_connect('button_press_event', self.on_right_click)
        else:
            if hasattr(self, 'motion_cid') and self.motion_cid is not None:
                self.canvas.mpl_disconnect(self.motion_cid)
                self.motion_cid = None
            if hasattr(self, 'right_click_cid') and self.right_click_cid is not None:
                self.canvas.mpl_disconnect(self.right_click_cid)
                self.right_click_cid = None
            self.clear_cursor_lines()
            self.data_box_label.config(text="")

        self.canvas.draw()

    def on_mouse_move(self, event):
        if not event.inaxes or not self.cursor_dynamics_enabled:
            return

        x = event.xdata
        self.last_cursor_x = x
        self.clear_cursor_lines()

        temporal_axes = self.time_axes + self.time_residual_axes
        spectrum_axes = self.spec_axes + self.spec_residual_axes

        if event.inaxes in temporal_axes:
            # Synchronize the cursor across all temporal plots: Bt, Ip and H-alpha.
            target_axes = temporal_axes
            channel = 'time'
        elif event.inaxes in spectrum_axes:
            # Synchronize the cursor across spectroscopy and spectroscopy residual.
            target_axes = spectrum_axes
            channel = 'spectrum'
        else:
            return

        for ax in target_axes:
            self.cursor_lines.append(
                ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.8)
            )

        rows = ["Shot\tX\tBt\tIp\tH-alpha\tS(lambda)"]

        for data in self.processed_data:
            xb, yb, xi, yi, xh, yh = self.get_display_time_arrays(data)
            wl, sy = self.get_display_spectrum_arrays(data)

            if channel == 'time':
                bt_val = ip_val = ha_val = ""
                if len(xb) > 0:
                    idxb = int(np.abs(xb - x).argmin())
                    bt_val = f"{yb[idxb]:.4g}"
                if len(xi) > 0:
                    idxi = int(np.abs(xi - x).argmin())
                    ip_val = f"{yi[idxi]:.4g}"
                if len(xh) > 0:
                    idxh = int(np.abs(xh - x).argmin())
                    ha_val = f"{yh[idxh]:.4g}"

                rows.append(
                    f"{data['shot_number']}\t{x:.4g}\t{bt_val}\t{ip_val}\t{ha_val}\t"
                )

            elif channel == 'spectrum' and len(wl) > 0:
                idx = int(np.abs(wl - x).argmin())
                rows.append(
                    f"{data['shot_number']}\t{wl[idx]:.4g}\t\t\t\t{sy[idx]:.4g}"
                )

        self.data_box_label.config(text="\n".join(rows))
        self.canvas.draw_idle()

    def on_right_click(self, event):
        if not event.inaxes or not self.cursor_dynamics_enabled or event.button != 3:
            return
        pyperclip.copy(self.data_box_label.cget("text"))
        messagebox.showinfo("Copied", "Cursor table copied to clipboard.")

    def clear_cursor_lines(self):
        for line in self.cursor_lines:
            try:
                line.remove()
            except Exception:
                pass
        self.cursor_lines.clear()

    def draw_cursor_at(self, x):
        if x is None or not self.cursor_dynamics_enabled:
            return

        self.clear_cursor_lines()

        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            self.cursor_lines.append(
                ax.axvline(x=x, color='gray', linestyle='--', linewidth=0.8)
            )

        self.canvas.draw_idle()

    # -----------------------------------------------------
    # NORMALIZATION DIAGNOSTICS / DISPLAY HELPERS
    # -----------------------------------------------------
    def get_ip_normalization_factor_for_data(self, data):
        """
        Returns the exact Ip normalization factor being used in the display.
        For τ / ∫Ip, this is the physical-time factor ∫Ip_+(t)dt.
        """
        tau, plasma_duration, active_mask, tau_active, Ip_active = get_tau_active_and_ip(
            data['Time'],
            data['Ip'],
            start_time=data['Ip_start_time'],
            end_time=data['Ip_end_time']
        )
        time_active = data['Time'][active_mask]
        factor = get_ip_normalization_factor(
            tau_active,
            Ip_active,
            self.normalization_mode,
            time_active=time_active
        )
        return factor, plasma_duration

    def get_ip_charge_factor_for_data(self, data):
        """Physical charge-like integral ∫Ip_+(t)dt, reported only as diagnostic."""
        tau, plasma_duration, active_mask, tau_active, Ip_active = get_tau_active_and_ip(
            data['Time'],
            data['Ip'],
            start_time=data['Ip_start_time'],
            end_time=data['Ip_end_time']
        )
        time_active = data['Time'][active_mask]
        return get_ip_time_area_factor(time_active, Ip_active), plasma_duration

    def get_folder_label_for_data(self, data):
        # Only shots loaded through Load Folder should display/use a folder label.
        # Manually selected shots keep the previous legend behavior: shot number only.
        if not data.get('loaded_from_folder', False):
            return ''
        folder_label = data.get('folder_label') or data.get('pressure_group') or ''
        folder_label = str(folder_label).strip().replace(" ", "")
        return folder_label

    def get_plot_label_for_data(self, data):
        """Compact legend label.

        - Load Shots: '2626'
        - Load Folder: '2626, 20mPa'
        """
        shot = str(data.get('shot_number', 'shot'))
        folder_label = self.get_folder_label_for_data(data)
        return f"{shot}, {folder_label}" if folder_label else shot

    def get_color_for_data(self, data, fallback_index=0):
        """Return the plot color for a shot.

        - Load Shots: original fixed color palette.
        - Load Folder: folder-aware colors, with similar colors inside each folder.
        """
        folder_label = self.get_folder_label_for_data(data)

        if not folder_label:
            return self.color_palette[fallback_index % len(self.color_palette)]

        self._register_folder(folder_label)

        if folder_label not in self.folder_color_state:
            folder_index = self.folder_order.index(folder_label) if folder_label in self.folder_order else 0
            hue = self.folder_base_hues[folder_index % len(self.folder_base_hues)]
            self.folder_color_state[folder_label] = {'hue': hue, 'count': 0}

        state = self.folder_color_state[folder_label]
        k = state['count']
        state['count'] += 1

        # Cycle through lightness/saturation combinations around the same hue.
        lightness_values = [0.38, 0.48, 0.58, 0.30, 0.68, 0.43, 0.53, 0.63]
        saturation_values = [0.85, 0.72, 0.95, 0.65, 0.80, 0.55, 0.90, 0.70]
        lightness = lightness_values[k % len(lightness_values)]
        saturation = saturation_values[k % len(saturation_values)]
        r, g, b = colorsys.hls_to_rgb(state['hue'], lightness, saturation)
        return (r, g, b)

    def update_normalization_status_text(self):
        """
        Writes a small status line in the toolbar area after applying a
        normalization. This confirms that the button changed the plotted data.
        """
        if not self.processed_data:
            self.data_box_label.config(text="")
            return

        if self.normalization_mode == NORMALIZATION_NONE:
            self.data_box_label.config(text="Normalization: none")
            return

        rows = [f"Normalization: {get_normalization_label(self.normalization_mode)}"]
        for d in self.processed_data:
            factor, duration = self.get_ip_normalization_factor_for_data(d)
            if self.normalization_mode == NORMALIZATION_TAU_AREA:
                rows.append(
                    f"{d['shot_number']}: factor usado = ∫Ip+dt = {factor:.6g} C; chequeo: ∫Ip_norm dt = 1; Δt_p = {duration*1000:.4g} ms"
                )
            elif self.normalization_mode == NORMALIZATION_TAU_MAX:
                rows.append(
                    f"{d['shot_number']}: Ip,max_rep = {factor:.6g} A, Δt_p = {duration*1000:.4g} ms"
                )
            elif self.normalization_mode == NORMALIZATION_TAU:
                rows.append(
                    f"{d['shot_number']}: τ active, Δt_p = {duration*1000:.4g} ms"
                )

        self.data_box_label.config(text="\n".join(rows))

    # -----------------------------------------------------
    # DISPLAY DATA
    # -----------------------------------------------------
    def get_display_time_arrays(self, data):
        m = self.normalization_mode
        start_time = data['Ip_start_time']
        end_time = data['Ip_end_time']

        # Bt always keeps its own synchronized/raw time. It is never converted to tau.
        xb, yb = get_normalized_temporal_signal(
            data['Time'], data['B_phi'], data['Ip'], NORMALIZATION_NONE,
            signal_kind="bt", display_mode=self.display_time_mode,
            sync_time=data['Bt_sync_time'], force_tau=False,
            start_time=start_time, end_time=end_time
        )

        # Ip and H-alpha use Ip synchronization and can be converted to tau.
        # The tau end is now the plasma end detected from Ip after its maximum.
        xi, yi = get_normalized_temporal_signal(
            data['Time'], data['Ip'], data['Ip'], m,
            signal_kind="ip", display_mode=self.display_time_mode,
            sync_time=start_time, force_tau=(m != NORMALIZATION_NONE),
            start_time=start_time, end_time=end_time
        )

        xh, yh = get_normalized_temporal_signal(
            data['Time'], data['Photod'], data['Ip'], m,
            signal_kind="halpha", display_mode=self.display_time_mode,
            sync_time=start_time, force_tau=(m != NORMALIZATION_NONE),
            start_time=start_time, end_time=end_time
        )

        # In no-normalization and tau-only modes, Ip is still physically displayed in kA.
        # In tau_max and tau_area, Ip is normalized and must not be divided by 1000.
        if m in [NORMALIZATION_NONE, NORMALIZATION_TAU]:
            yi = yi / 1000

        return xb, yb, xi, yi, xh, yh

    def get_display_spectrum_arrays(self, data):
        tau, plasma_duration, active_mask, tau_active, Ip_active = get_tau_active_and_ip(
            data['Time'],
            data['Ip'],
            start_time=data['Ip_start_time'],
            end_time=data['Ip_end_time']
        )

        time_active = data['Time'][active_mask]

        ip_norm = get_ip_normalization_factor(
            tau_active,
            Ip_active,
            self.normalization_mode,
            time_active=time_active
        )

        return get_normalized_spectrum(
            data['wavelengths_Avantes'],
            data['intensities_Avantes_raw'],
            plasma_duration,
            self.normalization_mode,
            ip_norm
        )

    def plot_data(self):
        self.rebuild_plot_axes()

        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            if ax is not None:
                ax.clear()

        # Remove the single figure-level legend from the previous redraw, if any.
        for legend in list(self.fig.legends):
            try:
                legend.remove()
            except Exception:
                pass

        self._set_axis_labels()

        if not self.processed_data:
            self.connect_xlim_sync_callbacks()
            self.canvas.draw()
            return

        # Recompute folder-aware colors on every redraw so colors stay stable
        # after loading/clearing shots.
        self.folder_color_state = {}
        display_cache = []

        for plot_index, d in enumerate(self.processed_data):
            c = self.get_color_for_data(d, fallback_index=plot_index)
            plot_label = self.get_plot_label_for_data(d)
            xb, yb, xi, yi, xh, yh = self.get_display_time_arrays(d)
            wl, sy = self.get_display_spectrum_arrays(d)

            display_cache.append({
                'data': d,
                'xb': xb,
                'yb': yb,
                'xi': xi,
                'yi': yi,
                'xh': xh,
                'yh': yh,
                'wl': wl,
                'sy': sy,
            })

            self.ax_bt.plot(xb, yb, label=plot_label, color=c)
            self.ax_ip.plot(xi, yi, label=plot_label, color=c)
            self.ax_halpha.plot(xh, yh, label=plot_label, color=c)
            if wl.size > 0 and sy.size > 0 and wl.shape == sy.shape:
                self.ax_avantes.plot(wl, sy, label=plot_label, color=c)

        # Overlay selected local NIST lines only after experimental spectra exist.
        self.plot_selected_nist_lines()

        residual_axes_ready = (
            self.show_residuals
            and self.ax_bt_residual is not None
            and self.ax_ip_residual is not None
            and self.ax_halpha_residual is not None
            and self.ax_avantes_residual is not None
        )

        if residual_axes_ready and len(display_cache) == 2:
            d1 = display_cache[0]
            d2 = display_cache[1]

            self.ax_bt_residual.plot(
                d1['xb'],
                d1['yb'] - np.interp(d1['xb'], d2['xb'], d2['yb']),
                color='red',
                label='Difference'
            )
            self.ax_ip_residual.plot(
                d1['xi'],
                d1['yi'] - np.interp(d1['xi'], d2['xi'], d2['yi']),
                color='red',
                label='Difference'
            )
            self.ax_halpha_residual.plot(
                d1['xh'],
                d1['yh'] - np.interp(d1['xh'], d2['xh'], d2['yh']),
                color='red',
                label='Difference'
            )

            if d1['wl'].size > 0 and d2['wl'].size > 0 and np.array_equal(d1['wl'], d2['wl']):
                self.ax_avantes_residual.plot(
                    d1['wl'],
                    d1['sy'] - d2['sy'],
                    color='red',
                    label='Difference'
                )

            for ax in self.time_residual_axes + self.spec_residual_axes:
                if ax is not None and ax.has_data():
                    ax.axhline(0, color='gray', lw=0.5)

        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            if ax is not None:
                ax.grid(True, linestyle='--', linewidth=0.5)

        # Only one legend is shown for the full comparison figure.
        # It is placed in the upper white band of the figure, not inside any subplot.
        if self.ax_bt.has_data():
            handles, labels = self.ax_bt.get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            legend_labels = list(by_label.keys())
            legend_handles = list(by_label.values())
            uses_folder_labels = any(',' in label for label in legend_labels)
            ncol = min(max(len(legend_labels), 1), 6)
            self.fig.legend(
                legend_handles,
                legend_labels,
                loc='upper center',
                bbox_to_anchor=(0.52, 0.985),
                ncol=ncol,
                fontsize='small',
                title='Shot, folder' if uses_folder_labels else 'Shot',
                frameon=True,
                borderaxespad=0.2
            )

        if self.ax_avantes.has_data():
            self.ax_avantes.set_xlim(350, 1000)
            if self.ax_avantes_residual is not None and self.ax_avantes_residual.has_data():
                self.ax_avantes_residual.set_xlim(350, 1000)
        else:
            self.ax_avantes.text(
                0.5,
                0.5,
                'No spectroscopy data',
                horizontalalignment='center',
                verticalalignment='center',
                transform=self.ax_avantes.transAxes,
                fontsize=10,
                alpha=0.7
            )

        if self.normalization_mode != NORMALIZATION_NONE:
            # Only Ip and H-alpha are in tau. Bt keeps its own time axis.
            for ax in [self.ax_ip, self.ax_ip_residual, self.ax_halpha, self.ax_halpha_residual]:
                if ax is not None:
                    ax.set_xlim(0, 1)

        if self.normalization_mode == NORMALIZATION_TAU_AREA:
            self.ax_ip.set_title("NORMALIZED: Ip_pos(tau) / int(Ip_pos(tau)dtau)")
            self.ax_halpha.set_title("NORMALIZED: H-alpha / int(Ip_pos(tau)dtau)")
            self.ax_avantes.set_title("NORMALIZED: spectrum / (dt_p * int(Ip_pos(tau)dtau))")
            for ax in [self.ax_ip, self.ax_halpha, self.ax_avantes]:
                if ax.has_data():
                    try:
                        ax.ticklabel_format(axis='y', style='sci', scilimits=(-2, 3))
                    except Exception:
                        pass
        else:
            self.ax_ip.set_title("")
            self.ax_halpha.set_title("")
            self.ax_avantes.set_title("")

        self.update_normalization_status_text()
        try:
            self.fig.subplots_adjust(right=0.82)
        except Exception:
            pass
        self.connect_xlim_sync_callbacks()
        self.canvas.draw()

    # -----------------------------------------------------
    # GROUP COMPARISON
    # -----------------------------------------------------
    def generate_group_comparison(self):
        manager = tk.Toplevel(self.app)
        manager.title("Group comparison")
        manager.geometry("900x540")

        groups = []

        tk.Label(
            manager,
            text=(
                "Add one or more shot folders. Each folder is treated as an independent group.\n"
                "If one shot is selected, it is plotted directly. If two or more shots are selected, mean ± std is computed.\n"
                "Synchronization is fixed: Bt with Bt start; Ip and H-alpha with Ip start."
            ),
            justify="left"
        ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        main_frame = tk.Frame(manager)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        group_listbox = tk.Listbox(main_frame, font=("Courier New", 10))
        group_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = tk.Scrollbar(main_frame, command=group_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        group_listbox.config(yscrollcommand=scrollbar.set)

        options_frame = tk.Frame(manager)
        options_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        tk.Label(options_frame, text="Std band factor:").pack(side=tk.LEFT, padx=5)
        band_factor_var = tk.DoubleVar(value=1.0)
        tk.Entry(options_frame, textvariable=band_factor_var, width=6).pack(side=tk.LEFT, padx=5)

        tk.Label(options_frame, text="Ip smoothing [us]:").pack(side=tk.LEFT, padx=5)
        smooth_ip_var = tk.DoubleVar(value=IP_COMPARISON_SMOOTH_US)
        tk.Entry(options_frame, textvariable=smooth_ip_var, width=6).pack(side=tk.LEFT, padx=5)

        tk.Label(options_frame, text="H-alpha smoothing [us]:").pack(side=tk.LEFT, padx=5)
        smooth_ha_var = tk.DoubleVar(value=HALPHA_COMPARISON_SMOOTH_US)
        tk.Entry(options_frame, textvariable=smooth_ha_var, width=6).pack(side=tk.LEFT, padx=5)

        def refresh_group_list():
            group_listbox.delete(0, tk.END)
            for i, group in enumerate(groups):
                group_listbox.insert(
                    tk.END,
                    f"{i + 1}. {group['label']} | {len(group['files'])} selected shot(s)"
                )

        def select_files_for_folder(folder_path):
            nxs_files = sorted(
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if f.lower().endswith(".nxs")
            )

            if not nxs_files:
                messagebox.showinfo("No files", "No .nxs files were found in the selected folder.")
                return None

            selection_window = tk.Toplevel(manager)
            selection_window.title(f"Select shots - {os.path.basename(folder_path)}")
            selection_window.geometry("620x520")

            tk.Label(
                selection_window,
                text="Select the shots to include in this group.",
                justify="left"
            ).pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

            frame_list = tk.Frame(selection_window)
            frame_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            scrollbar_files = tk.Scrollbar(frame_list)
            scrollbar_files.pack(side=tk.RIGHT, fill=tk.Y)

            listbox = tk.Listbox(
                frame_list,
                selectmode=tk.MULTIPLE,
                yscrollcommand=scrollbar_files.set,
                font=("Courier New", 10)
            )
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_files.config(command=listbox.yview)

            for file_path in nxs_files:
                listbox.insert(tk.END, os.path.basename(file_path))

            count_label = tk.Label(selection_window, text="Selected shots: 0")
            count_label.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

            def update_count(event=None):
                count_label.config(text=f"Selected shots: {len(listbox.curselection())}")

            listbox.bind("<<ListboxSelect>>", update_count)

            selected_files = {'files': None}
            button_frame = tk.Frame(selection_window)
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

            def select_all():
                listbox.select_set(0, tk.END)
                update_count()

            def clear_selection():
                listbox.selection_clear(0, tk.END)
                update_count()

            def confirm_selection():
                selected_indices = listbox.curselection()
                if len(selected_indices) < 1:
                    messagebox.showinfo("Insufficient selection", "Select at least one shot for this group.")
                    return
                selected_files['files'] = [nxs_files[i] for i in selected_indices]
                selection_window.destroy()

            tk.Button(button_frame, text="Select all", command=select_all).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Clear", command=clear_selection).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Accept", command=confirm_selection).pack(side=tk.RIGHT, padx=5)
            tk.Button(button_frame, text="Cancel", command=selection_window.destroy).pack(side=tk.RIGHT, padx=5)

            selection_window.wait_window()
            return selected_files['files']

        def add_folder():
            folder_path = filedialog.askdirectory(title="Select folder with .nxs shots")
            if not folder_path:
                return
            selected_files = select_files_for_folder(folder_path)
            if selected_files is None:
                return
            default_label = os.path.basename(folder_path)
            label = simpledialog.askstring(
                "Group name",
                "Name for this group:",
                initialvalue=default_label,
                parent=manager
            )
            if label is None or label.strip() == "":
                label = default_label
            groups.append({'folder_path': folder_path, 'label': label, 'files': selected_files})
            refresh_group_list()

        def remove_selected_group():
            selected = group_listbox.curselection()
            if not selected:
                return
            del groups[selected[0]]
            refresh_group_list()

        def generate_plot():
            if not groups:
                messagebox.showinfo("No groups", "Add at least one folder.")
                return

            try:
                band_factor = float(band_factor_var.get())
                smooth_ip_us = float(smooth_ip_var.get())
                smooth_halpha_us = float(smooth_ha_var.get())
            except Exception:
                messagebox.showerror("Error", "Check that numerical parameters are valid.")
                return

            all_results = []
            failed_files = []

            for group in groups:
                selected_data = []
                for file_path in group['files']:
                    data = process_shot_data(file_path, save_to_csv=False)
                    if data is not None:
                        selected_data.append(data)
                    else:
                        failed_files.append(os.path.basename(file_path))

                if len(selected_data) < 1:
                    messagebox.showwarning("Skipped group", f"Group {group['label']} has no valid shots.")
                    continue

                result = compute_group_average_variability(
                    selected_data,
                    band_factor=band_factor,
                    smooth_ip_us=smooth_ip_us,
                    smooth_halpha_us=smooth_halpha_us,
                    smooth_bt_us=0,
                    group_label=group['label']
                )
                if result is not None:
                    all_results.append(result)

            if not all_results:
                messagebox.showerror("Error", "No valid group could be generated.")
                return

            self.last_multi_group_comparison = all_results
            self.plot_multi_group_comparison(all_results)

            if failed_files:
                messagebox.showwarning(
                    "Warning",
                    "Some files could not be processed:\n" + "\n".join(failed_files)
                )

        button_frame = tk.Frame(manager)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        tk.Button(button_frame, text="Add folder", command=add_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove group", command=remove_selected_group).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Generate plot", command=generate_plot).pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Close", command=manager.destroy).pack(side=tk.RIGHT, padx=5)

    def connect_multi_axis_xlim_sync(self, fig, canvas, axes):
        """
        Synchronize zoom/pan x-limits across all axes in a comparison figure.
        This is used by Generate comparison.
        """
        sync_state = {"active": False}
        axes = [ax for ax in axes if ax is not None]

        def on_xlim_changed(source_ax):
            if sync_state["active"]:
                return
            try:
                xlim = source_ax.get_xlim()
            except Exception:
                return

            sync_state["active"] = True
            try:
                for ax in axes:
                    if ax is source_ax:
                        continue
                    ax.set_xlim(xlim, emit=False)
                canvas.draw_idle()
            finally:
                sync_state["active"] = False

        for ax in axes:
            ax.callbacks.connect("xlim_changed", on_xlim_changed)


    def plot_multi_group_comparison(self, results):
        win = tk.Toplevel(self.app)
        win.title("Pressure group comparison")
        win.geometry("1200x900")

        fig = Figure(figsize=(11, 8), facecolor='white')
        ax_bt = fig.add_subplot(3, 1, 1)
        ax_ip = fig.add_subplot(3, 1, 2)
        ax_ha = fig.add_subplot(3, 1, 3)

        color_cycle = itertools.cycle(self.color_palette)

        for result in results:
            color = next(color_cycle)
            label = result['group_label']
            band_factor = result['band_factor']
            n_shots = result['n_shots']
            is_single = result.get('is_single_shot', False)

            if is_single:
                label_mean = f"{label} | 1 shot"
                label_band = None
            else:
                label_mean = f"{label} mean | N={n_shots}"
                label_band = f"{label} ± {band_factor:g} std"

            t_bt_ms = result['ref_time_bt'] * 1000
            t_ip_ms = result['ref_time_ip'] * 1000

            ax_bt.plot(t_bt_ms, result['Bt_mean'], color=color, label=label_mean)
            ax_ip.plot(t_ip_ms, result['Ip_mean'] / 1000, color=color, label=label_mean)
            ax_ha.plot(t_ip_ms, result['Ha_mean'], color=color, label=label_mean)

            if not is_single:
                ax_bt.fill_between(t_bt_ms, result['Bt_lower'], result['Bt_upper'], color=color, alpha=0.18, label=label_band)
                ax_ip.fill_between(t_ip_ms, result['Ip_lower'] / 1000, result['Ip_upper'] / 1000, color=color, alpha=0.18, label=label_band)
                ax_ha.fill_between(t_ip_ms, result['Ha_lower'], result['Ha_upper'], color=color, alpha=0.18, label=label_band)

        ax_bt.set_ylabel("Bt [mT]")
        ax_bt.set_xlabel("Time synchronized with Bt start [ms]")
        ax_ip.set_ylabel("Ip [kA]")
        ax_ip.set_xlabel("Time synchronized with Ip start [ms]")
        ax_ha.set_ylabel("H-alpha [a.u.]")
        ax_ha.set_xlabel("Time synchronized with Ip start [ms]")

        for ax in [ax_bt, ax_ip, ax_ha]:
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.legend(loc='best', fontsize='small')

        smooth_ip_us = results[0]['smooth_ip_us']
        smooth_halpha_us = results[0]['smooth_halpha_us']
        band_factor = results[0]['band_factor']
        fig.suptitle(
            (
                "Group comparison\n"
                f"If N >= 2: band = mean ± {band_factor:g} std | "
                f"Ip smoothing = {smooth_ip_us:g} us | "
                f"H-alpha smoothing = {smooth_halpha_us:g} us"
            ),
            fontsize=11
        )
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas_widget = canvas.get_tk_widget()
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        def export_multi_group_comparison():
            path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
            if not path:
                return
            try:
                export_tables = []
                summary_rows = []
                for result in results:
                    group_label = result['group_label']
                    sheet_name = group_label.replace("/", "_").replace("\\", "_").replace(":", "_")[:31]
                    export_tables.append((sheet_name, result['df_group']))
                    summary_rows.append({
                        'group': group_label,
                        'n_shots': result['n_shots'],
                        'is_single_shot': result.get('is_single_shot', False),
                        'shots': ", ".join(result['shot_numbers']),
                        'band_factor': result['band_factor'],
                        'smooth_ip_us': result['smooth_ip_us'],
                        'smooth_halpha_us': result['smooth_halpha_us'],
                        'smooth_bt_us': result['smooth_bt_us']
                    })

                export_tables.append(("summary", pd.DataFrame(summary_rows)))
                saved_path, mode = save_workbook_with_openpyxl_fallback(path, export_tables)

                if mode == "csv_folder":
                    messagebox.showinfo(
                        "Exported as CSV files",
                        "openpyxl is not installed, so the comparison was exported as CSV files in:\n"
                        f"{saved_path}"
                    )
                else:
                    messagebox.showinfo("Exported", "Group comparison exported successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(toolbar, text="Export comparison", command=export_multi_group_comparison).pack(side=tk.LEFT, padx=10)
        self.connect_multi_axis_xlim_sync(fig, canvas, [ax_bt, ax_ip, ax_ha])
        canvas.draw()

    # -----------------------------------------------------
    # REPRODUCIBILITY AND EXPORTS
    # -----------------------------------------------------
    def compute_reproducibility_gui(self):
        res = compute_reproducibility(self.processed_data)
        if res is None:
            return messagebox.showinfo("Error", "Need at least 2 shots.")

        df_time, df_global, df_delays, df_covariance = res
        win = tk.Toplevel(self.app)
        win.title("Reproducibility analysis")
        win.geometry("1200x650")
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True)

        tables = [
            ("Time-resolved", df_time),
            ("Global metrics", df_global),
            ("Timing delays", df_delays),
            ("Covariance/correlation", df_covariance),
        ]

        for tab_name, df in tables:
            frame = tk.Frame(notebook)
            notebook.add(frame, text=tab_name)

            tree = ttk.Treeview(frame)
            tree.pack(fill=tk.BOTH, expand=True)
            tree["columns"] = list(df.columns)
            tree["show"] = "headings"

            for col in df.columns:
                tree.heading(col, text=col)
                tree.column(col, width=140)

            for _, row in df.iterrows():
                values = [f"{v:.6g}" if isinstance(v, (float, np.floating)) else v for v in row]
                tree.insert("", tk.END, values=values)

    def export_full_analysis(self):
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")

        path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        try:
            tables = compute_all_analysis_tables(self.processed_data)
            saved_path, mode = save_workbook_with_openpyxl_fallback(path, tables)

            if mode == "csv_folder":
                messagebox.showinfo(
                    "Exported as CSV files",
                    "openpyxl is not installed, so the analysis was exported as CSV files in:\n"
                    f"{saved_path}"
                )
            else:
                messagebox.showinfo("Success", "Full analysis exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
