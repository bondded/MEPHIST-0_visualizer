"""
MEPHIST-0 spectroscopy: wavelength-cluster Voigt area by shot + statistical element sums.

Purpose
-------
This script separates two different questions that should not be mixed:

1) What is the measured Voigt area of the experimental peak at a given wavelength
   for each shot?
   -> This is independent of the element candidate assigned by NIST/Voigt ranking.

2) Once a wavelength cluster has been statistically associated with an element
   using repeated shots, how much total Voigt area does that element contribute
   in each shot?
   -> This sums the measured peak areas of all wavelength clusters whose
      dominant/statistical label is that element.

Input
-----
An Excel workbook exported by the visualizer containing a 'voigt_candidates'
sheet. The script also works if the file extension is .csv but the content is
actually an Excel workbook, as can happen with manual exports.

Output sheets
-------------
- Rank 1 Candidate Counts:
    Statistical element/ion counts by wavelength cluster using rank-1 candidates.
- Rank 2 Candidate Counts:
    Same for rank-2 candidates.
- Rank 3 Candidate Counts:
    Same for rank-3 candidates.
- All Candidate Counts:
    Counts whether an element/ion appears among rank 1-3 candidates.
- Wavelength Element Map:
    The final statistical label assigned to each wavelength cluster.
- Voigt Area By Wavelength Shot:
    The measured Voigt area for each wavelength cluster and each shot,
    independent of the assigned element.
- Voigt Area Sum By Statistical Element Shot:
    For each shot, sum of measured Voigt areas grouped by the statistical
    element label of the wavelength cluster.
- Voigt Area Sum By Statistical Ion Shot:
    Same idea, but separated by element + ionization state.
- Configuration:
    Parameters and detected input columns.

Important concept
-----------------
The Voigt area belongs to the measured experimental peak, not to a NIST element
candidate. Therefore, the area should be obtained once per shot/wavelength
cluster, and only afterward mapped to an element using the statistical element
classification obtained across all shots.
"""

from __future__ import annotations

from pathlib import Path
import math
import re

import numpy as np
import pandas as pd

# ============================================================
# USER CONFIGURATION
# ============================================================
INPUT_PATH = Path(r"C:\Users\chelo\Desktop\MephiST\Descargas\Nuevas descargas\Versión reporte\descargas antiguas candidatos y elegidos.xlsx")
OUTPUT_PATH = Path(r"C:\Users\chelo\Desktop\MephiST\Descargas\Nuevas descargas\Versión reporte\voigt_peak_area_by_statistical_elementantiguosss.xlsx")

# Peaks in different shots closer than this value are grouped as the same
# experimental wavelength/line. Increase if one physical peak is split into two
# rows; decrease if different nearby peaks are merged.
WAVELENGTH_CLUSTER_TOL_NM = 0.45

# Candidate ranks to count statistically.
RANKS_TO_EXPORT = [1, 2, 3]

# Filters. Keep conservative first. If you get too many missing cells, try:
#   USE_ONLY_VOIGT_QUALITY_OK = False
#   MAX_ABS_DELTA_NM = None
USE_ONLY_VOIGT_QUALITY_OK = True
MAX_ABS_DELTA_NM = 0.85
MIN_VOIGT_AREA = 0.0
MIN_PEAK_HEIGHT = 0.0

# Wavelength-cluster element label used to sum areas by element.
# Options:
#   "rank1_dominant" -> dominant element among rank-1 candidates.
#   "all_dominant"   -> dominant element among rank 1-3 candidates.
CLUSTER_LABEL_SOURCE = "rank1_dominant"

# If a wavelength cluster has no measured area for a given shot, use 0 in the
# element-sum table. This is practical for integrated totals, but remember that
# 0 can also mean "fit missing or peak not detected", not necessarily true zero.
MISSING_AREA_AS_ZERO_IN_SUMS = True

# In the wavelength-by-shot table, keep missing values as blank/NaN so you can
# see where no fitted peak/cluster was found.
MISSING_AREA_AS_ZERO_IN_WAVELENGTH_TABLE = False

# Representative intensity shown in the first column.
# Options: 'max_peak_height', 'median_peak_height', 'max_area', 'median_area'
INTENSITY_MODE = "max_peak_height"

# Preferred element order. Other elements found in the file are appended after these.
PREFERRED_ELEMENT_ORDER = ["H", "Fe", "Li", "W", "C", "N", "O"]

