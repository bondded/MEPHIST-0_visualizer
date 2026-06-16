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
NIST_MATCH_TOLERANCE_NM = 0.60
NIST_MIN_RELATIVE_PEAK_HEIGHT = 0.03
NIST_NOISE_SIGMA_FACTOR = 5.0
NIST_LOCAL_BACKGROUND_WINDOW_NM = 2.0
NIST_MIN_PROMINENCE_RELATIVE = 0.01

# Spectroscopy calibration and robust peak/feature matching.
# Balmer wavelengths are used only for an optional calibration step; matching
# can still be performed without calibration. Wavelengths are in air [nm].
HYDROGEN_BALMER_LINES_NM = [
    ("H_alpha", 656.2790),
    ("H_beta", 486.1350),
    ("H_gamma", 434.0472),
    ("H_delta", 410.1734),
    ("H_epsilon", 397.0075),
    ("H_zeta", 388.9064),
]
SPECTROSCOPY_CALIBRATION_SEARCH_WINDOW_NM = 1.5
SPECTROSCOPY_CALIBRATION_DEFAULT_DEGREE = 2
SPECTROSCOPY_FEATURE_MERGE_NM = 0.55
SPECTROSCOPY_MIN_FEATURE_WIDTH_POINTS = 2

# Balmer lines are physically privileged for H discharges. Fe has a very dense
# visible spectrum and can otherwise steal broad/plateau-like Balmer features.
# These constants only affect known H Balmer transitions and keep NIST intensity
# as secondary information.
SPECTROSCOPY_BALMER_MATCH_TOLERANCE_NM = 0.60
SPECTROSCOPY_BALMER_PRIORITY_BOOST = 0.65
SPECTROSCOPY_DEFAULT_SHOW_ONLY_GLOBAL_BEST = True

# Instrument-resolution exclusion rule for final accepted lines.
# After calibration, accepted H Balmer anchors are kept fixed and every accepted
# line blocks +/- this half-width in NIST wavelength space. This avoids assigning
# several "best" global lines inside one unresolved instrumental-resolution band.
SPECTROSCOPY_ACCEPTED_LINE_EXCLUSION_HALF_WIDTH_NM = 0.60

# Physical priors used only as a weak tie-breaker in ambiguous multi-element
# assignments. Nitrogen is intentionally above oxygen because residual air is
# mostly N2; carbon is kept as a low-priority contaminant unless the data strongly
# supports it. These values are not probabilities, only ranking weights.
SPECTROSCOPY_ELEMENT_PRIOR = {
    "H": 1.00,
    "Fe": 0.86,
    "W": 0.82,
    "N": 0.58,
    "O": 0.48,
    "C": 0.34,
    "Ar": 0.25,
    "He": 0.25,
}
SPECTROSCOPY_ELEMENT_PRIOR_WEIGHT = 0.12
# No density penalty is applied: if Fe has many lines, that is physical/diagnostic
# information rather than something to suppress. The column can still be exported
# for diagnostics, but its weight is zero.
SPECTROSCOPY_LINE_DENSITY_PENALTY_WEIGHT = 0.0

# Temporal H-alpha is kept as diagnostic support for spectroscopy. It is not used
# as a hard absolute threshold by default because the photodiode H-alpha signal and
# the Avantes spectrum are in different arbitrary units. The table exports the
# integral, duration and mean over the real H-alpha window so you can correlate
# line identifications with temporal H-alpha strength.
SPECTROSCOPY_USE_HALPHA_TEMPORAL_SUPPORT_FILTER = False
SPECTROSCOPY_HALPHA_TEMPORAL_MIN_MEAN = 0.0



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


def normalize_01(values):
    """Return values scaled to [0, 1] while keeping NaNs as 0."""
    arr = pd.to_numeric(pd.Series(values), errors="coerce").astype(float)
    arr = arr.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    vmin = float(arr.min()) if len(arr) else 0.0
    vmax = float(arr.max()) if len(arr) else 0.0
    if not np.isfinite(vmax - vmin) or abs(vmax - vmin) < 1e-15:
        return np.zeros(len(arr), dtype=float)
    return ((arr - vmin) / (vmax - vmin)).to_numpy(dtype=float)


def apply_wavelength_calibration(wavelengths, coefficients):
    """Apply polynomial calibration lambda_true = poly(lambda_measured)."""
    wl = np.asarray(wavelengths, dtype=float)
    if coefficients is None:
        return wl
    try:
        coeffs = np.asarray(coefficients, dtype=float)
    except Exception:
        return wl
    if coeffs.size == 0 or not np.all(np.isfinite(coeffs)):
        return wl
    return np.polyval(coeffs, wl)



def get_hydrogen_balmer_match(wavelength_nm, tolerance_nm=0.08):
    """Return (name, lambda_nist, distance) for a known Balmer line, or None."""
    try:
        lam = float(wavelength_nm)
    except Exception:
        return None
    if not np.isfinite(lam):
        return None
    best = None
    for name, lam0 in HYDROGEN_BALMER_LINES_NM:
        d = abs(lam - float(lam0))
        if d <= tolerance_nm and (best is None or d < best[2]):
            best = (name, float(lam0), float(d))
    return best


def is_hydrogen_balmer_candidate(element_label, wavelength_nm):
    """True only for H candidates that correspond to one of the Balmer lines."""
    if str(element_label).strip().lower() not in {"h", "h i", "hi", "hydrogen"}:
        return False
    return get_hydrogen_balmer_match(wavelength_nm) is not None


def get_match_tolerance_for_candidate(element_label, wavelength_nm, base_tolerance_nm):
    """Use a slightly wider matching window only for known H Balmer lines."""
    if is_hydrogen_balmer_candidate(element_label, wavelength_nm):
        return max(float(base_tolerance_nm), float(SPECTROSCOPY_BALMER_MATCH_TOLERANCE_NM))
    return float(base_tolerance_nm)


def normalize_element_label(element_label):
    """Normalize element labels from local NIST filenames/tables."""
    s = str(element_label).strip()
    if not s:
        return ""
    # Keep only the leading chemical symbol, e.g. 'Fe I' -> 'Fe'.
    m = re.match(r"([A-Za-z]{1,2})", s)
    if not m:
        return s
    sym = m.group(1)
    return sym[0].upper() + sym[1:].lower()


def get_element_prior_score(element_label):
    """Weak physical prior used only for ambiguous feature assignment."""
    sym = normalize_element_label(element_label)
    return float(SPECTROSCOPY_ELEMENT_PRIOR.get(sym, 0.30))


def get_halpha_temporal_support_metrics(data):
    """Return H-alpha temporal metrics over its own emission window.

    This uses Halpha_start_5pct -> Halpha_end, not the full Ip plasma duration.
    The result is diagnostic support for spectroscopy, not an absolute cross-device
    intensity calibration.
    """
    try:
        m = compute_halpha_integral_metrics(data)
    except Exception:
        m = None
    if not m:
        return {
            "halpha_temporal_integral_real_time_positive": np.nan,
            "halpha_temporal_duration_s_real_window": np.nan,
            "halpha_temporal_mean_real_window": np.nan,
            "halpha_temporal_start_ms": np.nan,
            "halpha_temporal_end_ms": np.nan,
        }
    duration_ms = m.get("Halpha_real_duration_ms_5pct_to_end", np.nan)
    duration_s = duration_ms / 1000.0 if np.isfinite(duration_ms) else np.nan
    integral = m.get("Halpha_integral_real_time_positive", np.nan)
    mean_val = integral / duration_s if np.isfinite(integral) and np.isfinite(duration_s) and duration_s > 0 else np.nan
    return {
        "halpha_temporal_integral_real_time_positive": integral,
        "halpha_temporal_duration_s_real_window": duration_s,
        "halpha_temporal_mean_real_window": mean_val,
        "halpha_temporal_start_ms": m.get("Halpha_start_5pct_ms", np.nan),
        "halpha_temporal_end_ms": m.get("Halpha_end_ms", np.nan),
    }


def estimate_local_spectral_center(
    wavelengths,
    intensities,
    line_center_nm,
    window_nm=NIST_MATCH_TOLERANCE_NM,
    background_window_nm=NIST_LOCAL_BACKGROUND_WINDOW_NM,
    raw_wavelengths=None,
):
    """
    Estimate a robust experimental wavelength for a candidate line.

    Instead of taking only the single highest sample, this computes a centroid
    of the positive signal above a local background inside the matching window.
    This reduces the bias introduced when a physical line is sampled by several
    spectrometer pixels or appears as a small plateau.
    """
    wl = np.asarray(wavelengths, dtype=float)
    y = np.asarray(intensities, dtype=float)
    raw_wl = np.asarray(raw_wavelengths, dtype=float) if raw_wavelengths is not None else wl.copy()
    if raw_wl.shape != wl.shape:
        raw_wl = wl.copy()

    mask = np.isfinite(wl) & np.isfinite(y) & np.isfinite(raw_wl) & (np.abs(wl - line_center_nm) <= window_nm)
    if np.sum(mask) < 1:
        return None

    local_wl = wl[mask]
    local_raw_wl = raw_wl[mask]
    local_y = y[mask]
    if local_wl.size == 0:
        return None

    bg_mask = (
        np.isfinite(wl) & np.isfinite(y)
        & (wl >= line_center_nm - background_window_nm)
        & (wl <= line_center_nm + background_window_nm)
        & (np.abs(wl - line_center_nm) > window_nm)
    )
    if np.any(bg_mask):
        local_background = float(np.nanmedian(y[bg_mask]))
    else:
        local_background = float(np.nanmedian(y[np.isfinite(y)])) if np.any(np.isfinite(y)) else 0.0

    weights = positive_part(local_y - local_background)
    peak_pos = int(np.nanargmax(local_y))
    peak_wl = float(local_wl[peak_pos])
    peak_intensity = float(local_y[peak_pos])

    if np.sum(weights) > 0:
        centroid_wl = float(np.sum(local_wl * weights) / np.sum(weights))
        centroid_raw_wl = float(np.sum(local_raw_wl * weights) / np.sum(weights))
    else:
        centroid_wl = peak_wl
        centroid_raw_wl = float(local_raw_wl[peak_pos])

    local_excess = peak_intensity - local_background
    local_integral = safe_area(local_wl, weights)
    local_mean = float(np.nanmean(local_y)) if local_y.size else np.nan
    width_nm = float(np.nanmax(local_wl) - np.nanmin(local_wl)) if local_wl.size > 1 else 0.0

    return {
        "center_nm": centroid_wl,
        "raw_center_nm": centroid_raw_wl,
        "peak_wavelength_nm": peak_wl,
        "raw_peak_wavelength_nm": float(local_raw_wl[peak_pos]),
        "peak_intensity": peak_intensity,
        "local_background": local_background,
        "local_excess": local_excess,
        "local_integrated_intensity": local_integral,
        "local_mean_intensity": local_mean,
        "window_width_nm": width_nm,
        "n_points_in_window": int(local_wl.size),
    }


