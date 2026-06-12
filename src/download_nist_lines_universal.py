"""
download_nist_lines.py

Small standalone script to download local NIST ASD line tables as CSV files.

The output directory is resolved in the same way used by the spectroscopy
filter code in shot_comparison_tab:

Priority:
  1) Environment variable MEPHIST_EMISSION_LINES_DIR
  2) Project folder / "Lineas de emisión"
  3) Current working directory / "Lineas de emisión"

Recommended location in the repository:
  MEPHIST-0_visualizer/
      download_nist_lines.py
      Lineas de emisión/
      src/
          shot_comparison_tab.py
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode
import os
import sys
import requests


NIST_URL = "https://physics.nist.gov/cgi-bin/ASD/lines1.pl"
DEFAULT_FOLDER_NAME = "Lineas de emisión"
ENV_VAR_NAME = "MEPHIST_EMISSION_LINES_DIR"


def get_project_root() -> Path:
    """
    Best-effort project-root detection.

    If this script is inside the project root, return its parent folder.
    If it is inside src/, return the parent of src/.
    Otherwise, use the current working directory.
    """
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent

    if script_dir.name.lower() == "src":
        return script_dir.parent

    # If the script is in the project root, this is already correct.
    if (script_dir / "src").exists() or (script_dir / ".git").exists():
        return script_dir

    # Fallback: current folder from which the script is executed.
    return Path.cwd().resolve()


def get_emission_lines_dir() -> Path:
    """
    Resolve the local folder where NIST CSV files will be saved.

    This matches the logic expected by the updated shot_comparison_tab:
      - If MEPHIST_EMISSION_LINES_DIR exists, use that.
      - Otherwise use a repository-relative folder: "Lineas de emisión".
    """
    env_path = os.environ.get(ENV_VAR_NAME, "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()

    project_root = get_project_root()
    return (project_root / DEFAULT_FOLDER_NAME).resolve()


def build_nist_url(
    element: str,
    low_nm: float,
    high_nm: float,
    ion_range: str = "",
) -> str:
    """
    Build a NIST ASD Lines URL.

    Examples
    --------
    element="Fe", ion_range=""      -> spectra="Fe"
    element="Fe", ion_range="I"     -> spectra="Fe I"
    element="Fe", ion_range="I-II"  -> spectra="Fe I-II"
    element="Ar", ion_range="I-II"  -> spectra="Ar I-II"

    The output is configured for CSV text and for wavelengths in nm.
    """
    element = element.strip()
    ion_range = ion_range.strip()

    if not element:
        raise ValueError("Element cannot be empty.")

    spectra = f"{element} {ion_range}" if ion_range else element

    params = {
        "spectra": spectra,
        "output_type": 0,
        "low_w": low_nm,
        "upp_w": high_nm,
        "unit": 1,              # nm
        "submit": "Retrieve Data",
        "de": 0,
        "plot_out": 0,
        "I_scale_type": 1,

        # CSV text output
        # This is the format later read by shot_comparison_tab.
        "format": 2,

        "line_out": 0,
        "en_unit": 0,           # cm^-1
        "output": 0,
        "bibrefs": 1,
        "page_size": 100000,

        # Wavelength data
        "show_obs_wl": 1,
        "show_calc_wl": 1,
        "unc_out": 1,

        # Output ordering: wavelength
        "order_out": 0,

        # Optional criteria: leave empty to avoid losing candidate lines
        "max_low_enrg": "",
        "max_upp_enrg": "",
        "tsb_value": 0,
        "min_str": "",
        "max_str": "",
        "min_accur": "",
        "min_intens": "",

        # Transition strength / relative intensity
        "A_out": 1,
        "intens_out": "on",

        # Include both allowed and forbidden lines
        "allowed_out": 1,
        "forbid_out": 1,

        # Level information
        "show_av": 2,
        "conf_out": "on",
        "term_out": "on",
        "enrg_out": "on",
        "J_out": "on",

        # Practical output options
        # These names are accepted by the NIST endpoint in many queries;
        # if ignored by NIST, the CSV is still readable by the robust parser.
        "no_spaces": "on",
    }

    return NIST_URL + "?" + urlencode(params)


def sanitize_filename_part(text: str) -> str:
    """Return a simple filesystem-safe token."""
    text = text.strip().replace(" ", "_").replace("-", "_")
    keep = []
    for ch in text:
        if ch.isalnum() or ch in ["_", "."]:
            keep.append(ch)
    return "".join(keep)


def make_output_filename(
    element: str,
    ion_range: str,
    low_nm: float,
    high_nm: float,
) -> str:
    """
    Create a consistent filename.

    Example:
      Fe + I-II + 290 + 1110 -> Fe_I_II_290_1110_nm.csv
    """
    element_part = sanitize_filename_part(element)

    ion_part = sanitize_filename_part(ion_range)
    if ion_part:
        stem = f"{element_part}_{ion_part}"
    else:
        stem = element_part

    return f"{stem}_{low_nm:g}_{high_nm:g}_nm.csv"


def looks_like_nist_error(text: str) -> bool:
    """Detect common NIST error/empty-result pages."""
    lowered = text.lower()
    error_markers = [
        "error",
        "no lines were found",
        "invalid",
        "not recognized",
        "no data",
    ]
    return any(marker in lowered for marker in error_markers)


def download_nist_csv(
    element: str,
    low_nm: float,
    high_nm: float,
    ion_range: str = "",
    output_dir: Path | None = None,
    overwrite: bool = True,
) -> Path:
    """
    Download one NIST CSV file and save it in the local emission-line folder.
    """
    if low_nm >= high_nm:
        raise ValueError("low_nm must be smaller than high_nm.")

    if output_dir is None:
        output_dir = get_emission_lines_dir()

    output_dir.mkdir(parents=True, exist_ok=True)

    url = build_nist_url(
        element=element,
        ion_range=ion_range,
        low_nm=low_nm,
        high_nm=high_nm,
    )

    filename = make_output_filename(
        element=element,
        ion_range=ion_range,
        low_nm=low_nm,
        high_nm=high_nm,
    )
    file_path = output_dir / filename

    if file_path.exists() and not overwrite:
        print(f"File already exists and overwrite=False:\n{file_path}")
        return file_path

    spectra = f"{element.strip()} {ion_range.strip()}".strip()

    print("\nConsulting NIST ASD...")
    print(f"Spectrum: {spectra}")
    print(f"Wavelength range: {low_nm:g} - {high_nm:g} nm")
    print(f"Output folder: {output_dir}")
    print(f"Output file: {file_path.name}")
    print(f"URL:\n{url}\n")

    response = requests.get(url, timeout=90)
    response.raise_for_status()

    text = response.text

    # Save anyway, but warn if it looks like an error page.
    file_path.write_text(text, encoding="utf-8")

    if looks_like_nist_error(text):
        print(
            "\nWarning: the downloaded file may contain a NIST message/error "
            "instead of a normal table. Open the CSV and check the first lines."
        )

    print(f"\nSaved successfully:\n{file_path.resolve()}")
    return file_path


def interactive_main() -> None:
    print("=== NIST ASD emission-line CSV downloader ===")
    print(f"Default output folder:\n{get_emission_lines_dir()}\n")
    print(
        "Tip: set the environment variable "
        f"{ENV_VAR_NAME} to use another folder without editing the code.\n"
    )

    element = input("Chemical element, e.g. H, Fe, W, Ar: ").strip()

    ion_range = input(
        "Ionization state/range, e.g. I, II, I-II, I-III "
        "(leave empty for all available): "
    ).strip()

    low_nm = float(input("Minimum wavelength [nm], e.g. 290: ").strip())
    high_nm = float(input("Maximum wavelength [nm], e.g. 1110: ").strip())

    download_nist_csv(
        element=element,
        ion_range=ion_range,
        low_nm=low_nm,
        high_nm=high_nm,
    )


def cli_main(argv: list[str]) -> None:
    """
    Optional command-line usage:
      python download_nist_lines.py Fe I-II 290 1110
      python download_nist_lines.py H I 290 1110
    """
    if len(argv) == 1:
        interactive_main()
        return

    if len(argv) not in [4, 5]:
        print(
            "Usage:\n"
            "  python download_nist_lines.py\n"
            "  python download_nist_lines.py Fe I-II 290 1110\n"
            "  python download_nist_lines.py Fe 290 1110\n"
        )
        raise SystemExit(1)

    element = argv[1]

    if len(argv) == 5:
        ion_range = argv[2]
        low_nm = float(argv[3])
        high_nm = float(argv[4])
    else:
        ion_range = ""
        low_nm = float(argv[2])
        high_nm = float(argv[3])

    download_nist_csv(
        element=element,
        ion_range=ion_range,
        low_nm=low_nm,
        high_nm=high_nm,
    )


if __name__ == "__main__":
    cli_main(sys.argv)