# Shot order requested by the user.
SHOT_GROUP_ORDER = [
    ("1.2 mPa", ["4255", "4258", "4259"]),
    ("1.5 mPa", ["4244", "4251", "4256", "4257", "4262"]),
    ("1.8 mPa", ["4242", "4245", "4249", "4254", "4260", "4261", "4263"]),
    ("2.1 mPa", ["4241", "4243", "4250", "4252", "4253"]),
    ("3.3 mPa", ["4247", "4246", "4248", "4266", "4265"]),
    ("5 mPa", ["4264"]),
]
INCLUDE_EXTRA_SHOTS_AFTER_ORDER = True

# ============================================================
# BASIC HELPERS
# ============================================================
def normalize_column_name(name: str) -> str:
    text = str(name).strip().lower().replace("λ", "lambda")
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def make_column_lookup(columns) -> dict[str, str]:
    return {normalize_column_name(c): c for c in columns}


def find_column(df: pd.DataFrame, aliases: list[str], required: bool = True) -> str | None:
    lookup = make_column_lookup(df.columns)
    for alias in aliases:
        key = normalize_column_name(alias)
        if key in lookup:
            return lookup[key]

    # fallback: all words contained in normalized column name
    for alias in aliases:
        words = [w for w in normalize_column_name(alias).split("_") if w]
        for key, original in lookup.items():
            if all(w in key for w in words):
                return original

    if required:
        raise KeyError(
            f"Could not find required column. Tried aliases={aliases}.\n"
            f"Available columns are:\n{list(df.columns)}"
        )
    return None


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def truthy_series(series: pd.Series) -> pd.Series:
    if series is None:
        return pd.Series(False)
    s = series.astype(str).str.strip().str.lower()
    return s.isin(["1", "true", "t", "yes", "y", "ok"])


def roman_sort_key(ion: str) -> tuple[int, str]:
    roman = {
        "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
        "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11, "XII": 12,
    }
    ion = str(ion).strip()
    return (roman.get(ion, 999), ion)


def clean_element(value) -> str:
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "unknown"}:
        return "Unknown"
    m = re.match(r"([A-Za-z]{1,2})", s)
    if not m:
        return s
    sym = m.group(1)
    return sym[0].upper() + sym[1:].lower()


def clean_ion(value) -> str:
    s = str(value).strip()
    if not s or s.lower() in {"nan", "none", "unknown"}:
        return "Unknown"
    return s.upper()


def numeric_shot_sort_key(shot: str):
    s = str(shot).strip()
    m = re.search(r"\d+", s)
    if m:
        return (0, int(m.group(0)), s)
    return (1, math.inf, s)


def get_requested_shot_order(work: pd.DataFrame) -> list[tuple[str, str]]:
    available = set(work["_shot"].astype(str).str.strip())
    ordered: list[tuple[str, str]] = []
    used = set()

    for group_label, shots in SHOT_GROUP_ORDER:
        for shot in shots:
            shot_s = str(shot).strip()
            ordered.append((group_label, shot_s))
            if shot_s in available:
                used.add(shot_s)

    if INCLUDE_EXTRA_SHOTS_AFTER_ORDER:
        extras = sorted(available - used, key=numeric_shot_sort_key)
        for shot in extras:
            ordered.append(("Extra", shot))

    return ordered


def pretty_header(name: str) -> str:
    """Readable multiline headers for Excel: Wavelength [nm] -> Wavelength\n[nm]."""
    text = str(name).strip().replace("_", " ")

    unit = None
    m = re.search(r"\[([^\]]+)\]", text)
    if m:
        unit = m.group(1)
        text = re.sub(r"\s*\[[^\]]+\]\s*", " ", text).strip()

    suffix_units = {
        " nm": "nm",
        " ms": "ms",
        " kA": "kA",
        " mT": "mT",
        " mPa": "mPa",
        " counts": "counts",
        " counts nm": "counts nm",
        " %": "%",
    }
    for suffix, detected_unit in sorted(suffix_units.items(), key=lambda x: len(x[0]), reverse=True):
        if text.endswith(suffix):
            text = text[: -len(suffix)].strip()
            unit = unit or detected_unit
            break

    words = [w for w in re.split(r"\s+", text) if w]
    header = "\n".join(words)
    if unit:
        header += f"\n[{unit}]"
    return header