def detect_spectrum_features(
    wavelengths,
    intensities,
    min_relative_peak_height=NIST_MIN_RELATIVE_PEAK_HEIGHT,
    noise_sigma_factor=NIST_NOISE_SIGMA_FACTOR,
    merge_nm=SPECTROSCOPY_FEATURE_MERGE_NM,
):
    """
    Detect experimental spectral features before assigning elements.

    A feature is a contiguous significant region of the experimental spectrum.
    This prevents many adjacent spectrometer samples on the same broad line or
    plateau from being interpreted as many independent physical lines.
    """
    wl = np.asarray(wavelengths, dtype=float)
    y = np.asarray(intensities, dtype=float)

    # This detector only needs the wavelength axis currently used for matching
    # (raw if uncalibrated, calibrated if calibration is enabled). A previous
    # draft accidentally referenced raw_wl here without defining it, which broke
    # the spectroscopy buttons at runtime.
    finite = np.isfinite(wl) & np.isfinite(y)
    wl = wl[finite]
    y = y[finite]

    if wl.size < 3:
        return pd.DataFrame()

    order = np.argsort(wl)
    wl = wl[order]
    y = y[order]

    y_max = float(np.nanmax(y))
    if not np.isfinite(y_max) or y_max <= 0:
        return pd.DataFrame()

    baseline, sigma = robust_noise_level(y)
    threshold = max(baseline + noise_sigma_factor * sigma, min_relative_peak_height * y_max)
    above = y >= threshold

    features = []
    i = 0
    feature_id = 0
    n = len(wl)

    while i < n:
        if not above[i]:
            i += 1
            continue

        start_idx = i
        last_idx = i
        i += 1
        while i < n and above[i] and (wl[i] - wl[last_idx] <= max(merge_nm, 1e-12)):
            last_idx = i
            i += 1

        end_idx = last_idx
        if end_idx - start_idx + 1 < SPECTROSCOPY_MIN_FEATURE_WIDTH_POINTS:
            # Keep very narrow but very strong isolated samples; otherwise skip.
            if y[start_idx] < 0.25 * y_max:
                continue

        region_wl = wl[start_idx:end_idx + 1]
        region_y = y[start_idx:end_idx + 1]
        peak_local = int(np.nanargmax(region_y))
        peak_idx = start_idx + peak_local
        peak_wl = float(wl[peak_idx])
        peak_intensity = float(y[peak_idx])

        ring_mask = (
            (wl >= region_wl[0] - NIST_LOCAL_BACKGROUND_WINDOW_NM)
            & (wl <= region_wl[-1] + NIST_LOCAL_BACKGROUND_WINDOW_NM)
            & ((wl < region_wl[0]) | (wl > region_wl[-1]))
        )
        if np.any(ring_mask):
            local_background = float(np.nanmedian(y[ring_mask]))
        else:
            local_background = baseline

        weights = positive_part(region_y - local_background)
        if np.sum(weights) > 0:
            center_nm = float(np.sum(region_wl * weights) / np.sum(weights))
        else:
            center_nm = peak_wl

        local_excess = peak_intensity - local_background
        feature_width_nm = float(region_wl[-1] - region_wl[0]) if len(region_wl) > 1 else 0.0

        features.append({
            "experimental_feature_id": feature_id,
            "feature_center_nm": center_nm,
            "feature_peak_wavelength_nm": peak_wl,
            "feature_peak_intensity": peak_intensity,
            "feature_start_nm": float(region_wl[0]),
            "feature_end_nm": float(region_wl[-1]),
            "feature_width_nm": feature_width_nm,
            "feature_start_index": int(start_idx),
            "feature_end_index": int(end_idx),
            "feature_background": local_background,
            "feature_excess": local_excess,
            "feature_integrated_intensity": safe_area(region_wl, positive_part(region_y - local_background)),
            "feature_n_points": int(len(region_wl)),
            "feature_relative_intensity": peak_intensity / y_max if y_max > 0 else np.nan,
        })
        feature_id += 1

    return pd.DataFrame(features)


def assign_feature_to_candidate(features_df, experimental_wavelength_nm, nist_wavelength_nm, tolerance_nm):
    """Assign a candidate to an already detected experimental spectral feature."""
    if features_df is None or features_df.empty:
        bin_width = max(tolerance_nm / 2.0, 1e-9)
        return {
            "experimental_feature_id": int(np.round(experimental_wavelength_nm / bin_width)),
            "feature_center_nm": experimental_wavelength_nm,
            "feature_peak_wavelength_nm": experimental_wavelength_nm,
            "feature_start_nm": experimental_wavelength_nm,
            "feature_end_nm": experimental_wavelength_nm,
            "feature_width_nm": 0.0,
            "feature_n_points": 1,
        }

    f = features_df.copy()
    overlaps = f[
        (f["feature_start_nm"] <= nist_wavelength_nm + tolerance_nm)
        & (f["feature_end_nm"] >= nist_wavelength_nm - tolerance_nm)
    ].copy()

    if overlaps.empty:
        overlaps = f.copy()

    overlaps["distance_to_candidate"] = np.minimum(
        np.abs(overlaps["feature_center_nm"].astype(float) - experimental_wavelength_nm),
        np.abs(overlaps["feature_peak_wavelength_nm"].astype(float) - experimental_wavelength_nm),
    )
    best = overlaps.sort_values("distance_to_candidate").iloc[0]
    return best.to_dict()


