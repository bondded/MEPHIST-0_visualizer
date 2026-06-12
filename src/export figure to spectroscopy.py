import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# =========================================================
# USER PARAMETERS
# =========================================================

csv_path = r"C:\Users\chelo\Desktop\MephiST\Descargas\18 mPa\matched_spectroscopy_lines.csv"

# Máximo rank_in_shot a mostrar
max_rank_in_shot = 10

# Si quieres mostrar solo ciertos shots, déjalo en None
selected_shots = [2621, 2623, 2628, 2629]
# selected_shots = None

# Modo del intervalo horizontal
# "tolerance"  -> experimental_wavelength_nm ± window_half_width_nm
# "match_span" -> línea entre wavelength y experimental_wavelength_nm
interval_mode = "tolerance"

window_half_width_nm = 0.8

# Intervalo del eje X que se quiere cortar
cut_min = 525
cut_max = 625

figsize = (15, 7)

interval_alpha = 0.85
interval_linewidth = 2.5

marker_size = 95
label_fontsize = 9
show_rank_label = True

# =========================================================
# LOAD DATA
# =========================================================

df = pd.read_csv(csv_path)

numeric_cols = [
    "shot", "wavelength", "intensity", "rank_in_shot",
    "experimental_wavelength_nm", "delta_nm"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["shot", "wavelength", "intensity", "rank_in_shot"])
df = df[df["rank_in_shot"] <= max_rank_in_shot].copy()

if selected_shots is not None:
    df = df[df["shot"].isin(selected_shots)].copy()

if df.empty:
    raise ValueError("No data remain after filtering. Check max_rank_in_shot or selected_shots.")

# Quitar puntos que caigan realmente dentro del intervalo cortado
df = df[(df["wavelength"] < cut_min) | (df["wavelength"] > cut_max)].copy()

if df.empty:
    raise ValueError("All points fall inside the removed wavelength interval.")

# =========================================================
# MARKERS BY ELEMENT
# =========================================================

marker_map = {
    "H": "x",
    "Fe": "^",
    "W": "s",
    "Ar": "o"
}

def get_marker(element):
    return marker_map.get(str(element).strip(), "o")

# =========================================================
# COLORS BY SHOT
# =========================================================

unique_shots = sorted(df["shot"].unique())

distinct_colors = [
    "#1f77b4",  # blue
    "#d62728",  # red
    "#2ca02c",  # green
    "#9467bd",  # purple
    "#ff7f0e",  # orange
    "#17becf",  # cyan
    "#8c564b",  # brown
    "#e377c2",  # magenta
    "#bcbd22",  # olive
    "#000000",  # black
    "#7f7f7f",  # gray
    "#005f73",  # dark teal
    "#9b2226",  # dark red
    "#3a0ca3",  # deep violet
    "#f77f00",  # strong orange
    "#008000",  # dark green
    "#00b4d8",  # bright cyan
    "#6a040f",  # wine
    "#ff006e",  # hot pink
    "#4361ee",  # vivid blue
]

shot_color_map = {
    shot: distinct_colors[i % len(distinct_colors)]
    for i, shot in enumerate(unique_shots)
}

# =========================================================
# INTERVAL COMPUTATION
# =========================================================

def get_interval(row):
    wavelength = row["wavelength"]

    if interval_mode == "tolerance":
        if "experimental_wavelength_nm" in row and pd.notna(row["experimental_wavelength_nm"]):
            center = row["experimental_wavelength_nm"]
        else:
            center = wavelength
        return center - window_half_width_nm, center + window_half_width_nm

    elif interval_mode == "match_span":
        if "experimental_wavelength_nm" in row and pd.notna(row["experimental_wavelength_nm"]):
            a = row["experimental_wavelength_nm"]
            b = wavelength
            return min(a, b), max(a, b)
        else:
            return wavelength, wavelength

    else:
        raise ValueError("interval_mode must be 'tolerance' or 'match_span'.")

# =========================================================
# X LIMITS FOR EACH PANEL
# =========================================================

left_df = df[df["wavelength"] < cut_min].copy()
right_df = df[df["wavelength"] > cut_max].copy()

if left_df.empty or right_df.empty:
    raise ValueError(
        "To use the broken axis, you need points on both sides of the removed interval."
    )

left_min = left_df["wavelength"].min()
left_max = left_df["wavelength"].max()
right_min = right_df["wavelength"].min()
right_max = right_df["wavelength"].max()

left_margin = max(0.5, 0.06 * (left_max - left_min if left_max > left_min else 1.0))
right_margin = max(0.5, 0.06 * (right_max - right_min if right_max > right_min else 1.0))

# =========================================================
# FIGURE WITH BROKEN X AXIS
# =========================================================

fig, (ax1, ax2) = plt.subplots(
    1, 2,
    sharey=True,
    figsize=figsize,
    gridspec_kw={"width_ratios": [1, 1]}
)