# ============================================================
# INPUT LOADING AND PREPARATION
# ============================================================
def load_voigt_table(input_path: Path) -> tuple[pd.DataFrame, str]:
    input_path = Path(input_path)
    try:
        xls = pd.ExcelFile(input_path)
        lower = {s.lower(): s for s in xls.sheet_names}
        if "voigt_candidates" in lower:
            sheet = lower["voigt_candidates"]
        elif "voigt_best" in lower:
            sheet = lower["voigt_best"]
        else:
            sheet = xls.sheet_names[0]
        return pd.read_excel(input_path, sheet_name=sheet), sheet
    except Exception:
        return pd.read_csv(input_path, sep=None, engine="python"), "csv"


def prepare_voigt_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None]]:
    shot_col = find_column(df, ["Shot"])
    element_col = find_column(df, ["Type Of Element", "Element", "Type Element"])
    ion_col = find_column(df, ["Ionization State", "Ion"])
    wl_col = find_column(
        df,
        [
            "Experimental Calibrated Wavelength nm",
            "Experimental Calibrated Wavelength",
            "Lambda Fit Calibrated nm",
            "Wavelength",
            "Lambda Nist nm",
        ],
    )
    rank_col = find_column(df, ["Candidate Rank For Feature", "Rank In Shot", "Global Rank In Shot"])
    feature_rank_col = find_column(df, ["Feature Rank In Shot"], required=False)
    area_col = find_column(df, ["Voigt Area"], required=False)
    peak_col = find_column(df, ["Voigt Peak Height", "Peak Height"], required=False)
    score_col = find_column(df, ["Candidate Score", "Fit Quality Score", "Voigt Area"], required=False)
    quality_col = find_column(df, ["Voigt Quality Ok"], required=False)
    delta_col = find_column(df, ["Delta nm", "Delta"], required=False)

    work = df.copy()
    work["_shot"] = work[shot_col].astype(str).str.strip()
    work["_element"] = work[element_col].map(clean_element)
    work["_ion"] = work[ion_col].map(clean_ion)
    work["_element_ion"] = work["_element"] + " " + work["_ion"]
    work["_wavelength_nm"] = to_number(work[wl_col])
    work["_candidate_rank"] = to_number(work[rank_col]).round().astype("Int64")

    if feature_rank_col is not None:
        work["_feature_rank"] = to_number(work[feature_rank_col]).round().astype("Int64")
    else:
        work["_feature_rank"] = (work["_wavelength_nm"] / max(WAVELENGTH_CLUSTER_TOL_NM, 1e-9)).round().astype("Int64")

    work["_voigt_area"] = to_number(work[area_col]) if area_col is not None else np.nan
    work["_peak_height"] = to_number(work[peak_col]) if peak_col is not None else np.nan
    work["_score"] = to_number(work[score_col]) if score_col is not None else work["_voigt_area"]

    work = work.dropna(subset=["_wavelength_nm", "_candidate_rank"])

    if USE_ONLY_VOIGT_QUALITY_OK and quality_col is not None:
        work = work[truthy_series(work[quality_col])].copy()
    if MAX_ABS_DELTA_NM is not None and delta_col is not None:
        delta = to_number(work[delta_col]).abs()
        work = work[(delta <= float(MAX_ABS_DELTA_NM)) | delta.isna()].copy()
    if MIN_VOIGT_AREA is not None and area_col is not None:
        work = work[(work["_voigt_area"] >= float(MIN_VOIGT_AREA)) | work["_voigt_area"].isna()].copy()
    if MIN_PEAK_HEIGHT is not None and peak_col is not None:
        work = work[(work["_peak_height"] >= float(MIN_PEAK_HEIGHT)) | work["_peak_height"].isna()].copy()

    cols = {
        "shot_col": shot_col,
        "element_col": element_col,
        "ion_col": ion_col,
        "wavelength_col": wl_col,
        "candidate_rank_col": rank_col,
        "feature_rank_col": feature_rank_col,
        "voigt_area_col": area_col,
        "peak_height_col": peak_col,
        "score_col": score_col,
        "quality_col": quality_col,
        "delta_col": delta_col,
    }
    return work, cols