def match_nist_lines_for_shot(
    wavelengths_exp,
    intensity_exp,
    nist_df,
    element_label,
    shot_number,
    wavelengths_raw=None,
    tolerance_nm=NIST_MATCH_TOLERANCE_NM,
    min_relative_peak_height=NIST_MIN_RELATIVE_PEAK_HEIGHT,
    noise_sigma_factor=NIST_NOISE_SIGMA_FACTOR,
    local_background_window_nm=NIST_LOCAL_BACKGROUND_WINDOW_NM,
    min_prominence_relative=NIST_MIN_PROMINENCE_RELATIVE,
):
    """
    Build candidate NIST-element matches for one shot and one element file.

    Key changes relative to the older pointwise matcher:
      - experimental spectral features are detected before element assignment;
      - each NIST line is matched to a robust centroid/peak within its tolerance
        window, instead of blindly using every high sample as a separate line;
      - NIST relative intensity is stored but is not the main physical ranking
        criterion across different elements.
    """
    wl = np.asarray(wavelengths_exp, dtype=float)
    y = np.asarray(intensity_exp, dtype=float)
    raw_wl = np.asarray(wavelengths_raw, dtype=float) if wavelengths_raw is not None else wl.copy()

    if wl.size == 0 or y.size == 0 or wl.shape != y.shape or raw_wl.shape != wl.shape or nist_df is None or len(nist_df) == 0:
        return pd.DataFrame()

    finite = np.isfinite(wl) & np.isfinite(y) & np.isfinite(raw_wl)
    wl = wl[finite]
    raw_wl = raw_wl[finite]
    y = y[finite]
    if wl.size < 3:
        return pd.DataFrame()

    order = np.argsort(wl)
    wl = wl[order]
    raw_wl = raw_wl[order]
    y = y[order]

    y_max = float(np.nanmax(y))
    if not np.isfinite(y_max) or y_max <= 0:
        return pd.DataFrame()

    baseline, noise_sigma = robust_noise_level(y)
    absolute_threshold = max(
        baseline + noise_sigma_factor * noise_sigma,
        min_relative_peak_height * y_max,
    )
    min_local_excess = max(
        noise_sigma_factor * noise_sigma,
        min_prominence_relative * y_max,
    )

    features_df = detect_spectrum_features(
        wl,
        y,
        min_relative_peak_height=min_relative_peak_height,
        noise_sigma_factor=noise_sigma_factor,
        merge_nm=max(tolerance_nm * 0.55, SPECTROSCOPY_FEATURE_MERGE_NM),
    )

    nist_intensity_col = None
    for candidate in ['intens', 'Intensity', 'Rel.', 'rel_intensity']:
        if candidate in nist_df.columns:
            nist_intensity_col = candidate
            break

    source_file = str(nist_df['source_file'].iloc[0]) if 'source_file' in nist_df.columns and len(nist_df) else ''
    lambda_source = str(nist_df['lambda_source'].iloc[0]) if 'lambda_source' in nist_df.columns and len(nist_df) else ''
    try:
        nist_lambda_array = pd.to_numeric(nist_df.get('lambda_nm', pd.Series(dtype=float)), errors='coerce').dropna().to_numpy(dtype=float)
    except Exception:
        nist_lambda_array = np.array([], dtype=float)

    rows = []
    for _, line in nist_df.iterrows():
        lam_nist = float(line.get('lambda_nm', np.nan))
        if not np.isfinite(lam_nist):
            continue

        is_balmer = is_hydrogen_balmer_candidate(element_label, lam_nist)
        balmer_info = get_hydrogen_balmer_match(lam_nist) if is_balmer else None
        local_tolerance_nm = get_match_tolerance_for_candidate(
            element_label,
            lam_nist,
            tolerance_nm
        )

        local = estimate_local_spectral_center(
            wl,
            y,
            lam_nist,
            window_nm=local_tolerance_nm,
            background_window_nm=local_background_window_nm,
            raw_wavelengths=raw_wl,
        )
        if local is None:
            continue

        best_intensity = float(local["peak_intensity"])
        if best_intensity < absolute_threshold:
            continue

        rel_height = best_intensity / y_max if y_max > 0 else np.nan
        if rel_height < min_relative_peak_height:
            continue

        if float(local["local_excess"]) < min_local_excess:
            continue

        exp_wl = float(local["center_nm"])
        exp_raw_wl = float(local.get("raw_center_nm", exp_wl))
        delta_nm = exp_wl - lam_nist
        feature = assign_feature_to_candidate(features_df, exp_wl, lam_nist, local_tolerance_nm)

        local_line_density = int(np.sum(np.abs(nist_lambda_array - lam_nist) <= local_tolerance_nm)) if nist_lambda_array.size else 1

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
            'experimental_wavelength_nm': exp_wl,
            'experimental_raw_wavelength_nm': exp_raw_wl,
            'experimental_calibrated_wavelength_nm': exp_wl,
            'experimental_peak_wavelength_nm': float(local["peak_wavelength_nm"]),
            'experimental_raw_peak_wavelength_nm': float(local.get("raw_peak_wavelength_nm", local["peak_wavelength_nm"])),
            'delta_nm': delta_nm,
            'relative_intensity_in_shot': rel_height,
            'local_background': float(local["local_background"]),
            'local_excess': float(local["local_excess"]),
            'local_mean_intensity': float(local["local_mean_intensity"]),
            'local_integrated_intensity': float(local["local_integrated_intensity"]),
            'n_points_in_matching_window': int(local["n_points_in_window"]),
            'matching_window_width_nm': float(local["window_width_nm"]),
            'match_tolerance_used_nm': float(local_tolerance_nm),
            'nist_local_line_density': local_line_density,
            'element_prior_score': get_element_prior_score(element_label),
            'is_hydrogen_balmer': bool(is_balmer),
            'hydrogen_balmer_name': balmer_info[0] if balmer_info is not None else "",
            'hydrogen_balmer_nist_nm': balmer_info[1] if balmer_info is not None else np.nan,
            'hydrogen_balmer_priority_boost': float(SPECTROSCOPY_BALMER_PRIORITY_BOOST) if is_balmer else 0.0,
            'nist_relative_intensity': nist_intensity,
            'nist_relative_intensity_numeric': nist_intensity_numeric,
            'source_file': source_file,
            'wavelength_source': lambda_source,
            'matching_method': 'feature_centroid_window_experimental_first',
            'experimental_feature_id': feature.get('experimental_feature_id', np.nan),
            'feature_center_nm': feature.get('feature_center_nm', np.nan),
            'feature_peak_wavelength_nm': feature.get('feature_peak_wavelength_nm', np.nan),
            'feature_start_nm': feature.get('feature_start_nm', np.nan),
            'feature_end_nm': feature.get('feature_end_nm', np.nan),
            'feature_width_nm': feature.get('feature_width_nm', np.nan),
            'feature_n_points': feature.get('feature_n_points', np.nan),
        })

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows)
    out['abs_delta_nm'] = out['delta_nm'].abs()
    tol_for_score = pd.to_numeric(
        out.get('match_tolerance_used_nm', tolerance_nm),
        errors='coerce'
    ).fillna(float(tolerance_nm)).astype(float).clip(lower=1e-12)
    out['proximity_score'] = np.clip(
        1.0 - out['abs_delta_nm'].astype(float) / tol_for_score,
        0.0,
        1.0,
    )
    out['nist_intensity_for_score'] = pd.to_numeric(
        out.get('nist_relative_intensity_numeric', np.nan),
        errors='coerce'
    ).fillna(0.0)
    out['nist_log_for_score'] = np.log10(out['nist_intensity_for_score'].clip(lower=0.0) + 1.0)
    out['nist_score_norm'] = normalize_01(out['nist_log_for_score'])
    out['experimental_score_norm'] = normalize_01(out['local_excess'])
    out['element_prior_score'] = pd.to_numeric(
        out.get('element_prior_score', 0.30), errors='coerce'
    ).fillna(0.30).astype(float)
    density = pd.to_numeric(out.get('nist_local_line_density', 1), errors='coerce').fillna(1.0).astype(float).clip(lower=1.0)
    out['line_density_penalty_score'] = normalize_01(np.log1p(density))
    balmer_boost = pd.to_numeric(
        out.get('hydrogen_balmer_priority_boost', 0.0),
        errors='coerce'
    ).fillna(0.0).astype(float)
    out['candidate_score'] = (
        0.55 * out['proximity_score'].astype(float)
        + 0.25 * out['experimental_score_norm'].astype(float)
        + 0.08 * out['nist_score_norm'].astype(float)
        + SPECTROSCOPY_ELEMENT_PRIOR_WEIGHT * out['element_prior_score'].astype(float)
        + balmer_boost
    )

    # Deduplicate only within the same element/file/experimental feature. Keep
    # the most plausible transition for that element. Cross-element alternatives
    # are preserved and marked later as best/secondary candidates.
    feature_key_col = 'experimental_feature_id'
    out = (
        out.sort_values(
            ['shot', 'type of element', 'source_file', feature_key_col, 'candidate_score', 'abs_delta_nm', 'intensity'],
            ascending=[True, True, True, True, False, True, False]
        )
        .drop_duplicates(
            subset=['shot', 'type of element', 'source_file', feature_key_col],
            keep='first'
        )
        .reset_index(drop=True)
    )
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
        # Show/export only the first N experimental spectral features per shot.
        # All local NIST files are matched first. Toggle selected only filters
        # precomputed candidates; it does not recompute ownership after selection.
        self.nist_display_max_lines = 10
        self.nist_all_matches_cache = None
        self.nist_all_matches_cache_key = None
        self.nist_all_candidates_cache = None

        # Optional wavelength calibration from hydrogen Balmer lines. Coefficients
        # are stored per loaded shot in data['spectroscopy_calibration_coefficients'].
        self.spectroscopy_calibration_enabled = False
        self.spectroscopy_calibration_degree = SPECTROSCOPY_CALIBRATION_DEFAULT_DEGREE
        self.spectroscopy_calibration_window_nm = SPECTROSCOPY_CALIBRATION_SEARCH_WINDOW_NM
        self.spectroscopy_last_calibration_table = pd.DataFrame()
        self.nist_show_candidate_alternatives = False

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

        def show_best_matches():
            if not read_params():
                return
            df = self.compute_spectroscopy_best_global_table()
            if df.empty:
                messagebox.showinfo(
                    "No best matched lines",
                    "No accepted global-best NIST lines were found for the selected elements/files.\n"
                    "Try selecting more elements, increasing the tolerance, or reducing the intensity threshold."
                )
                return
            self.show_dataframe_window(
                df,
                title="Best global spectroscopy matches",
                default_filename_base="matched_spectroscopy_best_global",
                plot_callback=self.show_matched_spectroscopy_figure
            )

        def show_candidate_matches():
            if not read_params():
                return
            df = self.compute_spectroscopy_candidate_table()
            if df.empty:
                messagebox.showinfo(
                    "No candidate lines",
                    "No candidate NIST lines were found for the selected elements/files.\n"
                    "Try selecting an element, increasing the tolerance, or reducing the intensity threshold."
                )
                return
            self.show_dataframe_window(
                df,
                title="All spectroscopy candidates by experimental feature",
                default_filename_base="matched_spectroscopy_all_candidates"
            )

        def run_gui_action(action):
            try:
                action()
            except Exception as exc:
                messagebox.showerror(
                    "Spectroscopy tool error",
                    f"The requested spectroscopy action failed:\n{exc}\n\n"
                    "Check the terminal for the full traceback."
                )
                traceback.print_exc()

        def update_displayed_line_limit():
            if read_params():
                self.plot_data()

        def calibrate_now():
            if read_params():
                self.calibrate_spectroscopy_gui()

        tk.Button(btn_frame, text="Toggle selected", command=lambda: run_gui_action(toggle_selected)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Apply filter", command=lambda: run_gui_action(apply_filter)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear filter", command=lambda: run_gui_action(clear_filter)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show available files", command=lambda: run_gui_action(show_available_files)).pack(side=tk.LEFT, padx=5)

        # Max lines/shot shown controls the top-N experimental features shown per shot.
        # Apply/redraw top N only refreshes the display after editing that number.
        tk.Button(btn_frame, text="Apply/redraw top N", command=lambda: run_gui_action(update_displayed_line_limit)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Calibrate spectroscopy", command=lambda: run_gui_action(calibrate_now)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Show best global table", command=lambda: run_gui_action(show_best_matches)).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Show all candidates table", command=lambda: run_gui_action(show_candidate_matches)).pack(side=tk.RIGHT, padx=5)

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
        calibration_key = tuple(
            (
                str(d.get('shot_number', '')),
                bool(d.get('spectroscopy_calibration_enabled', False)),
                tuple(np.asarray(d.get('spectroscopy_calibration_coefficients', []), dtype=float).round(10))
                if d.get('spectroscopy_calibration_coefficients', None) is not None else tuple(),
            )
            for d in self.processed_data
        )
        return (
            shots,
            files,
            float(self.nist_match_tolerance_nm),
            float(self.nist_min_relative_peak_height),
            float(self.nist_noise_sigma_factor),
            calibration_key,
        )

    def apply_spectroscopy_calibration_to_wavelengths(self, data, wavelengths):
        """Apply per-shot wavelength calibration when available and enabled."""
        if not getattr(self, "spectroscopy_calibration_enabled", False):
            return np.asarray(wavelengths, dtype=float)
        if data is None or not data.get('spectroscopy_calibration_enabled', False):
            return np.asarray(wavelengths, dtype=float)
        return apply_wavelength_calibration(
            wavelengths,
            data.get('spectroscopy_calibration_coefficients', None)
        )

    def get_matching_spectrum_arrays(self, data):
        """Return wavelength/intensity arrays used by the spectroscopy matcher."""
        wl, intensity_norm, spec_meta = get_spectroscopy_rw_normalized_arrays(data)
        wl = self.apply_spectroscopy_calibration_to_wavelengths(data, wl)
        if getattr(self, "spectroscopy_calibration_enabled", False) and data.get('spectroscopy_calibration_enabled', False):
            spec_meta = dict(spec_meta)
            spec_meta["wavelength_calibration"] = data.get("spectroscopy_calibration_label", "enabled")
        return wl, intensity_norm, spec_meta

    def estimate_hydrogen_balmer_calibration_for_data(self, data, degree=2, search_window_nm=SPECTROSCOPY_CALIBRATION_SEARCH_WINDOW_NM):
        """
        Estimate a wavelength calibration using visible H Balmer lines.

        It searches local centroids around H_alpha, H_beta, H_gamma, etc. in the
        uncalibrated experimental spectrum and fits:
            lambda_NIST = poly(lambda_measured)
        """
        wl_raw, intensity_norm, spec_meta = get_spectroscopy_rw_normalized_arrays(data)
        wl_raw = np.asarray(wl_raw, dtype=float)
        intensity_norm = np.asarray(intensity_norm, dtype=float)

        if wl_raw.size < 3 or intensity_norm.size < 3 or wl_raw.shape != intensity_norm.shape:
            return pd.DataFrame(), None

        finite = np.isfinite(wl_raw) & np.isfinite(intensity_norm)
        wl_raw = wl_raw[finite]
        intensity_norm = intensity_norm[finite]
        if wl_raw.size < 3:
            return pd.DataFrame(), None

        baseline, sigma = robust_noise_level(intensity_norm)
        y_max = float(np.nanmax(intensity_norm))
        min_excess = max(
            self.nist_noise_sigma_factor * sigma,
            self.nist_min_relative_peak_height * y_max
        )

        rows = []
        for line_name, lambda_nist in HYDROGEN_BALMER_LINES_NM:
            if lambda_nist < np.nanmin(wl_raw) or lambda_nist > np.nanmax(wl_raw):
                continue

            local = estimate_local_spectral_center(
                wl_raw,
                intensity_norm,
                lambda_nist,
                window_nm=search_window_nm,
                background_window_nm=max(2.5 * search_window_nm, NIST_LOCAL_BACKGROUND_WINDOW_NM),
            )
            if local is None:
                continue

            if local["local_excess"] < min_excess:
                continue

            measured = float(local["center_nm"])
            rows.append({
                "shot": data.get("shot_number", ""),
                "line": line_name,
                "lambda_nist_nm": float(lambda_nist),
                "lambda_measured_nm": measured,
                "raw_delta_measured_minus_nist_nm": measured - float(lambda_nist),
                "peak_wavelength_nm": float(local["peak_wavelength_nm"]),
                "peak_intensity": float(local["peak_intensity"]),
                "local_excess": float(local["local_excess"]),
                "n_points_in_window": int(local["n_points_in_window"]),
            })

        cal_df = pd.DataFrame(rows)
        if cal_df.empty or len(cal_df) < 2:
            return cal_df, None

        degree_eff = int(min(max(int(degree), 1), len(cal_df) - 1, 2))
        coeffs = np.polyfit(
            cal_df["lambda_measured_nm"].to_numpy(dtype=float),
            cal_df["lambda_nist_nm"].to_numpy(dtype=float),
            deg=degree_eff,
        )
        cal_df["calibration_degree"] = degree_eff
        cal_df["lambda_calibrated_nm"] = np.polyval(coeffs, cal_df["lambda_measured_nm"].to_numpy(dtype=float))
        cal_df["residual_after_calibration_nm"] = cal_df["lambda_nist_nm"] - cal_df["lambda_calibrated_nm"]
        cal_df["calibration_coefficients_high_to_low"] = ", ".join(f"{c:.12g}" for c in coeffs)
        return cal_df, coeffs

    def calibrate_spectroscopy_gui(self):
        """Button callback: calibrate spectra using H Balmer lines."""
        if not self.processed_data:
            messagebox.showinfo("No shots", "Load at least one shot before calibrating spectroscopy.")
            return

        degree = simpledialog.askinteger(
            "Spectroscopy calibration",
            "Polynomial degree for wavelength calibration (1 = linear, 2 = quadratic):",
            initialvalue=int(getattr(self, "spectroscopy_calibration_degree", 2)),
            minvalue=1,
            maxvalue=2,
            parent=self.app
        )
        if degree is None:
            return

        window_nm = simpledialog.askfloat(
            "Spectroscopy calibration",
            "Search half-window around each H Balmer line [nm] (recommended: 1.5):",
            initialvalue=float(getattr(self, "spectroscopy_calibration_window_nm", SPECTROSCOPY_CALIBRATION_SEARCH_WINDOW_NM)),
            minvalue=0.2,
            maxvalue=10.0,
            parent=self.app
        )
        if window_nm is None:
            return

        self.spectroscopy_calibration_degree = int(degree)
        self.spectroscopy_calibration_window_nm = float(window_nm)

        all_rows = []
        calibrated_count = 0
        for data in self.processed_data:
            cal_df, coeffs = self.estimate_hydrogen_balmer_calibration_for_data(
                data,
                degree=degree,
                search_window_nm=window_nm,
            )
            if cal_df is not None and not cal_df.empty:
                all_rows.append(cal_df)

            if coeffs is not None and len(coeffs) >= 2:
                data['spectroscopy_calibration_coefficients'] = [float(c) for c in coeffs]
                data['spectroscopy_calibration_enabled'] = True
                data['spectroscopy_calibration_label'] = (
                    f"H Balmer polynomial degree {min(int(degree), len(coeffs)-1)}"
                )
                data['spectroscopy_calibration_anchors'] = cal_df.to_dict(orient="records")
                calibrated_count += 1
            else:
                data['spectroscopy_calibration_coefficients'] = None
                data['spectroscopy_calibration_enabled'] = False
                data['spectroscopy_calibration_label'] = "not enough H lines"
                data['spectroscopy_calibration_anchors'] = []

        self.spectroscopy_calibration_enabled = calibrated_count > 0
        self.nist_all_matches_cache = None
        self.nist_all_matches_cache_key = None
        self.nist_all_candidates_cache = None

        if all_rows:
            result_df = pd.concat(all_rows, ignore_index=True)
        else:
            result_df = pd.DataFrame()
        self.spectroscopy_last_calibration_table = result_df

        if result_df.empty:
            messagebox.showwarning(
                "Spectroscopy calibration",
                "No usable H Balmer lines were found. Calibration was not applied."
            )
            return

        messagebox.showinfo(
            "Spectroscopy calibration",
            f"Calibration applied to {calibrated_count} shot(s).\n"
            "The NIST filter will now use the calibrated wavelength axis."
        )
        self.show_dataframe_window(
            result_df,
            title="Spectroscopy calibration from H Balmer lines",
            default_filename_base="spectroscopy_hydrogen_calibration"
        )
        self.plot_data()

    def compute_all_spectroscopy_matches(self):
        """
        Compute candidate matched-line table using ALL local NIST files.

        Final accepted/global-best rows are chosen with an instrument-resolution
        exclusion rule:

          1) H Balmer lines used in calibration are accepted first as anchors.
          2) Each accepted line blocks +/- 0.6 nm around its NIST wavelength.
          3) Remaining candidates are considered by candidate_score. Once a
             candidate is accepted, it also blocks +/- 0.6 nm.
          4) The diagnostic candidate table still keeps all candidates, including
             suppressed/blocked rows.

        This gives a clean global ranking table while preserving all alternatives
        for inspection.
        """
        base_cols = [
            "shot", "type of element", "wavelength", "intensity", "rank_in_shot",
            "experimental_wavelength_nm", "delta_nm", "relative_intensity_in_shot",
            "candidate_score", "proximity_score", "is_global_best",
            "spectrum_source", "spectrum_normalization",
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

        # First available H NIST file. Synthetic calibration-anchor rows use this
        # source file so they remain visible when the user selects H in the filter.
        hydrogen_source_file = ""
        for _el, _file, _df in all_nist:
            if normalize_element_label(_el) == "H":
                hydrogen_source_file = _file
                break

        shot_tables = []
        exclusion_half_width_nm = float(SPECTROSCOPY_ACCEPTED_LINE_EXCLUSION_HALF_WIDTH_NM)

        for shot_order, data in enumerate(self.processed_data):
            wl_raw_for_match, _, _ = get_spectroscopy_rw_normalized_arrays(data)
            wl, intensity_norm, spec_meta = self.get_matching_spectrum_arrays(data)
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
                    wavelengths_raw=wl_raw_for_match,
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
                        "Ip_integral_plasma_tau_positive_A_for_spectrum", np.nan
                    )
                    matched["Ip_integral_plasma_time_positive_C_for_spectrum"] = spec_meta.get(
                        "Ip_integral_plasma_time_positive_C_for_spectrum", np.nan
                    )
                    matched["wavelength_calibration"] = spec_meta.get("wavelength_calibration", "none")
                    _halpha_support = get_halpha_temporal_support_metrics(data)
                    for _hk, _hv in _halpha_support.items():
                        matched[_hk] = _hv

                    if SPECTROSCOPY_USE_HALPHA_TEMPORAL_SUPPORT_FILTER and "is_hydrogen_balmer" in matched.columns:
                        _hmean = _halpha_support.get("halpha_temporal_mean_real_window", np.nan)
                        if (not np.isfinite(_hmean)) or (_hmean < SPECTROSCOPY_HALPHA_TEMPORAL_MIN_MEAN):
                            matched = matched[~matched["is_hydrogen_balmer"].astype(bool)].copy()

                    matched["shot_order"] = shot_order
                    rows_for_shot.append(matched)

            if not rows_for_shot:
                continue

            shot_df = pd.concat(rows_for_shot, ignore_index=True).reset_index(drop=True)
            shot_df["_candidate_row_id"] = np.arange(len(shot_df), dtype=int)
            shot_df["abs_delta_nm"] = pd.to_numeric(shot_df["delta_nm"], errors="coerce").abs()

            # Robust feature key: prefer the experimental feature id; fallback to a
            # wavelength bin if an old/empty candidate table lacks that column.
            if "experimental_feature_id" in shot_df.columns:
                shot_df["experimental_feature_id_global"] = pd.to_numeric(
                    shot_df["experimental_feature_id"], errors="coerce"
                ).fillna(-1).astype(int)
            else:
                bin_width = max(self.nist_match_tolerance_nm / 2.0, 1e-9)
                shot_df["experimental_feature_id_global"] = np.round(
                    shot_df["experimental_wavelength_nm"].astype(float) / bin_width
                ).astype(int)

            def _bool_series(df, col, default=False):
                if col in df.columns:
                    return df[col].fillna(default).astype(bool)
                return pd.Series(default, index=df.index, dtype=bool)

            def _str_series(df, col, default=""):
                if col in df.columns:
                    return df[col].fillna(default).astype(str)
                return pd.Series(default, index=df.index, dtype=str)

            def _num_series(df, col, default=np.nan):
                if col in df.columns:
                    return pd.to_numeric(df[col], errors="coerce")
                return pd.Series(default, index=df.index, dtype=float)

            # Calibration anchors:
            # If H_alpha, H_beta, etc. were used to calibrate the spectrum, they
            # are forced into the accepted-line table before any other element.
            # This avoids the inconsistency:
            #   "use H_alpha for calibration, but later assign that same region to O/Fe".
            #
            # Important: the anchor can be an existing H candidate row, or, if the
            # 0.6 nm matching window failed to create an H row, a synthetic H-anchor
            # row is added from the calibration table. The diagnostic candidates
            # table still keeps all Fe/O/W/N alternatives.
            shot_df["is_calibration_anchor"] = False
            shot_df["calibration_anchor_line"] = ""
            shot_df["calibration_anchor_nist_nm"] = np.nan
            shot_df["is_synthetic_calibration_anchor"] = False
            anchors = data.get("spectroscopy_calibration_anchors", []) if isinstance(data, dict) else []

            def _get_anchor_value(anchor, keys, default=np.nan):
                for key in keys:
                    if key in anchor:
                        val = anchor.get(key)
                        if isinstance(default, str):
                            if val is not None and str(val) != "":
                                return str(val)
                        else:
                            try:
                                fval = float(val)
                                if np.isfinite(fval):
                                    return fval
                            except Exception:
                                pass
                return default

            def _make_synthetic_anchor_row(anchor_index, anchor_line, anchor_nist, anchor_measured, anchor_calibrated, anchor_peak, anchor_intensity):
                # Feature id is intentionally negative so it cannot collide with
                # real detected experimental feature ids.
                synthetic_feature_id = -100000 - 1000 * int(shot_order) - int(anchor_index)

                if not np.isfinite(anchor_calibrated):
                    coeffs = data.get("spectroscopy_calibration_coefficients", None)
                    if coeffs is not None and np.isfinite(anchor_measured):
                        try:
                            anchor_calibrated = float(np.polyval(np.asarray(coeffs, dtype=float), anchor_measured))
                        except Exception:
                            anchor_calibrated = anchor_nist

                if not np.isfinite(anchor_calibrated):
                    anchor_calibrated = anchor_nist
                if not np.isfinite(anchor_measured):
                    anchor_measured = anchor_calibrated
                if not np.isfinite(anchor_peak):
                    anchor_peak = anchor_measured
                if not np.isfinite(anchor_intensity):
                    # Fall back to the strongest local experimental point around the
                    # measured anchor if possible.
                    try:
                        local = estimate_local_spectral_center(
                            wl_raw_for_match,
                            intensity_norm,
                            anchor_measured,
                            window_nm=max(exclusion_half_width_nm, 0.60),
                            background_window_nm=NIST_LOCAL_BACKGROUND_WINDOW_NM,
                        )
                        if local is not None:
                            anchor_intensity = float(local.get("peak_intensity", np.nan))
                    except Exception:
                        pass
                if not np.isfinite(anchor_intensity):
                    anchor_intensity = float(np.nanmax(intensity_norm)) if len(intensity_norm) else np.nan

                delta = float(anchor_calibrated - anchor_nist)
                abs_delta = abs(delta)
                y_max_local = float(np.nanmax(intensity_norm)) if len(intensity_norm) else np.nan
                rel_intensity = anchor_intensity / y_max_local if np.isfinite(y_max_local) and y_max_local > 0 else np.nan
                prox = max(0.0, 1.0 - abs_delta / max(exclusion_half_width_nm, 1e-12))

                balmer_info = get_hydrogen_balmer_match(anchor_nist, tolerance_nm=0.15)
                anchor_row = {
                    "shot": shot,
                    "type of element": "H",
                    "wavelength": float(anchor_nist),
                    "intensity": float(anchor_intensity),
                    "experimental_wavelength_nm": float(anchor_calibrated),
                    "experimental_raw_wavelength_nm": float(anchor_measured),
                    "experimental_calibrated_wavelength_nm": float(anchor_calibrated),
                    "experimental_peak_wavelength_nm": float(anchor_calibrated),
                    "experimental_raw_peak_wavelength_nm": float(anchor_peak),
                    "delta_nm": delta,
                    "relative_intensity_in_shot": rel_intensity,
                    "local_background": np.nan,
                    "local_excess": float(anchor_intensity),
                    "local_mean_intensity": float(anchor_intensity),
                    "local_integrated_intensity": np.nan,
                    "n_points_in_matching_window": np.nan,
                    "matching_window_width_nm": np.nan,
                    "match_tolerance_used_nm": float(exclusion_half_width_nm),
                    "nist_local_line_density": 1,
                    "element_prior_score": get_element_prior_score("H"),
                    "is_hydrogen_balmer": True,
                    "hydrogen_balmer_name": anchor_line,
                    "hydrogen_balmer_nist_nm": float(anchor_nist),
                    "hydrogen_balmer_priority_boost": float(SPECTROSCOPY_BALMER_PRIORITY_BOOST),
                    "nist_relative_intensity": "",
                    "nist_relative_intensity_numeric": np.nan,
                    "source_file": hydrogen_source_file if hydrogen_source_file else "calibration_anchor_H",
                    "wavelength_source": "H_Balmer_reference",
                    "matching_method": "forced_calibration_anchor",
                    "experimental_feature_id": synthetic_feature_id,
                    "experimental_feature_id_global": synthetic_feature_id,
                    "feature_center_nm": float(anchor_calibrated),
                    "feature_peak_wavelength_nm": float(anchor_calibrated),
                    "feature_start_nm": float(anchor_calibrated) - float(exclusion_half_width_nm),
                    "feature_end_nm": float(anchor_calibrated) + float(exclusion_half_width_nm),
                    "feature_width_nm": 2.0 * float(exclusion_half_width_nm),
                    "feature_n_points": np.nan,
                    "spectrum_source": spec_meta.get("spectrum_source", ""),
                    "spectrum_normalization": "S_rw / (plasma_duration_s * Ip_integral_plasma_tau_A)",
                    "spectrum_normalization_factor": spec_meta.get("spectrum_normalization_factor", np.nan),
                    "plasma_duration_s_for_spectrum": spec_meta.get("plasma_duration_s_for_spectrum", np.nan),
                    "Ip_integral_plasma_tau_positive_A_for_spectrum": spec_meta.get("Ip_integral_plasma_tau_positive_A_for_spectrum", np.nan),
                    "Ip_integral_plasma_time_positive_C_for_spectrum": spec_meta.get("Ip_integral_plasma_time_positive_C_for_spectrum", np.nan),
                    "wavelength_calibration": spec_meta.get("wavelength_calibration", "none"),
                    "shot_order": shot_order,
                    "abs_delta_nm": abs_delta,
                    "proximity_score": prox,
                    "experimental_score_norm": 1.0,
                    "nist_score_norm": 0.0,
                    "line_density_penalty_score": 0.0,
                    "candidate_score": 10.0 + float(SPECTROSCOPY_BALMER_PRIORITY_BOOST),
                    "is_calibration_anchor": True,
                    "calibration_anchor_line": anchor_line,
                    "calibration_anchor_nist_nm": float(anchor_nist),
                    "is_synthetic_calibration_anchor": True,
                }
                _halpha_support = get_halpha_temporal_support_metrics(data)
                for _hk, _hv in _halpha_support.items():
                    anchor_row[_hk] = _hv
                return anchor_row

            synthetic_anchor_rows = []

            for anchor_index, anchor in enumerate(anchors or []):
                anchor_line = _get_anchor_value(
                    anchor,
                    ["line", "hydrogen_balmer_name", "calibration_anchor_line"],
                    default=""
                )
                anchor_nist = _get_anchor_value(
                    anchor,
                    ["lambda_nist_nm", "hydrogen_balmer_nist_nm", "calibration_anchor_nist_nm"],
                    default=np.nan
                )
                anchor_measured = _get_anchor_value(
                    anchor,
                    ["lambda_measured_nm", "experimental_raw_wavelength_nm", "measured_wavelength_nm"],
                    default=np.nan
                )
                anchor_calibrated = _get_anchor_value(
                    anchor,
                    ["lambda_calibrated_nm", "experimental_calibrated_wavelength_nm", "experimental_wavelength_nm"],
                    default=np.nan
                )
                anchor_peak = _get_anchor_value(
                    anchor,
                    ["peak_wavelength_nm", "experimental_raw_peak_wavelength_nm"],
                    default=np.nan
                )
                anchor_intensity = _get_anchor_value(
                    anchor,
                    ["peak_intensity", "intensity"],
                    default=np.nan
                )

                if not anchor_line or not np.isfinite(anchor_nist):
                    continue

                # First try to mark an existing H Balmer candidate.
                mask_anchor = (
                    _bool_series(shot_df, "is_hydrogen_balmer")
                    & _str_series(shot_df, "hydrogen_balmer_name").eq(anchor_line)
                    & (_num_series(shot_df, "wavelength").sub(anchor_nist).abs() <= 0.15)
                )

                if mask_anchor.any():
                    candidates_for_anchor = shot_df.loc[mask_anchor].copy()
                    if np.isfinite(anchor_measured) and "experimental_raw_wavelength_nm" in candidates_for_anchor.columns:
                        candidates_for_anchor["_anchor_raw_distance"] = (
                            pd.to_numeric(candidates_for_anchor["experimental_raw_wavelength_nm"], errors="coerce")
                            .sub(anchor_measured)
                            .abs()
                        )
                    else:
                        candidates_for_anchor["_anchor_raw_distance"] = 0.0

                    candidates_for_anchor["_anchor_delta"] = pd.to_numeric(
                        candidates_for_anchor.get("delta_nm", np.nan), errors="coerce"
                    ).abs()

                    chosen_idx = candidates_for_anchor.sort_values(
                        ["_anchor_raw_distance", "_anchor_delta", "candidate_score", "intensity"],
                        ascending=[True, True, False, False]
                    ).index[0]

                    feature_id = int(shot_df.loc[chosen_idx, "experimental_feature_id_global"])
                    feature_mask = shot_df["experimental_feature_id_global"].astype(int).eq(feature_id)
                    shot_df.loc[feature_mask, "calibration_anchor_line"] = anchor_line
                    shot_df.loc[feature_mask, "calibration_anchor_nist_nm"] = anchor_nist
                    shot_df.loc[chosen_idx, "is_calibration_anchor"] = True
                    shot_df.loc[chosen_idx, "is_synthetic_calibration_anchor"] = False
                else:
                    # If no row exists because the 0.6 nm candidate window was too
                    # strict, keep the calibration anchor anyway.
                    synthetic_anchor_rows.append(
                        _make_synthetic_anchor_row(
                            anchor_index,
                            anchor_line,
                            anchor_nist,
                            anchor_measured,
                            anchor_calibrated,
                            anchor_peak,
                            anchor_intensity,
                        )
                    )

            if synthetic_anchor_rows:
                synthetic_df = pd.DataFrame(synthetic_anchor_rows)
                next_id = int(shot_df["_candidate_row_id"].max()) + 1 if "_candidate_row_id" in shot_df.columns and len(shot_df) else 0
                synthetic_df["_candidate_row_id"] = np.arange(next_id, next_id + len(synthetic_df), dtype=int)
                # Ensure all missing columns exist before concatenation.
                for col in shot_df.columns:
                    if col not in synthetic_df.columns:
                        synthetic_df[col] = np.nan
                for col in synthetic_df.columns:
                    if col not in shot_df.columns:
                        shot_df[col] = np.nan
                shot_df = pd.concat([shot_df, synthetic_df[shot_df.columns]], ignore_index=True)
                shot_df["abs_delta_nm"] = pd.to_numeric(shot_df["delta_nm"], errors="coerce").abs()

            # Recompute cross-element score. No density penalty is applied: dense
            # Fe spectra are not suppressed; they only compete by wavelength, signal
            # strength, NIST weak prior, and physical element prior.
            tol_for_score = pd.to_numeric(
                shot_df.get("match_tolerance_used_nm", self.nist_match_tolerance_nm),
                errors="coerce"
            ).fillna(float(self.nist_match_tolerance_nm)).astype(float).clip(lower=1e-12)
            shot_df["proximity_score"] = np.clip(
                1.0 - shot_df["abs_delta_nm"].astype(float) / tol_for_score,
                0.0, 1.0
            )
            if "local_excess" in shot_df.columns:
                shot_df["experimental_score_norm"] = normalize_01(shot_df["local_excess"])
            else:
                shot_df["experimental_score_norm"] = normalize_01(shot_df["intensity"])

            shot_df["nist_intensity_for_score"] = pd.to_numeric(
                shot_df.get("nist_relative_intensity_numeric", np.nan), errors="coerce"
            ).fillna(0.0)
            shot_df["nist_log_for_score"] = np.log10(shot_df["nist_intensity_for_score"].clip(lower=0.0) + 1.0)
            shot_df["nist_score_norm"] = normalize_01(shot_df["nist_log_for_score"])
            shot_df["element_prior_score"] = pd.to_numeric(
                shot_df.get("element_prior_score", 0.30), errors="coerce"
            ).fillna(0.30).astype(float)
            density = pd.to_numeric(shot_df.get("nist_local_line_density", 1), errors="coerce").fillna(1.0).astype(float).clip(lower=1.0)
            shot_df["line_density_penalty_score"] = 0.0 * normalize_01(np.log1p(density))
            balmer_boost = pd.to_numeric(
                shot_df.get("hydrogen_balmer_priority_boost", 0.0),
                errors="coerce"
            ).fillna(0.0).astype(float)
            anchor_boost = pd.Series(0.0, index=shot_df.index)
            if "is_calibration_anchor" in shot_df.columns:
                anchor_boost = shot_df["is_calibration_anchor"].astype(bool).astype(float) * 2.0

            shot_df["candidate_score"] = (
                0.55 * shot_df["proximity_score"].astype(float)
                + 0.25 * shot_df["experimental_score_norm"].astype(float)
                + 0.08 * shot_df["nist_score_norm"].astype(float)
                + SPECTROSCOPY_ELEMENT_PRIOR_WEIGHT * shot_df["element_prior_score"].astype(float)
                + balmer_boost
                + anchor_boost
            )

            # Feature intensity rank for diagnostic candidate table. This is
            # independent of the accepted-line exclusion algorithm.
            feature_intensity = (
                shot_df.groupby(["shot", "experimental_feature_id_global"], dropna=False)["intensity"]
                .max()
                .reset_index()
                .sort_values(["shot", "intensity"], ascending=[True, False])
            )
            feature_intensity["feature_rank_in_shot"] = feature_intensity.groupby("shot").cumcount() + 1
            feature_rank_all = {
                (r["shot"], r["experimental_feature_id_global"]): int(r["feature_rank_in_shot"])
                for _, r in feature_intensity.iterrows()
            }
            shot_df["feature_rank_in_shot"] = [
                feature_rank_all.get((r["shot"], r["experimental_feature_id_global"]), np.nan)
                for _, r in shot_df.iterrows()
            ]

            # Greedy accepted-line selection with +/-0.6 nm exclusion.
            accepted_ids = []
            accepted_features = set()
            blocked_windows = []  # list of dict(center, half_width, element, row_id, reason)

            shot_df["is_suppressed_by_exclusion_window"] = False
            shot_df["suppression_reason"] = ""
            shot_df["suppressed_by_element"] = ""
            shot_df["suppressed_by_wavelength_nm"] = np.nan
            shot_df["accepted_exclusion_half_width_nm"] = exclusion_half_width_nm

            def _row_wavelength(row):
                try:
                    return float(row.get("wavelength", np.nan))
                except Exception:
                    return np.nan

            def _feature_key(row):
                return (row.get("shot", None), row.get("experimental_feature_id_global", None))

            def _blocking_window_for(row, reason):
                return {
                    "center_nm": _row_wavelength(row),
                    "half_width_nm": exclusion_half_width_nm,
                    "element": str(row.get("type of element", "")),
                    "row_id": int(row.get("_candidate_row_id", -1)),
                    "reason": reason,
                }

            def _find_blocking_window(row):
                lam = _row_wavelength(row)
                if not np.isfinite(lam):
                    return None
                for win in blocked_windows:
                    c = float(win.get("center_nm", np.nan))
                    hw = float(win.get("half_width_nm", exclusion_half_width_nm))
                    if np.isfinite(c) and abs(lam - c) <= hw:
                        return win
                return None

            def _accept_row(row, reason):
                row_id = int(row.get("_candidate_row_id"))
                feature_key = _feature_key(row)
                if row_id in accepted_ids or feature_key in accepted_features:
                    return False
                accepted_ids.append(row_id)
                accepted_features.add(feature_key)
                blocked_windows.append(_blocking_window_for(row, reason))
                return True

            # 1) Accept H calibration anchors first.
            anchors_df = shot_df[shot_df["is_calibration_anchor"].astype(bool)].copy()
            if not anchors_df.empty:
                anchors_df["_anchor_line_sort"] = anchors_df.get("calibration_anchor_line", "").astype(str)
                anchors_df = anchors_df.sort_values(
                    ["_anchor_line_sort", "candidate_score", "proximity_score", "abs_delta_nm", "intensity"],
                    ascending=[True, False, False, True, False]
                )
                for _, row in anchors_df.iterrows():
                    block = _find_blocking_window(row)
                    if block is None:
                        _accept_row(row, "accepted_H_calibration_anchor")

            # 2) Accept remaining candidates by score, while respecting both
            # the spectral exclusion window and the one-candidate-per-feature rule.
            remaining = shot_df[~shot_df["_candidate_row_id"].isin(accepted_ids)].copy()
            if not remaining.empty:
                remaining = remaining.sort_values(
                    ["candidate_score", "proximity_score", "intensity", "abs_delta_nm"],
                    ascending=[False, False, False, True]
                )
                for _, row in remaining.iterrows():
                    row_id = int(row.get("_candidate_row_id"))
                    feature_key = _feature_key(row)
                    if row_id in accepted_ids or feature_key in accepted_features:
                        continue

                    block = _find_blocking_window(row)
                    if block is not None:
                        # Mark every candidate inside a blocked spectral interval.
                        lam = _row_wavelength(row)
                        if np.isfinite(lam):
                            in_block = pd.to_numeric(shot_df["wavelength"], errors="coerce").sub(float(block["center_nm"])).abs() <= float(block["half_width_nm"])
                            shot_df.loc[in_block & ~shot_df["_candidate_row_id"].isin(accepted_ids), "is_suppressed_by_exclusion_window"] = True
                            shot_df.loc[in_block & ~shot_df["_candidate_row_id"].isin(accepted_ids), "suppression_reason"] = (
                                "inside_accepted_line_window"
                            )
                            shot_df.loc[in_block & ~shot_df["_candidate_row_id"].isin(accepted_ids), "suppressed_by_element"] = block.get("element", "")
                            shot_df.loc[in_block & ~shot_df["_candidate_row_id"].isin(accepted_ids), "suppressed_by_wavelength_nm"] = block.get("center_nm", np.nan)
                        continue

                    _accept_row(row, "accepted_global_candidate")

            accepted_set = set(accepted_ids)
            shot_df["is_global_best"] = shot_df["_candidate_row_id"].isin(accepted_set)

            best = shot_df[shot_df["is_global_best"].astype(bool)].copy()

            # Accepted global ranking by experimental intensity.
            # Calibration anchors are placed first only when intensities are tied
            # or nearly tied, so H_alpha/H_beta used for calibration cannot be
            # pushed below an equally intense O/Fe candidate.
            if not best.empty:
                best["_rank_anchor_sort"] = (
                    best["is_calibration_anchor"].astype(bool).astype(int)
                    if "is_calibration_anchor" in best.columns else 0
                )
                feature_rank_df = best.sort_values(
                    ["intensity", "_rank_anchor_sort", "candidate_score", "proximity_score"],
                    ascending=[False, False, False, False]
                ).drop(columns=["_rank_anchor_sort"], errors="ignore").reset_index(drop=True)
                accepted_rank_map = {
                    int(row["_candidate_row_id"]): i + 1
                    for i, row in feature_rank_df.iterrows()
                }
                accepted_feature_rank_map = {
                    (row["shot"], row["experimental_feature_id_global"]): i + 1
                    for i, row in feature_rank_df.iterrows()
                }
            else:
                feature_rank_df = pd.DataFrame()
                accepted_rank_map = {}
                accepted_feature_rank_map = {}

            shot_df["rank_in_shot"] = [
                accepted_feature_rank_map.get((r["shot"], r["experimental_feature_id_global"]), np.nan)
                for _, r in shot_df.iterrows()
            ]
            shot_df["accepted_line_rank_in_shot"] = [
                accepted_rank_map.get(int(r["_candidate_row_id"]), np.nan)
                for _, r in shot_df.iterrows()
            ]

            # Per-feature best/second diagnostics. Use the accepted row when the
            # feature is accepted. Otherwise keep the best candidate by score for
            # diagnostics only.
            best_rows_for_lookup = []
            second_rows = []
            for key, group in shot_df.groupby(["shot", "experimental_feature_id_global"], dropna=False):
                accepted_g = group[group["is_global_best"].astype(bool)]
                if not accepted_g.empty:
                    ranked = accepted_g.sort_values(
                        ["candidate_score", "proximity_score", "abs_delta_nm", "intensity"],
                        ascending=[False, False, True, False]
                    )
                else:
                    ranked = group.sort_values(
                        ["candidate_score", "proximity_score", "abs_delta_nm", "intensity"],
                        ascending=[False, False, True, False]
                    )

                if ranked.empty:
                    continue

                best_row = ranked.iloc[0]
                best_rows_for_lookup.append(best_row)

                alt = group.copy()
                same_best = (
                    alt["type of element"].astype(str).eq(str(best_row["type of element"]))
                    & np.isclose(pd.to_numeric(alt["wavelength"], errors="coerce"), float(best_row["wavelength"]), equal_nan=False)
                )
                alt = alt[~same_best]
                if not alt.empty:
                    alt = alt.sort_values(
                        ["candidate_score", "proximity_score", "abs_delta_nm", "intensity"],
                        ascending=[False, False, True, False]
                    )
                    second_rows.append(alt.iloc[0])

            best_lookup_df = pd.DataFrame(best_rows_for_lookup) if best_rows_for_lookup else pd.DataFrame()
            best_lookup = best_lookup_df.set_index(["shot", "experimental_feature_id_global"]) if not best_lookup_df.empty else None
            second = pd.DataFrame(second_rows) if second_rows else pd.DataFrame()
            second_lookup = second.set_index(["shot", "experimental_feature_id_global"]) if not second.empty else None

            def lookup_col(row, lookup, col, default=np.nan):
                if lookup is None:
                    return default
                try:
                    return lookup.loc[(row["shot"], row["experimental_feature_id_global"]), col]
                except Exception:
                    return default

            shot_df["best_element_for_feature"] = [lookup_col(r, best_lookup, "type of element", "") for _, r in shot_df.iterrows()]
            shot_df["best_wavelength_for_feature_nm"] = [lookup_col(r, best_lookup, "wavelength", np.nan) for _, r in shot_df.iterrows()]
            shot_df["best_delta_for_feature_nm"] = [lookup_col(r, best_lookup, "delta_nm", np.nan) for _, r in shot_df.iterrows()]
            shot_df["best_candidate_score_for_feature"] = [lookup_col(r, best_lookup, "candidate_score", np.nan) for _, r in shot_df.iterrows()]

            if second_lookup is not None:
                shot_df["second_element_for_feature"] = [lookup_col(r, second_lookup, "type of element", "") for _, r in shot_df.iterrows()]
                shot_df["second_wavelength_for_feature_nm"] = [lookup_col(r, second_lookup, "wavelength", np.nan) for _, r in shot_df.iterrows()]
                shot_df["second_delta_for_feature_nm"] = [lookup_col(r, second_lookup, "delta_nm", np.nan) for _, r in shot_df.iterrows()]
                shot_df["second_candidate_score_for_feature"] = [lookup_col(r, second_lookup, "candidate_score", np.nan) for _, r in shot_df.iterrows()]
            else:
                shot_df["second_element_for_feature"] = ""
                shot_df["second_wavelength_for_feature_nm"] = np.nan
                shot_df["second_delta_for_feature_nm"] = np.nan
                shot_df["second_candidate_score_for_feature"] = np.nan

            shot_tables.append(shot_df)

        if not shot_tables:
            return pd.DataFrame(columns=base_cols)

        out = pd.concat(shot_tables, ignore_index=True)
        out = out.sort_values(
            ["rank_in_shot", "shot_order", "is_global_best", "candidate_score", "intensity"],
            ascending=[True, True, False, False, False],
            na_position="last"
        ).reset_index(drop=True)

        first_cols = [
            "shot", "type of element", "wavelength", "intensity", "rank_in_shot",
            "accepted_line_rank_in_shot", "feature_rank_in_shot",
            "experimental_raw_wavelength_nm", "experimental_calibrated_wavelength_nm",
            "experimental_wavelength_nm", "experimental_peak_wavelength_nm",
            "experimental_raw_peak_wavelength_nm", "delta_nm",
            "match_tolerance_used_nm", "accepted_exclusion_half_width_nm",
            "is_hydrogen_balmer", "hydrogen_balmer_name",
            "is_calibration_anchor", "calibration_anchor_line",
            "is_global_best", "is_suppressed_by_exclusion_window", "suppression_reason",
            "suppressed_by_element", "suppressed_by_wavelength_nm",
            "candidate_score", "proximity_score",
            "experimental_score_norm", "nist_score_norm", "element_prior_score", "line_density_penalty_score",
            "best_element_for_feature", "best_wavelength_for_feature_nm",
            "best_delta_for_feature_nm", "second_element_for_feature", "second_wavelength_for_feature_nm",
            "second_delta_for_feature_nm", "relative_intensity_in_shot",
            "nist_relative_intensity", "nist_relative_intensity_numeric",
        ]
        existing_first_cols = [c for c in first_cols if c in out.columns]
        other_cols = [
            c for c in out.columns
            if c not in existing_first_cols + ["shot_order", "abs_delta_nm", "nist_intensity_for_score", "nist_log_for_score"]
        ]
        out = out[existing_first_cols + other_cols]

        self.nist_all_candidates_cache = out.copy()
        self.nist_all_matches_cache = out.copy()
        self.nist_all_matches_cache_key = cache_key
        return out.copy()


    def _selected_spectroscopy_candidates(self):
        """
        Return all candidate rows restricted to the currently selected local NIST files.

        This method does not decide which candidate is physically preferred. It only
        applies the GUI file/element selection after the all-elements matching cache
        has already been computed.
        """
        all_candidates = self.compute_all_spectroscopy_matches()
        if all_candidates.empty:
            return all_candidates

        if not self.selected_nist_files:
            return all_candidates.iloc[0:0].copy()

        source_mask = all_candidates["source_file"].astype(str).isin(self.selected_nist_files)

        # Synthetic calibration-anchor rows may use the special fallback source
        # "calibration_anchor_H" if no local H file name was available. Keep them
        # visible whenever the user selected at least one H NIST file.
        selected_h = False
        try:
            for file_name in self.selected_nist_files:
                if normalize_element_label(guess_element_from_filename(file_name)) == "H":
                    selected_h = True
                    break
        except Exception:
            selected_h = False

        anchor_mask = pd.Series(False, index=all_candidates.index)
        if selected_h and "is_calibration_anchor" in all_candidates.columns:
            anchor_mask = (
                all_candidates["is_calibration_anchor"].fillna(False).astype(bool)
                & all_candidates["type of element"].astype(str).map(normalize_element_label).eq("H")
            )

        out = all_candidates[source_mask | anchor_mask].copy()

        return out.reset_index(drop=True)

    def _sort_candidates_by_feature(self, df):
        """
        Sort candidate rows inside each experimental feature and assign
        candidate_rank_for_feature.

        candidate_rank_for_feature = 1 means the most likely candidate for that
        feature among the rows passed to this helper. This is a diagnostic ranking;
        the accepted global assignment is still indicated by is_global_best.
        """
        if df is None or df.empty:
            return df.copy() if df is not None else pd.DataFrame()

        out = df.copy()

        if "experimental_feature_id_global" not in out.columns:
            if "experimental_feature_id" in out.columns:
                out["experimental_feature_id_global"] = pd.to_numeric(
                    out["experimental_feature_id"], errors="coerce"
                ).fillna(-1).astype(int)
            else:
                bin_width = max(float(getattr(self, "nist_match_tolerance_nm", NIST_MATCH_TOLERANCE_NM)) / 2.0, 1e-9)
                out["experimental_feature_id_global"] = np.round(
                    pd.to_numeric(out["experimental_wavelength_nm"], errors="coerce").fillna(0.0) / bin_width
                ).astype(int)

        if "feature_rank_in_shot" not in out.columns:
            if "rank_in_shot" in out.columns:
                out["feature_rank_in_shot"] = out["rank_in_shot"]
            else:
                out["feature_rank_in_shot"] = np.nan

        out["_score_sort"] = pd.to_numeric(out.get("candidate_score", np.nan), errors="coerce").fillna(-np.inf)
        out["_prox_sort"] = pd.to_numeric(out.get("proximity_score", np.nan), errors="coerce").fillna(-np.inf)
        out["_intensity_sort"] = pd.to_numeric(out.get("intensity", np.nan), errors="coerce").fillna(-np.inf)
        out["_abs_delta_sort"] = pd.to_numeric(out.get("delta_nm", np.nan), errors="coerce").abs().fillna(np.inf)
        out["_is_anchor_sort"] = (
            out["is_calibration_anchor"].astype(bool).astype(int)
            if "is_calibration_anchor" in out.columns else 0
        )
        out["_is_balmer_sort"] = (
            out["is_hydrogen_balmer"].astype(bool).astype(int)
            if "is_hydrogen_balmer" in out.columns else 0
        )

        out = out.sort_values(
            [
                "shot",
                "experimental_feature_id_global",
                "_is_anchor_sort",
                "_score_sort",
                "_is_balmer_sort",
                "_prox_sort",
                "_abs_delta_sort",
                "_intensity_sort",
            ],
            ascending=[True, True, False, False, False, False, True, False],
        ).reset_index(drop=True)

        out["candidate_rank_for_feature"] = (
            out.groupby(["shot", "experimental_feature_id_global"], dropna=False)
               .cumcount()
               + 1
        )

        return out.drop(
            columns=[
                "_score_sort", "_prox_sort", "_intensity_sort", "_abs_delta_sort",
                "_is_anchor_sort", "_is_balmer_sort",
            ],
            errors="ignore"
        )

    def _apply_feature_line_limit(self, df):
        """
        Apply the Max lines/shot limit as a feature-rank limit.

        For the best-candidate table this means top N accepted lines per shot.
        For the all-candidates table this means all candidate alternatives
        belonging to the top N experimental features per shot.
        """
        if df is None or df.empty:
            return df.copy() if df is not None else pd.DataFrame()

        out = df.copy()
        max_lines = int(getattr(self, "nist_display_max_lines", 10))
        if max_lines <= 0:
            return out

        rank_col = "feature_rank_in_shot" if "feature_rank_in_shot" in out.columns else "rank_in_shot"
        if rank_col in out.columns:
            ranks = pd.to_numeric(out[rank_col], errors="coerce")
            out = out[ranks <= max_lines].copy()

        return out.reset_index(drop=True)

    def _add_alternative_candidate_columns(self, best_df, candidates_df, max_alternatives=3):
        """
        Add candidate_2_*, candidate_3_*, ... columns to the best-candidate table.

        These columns are diagnostic only. The actual accepted candidate remains
        the main row itself:
            type of element, wavelength, delta_nm, candidate_score

        If Fe 655.455 nm is compatible with the same H-alpha feature, it can
        appear as candidate_2_* or candidate_3_* rather than being hidden.
        """
        if best_df is None or best_df.empty:
            return best_df.copy() if best_df is not None else pd.DataFrame()

        if candidates_df is None or candidates_df.empty:
            return best_df.copy()

        candidates_ranked = self._sort_candidates_by_feature(candidates_df)
        out = best_df.copy()

        group_cols = ["shot", "experimental_feature_id_global"]
        if not all(c in out.columns for c in group_cols) or not all(c in candidates_ranked.columns for c in group_cols):
            return out

        # Precompute candidate groups for quick lookup.
        grouped = {
            key: group.reset_index(drop=True)
            for key, group in candidates_ranked.groupby(group_cols, dropna=False)
        }

        for n in range(2, max_alternatives + 1):
            out[f"candidate_{n}_element"] = ""
            out[f"candidate_{n}_wavelength_nm"] = np.nan
            out[f"candidate_{n}_delta_nm"] = np.nan
            out[f"candidate_{n}_score"] = np.nan
            out[f"candidate_{n}_source_file"] = ""
            out[f"candidate_{n}_is_calibration_anchor"] = False

        for idx, row in out.iterrows():
            key = (row.get("shot", None), row.get("experimental_feature_id_global", None))
            group = grouped.get(key)
            if group is None or group.empty:
                continue

            alternatives = []
            main_element = str(row.get("type of element", ""))
            try:
                main_wavelength = float(row.get("wavelength", np.nan))
            except Exception:
                main_wavelength = np.nan

            for _, cand in group.iterrows():
                cand_element = str(cand.get("type of element", ""))
                try:
                    cand_wavelength = float(cand.get("wavelength", np.nan))
                except Exception:
                    cand_wavelength = np.nan

                same_as_main = (
                    cand_element == main_element
                    and np.isfinite(cand_wavelength)
                    and np.isfinite(main_wavelength)
                    and abs(cand_wavelength - main_wavelength) < 1e-9
                )
                if same_as_main:
                    continue
                alternatives.append(cand)

            for n, cand in enumerate(alternatives[: max_alternatives - 1], start=2):
                out.at[idx, f"candidate_{n}_element"] = cand.get("type of element", "")
                out.at[idx, f"candidate_{n}_wavelength_nm"] = cand.get("wavelength", np.nan)
                out.at[idx, f"candidate_{n}_delta_nm"] = cand.get("delta_nm", np.nan)
                out.at[idx, f"candidate_{n}_score"] = cand.get("candidate_score", np.nan)
                out.at[idx, f"candidate_{n}_source_file"] = cand.get("source_file", "")
                out.at[idx, f"candidate_{n}_is_calibration_anchor"] = bool(cand.get("is_calibration_anchor", False))

        return out

    def _reorder_best_spectroscopy_columns(self, df):
        """Put the physically important columns first in the best-candidate table."""
        if df is None or df.empty:
            return df.copy() if df is not None else pd.DataFrame()

        first_cols = [
            "rank_in_shot",
            "shot",
            "type of element",
            "wavelength",
            "intensity",
            "experimental_raw_wavelength_nm",
            "experimental_calibrated_wavelength_nm",
            "delta_nm",
            "match_tolerance_used_nm",
            "accepted_exclusion_half_width_nm",
            "is_hydrogen_balmer",
            "hydrogen_balmer_name",
            "is_calibration_anchor",
            "calibration_anchor_line",
            "is_suppressed_by_exclusion_window",
            "suppression_reason",
            "suppressed_by_element",
            "suppressed_by_wavelength_nm",
            "candidate_score",
            "proximity_score",
            "relative_intensity_in_shot",
            "source_file",
            "experimental_feature_id_global",
            "feature_center_nm",
            "feature_peak_wavelength_nm",
            "feature_width_nm",
            "feature_n_points",
            "local_background",
            "local_excess",
            "local_integrated_intensity",
            "nist_relative_intensity",
            "nist_relative_intensity_numeric",
            "element_prior_score",
            "line_density_penalty_score",
            "wavelength_calibration",
            "halpha_temporal_integral_real_time_positive",
            "halpha_temporal_duration_s_real_window",
            "halpha_temporal_mean_real_window",
        ]

        # Put alternatives after the main accepted identification, but before the
        # long diagnostic metadata block.
        alt_cols = []
        for n in range(2, 5):
            alt_cols.extend([
                f"candidate_{n}_element",
                f"candidate_{n}_wavelength_nm",
                f"candidate_{n}_delta_nm",
                f"candidate_{n}_score",
                f"candidate_{n}_source_file",
                f"candidate_{n}_is_calibration_anchor",
            ])

        existing = [c for c in first_cols + alt_cols if c in df.columns]
        hidden_or_redundant = {
            "global_rank_in_shot",
            "best_element_for_feature",
            "best_wavelength_for_feature_nm",
            "best_delta_for_feature_nm",
            "best_candidate_score_for_feature",
            "second_element_for_feature",
            "second_wavelength_for_feature_nm",
            "second_delta_for_feature_nm",
            "second_candidate_score_for_feature",
            "experimental_wavelength_nm",
            "experimental_peak_wavelength_nm",
            "experimental_raw_peak_wavelength_nm",
            "is_global_best",
        }
        rest = [c for c in df.columns if c not in existing and c not in hidden_or_redundant]
        return df[existing + rest]

    def _reorder_candidate_spectroscopy_columns(self, df):
        """Put the feature/candidate-rank columns first in the diagnostic table."""
        if df is None or df.empty:
            return df.copy() if df is not None else pd.DataFrame()

        first_cols = [
            "shot",
            "experimental_feature_id_global",
            "feature_rank_in_shot",
            "candidate_rank_for_feature",
            "is_global_best",
            "type of element",
            "wavelength",
            "intensity",
            "experimental_raw_wavelength_nm",
            "experimental_calibrated_wavelength_nm",
            "delta_nm",
            "match_tolerance_used_nm",
            "accepted_exclusion_half_width_nm",
            "is_suppressed_by_exclusion_window",
            "suppression_reason",
            "suppressed_by_element",
            "suppressed_by_wavelength_nm",
            "candidate_score",
            "proximity_score",
            "is_hydrogen_balmer",
            "hydrogen_balmer_name",
            "is_calibration_anchor",
            "calibration_anchor_line",
            "source_file",
            "relative_intensity_in_shot",
            "element_prior_score",
            "line_density_penalty_score",
            "nist_local_line_density",
            "nist_relative_intensity",
            "nist_relative_intensity_numeric",
            "feature_center_nm",
            "feature_peak_wavelength_nm",
            "feature_start_nm",
            "feature_end_nm",
            "feature_width_nm",
            "feature_n_points",
            "local_background",
            "local_excess",
            "local_integrated_intensity",
        ]
        existing = [c for c in first_cols if c in df.columns]
        # Keep compatibility wavelength aliases but move them away from the main
        # comparison columns so they do not confuse raw/calibrated/NIST lambda.
        late_aliases = [c for c in ["experimental_wavelength_nm", "experimental_peak_wavelength_nm", "experimental_raw_peak_wavelength_nm"] if c in df.columns]
        rest = [c for c in df.columns if c not in existing and c not in late_aliases]
        return df[existing + late_aliases + rest]

    def compute_spectroscopy_best_global_table(self):
        """
        Return the clean spectroscopy result table: one accepted candidate per
        experimental feature.

        This is the table intended for analysis. The ranking is always:
            rank_in_shot = 1, 2, 3, ...
        ordered by the experimental intensity of the accepted features in each shot.
        Candidate alternatives are not separate rows here; they are shown in
        candidate_2_*, candidate_3_* columns to the right.
        """
        selected_candidates = self._selected_spectroscopy_candidates()
        if selected_candidates.empty:
            return selected_candidates

        if "is_global_best" not in selected_candidates.columns:
            best = selected_candidates.copy()
        else:
            best = selected_candidates[selected_candidates["is_global_best"].astype(bool)].copy()

        if best.empty:
            return best

        # Re-rank only accepted rows by intensity within each shot.
        best["_intensity_sort"] = pd.to_numeric(best.get("intensity", np.nan), errors="coerce").fillna(-np.inf)
        best = best.sort_values(["shot", "_intensity_sort"], ascending=[True, False]).reset_index(drop=True)
        best["rank_in_shot"] = best.groupby("shot").cumcount() + 1
        best["feature_rank_in_shot"] = best["rank_in_shot"]

        best = self._apply_feature_line_limit(best)

        # Add second/third/fourth alternatives as diagnostic columns on the right.
        best = self._add_alternative_candidate_columns(
            best,
            selected_candidates,
            max_alternatives=4
        )

        best = best.drop(columns=["_intensity_sort"], errors="ignore")
        best = best.sort_values(["rank_in_shot", "shot"], ascending=[True, True]).reset_index(drop=True)
        return self._reorder_best_spectroscopy_columns(best)

    def compute_spectroscopy_candidate_table(self):
        """
        Return the diagnostic spectroscopy table: all candidate lines by feature.

        This table can contain several rows for the same experimental feature.
        Use candidate_rank_for_feature to see which candidate is most likely
        within that feature. Use is_global_best to see which one is accepted in
        the clean best-candidate table.
        """
        candidates = self._selected_spectroscopy_candidates()
        if candidates.empty:
            return candidates

        out = self._sort_candidates_by_feature(candidates)
        out = self._apply_feature_line_limit(out)

        out = out.sort_values(
            ["feature_rank_in_shot", "shot", "candidate_rank_for_feature"],
            ascending=[True, True, True]
        ).reset_index(drop=True)

        return self._reorder_candidate_spectroscopy_columns(out)

    def compute_selected_spectroscopy_matches(self):
        """
        Backward-compatible name used by the plot overlay.

        It now returns only the clean best-global table, not every candidate.
        To inspect all alternatives, use compute_spectroscopy_candidate_table().
        """
        return self.compute_spectroscopy_best_global_table()

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
        for col in ["shot", "wavelength", "intensity", "rank_in_shot", "experimental_wavelength_nm", "experimental_raw_wavelength_nm", "experimental_calibrated_wavelength_nm"]:
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

        # Keep only the first N selected matched lines per shot in the visualizer.
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
            f"NIST filter: {', '.join(sorted({str(x) for x in df['type of element'].unique()}))} | top {getattr(self, 'nist_display_max_lines', 10)} features/shot | {'calibrated' if getattr(self, 'spectroscopy_calibration_enabled', False) else 'raw λ'}",
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

        wl, spec_y = get_normalized_spectrum(
            data['wavelengths_Avantes'],
            data['intensities_Avantes_raw'],
            plasma_duration,
            self.normalization_mode,
            ip_norm
        )
        wl = self.apply_spectroscopy_calibration_to_wavelengths(data, wl)
        return wl, spec_y

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
