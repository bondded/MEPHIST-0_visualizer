from pathlib import Path
from urllib.parse import urlencode
import requests


NIST_URL = "https://physics.nist.gov/cgi-bin/ASD/lines1.pl"

# Carpeta local donde se guardarán los CSV
OUTPUT_DIR = Path(r"C:\Users\chelo\MEPHIST-0_visualizer\Lineas de emisión")


def build_nist_url(
    element: str,
    low_nm: float,
    high_nm: float,
    ion_range: str = ""
) -> str:
    """
    Construye la URL de consulta para NIST ASD Lines.

    Ejemplos:
        element = "Fe", ion_range = ""      -> "Fe"
        element = "Fe", ion_range = "I"     -> "Fe I"
        element = "Fe", ion_range = "I-II"  -> "Fe I-II"
    """

    element = element.strip()

    if ion_range.strip():
        spectra = f"{element} {ion_range.strip()}"
    else:
        spectra = element

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
        "format": 2,            # CSV text
        "line_out": 0,
        "en_unit": 0,
        "output": 0,
        "bibrefs": 1,
        "page_size": 100000,

        # Wavelength data
        "show_obs_wl": 1,
        "show_calc_wl": 1,
        "unc_out": 1,

        # Output ordering
        "order_out": 0,

        # Optional criteria
        "max_low_enrg": "",
        "max_upp_enrg": "",
        "show_av": 2,
        "tsb_value": 0,
        "min_str": "",
        "max_str": "",
        "A_out": 0,
        "intens_out": "on",
        "allowed_out": 1,
        "forbid_out": 1,
        "min_accur": "",
        "min_intens": "",

        # Level information
        "conf_out": "on",
        "term_out": "on",
        "enrg_out": "on",
        "J_out": "on",
    }

    return NIST_URL + "?" + urlencode(params)


def download_nist_csv(
    element: str,
    low_nm: float,
    high_nm: float,
    ion_range: str = ""
) -> Path:
    """
    Descarga un archivo CSV desde NIST ASD para un elemento dado.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    url = build_nist_url(
        element=element,
        low_nm=low_nm,
        high_nm=high_nm,
        ion_range=ion_range
    )

    if ion_range.strip():
        file_stem = f"{element}_{ion_range}".replace(" ", "_").replace("-", "_")
    else:
        file_stem = element

    file_name = f"{file_stem}_{low_nm:g}_{high_nm:g}_nm.csv"
    file_path = OUTPUT_DIR / file_name

    print("\nConsultando NIST ASD...")
    print(f"Elemento/espectro: {element} {ion_range}".strip())
    print(f"Rango: {low_nm} - {high_nm} nm")
    print(f"Guardando en: {file_path}")
    print(f"URL:\n{url}\n")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    file_path.write_text(response.text, encoding="utf-8")

    print(f"\nArchivo guardado correctamente en:\n{file_path.resolve()}")

    return file_path


def main():
    print("=== Descargador de líneas NIST ASD ===")

    element = input("Elemento químico, por ejemplo H, Fe, W, Ar: ").strip()

    ion_range = input(
        "Estado de ionización opcional, por ejemplo I, II, I-II, I-III "
        "(dejar vacío para todos los disponibles): "
    ).strip()

    low_nm = float(input("Longitud de onda mínima [nm], por ejemplo 290: "))
    high_nm = float(input("Longitud de onda máxima [nm], por ejemplo 1110: "))

    download_nist_csv(
        element=element,
        ion_range=ion_range,
        low_nm=low_nm,
        high_nm=high_nm
    )


if __name__ == "__main__":
    main()