def add_wavelength_clusters(work: pd.DataFrame, tolerance_nm: float) -> pd.DataFrame:
    """Cluster measured features across shots by calibrated wavelength."""
    feature_keys = ["_shot", "_feature_rank"]
    features = (
        work.groupby(feature_keys, dropna=False)
        .agg(
            _feature_wavelength_nm=("_wavelength_nm", "median"),
            _feature_peak_height=("_peak_height", "max"),
            _feature_area=("_voigt_area", "max"),
        )
        .reset_index()
        .sort_values("_feature_wavelength_nm")
    )

    cluster_ids = []
    current_cluster = -1
    current_values = []

    for wl in features["_feature_wavelength_nm"].to_numpy(dtype=float):
        if len(current_values) == 0:
            current_cluster += 1
            current_values = [wl]
        else:
            center = float(np.nanmedian(current_values))
            if abs(wl - center) <= tolerance_nm:
                current_values.append(wl)
            else:
                current_cluster += 1
                current_values = [wl]
        cluster_ids.append(current_cluster)

    features["_cluster_id"] = cluster_ids
    centers = features.groupby("_cluster_id")["_feature_wavelength_nm"].median().rename("_cluster_wavelength_nm")
    features = features.merge(centers, on="_cluster_id", how="left")

    return work.merge(features[feature_keys + ["_cluster_id", "_cluster_wavelength_nm"]], on=feature_keys, how="left")

# ============================================================
# STATISTICAL CANDIDATE COUNT TABLES
# ============================================================
def ordered_elements(work: pd.DataFrame) -> list[str]:
    found = sorted(set(work["_element"].dropna().astype(str)))
    out = [e for e in PREFERRED_ELEMENT_ORDER if e in found]
    out += [e for e in found if e not in out]
    return out


def build_element_count_columns(work: pd.DataFrame) -> list[str]:
    cols = []
    for elem in ordered_elements(work):
        ions = sorted(set(work.loc[work["_element"] == elem, "_ion"].astype(str)), key=roman_sort_key)
        cols.append(f"{elem} Total")
        for ion in ions:
            cols.append(f"{elem} {ion}")
    return cols


def representative_intensity(rows: pd.DataFrame) -> float:
    if INTENSITY_MODE == "max_peak_height":
        return float(np.nanmax(rows["_peak_height"])) if rows["_peak_height"].notna().any() else np.nan
    if INTENSITY_MODE == "median_peak_height":
        return float(np.nanmedian(rows["_peak_height"])) if rows["_peak_height"].notna().any() else np.nan
    if INTENSITY_MODE == "max_area":
        return float(np.nanmax(rows["_voigt_area"])) if rows["_voigt_area"].notna().any() else np.nan
    if INTENSITY_MODE == "median_area":
        return float(np.nanmedian(rows["_voigt_area"])) if rows["_voigt_area"].notna().any() else np.nan
    raise ValueError(f"Unknown INTENSITY_MODE={INTENSITY_MODE}")


def select_one_candidate_per_shot_cluster(rank_rows: pd.DataFrame) -> pd.DataFrame:
    if rank_rows.empty:
        return rank_rows.copy()
    rows = rank_rows.sort_values(
        ["_cluster_id", "_shot", "_score", "_voigt_area"],
        ascending=[True, True, False, False],
    )
    return rows.drop_duplicates(["_cluster_id", "_shot"], keep="first").copy()


def count_table_for_subset(work: pd.DataFrame, subset: pd.DataFrame, element_columns: list[str]) -> pd.DataFrame:
    out_rows = []
    for cid in sorted(work["_cluster_id"].dropna().unique()):
        cluster_all = work[work["_cluster_id"] == cid]
        cluster_subset = subset[subset["_cluster_id"] == cid]
        n_assignments = int(len(cluster_subset))
        n_shots_with_peak = int(cluster_all["_shot"].nunique())

        row = {
            "Intensity [counts]": representative_intensity(cluster_all),
            "Wavelength [nm]": float(np.nanmedian(cluster_all["_cluster_wavelength_nm"])),
            "Number Of Shots With Peak": n_shots_with_peak,
            "Number Of Assignments Counted": n_assignments,
            "Dominant Element": "",
            "Dominant Element Count": 0,
            "Dominant Element Fraction [%]": np.nan,
            "Dominant Ion Label": "",
            "Dominant Ion Count": 0,
            "Dominant Ion Fraction [%]": np.nan,
        }
        for col in element_columns:
            row[col] = 0

        if not cluster_subset.empty:
            ion_counts = cluster_subset.groupby(["_element", "_ion"]).size()
            for (elem, ion), count in ion_counts.items():
                key = f"{elem} {ion}"
                if key in row:
                    row[key] = int(count)

            elem_counts = cluster_subset.groupby("_element").size().sort_values(ascending=False)
            for elem, count in elem_counts.items():
                key = f"{elem} Total"
                if key in row:
                    row[key] = int(count)

            if len(elem_counts):
                dom_elem = str(elem_counts.index[0])
                dom_count = int(elem_counts.iloc[0])
                row["Dominant Element"] = dom_elem
                row["Dominant Element Count"] = dom_count
                row["Dominant Element Fraction [%]"] = 100.0 * dom_count / max(n_assignments, 1)

            ion_counts_sorted = ion_counts.sort_values(ascending=False)
            if len(ion_counts_sorted):
                elem_ion = ion_counts_sorted.index[0]
                ion_label = f"{elem_ion[0]} {elem_ion[1]}"
                ion_count = int(ion_counts_sorted.iloc[0])
                row["Dominant Ion Label"] = ion_label
                row["Dominant Ion Count"] = ion_count
                row["Dominant Ion Fraction [%]"] = 100.0 * ion_count / max(n_assignments, 1)

        out_rows.append(row)

    df = pd.DataFrame(out_rows).sort_values("Wavelength [nm]").reset_index(drop=True)
    fixed = [
        "Intensity [counts]", "Wavelength [nm]", "Number Of Shots With Peak",
        "Number Of Assignments Counted", "Dominant Element", "Dominant Element Count",
        "Dominant Element Fraction [%]", "Dominant Ion Label", "Dominant Ion Count",
        "Dominant Ion Fraction [%]",
    ]
    return df[fixed + [c for c in df.columns if c not in fixed]]