# =========================================================
# LABEL OFFSET FUNCTION
# =========================================================

def get_label_offset(idx):
    """
    Alterna offsets para evitar superposición excesiva.
    """
    offsets = [
        (4, 6),
        (4, -10),
        (-18, 6),
        (-18, -10),
        (8, 12),
        (8, -16),
        (-24, 12),
        (-24, -16),
    ]
    return offsets[idx % len(offsets)]

# =========================================================
# DRAW DATA
# =========================================================

for i, (_, row) in enumerate(df.iterrows()):
    shot = int(row["shot"])
    wavelength = row["wavelength"]
    intensity = row["intensity"]
    element = str(row["type of element"]).strip()
    rank = int(row["rank_in_shot"])

    color = shot_color_map[shot]
    marker = get_marker(element)

    x0, x1 = get_interval(row)

    # Elegir eje según longitud de onda
    if wavelength < cut_min:
        ax = ax1
    elif wavelength > cut_max:
        ax = ax2
    else:
        continue

    # Barra horizontal del intervalo
    x0_plot = x0
    x1_plot = x1

    # Recortar la barra al rango visible del panel
    if ax is ax1:
        x0_plot = min(max(x0, left_min - left_margin), left_max + left_margin)
        x1_plot = min(max(x1, left_min - left_margin), left_max + left_margin)
    else:
        x0_plot = min(max(x0, right_min - right_margin), right_max + right_margin)
        x1_plot = min(max(x1, right_min - right_margin), right_max + right_margin)

    ax.hlines(
        y=intensity,
        xmin=x0_plot,
        xmax=x1_plot,
        color=color,
        linewidth=interval_linewidth,
        alpha=interval_alpha,
        zorder=2
    )

    # Punto
    ax.scatter(
        wavelength,
        intensity,
        color=color,
        edgecolor="black",
        linewidth=0.5,
        marker=marker,
        s=marker_size,
        zorder=3
    )

    # Etiqueta
    if show_rank_label:
        dx, dy = get_label_offset(i)
        label_text = f"{element} r{rank}"
        ax.annotate(
            label_text,
            (wavelength, intensity),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=label_fontsize
        )

# =========================================================
# AXIS FORMATTING
# =========================================================

ax1.set_xlim(left_min - left_margin, left_max + left_margin)
ax2.set_xlim(right_min - right_margin, right_max + right_margin)

ax1.grid(True, alpha=0.3)
ax2.grid(True, alpha=0.3)

ax1.set_ylabel("Intensity [a.u.]", fontsize=12)
fig.supxlabel("Wavelength [nm]", fontsize=12)
fig.suptitle(
    f"Matched spectroscopy lines up to rank_in_shot = {max_rank_in_shot}",
    fontsize=18
)

# Esconder espinas entre ejes
ax1.spines["right"].set_visible(False)
ax2.spines["left"].set_visible(False)
ax2.yaxis.tick_right()
ax2.tick_params(labelright=False)
ax2.tick_params(right=False)

# Marcas diagonales para indicar eje roto
d = 0.015
kwargs = dict(transform=ax1.transAxes, color='k', clip_on=False)
ax1.plot((1 - d, 1 + d), (-d, +d), **kwargs)
ax1.plot((1 - d, 1 + d), (1 - d, 1 + d), **kwargs)

kwargs.update(transform=ax2.transAxes)
ax2.plot((-d, +d), (-d, +d), **kwargs)
ax2.plot((-d, +d), (1 - d, 1 + d), **kwargs)

# =========================================================
# LEGENDS
# =========================================================

shot_handles = [
    Line2D(
        [0], [0],
        marker='o',
        color='w',
        markerfacecolor=shot_color_map[shot],
        markeredgecolor="black",
        markersize=9,
        label=f"Shot {shot}"
    )
    for shot in unique_shots
]

element_handles = [
    Line2D([0], [0], marker='x', color='black', linestyle='None', markersize=8, label='H'),
    Line2D([0], [0], marker='^', color='black', linestyle='None', markersize=8, label='Fe'),
    Line2D([0], [0], marker='s', color='black', linestyle='None', markersize=8, label='W'),
    Line2D([0], [0], marker='o', color='black', linestyle='None', markersize=8, label='Other'),
]

legend1 = ax2.legend(
    handles=shot_handles,
    title="Shots",
    loc="upper left",
    bbox_to_anchor=(1.10, 1.0),
    fontsize=11,
    title_fontsize=12
)
ax2.add_artist(legend1)

ax2.legend(
    handles=element_handles,
    title="Element markers",
    loc="upper left",
    bbox_to_anchor=(1.10, 0.62),
    fontsize=11,
    title_fontsize=12
)

plt.tight_layout()
plt.show()