def build_candidate_count_tables(work: pd.DataFrame) -> dict[str, pd.DataFrame]:
    element_columns = build_element_count_columns(work)
    tables = {}

    for rank in RANKS_TO_EXPORT:
        rr = select_one_candidate_per_shot_cluster(work[work["_candidate_rank"] == rank].copy())
        tables[f"Rank {rank} Candidate Counts"] = count_table_for_subset(work, rr, element_columns)

    all_rows = work[work["_candidate_rank"].isin(RANKS_TO_EXPORT)].copy()
    all_rows = all_rows.sort_values(["_cluster_id", "_shot", "_element", "_ion", "_candidate_rank"])
    all_rows = all_rows.drop_duplicates(["_cluster_id", "_shot", "_element", "_ion"], keep="first")
    tables["All Candidate Counts"] = count_table_for_subset(work, all_rows, element_columns)
    return tables

# ============================================================
# MEASURED VOIGT AREA TABLES
# ============================================================
def feature_area_table(work: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse candidate rows into one measured feature area per shot/cluster.

    This is the key correction: the area is obtained from the fitted experimental
    feature and does not depend on the candidate element assignment.
    """
    features = (
        work.groupby(["_cluster_id", "_shot", "_feature_rank"], dropna=False)
        .agg(
            feature_wavelength_nm=("_wavelength_nm", "median"),
            feature_peak_height=("_peak_height", "max"),
            feature_voigt_area=("_voigt_area", "max"),
        )
        .reset_index()
    )

    # If several fitted features from the same shot fall into the same wavelength
    # cluster, keep the strongest. This avoids double counting close duplicate fits.
    shot_area = (
        features.groupby(["_cluster_id", "_shot"], dropna=False)
        .agg(
            shot_voigt_area=("feature_voigt_area", "max"),
            shot_peak_height=("feature_peak_height", "max"),
            shot_feature_wavelength_nm=("feature_wavelength_nm", "median"),
        )
        .reset_index()
    )
    return shot_area


def dominant_label_table(work: pd.DataFrame) -> pd.DataFrame:
    """
    Assign one statistical element/ion label to every wavelength cluster.

    The label comes from repeated candidate assignments across shots, not from
    the individual shot whose area is later summed.
    """
    rows = []
    for cid in sorted(work["_cluster_id"].dropna().unique()):
        cluster = work[work["_cluster_id"] == cid]
        wl = float(np.nanmedian(cluster["_cluster_wavelength_nm"]))
        intensity = representative_intensity(cluster)
        n_shots = int(cluster["_shot"].nunique())

        rank1 = select_one_candidate_per_shot_cluster(cluster[cluster["_candidate_rank"] == 1].copy())
        allc = cluster[cluster["_candidate_rank"].isin(RANKS_TO_EXPORT)].copy()
        allc = allc.drop_duplicates(["_cluster_id", "_shot", "_element", "_ion"], keep="first")

        def dom_info(sub: pd.DataFrame) -> dict:
            if sub.empty:
                return {
                    "element": "Unassigned", "element_count": 0, "element_fraction": np.nan,
                    "ion_label": "Unassigned", "ion_count": 0, "ion_fraction": np.nan,
                }
            elem_counts = sub.groupby("_element").size().sort_values(ascending=False)
            elem = str(elem_counts.index[0])
            elem_count = int(elem_counts.iloc[0])
            ion_counts = sub.groupby(["_element", "_ion"]).size().sort_values(ascending=False)
            ion_pair = ion_counts.index[0]
            ion_label = f"{ion_pair[0]} {ion_pair[1]}"
            ion_count = int(ion_counts.iloc[0])
            denom = max(int(sub["_shot"].nunique()), 1)
            return {
                "element": elem,
                "element_count": elem_count,
                "element_fraction": 100.0 * elem_count / denom,
                "ion_label": ion_label,
                "ion_count": ion_count,
                "ion_fraction": 100.0 * ion_count / denom,
            }

        d1 = dom_info(rank1)
        da = dom_info(allc)
        if CLUSTER_LABEL_SOURCE == "all_dominant":
            final_element = da["element"]
            final_ion_label = da["ion_label"]
            final_fraction = da["element_fraction"]
        else:
            final_element = d1["element"]
            final_ion_label = d1["ion_label"]
            final_fraction = d1["element_fraction"]

        rows.append({
            "Cluster Id": int(cid),
            "Intensity [counts]": intensity,
            "Wavelength [nm]": wl,
            "Number Of Shots With Peak": n_shots,
            "Final Statistical Element": final_element,
            "Final Statistical Ion Label": final_ion_label,
            "Final Statistical Element Fraction [%]": final_fraction,
            "Rank 1 Dominant Element": d1["element"],
            "Rank 1 Dominant Element Count": d1["element_count"],
            "Rank 1 Dominant Element Fraction [%]": d1["element_fraction"],
            "Rank 1 Dominant Ion Label": d1["ion_label"],
            "Rank 1 Dominant Ion Count": d1["ion_count"],
            "Rank 1 Dominant Ion Fraction [%]": d1["ion_fraction"],
            "All Candidates Dominant Element": da["element"],
            "All Candidates Dominant Element Count": da["element_count"],
            "All Candidates Dominant Element Fraction [%]": da["element_fraction"],
            "All Candidates Dominant Ion Label": da["ion_label"],
            "All Candidates Dominant Ion Count": da["ion_count"],
            "All Candidates Dominant Ion Fraction [%]": da["ion_fraction"],
        })

    return pd.DataFrame(rows).sort_values("Wavelength [nm]").reset_index(drop=True)


def build_voigt_area_by_wavelength_shot(work: pd.DataFrame, label_map: pd.DataFrame, shot_area: pd.DataFrame) -> pd.DataFrame:
    shot_order = get_requested_shot_order(work)
    area_lookup = {
        (int(r["_cluster_id"]), str(r["_shot"]).strip()): r["shot_voigt_area"]
        for _, r in shot_area.iterrows()
        if pd.notna(r["_cluster_id"])
    }

    label_by_cluster = label_map.set_index("Cluster Id").to_dict(orient="index")
    rows = []
    for cid in sorted(work["_cluster_id"].dropna().unique()):
        cid_i = int(cid)
        lm = label_by_cluster.get(cid_i, {})
        cluster_areas = pd.to_numeric(
            shot_area.loc[shot_area["_cluster_id"] == cid, "shot_voigt_area"], errors="coerce"
        ).dropna()

        row = {
            "Intensity [counts]": lm.get("Intensity [counts]", np.nan),
            "Wavelength [nm]": lm.get("Wavelength [nm]", np.nan),
            "Final Statistical Element": lm.get("Final Statistical Element", ""),
            "Final Statistical Ion Label": lm.get("Final Statistical Ion Label", ""),
            "Final Statistical Element Fraction [%]": lm.get("Final Statistical Element Fraction [%]", np.nan),
            "Number Of Shots With Peak": lm.get("Number Of Shots With Peak", np.nan),
            "Mean Voigt Area [counts nm]": float(cluster_areas.mean()) if len(cluster_areas) else np.nan,
            "Median Voigt Area [counts nm]": float(cluster_areas.median()) if len(cluster_areas) else np.nan,
            "Max Voigt Area [counts nm]": float(cluster_areas.max()) if len(cluster_areas) else np.nan,
            "Min Voigt Area [counts nm]": float(cluster_areas.min()) if len(cluster_areas) else np.nan,
            "Std Voigt Area [counts nm]": float(cluster_areas.std(ddof=1)) if len(cluster_areas) > 1 else np.nan,
        }

        for group_label, shot in shot_order:
            value = area_lookup.get((cid_i, str(shot).strip()), np.nan)
            if MISSING_AREA_AS_ZERO_IN_WAVELENGTH_TABLE and pd.isna(value):
                value = 0.0
            row[f"{group_label} Shot {shot} Voigt Area [counts nm]"] = value
        rows.append(row)

    return pd.DataFrame(rows).sort_values("Wavelength [nm]").reset_index(drop=True)


def build_area_sum_by_statistical_element_shot(
    work: pd.DataFrame,
    label_map: pd.DataFrame,
    shot_area: pd.DataFrame,
    by_ion: bool = False,
) -> pd.DataFrame:
    """
    Sum measured peak areas by statistical wavelength label.

    This is not per-shot candidate assignment. It uses:
      measured area for cluster c in shot s
      + final statistical label of cluster c from all shots
      -> add area to that element/ion total for shot s.
    """
    shot_order = get_requested_shot_order(work)

    labels = label_map[["Cluster Id", "Final Statistical Element", "Final Statistical Ion Label"]].copy()
    labels = labels.rename(columns={"Cluster Id": "_cluster_id"})
    areas = shot_area.merge(labels, on="_cluster_id", how="left")
    areas["shot_voigt_area"] = pd.to_numeric(areas["shot_voigt_area"], errors="coerce")

    # Define ordered output labels.
    if by_ion:
        labels_found = sorted(set(areas["Final Statistical Ion Label"].dropna().astype(str)))
        # Ordered by preferred element first, then roman ion.
        def ion_label_sort_key(label: str):
            parts = str(label).split()
            elem = parts[0] if parts else "Unknown"
            ion = parts[1] if len(parts) > 1 else "Unknown"
            elem_order = PREFERRED_ELEMENT_ORDER.index(elem) if elem in PREFERRED_ELEMENT_ORDER else 999
            return (elem_order, elem, roman_sort_key(ion), label)
        output_labels = sorted(labels_found, key=ion_label_sort_key)
        value_col = "Final Statistical Ion Label"
        suffix = "Voigt Area [counts nm]"
        sheet_kind = "Ion"
    else:
        elems_found = sorted(set(areas["Final Statistical Element"].dropna().astype(str)))
        output_labels = [e for e in PREFERRED_ELEMENT_ORDER if e in elems_found]
        output_labels += [e for e in elems_found if e not in output_labels]
        value_col = "Final Statistical Element"
        suffix = "Total Voigt Area [counts nm]"
        sheet_kind = "Element"

    rows = []
    for group_label, shot in shot_order:
        shot_s = str(shot).strip()
        shot_rows = areas[areas["_shot"].astype(str).str.strip() == shot_s].copy()

        row = {
            "Group": group_label,
            "Shot": shot_s,
            f"Number Of Fitted Wavelengths Used For {sheet_kind} Sum": int(shot_rows["_cluster_id"].nunique()) if not shot_rows.empty else 0,
            "Total Voigt Area [counts nm]": float(shot_rows["shot_voigt_area"].sum(skipna=True)) if not shot_rows.empty else 0.0,
            f"Dominant {sheet_kind} By Area": "",
            f"Dominant {sheet_kind} Area [counts nm]": np.nan,
            f"Dominant {sheet_kind} Fraction [%]": np.nan,
        }

        for label in output_labels:
            row[f"{label} {suffix}"] = 0.0

        if not shot_rows.empty:
            sums = shot_rows.groupby(value_col)["shot_voigt_area"].sum(min_count=1).dropna()
            for label, area in sums.items():
                key = f"{label} {suffix}"
                if key in row:
                    row[key] = float(area)

            total = float(shot_rows["shot_voigt_area"].sum(skipna=True))
            if len(sums) and total > 0:
                sums_sorted = sums.sort_values(ascending=False)
                dom = str(sums_sorted.index[0])
                dom_area = float(sums_sorted.iloc[0])
                row[f"Dominant {sheet_kind} By Area"] = dom
                row[f"Dominant {sheet_kind} Area [counts nm]"] = dom_area
                row[f"Dominant {sheet_kind} Fraction [%]"] = 100.0 * dom_area / total

        rows.append(row)

    return pd.DataFrame(rows)


def build_all_tables(work: pd.DataFrame) -> dict[str, pd.DataFrame]:
    tables = build_candidate_count_tables(work)
    label_map = dominant_label_table(work)
    shot_area = feature_area_table(work)

    tables["Wavelength Element Map"] = label_map
    tables["Voigt Area By Wavelength Shot"] = build_voigt_area_by_wavelength_shot(work, label_map, shot_area)
    tables["Voigt Area Sum By Statistical Element Shot"] = build_area_sum_by_statistical_element_shot(
        work, label_map, shot_area, by_ion=False
    )
    tables["Voigt Area Sum By Statistical Ion Shot"] = build_area_sum_by_statistical_element_shot(
        work, label_map, shot_area, by_ion=True
    )
    return tables

# ============================================================
# EXCEL EXPORT
# ============================================================
def export_tables_to_excel(tables: dict[str, pd.DataFrame], output_path: Path, config: dict):
    import openpyxl
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
    from openpyxl.utils import get_column_letter

    output_path = Path(output_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, table in tables.items():
            pretty = table.rename(columns={c: pretty_header(c) for c in table.columns})
            pretty.to_excel(writer, sheet_name=sheet_name[:31], index=False)
        pd.DataFrame([{"Parameter": k, "Value": v} for k, v in config.items()]).to_excel(
            writer, sheet_name="Configuration", index=False
        )

    wb = openpyxl.load_workbook(output_path)
    header_fill = PatternFill("solid", fgColor="F4B183")
    header_font = Font(bold=True, color="000000")
    thin = Side(style="thin", color="808080")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for ws in wb.worksheets:
        ws.freeze_panes = "A2"
        ws.sheet_view.showGridLines = True

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border
        ws.row_dimensions[1].height = 78

        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
                cell.border = border

        for col_idx in range(1, ws.max_column + 1):
            letter = get_column_letter(col_idx)
            if col_idx <= 2:
                ws.column_dimensions[letter].width = 14
            elif col_idx <= 8:
                ws.column_dimensions[letter].width = 16
            else:
                ws.column_dimensions[letter].width = 12

        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if isinstance(cell.value, (float, int)) and cell.value is not None:
                    header = str(ws.cell(row=1, column=cell.column).value)
                    if "Fraction" in header:
                        cell.number_format = "0.0"
                    elif "Wavelength" in header:
                        cell.number_format = "0.000"
                    elif "Area" in header or "Intensity" in header:
                        cell.number_format = "0.000"
                    else:
                        cell.number_format = "0"

        ws.auto_filter.ref = ws.dimensions

    wb.save(output_path)

# ============================================================
# MAIN
# ============================================================
def main():
    raw, source_sheet = load_voigt_table(INPUT_PATH)
    work, cols = prepare_voigt_dataframe(raw)
    work = add_wavelength_clusters(work, WAVELENGTH_CLUSTER_TOL_NM)
    tables = build_all_tables(work)

    config = {
        "input_path": str(INPUT_PATH),
        "source_sheet_used": source_sheet,
        "output_path": str(OUTPUT_PATH),
        "wavelength_cluster_tolerance_nm": WAVELENGTH_CLUSTER_TOL_NM,
        "cluster_label_source": CLUSTER_LABEL_SOURCE,
        "ranks_exported": ", ".join(map(str, RANKS_TO_EXPORT)),
        "use_only_voigt_quality_ok": USE_ONLY_VOIGT_QUALITY_OK,
        "max_abs_delta_nm": MAX_ABS_DELTA_NM,
        "min_voigt_area": MIN_VOIGT_AREA,
        "min_peak_height": MIN_PEAK_HEIGHT,
        "intensity_mode": INTENSITY_MODE,
        "missing_area_as_zero_in_sums": MISSING_AREA_AS_ZERO_IN_SUMS,
        "missing_area_as_zero_in_wavelength_table": MISSING_AREA_AS_ZERO_IN_WAVELENGTH_TABLE,
        "unique_shots_in_file": int(work["_shot"].nunique()),
        "n_wavelength_clusters": int(work["_cluster_id"].nunique()),
        "detected_columns": str(cols),
        "shot_group_order": " | ".join([f"{g}: {', '.join(s)}" for g, s in SHOT_GROUP_ORDER]),
    }

    export_tables_to_excel(tables, OUTPUT_PATH, config)
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Source sheet used: {source_sheet}")
    print(f"Unique shots: {work['_shot'].nunique()}")
    print(f"Wavelength clusters: {work['_cluster_id'].nunique()}")


if __name__ == "__main__":
    main()
