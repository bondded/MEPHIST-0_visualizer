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
import shutil
import subprocess
import sys
from pathlib import Path

# =========================================================
# INTERFAZ Y GRÁFICOS EN ESPAÑOL
# =========================================================
#
# Las claves internas, los nombres de datasets y las columnas de cálculo se
# conservan en inglés para no alterar la lectura de los archivos NXS ni las
# exportaciones utilizadas por otras partes del programa.  Esta capa traduce
# únicamente el texto que ve el usuario: títulos, ejes, leyendas, anotaciones,
# botones, cuadros de diálogo y títulos de ventanas.

_TRADUCCIONES_ES = {
    # Títulos y nombres de figuras.
    "Pressure group comparison": "Comparación de grupos de presión",
    "Group comparison": "Comparación de grupos",
    "Official-style diagnostics": "Diagnósticos con estilo oficial",
    "Available spectrum sources": "Fuentes de espectro disponibles",
    "Available spectra: OceanFX and Avantes": "Espectros disponibles: OceanFX y Avantes",
    "Matched spectroscopy lines figure": "Figura de líneas espectroscópicas identificadas",
    "Quick spectroscopy candidates - NIST preview": "Candidatos espectroscópicos rápidos — vista previa NIST",
    "Spectroscopy analysis - Voigt fits": "Análisis espectroscópico — ajustes Voigt",
    "Voigt fit diagnostics: local windows": "Diagnóstico de ajustes Voigt: ventanas locales",
    "Voigt candidate fit diagnostics: local windows": "Diagnóstico de candidatos Voigt: ventanas locales",
    "Reproducibility analysis": "Análisis de reproducibilidad",
    "Normalization mode": "Modo de normalización",

    # Ejes y etiquetas científicas.
    "Time relative to Ip-only start [ms]": "Tiempo relativo al inicio de Ip [ms]",
    "Time - t_Ip,start [ms]": "Tiempo - t_Ip,inicio [ms]",
    "time [ms]": "Tiempo [ms]",
    "Time [ms]": "Tiempo [ms]",
    "Calibrated wavelength [nm]": "Longitud de onda calibrada [nm]",
    "Raw wavelength [nm]": "Longitud de onda sin calibrar [nm]",
    "raw wavelength [nm]": "Longitud de onda sin calibrar [nm]",
    "Wavelength [nm]": "Longitud de onda [nm]",
    "wavelength [nm]": "Longitud de onda [nm]",
    "Normalized intensity": "Intensidad normalizada",
    "relative intensity [a.u.]": "Intensidad relativa [u.a.]",
    "Intensity [a.u.]": "Intensidad [u.a.]",
    "intensity [counts]": "Intensidad [cuentas]",
    "counts": "cuentas",
    "coil current [kA]": "Corriente de bobinas [kA]",
    "current [kA]": "Corriente [kA]",
    "Plasma current and loop voltage": "Corriente de plasma y voltaje de lazo",
    "H-alpha / visible emission": "H-alpha / emisión visible",
    "CS and PF coils currents": "Corrientes de las bobinas CS y PF",
    "Toroidal magnetic field": "Campo magnético toroidal",
    "Survey visible spectrum, raw counts": "Espectro visible exploratorio, cuentas brutas",

    # Video y eventos temporales.
    "Event markers": "Marcadores de eventos",
    "Ip-only start": "Inicio de Ip",
    "Ip-only end": "Fin de Ip",
    "Selected camera start": "Inicio seleccionado de la cámara",
    "Current-quench Vloop peak": "Pico de Vloop durante la extinción de corriente",
    "H-alpha start": "Inicio de H-alpha",
    "H-alpha end": "Fin de H-alpha",
    "Normalized H-alpha": "H-alpha normalizado",
    "H-alpha threshold": "Umbral de H-alpha",
    "Video frames unavailable": "Fotogramas de video no disponibles",
    "Video frame": "Fotograma de video",
    "Relative time": "Tiempo relativo",
    "Video time": "Tiempo del video",

    # Espectroscopía y leyendas.
    "Shots": "Descargas",
    "Shot": "Descarga",
    "Element markers": "Marcadores de elementos",
    "Legend": "Leyenda",
    "Group": "Grupo",
    "Shot, folder": "Descarga, carpeta",
    "Voigt component": "Componente Voigt",
    "component": "componente",
    "NIST λ": "λ NIST",
    "Difference": "Diferencia",
    "No spectroscopy data": "No hay datos de espectroscopía",

    # Controles y mensajes breves.
    "Load Shots": "Cargar descargas",
    "Load Folder": "Cargar carpeta",
    "Clear Shots": "Borrar descargas",
    "Display: synchronized": "Visualización: sincronizada",
    "Display: raw time": "Visualización: tiempo original",
    "Show residuals": "Mostrar residuos",
    "Hide residuals": "Ocultar residuos",
    "Normalization": "Normalización",
    "No norm": "Sin normalización",
    "No normalization": "Sin normalización",
    "Bottom info": "Información inferior",
    "Enable cursor dynamics": "Activar cursor dinámico",
    "Disable cursor dynamics": "Desactivar cursor dinámico",
    "Hover labels": "Etiquetas al pasar el cursor",
    "Spectrum:": "Espectro:",
    "Plots:": "Gráficos:",
    "coils": "bobinas",
    "spectrum": "espectro",
    "Ip start-end": "Inicio-fin de Ip",
    "H-alpha start-end (-. / --)": "Inicio-fin de H-alpha (-. / --)",
    "Shot summary table": "Tabla resumen de descargas",
    "Official-style plots": "Gráficos con estilo oficial",
    "Compute reproducibility": "Calcular reproducibilidad",
    "Generate comparison": "Generar comparación",
    "Compare with video": "Comparar con video",
    "Export full analysis": "Exportar análisis completo",
    "Spectroscopy:": "Espectroscopía:",
    "Quick candidates (NIST preview)": "Candidatos rápidos (vista previa NIST)",
    "Voigt spectroscopy analysis": "Análisis espectroscópico Voigt",
    "Calibrate H Balmer": "Calibrar H de Balmer",
    "Spectrum sources": "Fuentes de espectro",
    "Spec: raw counts": "Espectro: cuentas brutas",
    "Spec: normalized": "Espectro: normalizado",
    "Show start/end markers": "Mostrar marcadores de inicio/fin",
    "Show event labels": "Mostrar leyenda de eventos",
    "Details...": "Detalles...",
    "Synchronization:": "Sincronización:",
    "Synchronization": "Sincronización",
    "Compare synchronizations": "Comparar sincronizaciones",
    "Synchronization ranking": "Ranking de sincronizaciones",
    "Top": "Posición",
    "Correlation": "Correlación",
    "Signal": "Señal",
    "Video duration [ms]": "Duración del video [ms]",
    "H-alpha duration error [%]": "Error de duración H-alpha [%]",
    "Frames": "Fotogramas",
    "Shift [ms]": "Desplazamiento [ms]",
    "Export comparison": "Exportar comparación",
    "Export data": "Exportar datos",
    "Export figure": "Exportar figura",
    "Export comparison figure": "Exportar figura de comparación",
    "Figure exported": "Figura exportada",
    "Export error": "Error de exportación",
    "The figure was saved successfully to:": "La figura se guardó correctamente en:",
    "Add folder": "Agregar carpeta",
    "Remove group": "Quitar grupo",
    "Generate Ip/H-alpha plot": "Generar gráfico Ip/H-alpha",
    "Close": "Cerrar",
    "Select all": "Seleccionar todo",
    "Clear": "Limpiar",
    "Accept": "Aceptar",
    "Cancel": "Cancelar",
    "Apply": "Aplicar",
    "Export table": "Exportar tabla",
    "Export Excel": "Exportar Excel",
    "Plot figure": "Graficar figura",
    "General:": "General:",
    "Plots in Spanish": "Gráficos en español",
    "Plot font:": "Fuente de gráficos:",
    "Text scale:": "Escala de texto:",
    "Normal": "Normal",
    "Report": "Informe",
    "Large": "Grande",
    "Open legend": "Abrir leyenda",
    "Show compact legend": "Mostrar leyenda compacta",
    "Copy labels": "Copiar etiquetas",
    "Color": "Color",
    "Line style": "Estilo de línea",
    "Label": "Etiqueta",

    # Diálogos habituales.
    "No data": "Sin datos",
    "No files": "Sin archivos",
    "No shots": "Sin descargas",
    "Error": "Error",
    "Warning": "Advertencia",
    "Success": "Éxito",
    "Loaded": "Cargado",
    "Skipped": "Omitido",
    "Copied": "Copiado",
    "Exported": "Exportado",
}

_REEMPLAZOS_ES = (
    # Se aplican después de las coincidencias exactas para cubrir textos
    # dinámicos que incluyen el número de descarga, N, porcentajes o tiempos.
    ("Group comparison", "Comparación de grupos"),
    ("Synchronization ", "Sincronización "),
    ("Synchronization", "Sincronización"),
    ("Compare synchronizations", "Comparar sincronizaciones"),
    ("Camera alignment", "Alineación de cámara"),
    ("diagnostics vs video", "diagnósticos y video"),
    ("Correlation:", "Correlación:"),
    ("Signal:", "Señal:"),
    ("frames ", "fotogramas "),
    ("H-alpha and camera comparison", "Comparación de H-alpha y cámara"),
    ("total grayscale camera luminosity", "luminosidad total en escala de grises de la cámara"),
    ("Total grayscale camera luminosity", "Luminosidad total en escala de grises de la cámara"),
    ("red-channel camera intensity", "intensidad del canal rojo de la cámara"),
    ("Red-channel camera intensity", "Intensidad del canal rojo de la cámara"),
    ("Available spectra", "Espectros disponibles"),
    ("Matched spectroscopy lines", "Líneas espectroscópicas identificadas"),
    ("Voigt fit diagnostics", "Diagnóstico de ajustes Voigt"),
    ("Voigt candidate fit diagnostics", "Diagnóstico de candidatos Voigt"),
    ("Voigt fit", "Ajuste Voigt"),
    ("candidate Voigt", "candidato Voigt"),
    ("Quick NIST preview", "Vista previa rápida NIST"),
    ("lines/file", "líneas/archivo"),
    ("overlay", "superposición"),
    ("calibrated λ", "λ calibrada"),
    ("raw λ", "λ sin calibrar"),
    ("panels synchronized to", "paneles sincronizados con"),
    ("t_Ip,start", "t_Ip,inicio"),
    ("If N >= 2", "Si N ≥ 2"),
    ("band = mean ±", "banda = promedio ±"),
    ("Ip smoothing", "suavizado de Ip"),
    ("H-alpha smoothing", "suavizado de H-alpha"),
    (" mean | N=", " promedio | N="),
    (" | 1 shot", " | 1 descarga"),
    (" shots", " descargas"),
    ("Shot ", "Descarga "),
    ("shot ", "descarga "),
    ("Video frame ", "Fotograma de video "),
    ("Relative time=", "Tiempo relativo="),
    ("Video time=", "Tiempo del video="),
    ("Normalized camera luminosity", "Luminosidad normalizada de la cámara"),
    ("Normalized red channel", "Canal rojo normalizado"),
    ("Normalized total luminosity", "Luminosidad total normalizada"),
    ("camera luminosity", "luminosidad de la cámara"),
    ("Camera luminosity", "Luminosidad de la cámara"),
    (" threshold", " — umbral"),
    ("Threshold", "Umbral"),
    (" decay end", " — fin de caída"),
    (" end", " — fin"),
    ("Raw ", "Señal bruta "),
    ("raw ", "señal bruta "),
    ("Available ", "Disponibles: "),
    ("spectrum", "espectro"),
    ("Spectrum", "Espectro"),
    ("spectroscopy", "espectroscopía"),
    ("Spectroscopy", "Espectroscopía"),
    ("wavelength", "longitud de onda"),
    ("Wavelength", "Longitud de onda"),
    ("intensity", "intensidad"),
    ("Intensity", "Intensidad"),
    ("time", "tiempo"),
    ("Time", "Tiempo"),
    ("Group", "Grupo"),
    ("Legend", "Leyenda"),
    ("Element", "Elemento"),
    ("Timing delays relative to Bt start", "Desfases temporales respecto al inicio de Bt"),
    ("Top-N per element", "Top-N por elemento"),
    ("candidates/element", "candidatos/elemento"),
    ("measured lines/shot", "líneas medidas/descarga"),
    ("Run top-N per element Voigt fit", "Ejecutar ajuste Voigt top-N por elemento"),
    ("Full legend", "Leyenda completa"),
    ("Use this instead of a very large in-plot legend", "Úsela en lugar de una leyenda demasiado grande dentro del gráfico"),
    ("The figure was saved successfully to:", "La figura se guardó correctamente en:"),
    ("NORMALIZED", "NORMALIZADO"),
    ("TAU DISPLAY", "VISUALIZACIÓN EN TAU"),
    ("Delta", "Diferencia"),
    ("markers", "marcadores"),
    ("normalized", "normalizado"),
    ("Normalized", "Normalizado"),
    ("a.u.", "u.a."),
    ("std", "desv. est."),
    ("smoothing", "suavizado"),
    (" us", " µs"),
)

# Tamaños mínimos para figuras que luego se insertarán en Overleaf.  Los
# gráficos que ya soliciten un tamaño mayor conservan ese valor.
OVERLEAF_TITLE_SIZE = 15
OVERLEAF_SUPTITLE_SIZE = 16
OVERLEAF_AXIS_LABEL_SIZE = 14
OVERLEAF_TICK_SIZE = 12
OVERLEAF_LEGEND_SIZE = 11
OVERLEAF_LEGEND_TITLE_SIZE = 12
MOSTRAR_TEXTO_EN_ESPANOL = True
PLOT_FONT_FAMILY = "DejaVu Sans"
PLOT_FONT_SCALE = 1.0


def _tamano_plot(base):
    return float(base) * float(PLOT_FONT_SCALE)

# Valores por defecto para todos los gráficos, incluidas las figuras creadas
# con pyplot, Figure o ventanas secundarias de espectroscopía/video.
plt.rcParams.update({
    "font.family": PLOT_FONT_FAMILY,
    "axes.titlesize": OVERLEAF_TITLE_SIZE,
    "axes.labelsize": OVERLEAF_AXIS_LABEL_SIZE,
    "xtick.labelsize": OVERLEAF_TICK_SIZE,
    "ytick.labelsize": OVERLEAF_TICK_SIZE,
    "legend.fontsize": OVERLEAF_LEGEND_SIZE,
    "legend.title_fontsize": OVERLEAF_LEGEND_TITLE_SIZE,
    "figure.titlesize": OVERLEAF_SUPTITLE_SIZE,
    "lines.linewidth": 1.8,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.08,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})


def texto_es(texto):
    """Traduce solo texto visible; deja intactos números y objetos no textuales."""
    if not isinstance(texto, str) or not texto:
        return texto
    if not MOSTRAR_TEXTO_EN_ESPANOL:
        return texto
    traducido = _TRADUCCIONES_ES.get(texto, texto)
    for origen, destino in _REEMPLAZOS_ES:
        traducido = traducido.replace(origen, destino)
    return traducido


def _traducir_leyenda_es(leyenda):
    if leyenda is None:
        return leyenda
    for item in leyenda.get_texts():
        item.set_text(texto_es(item.get_text()))
        item.set_fontsize(max(float(item.get_fontsize()), _tamano_plot(OVERLEAF_LEGEND_SIZE)))
    titulo = leyenda.get_title()
    if titulo is not None:
        titulo.set_text(texto_es(titulo.get_text()))
        titulo.set_fontsize(max(float(titulo.get_fontsize()), _tamano_plot(OVERLEAF_LEGEND_TITLE_SIZE)))
    return leyenda


def _asegurar_tamano(kwargs, clave, minimo):
    """Impone un tamaño mínimo aunque el código original use 'small' o 7/8 pt."""
    actual = kwargs.get(clave, None)
    try:
        if actual is None or float(actual) < float(minimo):
            kwargs[clave] = minimo
    except (TypeError, ValueError):
        kwargs[clave] = minimo


def _instalar_traduccion_matplotlib():
    """Hace que toda figura creada por este módulo muestre texto en español."""
    from matplotlib.axes import Axes

    if getattr(Axes, "_mephist_es_instalado", False):
        return
    Axes._mephist_es_instalado = True

    original_set_title = Axes.set_title
    original_set_xlabel = Axes.set_xlabel
    original_set_ylabel = Axes.set_ylabel
    original_text = Axes.text
    original_annotate = Axes.annotate
    original_legend = Axes.legend
    original_set_xticklabels = Axes.set_xticklabels
    original_set_yticklabels = Axes.set_yticklabels
    original_suptitle = Figure.suptitle
    original_figure_legend = Figure.legend

    def set_title_es(self, label, *args, **kwargs):
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(OVERLEAF_TITLE_SIZE))
        return original_set_title(self, texto_es(label), *args, **kwargs)

    def set_xlabel_es(self, xlabel, *args, **kwargs):
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(OVERLEAF_AXIS_LABEL_SIZE))
        return original_set_xlabel(self, texto_es(xlabel), *args, **kwargs)

    def set_ylabel_es(self, ylabel, *args, **kwargs):
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(OVERLEAF_AXIS_LABEL_SIZE))
        return original_set_ylabel(self, texto_es(ylabel), *args, **kwargs)

    def text_es(self, x, y, s, *args, **kwargs):
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(10))
        return original_text(self, x, y, texto_es(s), *args, **kwargs)

    def annotate_es(self, text, *args, **kwargs):
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(10))
        return original_annotate(self, texto_es(text), *args, **kwargs)

    def legend_es(self, *args, **kwargs):
        args = list(args)
        if len(args) >= 2 and isinstance(args[1], (list, tuple)):
            args[1] = [texto_es(x) for x in args[1]]
        if "labels" in kwargs and kwargs["labels"] is not None:
            kwargs["labels"] = [texto_es(x) for x in kwargs["labels"]]
        if "title" in kwargs:
            kwargs["title"] = texto_es(kwargs["title"])
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(OVERLEAF_LEGEND_SIZE))
        _asegurar_tamano(kwargs, "title_fontsize", _tamano_plot(OVERLEAF_LEGEND_TITLE_SIZE))
        return _traducir_leyenda_es(original_legend(self, *args, **kwargs))

    def set_xticklabels_es(self, labels, *args, **kwargs):
        labels = [texto_es(x) if isinstance(x, str) else x for x in labels]
        return original_set_xticklabels(self, labels, *args, **kwargs)

    def set_yticklabels_es(self, labels, *args, **kwargs):
        labels = [texto_es(x) if isinstance(x, str) else x for x in labels]
        return original_set_yticklabels(self, labels, *args, **kwargs)

    def suptitle_es(self, t, *args, **kwargs):
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(OVERLEAF_SUPTITLE_SIZE))
        return original_suptitle(self, texto_es(t), *args, **kwargs)

    def figure_legend_es(self, *args, **kwargs):
        args = list(args)
        if len(args) >= 2 and isinstance(args[1], (list, tuple)):
            args[1] = [texto_es(x) for x in args[1]]
        if "labels" in kwargs and kwargs["labels"] is not None:
            kwargs["labels"] = [texto_es(x) for x in kwargs["labels"]]
        if "title" in kwargs:
            kwargs["title"] = texto_es(kwargs["title"])
        _asegurar_tamano(kwargs, "fontsize", _tamano_plot(OVERLEAF_LEGEND_SIZE))
        _asegurar_tamano(kwargs, "title_fontsize", _tamano_plot(OVERLEAF_LEGEND_TITLE_SIZE))
        return _traducir_leyenda_es(original_figure_legend(self, *args, **kwargs))

    Axes.set_title = set_title_es
    Axes.set_xlabel = set_xlabel_es
    Axes.set_ylabel = set_ylabel_es
    Axes.text = text_es
    Axes.annotate = annotate_es
    Axes.legend = legend_es
    Axes.set_xticklabels = set_xticklabels_es
    Axes.set_yticklabels = set_yticklabels_es
    Figure.suptitle = suptitle_es
    Figure.legend = figure_legend_es


def _instalar_traduccion_tk():
    """Traduce los controles y diálogos sin modificar sus valores internos."""
    clases = [
        tk.Button, tk.Label, tk.Checkbutton, tk.Radiobutton, tk.LabelFrame,
        ttk.Button, ttk.Label, ttk.Checkbutton, ttk.Radiobutton, ttk.LabelFrame,
    ]
    for clase in clases:
        if getattr(clase, "_mephist_es_instalado", False):
            continue
        clase._mephist_es_instalado = True
        init_original = clase.__init__
        configure_original = clase.configure

        def init_es(self, *args, __original=init_original, **kwargs):
            texto_original = kwargs.get("text", None)
            if "text" in kwargs:
                kwargs["text"] = texto_es(kwargs["text"])
            resultado = __original(self, *args, **kwargs)
            if isinstance(texto_original, str):
                self._mephist_texto_original = texto_original
            return resultado

        def configure_es(self, cnf=None, __original=configure_original, **kwargs):
            if isinstance(cnf, dict):
                cnf = dict(cnf)
                if "text" in cnf:
                    if isinstance(cnf["text"], str):
                        self._mephist_texto_original = cnf["text"]
                    cnf["text"] = texto_es(cnf["text"])
            if "text" in kwargs:
                if isinstance(kwargs["text"], str):
                    self._mephist_texto_original = kwargs["text"]
                kwargs["text"] = texto_es(kwargs["text"])
            return __original(self, cnf, **kwargs)

        clase.__init__ = init_es
        clase.configure = configure_es
        clase.config = configure_es

    # Encabezados de tablas Tk.
    if not getattr(ttk.Treeview, "_mephist_es_instalado", False):
        ttk.Treeview._mephist_es_instalado = True
        heading_original = ttk.Treeview.heading

        def heading_es(self, column, option=None, **kwargs):
            if "text" in kwargs:
                originales = getattr(self, "_mephist_heading_original", {})
                originales[column] = kwargs["text"]
                self._mephist_heading_original = originales
                kwargs["text"] = texto_es(kwargs["text"])
            return heading_original(self, column, option, **kwargs)

        ttk.Treeview.heading = heading_es

    # Títulos y mensajes de ventanas secundarias.
    if not getattr(tk.Wm, "_mephist_es_instalado", False):
        tk.Wm._mephist_es_instalado = True
        titulo_original = tk.Wm.wm_title

        def titulo_es(self, string=None):
            if isinstance(string, str):
                self._mephist_titulo_original = string
            return titulo_original(self, texto_es(string) if string is not None else string)

        tk.Wm.wm_title = titulo_es
        tk.Wm.title = titulo_es

    for modulo, nombres in (
        (messagebox, ("showinfo", "showwarning", "showerror", "askyesno", "askyesnocancel", "askokcancel")),
        (simpledialog, ("askstring", "askinteger", "askfloat")),
    ):
        for nombre in nombres:
            original = getattr(modulo, nombre, None)
            if original is None or getattr(original, "_mephist_es_instalado", False):
                continue

            def dialogo_es(title=None, message=None, *args, __original=original, **kwargs):
                return __original(texto_es(title), texto_es(message), *args, **kwargs)

            dialogo_es._mephist_es_instalado = True
            setattr(modulo, nombre, dialogo_es)

    for nombre in ("askopenfilename", "askopenfilenames", "asksaveasfilename", "askdirectory"):
        original = getattr(filedialog, nombre, None)
        if original is None or getattr(original, "_mephist_es_instalado", False):
            continue

        def archivo_es(*args, __original=original, **kwargs):
            if "title" in kwargs:
                kwargs["title"] = texto_es(kwargs["title"])
            return __original(*args, **kwargs)

        archivo_es._mephist_es_instalado = True
        setattr(filedialog, nombre, archivo_es)


def _actualizar_idioma_widgets(raiz):
    """Reconstruye textos ya visibles después de cambiar el idioma."""
    if raiz is None:
        return
    widgets = [raiz]
    try:
        widgets.extend(list(raiz.winfo_children()))
    except Exception:
        pass
    for widget in widgets:
        original = getattr(widget, "_mephist_texto_original", None)
        if isinstance(original, str):
            try:
                widget.configure(text=original)
            except Exception:
                pass
        if isinstance(widget, ttk.Treeview):
            for columna, texto in getattr(widget, "_mephist_heading_original", {}).items():
                try:
                    widget.heading(columna, text=texto)
                except Exception:
                    pass
        try:
            for hijo in widget.winfo_children():
                if hijo not in widgets:
                    widgets.append(hijo)
        except Exception:
            pass


_instalar_traduccion_matplotlib()
_instalar_traduccion_tk()

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
try:
    from scipy.signal import savgol_filter
except Exception:
    savgol_filter = None

try:
    from scipy.optimize import least_squares
    from scipy.special import wofz
except Exception:
    least_squares = None
    wofz = None

# =========================================================
# EXPORT HELPERS
# =========================================================
TABLE_HEADER_UNIT_SUFFIXES = [
    ("counts_nm", "counts nm"),
    ("file_units", "file units"),
    ("V_per_ms", "V/ms"),
    ("kA_per_ms", "kA/ms"),
    ("A_per_s", "A/s"),
    ("mPa", "mPa"),
    ("mbar", "mbar"),
    ("kA", "kA"),
    ("mT", "mT"),
    ("ms", "ms"),
    ("us", "us"),
    ("s", "s"),
    ("V", "V"),
    ("A", "A"),
    ("C", "C"),
    ("T", "T"),
    ("nm", "nm"),
    ("au", "a.u."),
]

TABLE_HEADER_EXPLICIT_UNITS = {
    "Halpha_integral_Ip_window": "a.u. s",
    "Halpha_integral_Halpha_window": "a.u. s",
    "Halpha_integral_over_Ip_integral_Ip_window": "a.u./C",
    "Halpha_integral_Halpha_window_over_Ip_integral_plasma": "a.u./C",
    "max_H_alpha_au": "a.u.",
}

TABLE_HEADER_TOKEN_REPLACEMENTS = {
    "Halpha": "H-alpha",
    "halpha": "H-alpha",
    "H_alpha": "H-alpha",
    "Ip": "Ip",
    "ip": "Ip",
    "Bt": "Bt",
    "bt": "Bt",
    "TF": "TF",
    "tf": "TF",
    "CS": "CS",
    "cs": "CS",
    "PF": "PF",
    "pf": "PF",
    "Voigt": "Voigt",
    "voigt": "Voigt",
    "MEPhIST": "MEPhIST",
    "MEPHIST": "MEPhIST",
    "qa": "qa",
}


def _split_camel_token(token):
    """Split CamelCase only when it improves readability."""
    token = str(token)
    if not token:
        return []
    if token in TABLE_HEADER_TOKEN_REPLACEMENTS:
        return [TABLE_HEADER_TOKEN_REPLACEMENTS[token]]
    # Keep compact diagnostic names readable instead of over-splitting them.
    if re.fullmatch(r"[A-Z]{2,}\d*", token):
        return [token]
    number_suffix = re.fullmatch(r"([A-Za-z]+)(\d+)", token)
    if number_suffix:
        return [number_suffix.group(1), number_suffix.group(2)]
    token = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", token)
    return token.split()


def format_table_column_header(column_name, multiline=True):
    """Return a human-readable table header for Tk tables and Excel exports.

    Examples:
        Vacuum_total_pressure_mPa -> Vacuum\ntotal\npressure\n[mPa]
        H_alpha_duration_Ip_window_ms -> H-alpha\nduration\nIp\nwindow\n[ms]

    Internal DataFrame column names are left unchanged for sorting and code logic;
    only the visible/exported headers are formatted.
    """
    original = str(column_name)
    name = original.strip()
    unit = TABLE_HEADER_EXPLICIT_UNITS.get(name, "")

    if not unit:
        for suffix, unit_label in TABLE_HEADER_UNIT_SUFFIXES:
            suffix_text = f"_{suffix}"
            if name.endswith(suffix_text):
                unit = unit_label
                name = name[:-len(suffix_text)]
                break

    # Normalize common H-alpha variants before splitting on underscores.
    name = name.replace("H_alpha", "Halpha")
    raw_tokens = [t for t in re.split(r"[_\s]+", name) if t]
    pretty_tokens = []
    for token in raw_tokens:
        if token in TABLE_HEADER_TOKEN_REPLACEMENTS:
            pretty_tokens.append(TABLE_HEADER_TOKEN_REPLACEMENTS[token])
            continue
        pretty_tokens.extend(_split_camel_token(token))

    if not pretty_tokens:
        pretty_tokens = [original]

    # Capitalize ordinary words, but preserve compact diagnostics/abbreviations.
    normalized = []
    for token in pretty_tokens:
        if token in {"Ip", "Bt", "TF", "CS", "PF", "MEPhIST", "Voigt", "H-alpha", "qa"}:
            normalized.append(token)
        elif re.fullmatch(r"[A-Z]{2,}\d*", token):
            normalized.append(token)
        elif token.isdigit():
            normalized.append(token)
        else:
            normalized.append(token[:1].upper() + token[1:])

    if unit:
        normalized.append(f"[{unit}]")

    separator = "\n" if multiline else " "
    return separator.join(normalized)


def dataframe_with_readable_headers(df, multiline=True):
    """Copy a DataFrame and replace only its column labels with readable headers."""
    if not isinstance(df, pd.DataFrame):
        return df
    out = df.copy()
    out.columns = [format_table_column_header(c, multiline=multiline) for c in out.columns]
    return out


def _style_excel_worksheet_for_readable_headers(worksheet):
    """Apply compact readable formatting to a worksheet created with pandas."""
    try:
        from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    except Exception:
        return

    header_fill = PatternFill(fill_type="solid", fgColor="F4A14A")
    thin_side = Side(style="thin", color="BFBFBF")
    border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

    worksheet.freeze_panes = "A2"
    worksheet.row_dimensions[1].height = 78

    for cell in worksheet[1]:
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.font = Font(bold=True, color="000000")
        cell.fill = header_fill
        cell.border = border

    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=False)
            cell.border = border

    for col_cells in worksheet.columns:
        col_letter = col_cells[0].column_letter
        header_text = str(col_cells[0].value or "")
        max_header_line = max([len(line) for line in header_text.split("\n")] + [8])
        max_body = 0
        for cell in col_cells[1:51]:
            if cell.value is not None:
                max_body = max(max_body, len(str(cell.value)))
        width = min(max(max_header_line + 3, min(max_body + 2, 28), 10), 32)
        worksheet.column_dimensions[col_letter].width = width

    try:
        worksheet.auto_filter.ref = worksheet.dimensions
    except Exception:
        pass


def save_dataframe_with_openpyxl_fallback(df, path, index=False):
    """
    Save one DataFrame as CSV or Excel.

    If the user chooses .xlsx but openpyxl is not installed, the code saves
    a .csv file with the same base name instead of failing. Visible/exported
    headers are converted to readable labels with spaces, line breaks and units.
    """
    p = Path(path)
    df_export = dataframe_with_readable_headers(df, multiline=True)

    if p.suffix.lower() == ".csv":
        df_export.to_csv(p, index=index)
        return p, "csv"

    try:
        import openpyxl  # noqa: F401
        with pd.ExcelWriter(p, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=index, sheet_name="table")
            _style_excel_worksheet_for_readable_headers(writer.sheets["table"])
        return p, "xlsx"
    except ImportError:
        fallback = p.with_suffix(".csv")
        df_export.to_csv(fallback, index=index)
        return fallback, "csv_fallback"


def save_workbook_with_openpyxl_fallback(path, tables):
    """
    Save several DataFrames as an Excel workbook.

    tables can be either:
        dict[str, DataFrame]
        list[tuple[str, DataFrame]]

    If openpyxl is not installed, creates a folder with one CSV per sheet.
    Visible/exported headers are converted to readable labels with spaces, line
    breaks and units.
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
                df_export = dataframe_with_readable_headers(df, multiline=True) if isinstance(df, pd.DataFrame) else df
                df_export.to_excel(writer, sheet_name=clean_name, index=False)
                _style_excel_worksheet_for_readable_headers(writer.sheets[clean_name])
        return p, "xlsx"
    except ImportError:
        out_dir = p.with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)

        for sheet_name, df in items:
            clean_name = str(sheet_name).replace("/", "_").replace("\\", "_").replace(":", "_")
            clean_name = re.sub(r"[^A-Za-z0-9_. -]+", "_", clean_name).strip() or "sheet"
            df_export = dataframe_with_readable_headers(df, multiline=True) if isinstance(df, pd.DataFrame) else df
            df_export.to_csv(out_dir / f"{clean_name}.csv", index=False)

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

# Ip start detector, robust behavior-change mode:
# The old 5% crossing is kept as a fallback/diagnostic. The preferred start is
# now the knee found by going backward from Ip,max and locating the transition
# from a quiet pre-plasma region to a sustained positive Ip rise.
IP_START_BEHAVIOR_CHANGE_ENABLED = True
IP_START_BEHAVIOR_SMOOTH_US = 25
IP_START_BEHAVIOR_PRE_WINDOW_US = 80
IP_START_BEHAVIOR_POST_WINDOW_US = 120
IP_START_BEHAVIOR_MAX_BEFORE_PEAK_MS = 3.0
IP_START_BEHAVIOR_MIN_BEFORE_PEAK_US = 20
IP_START_BEHAVIOR_MIN_RISE_RATIO = 0.06
IP_START_BEHAVIOR_MAX_START_LEVEL_RATIO = 0.35
IP_START_BEHAVIOR_FIXED_SLOPE_KA_PER_MS = 0.30
IP_START_BEHAVIOR_SLOPE_FRACTION_OF_MAX = 0.12
IP_START_BEHAVIOR_NOISE_SIGMA_FACTOR = 6.0
IP_START_BEHAVIOR_QUIET_VARIATION_RATIO = 0.07

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

# Recent-shot high-current residual plateau detector. Some recent shots use a
# simplified internal-Rogowski Ip reconstruction that can remain at a high flat
# offset after the real current phase. This detector is still Ip-based: it cuts
# only when Ip has dropped significantly after Ip,max and then becomes sustained
# flat. It does NOT use the MEPhIST H-alpha duration to define the main plasma
# window.
IP_HIGH_RESIDUAL_PLATEAU_DETECTION_ENABLED = True
IP_HIGH_RESIDUAL_MIN_AFTER_PEAK_US = 250
IP_HIGH_RESIDUAL_PRE_WINDOW_US = 700
IP_HIGH_RESIDUAL_POST_WINDOW_US = 300
IP_HIGH_RESIDUAL_DROP_RATIO = 0.12
IP_HIGH_RESIDUAL_POST_SLOPE_LIMIT_KA_PER_MS = 0.20
IP_HIGH_RESIDUAL_POST_VARIATION_RATIO = 0.035

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
HALPHA_END_THRESHOLD_RATIO = 0.05
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
# LOOP-VOLTAGE END DETECTION FOR PLASMA WINDOW
# =========================================================
# The plasma start is ALWAYS obtained from Ip.  Vloop is deliberately reserved
# for the end because using it for both boundaries can move the start from the
# Ip knee to a later CS/eddy-current feature and would also make the video test
# circular.
LOOP_VOLTAGE_EDGE_REFINEMENT_ENABLED = True
# Ip still supplies a local end anchor.  Inside that window we choose the LAST
# physically valid positive Vloop peak, not simply the largest peak in the whole
# record (which could be caused by a later CS command or an eddy-current pickup).
LOOP_VOLTAGE_START_SEARCH_BEFORE_MS = 0.25
LOOP_VOLTAGE_START_SEARCH_AFTER_MS = 0.55
LOOP_VOLTAGE_END_SEARCH_BEFORE_MS = 0.90
LOOP_VOLTAGE_END_SEARCH_AFTER_MS = 0.90
LOOP_VOLTAGE_EDGE_SMOOTH_US = 80
LOOP_VOLTAGE_EDGE_MIN_SIGMA = 3.0
LOOP_VOLTAGE_EDGE_MIN_ABS_DV_PER_MS = 0.20
LOOP_VOLTAGE_FEATURE_MIN_PROMINENCE_V = 0.20
LOOP_VOLTAGE_FEATURE_SIDE_WINDOW_MS = 0.45
LOOP_VOLTAGE_FEATURE_MAX_SHIFT_MS = 1.25
# Plasma end is represented by the completion of the falling edge of the last
# valid peak.  0.80 means that 80 % of the peak-to-right-baseline excursion has
# decayed.  The peak time is retained separately for validation plots.
LOOP_VOLTAGE_END_USE_FALLING_EDGE = True
LOOP_VOLTAGE_END_FALL_FRACTION = 0.70
LOOP_VOLTAGE_FALL_BASELINE_TAIL_FRACTION = 0.25
LOOP_VOLTAGE_FALL_MIN_SUSTAINED_US = 40
# Start refinement must remain local. A wider shift can jump from the Ip knee to
# the Vloop peak and make t_Ip_start too late. End refinement keeps the global
# default above.
LOOP_VOLTAGE_START_FEATURE_MAX_SHIFT_MS = 0.45

# Video comparison.  Exported WebM files often have a playback frame rate that
# is unrelated to the physical fast-camera cadence, so the GUI asks for the
# physical inter-frame interval.  The supplied MEPhIST videos use 100 us/frame.
VIDEO_DEFAULT_FRAME_INTERVAL_US = 100.0
VIDEO_BASELINE_PERCENTILE = 10.0
VIDEO_LIGHT_THRESHOLD_FRACTION = 0.08
VIDEO_LIGHT_MIN_CONSECUTIVE_FRAMES = 2
VIDEO_DURATION_MATCH_TOLERANCE_RATIO = 0.35
VIDEO_HALPHA_MAX_FINE_SHIFT_MS = 1.25
VIDEO_HALPHA_MIN_CORRELATION = 0.25
VIDEO_HALPHA_LOW_CORRELATION_WARNING = 0.50
VIDEO_MAX_SYNC_CANDIDATES = 3
HALPHA_MAIN_PEAK_SEARCH_BEFORE_IP_MS = 0.25
HALPHA_MAIN_PEAK_SEARCH_AFTER_IP_MS = 4.0
VIDEO_DISPLAY_MAX_WIDTH = 360
VIDEO_DISPLAY_MAX_HEIGHT = 650

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
    "C": 0.02,
    # Li is intentionally non-negligible because recent shots can have a lithium-coated chamber.
    # It is still not automatically accepted; it must fit the measured feature.
    "Li": 0.78,
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
# VOIGT-BASED SPECTROSCOPY ANALYSIS
# =========================================================
# This replaces the old point/centroid-based spectroscopy interpretation when
# the user explicitly runs the Voigt analysis. The old NIST candidate tables are
# kept available for comparison, but the reliable intensity metric for the new
# workflow is the Voigt component area, not the maximum sampled pixel.
VOIGT_FIT_DEFAULT_WINDOW_NM = 1.6
VOIGT_FIT_BALMER_WINDOW_NM = 2.2
VOIGT_FIT_SATURATED_BALMER_WINDOW_NM = 5.0
VOIGT_FIT_MAX_COMPONENTS_PER_FEATURE = 3
VOIGT_FIT_MIN_POINTS = 7
VOIGT_FIT_MIN_RELATIVE_HEIGHT = 0.015
VOIGT_FIT_NOISE_SIGMA_FACTOR = 4.0
VOIGT_FIT_CENTER_TOLERANCE_NM = 0.75
VOIGT_FIT_SATURATION_ADC_LEVEL = 65535.0
VOIGT_FIT_SATURATION_ABS_THRESHOLD = 62000.0
VOIGT_FIT_SATURATION_REL_THRESHOLD = 0.985
VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM = 0.60
VOIGT_FIT_OVERLAY_DEFAULT = False

# Voigt quality and overlay limits. Candidate tables keep all fits, but best
# tables/plots can ignore fits that are too far from the NIST line or too broad
# to be a reliable single-component assignment. Saturated H Balmer fits are
# allowed to be wider because the clipped top is reconstructed from the wings.
VOIGT_FIT_MIN_QUALITY_ACCEPTED = 0.015
VOIGT_FIT_MAX_FWHM_NM = 6.0
VOIGT_FIT_MAX_SATURATED_BALMER_FWHM_NM = 12.0
VOIGT_OVERLAY_DEFAULT_MAX_PER_ELEMENT = 5
VOIGT_OVERLAY_MAX_ABS_DELTA_NM = 0.85
VOIGT_OVERLAY_MIN_QUALITY = 0.015
VOIGT_OVERLAY_MAX_FWHM_NM = 12.0

# Fast Voigt mode. Instead of fitting every NIST line for every selected
# element, fit the strongest experimental candidates for each element and stop
# once this many reliable Voigt lines have been found. Rejected/attempted fits
# are still saved in the candidate table for diagnosis.
VOIGT_FIT_TOP_N_PER_ELEMENT = 3
VOIGT_FIT_PREFILTER_ATTEMPTS_PER_TARGET = 5
VOIGT_FIT_PREFILTER_MIN_ATTEMPTS_PER_ELEMENT = 8

# Elements that should always remain visible as diagnostic competitors in exhaustive
# spectroscopy overlays when they exist in the local NIST folder. This does not force
# them to win; it only keeps their best fits/markers visible for inspection.
VOIGT_ALWAYS_DIAGNOSTIC_ELEMENTS = ("Li",)
VOIGT_DIAGNOSTIC_ELEMENT_RADIUS_NM = 3.0
VOIGT_DIAGNOSTIC_CANDIDATES_PER_ELEMENT_PER_FEATURE = 8

# Full/complete Voigt mode: fit the strongest N experimental/NIST candidates
# across all local elements, ordered by measured local peak/excess intensity.
VOIGT_FIT_IMPORTANT_LINES_DEFAULT = 50

# Robust H-Balmer calibration parameters.  The calibration is not allowed to
# blindly trust a single local maximum: for every Balmer line, several local
# alternatives are fitted with Voigt and the most self-consistent set of anchors
# is selected by a robust weighted calibration fit.
VOIGT_BALMER_CALIBRATION_MAX_ALTERNATIVES_PER_LINE = 3
VOIGT_BALMER_CALIBRATION_SEARCH_WINDOW_NM = 3.2
VOIGT_BALMER_CALIBRATION_MAX_RAW_DELTA_SOFT_NM = 2.8
VOIGT_BALMER_CALIBRATION_GOOD_FWHM_NM = 1.2
VOIGT_BALMER_CALIBRATION_MAX_FWHM_STRONG_NM = 3.5
VOIGT_BALMER_CALIBRATION_MAX_RESIDUAL_USED_NM = 0.55

VOIGT_ELEMENT_COLORS = {
    "H": "#FFD400",      # yellow
    "Fe": "#2ca02c",     # green
    "O": "#1f77b4",      # blue
    "W": "#7b2cbf",      # purple
    "Li": "#ff7f0e",     # orange
    "N": "#17becf",      # cyan
    "C": "#8c564b",      # brown
    "Ar": "#e377c2",
    "He": "#bcbd22",
}


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

def detect_ip_start_behavior_change_from_peak(Time, Ip, peak_idx, ip_max_ref):
    """
    Detect Ip start as a behavior-change/knee before Ip,max.

    This implements the intended logic:
      1) locate Ip,max;
      2) move backward in the pre-peak region;
      3) find the transition from a quiet low-current segment to a sustained
         positive Ip rise;
      4) use the 5% crossing only as fallback/diagnostic.

    Returned dict is None when no reliable knee is found.
    """
    if not IP_START_BEHAVIOR_CHANGE_ENABLED:
        return None

    Time = np.asarray(Time, dtype=float)
    Ip = np.asarray(Ip, dtype=float)

    if Time.size < 8 or Ip.size < 8 or Time.shape != Ip.shape:
        return None
    if peak_idx is None or peak_idx <= 2 or peak_idx >= Time.size:
        return None
    if not np.isfinite(ip_max_ref) or ip_max_ref <= 0:
        return None

    dt = float(np.nanmedian(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return None

    Ip_smooth = smooth_signal_time(Time, Ip, window_us=IP_START_BEHAVIOR_SMOOTH_US)
    Ip_pos = positive_part(Ip_smooth)

    # d(Ip[kA])/d(t[ms]) = d(Ip[A])/d(t[s]) / 1e6.
    t_ms = Time * 1000.0
    try:
        dIp_dt_kA_per_ms = np.gradient(Ip_smooth / 1000.0, t_ms)
    except Exception:
        return None

    pre_samples = max(int(np.ceil((IP_START_BEHAVIOR_PRE_WINDOW_US * 1e-6) / dt)), 3)
    post_samples = max(int(np.ceil((IP_START_BEHAVIOR_POST_WINDOW_US * 1e-6) / dt)), 4)
    max_before_samples = max(int(np.ceil((IP_START_BEHAVIOR_MAX_BEFORE_PEAK_MS * 1e-3) / dt)), pre_samples + post_samples + 1)
    min_before_samples = max(int(np.ceil((IP_START_BEHAVIOR_MIN_BEFORE_PEAK_US * 1e-6) / dt)), 1)

    search_start = max(pre_samples, int(peak_idx) - max_before_samples)
    search_stop = int(peak_idx) - max(min_before_samples, post_samples + 1)
    if search_stop <= search_start:
        return None

    search_idx = np.arange(search_start, int(peak_idx) + 1)
    d_search = dIp_dt_kA_per_ms[search_idx]
    ip_search = Ip_pos[search_idx]

    finite = np.isfinite(d_search) & np.isfinite(ip_search)
    if np.sum(finite) < 5:
        return None

    # Estimate the quiet derivative noise from low-current pre-peak samples.
    low_mask = finite & (ip_search <= 0.12 * ip_max_ref)
    noise_values = d_search[low_mask]
    if noise_values.size < 5:
        noise_values = d_search[finite][:max(5, min(80, np.sum(finite)))]

    noise_med = float(np.nanmedian(noise_values)) if noise_values.size else 0.0
    noise_sigma = float(1.4826 * np.nanmedian(np.abs(noise_values - noise_med))) if noise_values.size else 0.0
    if not np.isfinite(noise_sigma) or noise_sigma <= 1e-15:
        noise_sigma = float(np.nanstd(noise_values)) if noise_values.size > 1 else 0.0

    positive_slopes = d_search[np.isfinite(d_search) & (d_search > 0)]
    if positive_slopes.size:
        max_slope_ref = float(np.nanpercentile(positive_slopes, 95))
    else:
        max_slope_ref = 0.0

    slope_threshold = max(
        float(IP_START_BEHAVIOR_FIXED_SLOPE_KA_PER_MS),
        float(IP_START_BEHAVIOR_NOISE_SIGMA_FACTOR) * max(noise_sigma, 0.0),
        float(IP_START_BEHAVIOR_SLOPE_FRACTION_OF_MAX) * max(max_slope_ref, 0.0),
    )
    quiet_slope_limit = max(0.15, 0.35 * slope_threshold, 4.0 * max(noise_sigma, 0.0))
    min_rise_A = float(IP_START_BEHAVIOR_MIN_RISE_RATIO) * float(ip_max_ref)
    max_start_level_A = float(IP_START_BEHAVIOR_MAX_START_LEVEL_RATIO) * float(ip_max_ref)
    quiet_variation_limit_A = float(IP_START_BEHAVIOR_QUIET_VARIATION_RATIO) * float(ip_max_ref)

    candidates = []
    for idx in range(search_start, search_stop + 1):
        pre0 = max(0, idx - pre_samples)
        pre1 = idx
        post0 = idx
        post1 = min(int(peak_idx) + 1, idx + post_samples)
        if pre1 - pre0 < 3 or post1 - post0 < 4:
            continue

        pre_ip = Ip_pos[pre0:pre1]
        post_ip = Ip_pos[post0:post1]
        pre_slope_abs = np.abs(dIp_dt_kA_per_ms[pre0:pre1])
        post_slope = dIp_dt_kA_per_ms[post0:post1]

        if not (np.any(np.isfinite(pre_ip)) and np.any(np.isfinite(post_ip))):
            continue

        start_level = float(Ip_pos[idx])
        if not np.isfinite(start_level) or start_level > max_start_level_A:
            continue

        pre_slope_med = float(np.nanmedian(pre_slope_abs))
        post_slope_med = float(np.nanmedian(post_slope))
        pre_variation = float(np.nanmax(pre_ip) - np.nanmin(pre_ip))
        post_rise = float(np.nanmax(post_ip) - np.nanmedian(pre_ip))

        if not np.isfinite(pre_slope_med) or not np.isfinite(post_slope_med) or not np.isfinite(post_rise):
            continue
        if pre_slope_med > quiet_slope_limit:
            continue
        if pre_variation > quiet_variation_limit_A:
            continue
        if post_slope_med < slope_threshold:
            continue
        if post_rise < min_rise_A:
            continue

        # The best candidate is a sharp transition: quiet before, strong rise after.
        score = (
            post_rise / max(min_rise_A, 1e-12)
            + post_slope_med / max(slope_threshold, 1e-12)
            - pre_slope_med / max(quiet_slope_limit, 1e-12)
            - pre_variation / max(quiet_variation_limit_A, 1e-12)
        )
        candidates.append({
            'idx': int(idx),
            'time': float(Time[idx]),
            'score': float(score),
            'pre_slope_kA_per_ms': pre_slope_med,
            'post_slope_kA_per_ms': post_slope_med,
            'post_rise_A': post_rise,
            'pre_variation_A': pre_variation,
            'slope_threshold_kA_per_ms': slope_threshold,
            'quiet_slope_limit_kA_per_ms': quiet_slope_limit,
            'noise_sigma_kA_per_ms': noise_sigma,
        })

    if not candidates:
        return None

    # Prefer the strongest transition. For nearly equal scores, choose the earlier
    # one to avoid placing t0 inside the ramp.
    best_score = max(c['score'] for c in candidates)
    near_best = [c for c in candidates if c['score'] >= best_score - 0.15 * max(abs(best_score), 1.0)]
    best = sorted(near_best, key=lambda c: c['idx'])[0]

    return {
        'start_time': best['time'],
        'start_idx': best['idx'],
        'method': 'Ip_start_backward_behavior_change',
        'score': best['score'],
        'pre_slope_kA_per_ms': best['pre_slope_kA_per_ms'],
        'post_slope_kA_per_ms': best['post_slope_kA_per_ms'],
        'post_rise_A': best['post_rise_A'],
        'pre_variation_A': best['pre_variation_A'],
        'slope_threshold_kA_per_ms': best['slope_threshold_kA_per_ms'],
        'quiet_slope_limit_kA_per_ms': best['quiet_slope_limit_kA_per_ms'],
        'noise_sigma_kA_per_ms': best['noise_sigma_kA_per_ms'],
    }


def get_ip_start_backward_from_peak_info(
    Time,
    Ip,
    threshold_ratio=IP_START_THRESHOLD_RATIO,
    min_duration_us=IP_MIN_DURATION_US,
    smooth_us=IP_START_BACKWARD_FROM_PEAK_SMOOTH_US
):
    """
    Official Ip-start detector based on a backward search from Ip,max.

    Preferred logic:
      1) Smooth Ip and find the main Ip maximum.
      2) Search backward from Ip,max for the behavior-change/knee where Ip
         leaves a quiet pre-plasma region and begins a sustained positive rise.
      3) Keep the old 5% upward crossing as a fallback and as a diagnostic.

    This avoids placing t_Ip,start too close to the current maximum when the
    5% crossing or a later Vloop peak is not a good proxy for breakdown.
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

    peak_idx = int(np.nanargmax(Ip_pos))
    threshold = threshold_ratio * ip_max_ref
    above = Ip_pos > threshold

    min_samples = max(
        int(np.ceil((min_duration_us * 1e-6) / dt)),
        1
    )

    # Old 5% detector, now used as fallback/diagnostic only.
    crossing_indices = np.where(np.diff(above.astype(int)) == 1)[0] + 1
    crossing_indices = crossing_indices[crossing_indices <= peak_idx]

    valid_crossings = []
    for idx in crossing_indices:
        if idx + min_samples <= len(above) and np.all(above[idx:idx + min_samples]):
            valid_crossings.append(idx)

    if valid_crossings:
        threshold_start_idx = int(valid_crossings[-1])
        threshold_start_time = Time[threshold_start_idx]
        threshold_method = 'Ip_start_backward_from_peak_5pct'
    else:
        above_before_peak = np.where(above[:peak_idx + 1])[0]
        if len(above_before_peak) > 0:
            threshold_start_idx = int(above_before_peak[0])
            threshold_start_time = Time[threshold_start_idx]
            threshold_method = 'Ip_start_backward_from_peak_already_above'
        else:
            threshold_start_idx = 0
            threshold_start_time = Time[0]
            threshold_method = 'Ip_start_backward_from_peak_not_found'

    behavior_info = detect_ip_start_behavior_change_from_peak(
        Time,
        Ip,
        peak_idx=peak_idx,
        ip_max_ref=ip_max_ref,
    )

    if behavior_info is not None:
        start_time = behavior_info.get('start_time', threshold_start_time)
        start_idx = behavior_info.get('start_idx', threshold_start_idx)
        method = behavior_info.get('method', 'Ip_start_backward_behavior_change')
    else:
        start_time = threshold_start_time
        start_idx = threshold_start_idx
        method = threshold_method
        behavior_info = {}

    return {
        'start_time': start_time,
        'method': method,
        'threshold_start_time': threshold_start_time,
        'ip_peak_time': Time[peak_idx],
        'ip_start_threshold_A': threshold,
        'ip_start_ip_max_ref_A': ip_max_ref,
        'ip_start_peak_idx': peak_idx,
        'ip_start_idx': start_idx,
        'ip_start_5pct_method': threshold_method,
        'ip_start_5pct_time': threshold_start_time,
        'ip_start_behavior_score': behavior_info.get('score', np.nan),
        'ip_start_behavior_pre_slope_kA_per_ms': behavior_info.get('pre_slope_kA_per_ms', np.nan),
        'ip_start_behavior_post_slope_kA_per_ms': behavior_info.get('post_slope_kA_per_ms', np.nan),
        'ip_start_behavior_post_rise_A': behavior_info.get('post_rise_A', np.nan),
        'ip_start_behavior_pre_variation_A': behavior_info.get('pre_variation_A', np.nan),
        'ip_start_behavior_slope_threshold_kA_per_ms': behavior_info.get('slope_threshold_kA_per_ms', np.nan),
        'ip_start_behavior_quiet_slope_limit_kA_per_ms': behavior_info.get('quiet_slope_limit_kA_per_ms', np.nan),
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


def detect_ip_high_residual_plateau_time(
    Time,
    Ip,
    start_time,
    peak_idx=None,
    ip_max_ref=None,
    smooth_us=IP_END_AFTER_MAX_SMOOTH_US
):
    """
    Detect a high-current residual plateau after a significant post-peak drop.

    This is intended for recent shots where the simplified internal-Rogowski
    reconstruction can leave a nearly flat high offset after the useful current
    phase. It remains an Ip-based criterion and is independent of the MEPhIST
    H-alpha duration.
    """
    if not IP_HIGH_RESIDUAL_PLATEAU_DETECTION_ENABLED:
        return None, "high_residual_plateau_disabled"

    Time = np.asarray(Time)
    Ip = np.asarray(Ip)
    if len(Time) < 10 or len(Ip) < 10:
        return None, "high_residual_plateau_invalid_signal"

    dt = float(np.median(np.diff(Time)))
    if not np.isfinite(dt) or dt <= 0:
        return None, "high_residual_plateau_invalid_dt"

    Ip_smooth_A = smooth_signal_time(Time, Ip, window_us=smooth_us)
    Ip_kA = Ip_smooth_A / 1000.0

    if peak_idx is None or peak_idx < 0 or peak_idx >= len(Time):
        after_indices = np.where(Time >= start_time)[0]
        if len(after_indices) < 2:
            return None, "high_residual_plateau_no_after_start"
        peak_idx = int(after_indices[int(np.nanargmax(Ip_kA[after_indices]))])

    if ip_max_ref is None or ip_max_ref <= 0:
        ip_max_ref = float(max(Ip_kA[peak_idx], 0.0) * 1000.0)

    ip_max_kA = float(ip_max_ref) / 1000.0
    if not np.isfinite(ip_max_kA) or ip_max_kA <= 0:
        return None, "high_residual_plateau_bad_ipmax"

    min_after = max(int(np.ceil((IP_HIGH_RESIDUAL_MIN_AFTER_PEAK_US * 1e-6) / dt)), 1)
    pre_samples = max(int(np.ceil((IP_HIGH_RESIDUAL_PRE_WINDOW_US * 1e-6) / dt)), 2)
    post_samples = max(int(np.ceil((IP_HIGH_RESIDUAL_POST_WINDOW_US * 1e-6) / dt)), 3)

    start_idx = min(peak_idx + min_after, len(Time) - post_samples - 1)
    stop_idx = len(Time) - post_samples - 1
    if start_idx >= stop_idx:
        return None, "high_residual_plateau_no_room"

    dIp_dt_kA_per_ms = np.gradient(Ip_kA, Time) / 1000.0
    slope_limit = float(IP_HIGH_RESIDUAL_POST_SLOPE_LIMIT_KA_PER_MS)
    drop_limit = float(IP_HIGH_RESIDUAL_DROP_RATIO) * ip_max_kA
    variation_limit = float(IP_HIGH_RESIDUAL_POST_VARIATION_RATIO) * ip_max_kA

    peak_to_now_max = ip_max_kA

    for idx in range(start_idx, stop_idx):
        peak_to_now_max = max(peak_to_now_max, float(np.nanmax(Ip_kA[max(peak_idx, idx - pre_samples):idx + 1])))
        post = Ip_kA[idx:idx + post_samples]
        post_slope = np.abs(dIp_dt_kA_per_ms[idx:idx + post_samples])
        if post.size < 3:
            continue
        post_mean = float(np.nanmean(post))
        post_range = float(np.nanmax(post) - np.nanmin(post))
        post_slope_mean = float(np.nanmean(post_slope))
        drop_from_peak = peak_to_now_max - post_mean

        if drop_from_peak < drop_limit:
            continue
        if post_range > variation_limit:
            continue
        if post_slope_mean > slope_limit:
            continue
        # Do not cut while Ip is still strongly decreasing. The first point of a
        # genuinely flat residual offset should already have small local slope.
        if abs(float(dIp_dt_kA_per_ms[idx])) > slope_limit:
            continue

        return Time[idx], "Ip_high_residual_plateau_after_drop"

    return None, "high_residual_plateau_not_found"


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

    high_residual_end = None
    high_residual_method = "high_residual_plateau_not_checked"
    if IP_HIGH_RESIDUAL_PLATEAU_DETECTION_ENABLED:
        high_residual_end, high_residual_method = detect_ip_high_residual_plateau_time(
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
    if high_residual_end is not None and np.isfinite(high_residual_end) and high_residual_end > start_time and high_residual_end <= threshold_end:
        candidates.append((high_residual_end, high_residual_method))

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
            "high_residual_plateau_end_time": high_residual_end,
            "high_residual_plateau_method": high_residual_method,
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
        'Ip_start_5pct_time_ms': data.get('Ip_start_5pct_time', np.nan) * 1000 if np.isfinite(data.get('Ip_start_5pct_time', np.nan)) else np.nan,
        'Ip_start_5pct_method': data.get('Ip_start_5pct_method', ''),
        'Ip_start_behavior_score': data.get('Ip_start_behavior_score', np.nan),
        'Ip_start_behavior_pre_slope_kA_per_ms': data.get('Ip_start_behavior_pre_slope_kA_per_ms', np.nan),
        'Ip_start_behavior_post_slope_kA_per_ms': data.get('Ip_start_behavior_post_slope_kA_per_ms', np.nan),
        'Ip_start_behavior_post_rise_A': data.get('Ip_start_behavior_post_rise_A', np.nan),
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
    shot_summary_rows, halpha_rows, halpha_real_rows, timing_rows, global_rows, covariance_rows, important_rows = [], [], [], [], [], [], []
    for data in processed_data:
        try:
            important_rows.append(compute_important_data_row(data))
        except Exception:
            pass
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
        'important_data': pd.DataFrame(important_rows),
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
    """Compute group averages on a common time base.

    Important convention used here:
      - Ip, H-alpha and Bt are all synchronized to the plasma-current start
        time, i.e. Time - t_Ip,start.

    Earlier versions used Time - t_Bt,start for the Bt panel.  That made the
    group-comparison figure inconsistent with the main page and made it harder
    to compare Bt at plasma start/end.  The Bt trace is now interpolated on the
    same Ip-synchronized time base as Ip and H-alpha.
    """
    if len(processed_data) < 1:
        return None

    is_single = len(processed_data) == 1

    # Use the Ip-synchronized reference axis for all time traces, including Bt.
    ref_time_ip = np.asarray(processed_data[0]['Time_sync_ip'], dtype=float)
    ref_time_bt = ref_time_ip

    Bt_all, Ip_all, Ha_all = [], [], []
    for data in processed_data:
        t_sync_ip = np.asarray(data['Time_sync_ip'], dtype=float)
        Bt_all.append(
            smooth_signal_time(
                ref_time_ip,
                np.interp(ref_time_ip, t_sync_ip, data['B_phi']),
                window_us=smooth_bt_us,
            )
        )
        Ip_all.append(
            smooth_signal_time(
                ref_time_ip,
                np.interp(ref_time_ip, t_sync_ip, data['Ip']),
                window_us=smooth_ip_us,
            )
        )
        Ha_all.append(
            smooth_signal_time(
                ref_time_ip,
                np.interp(ref_time_ip, t_sync_ip, data['Photod']),
                window_us=smooth_halpha_us,
            )
        )

    Bt_all, Ip_all, Ha_all = np.array(Bt_all), np.array(Ip_all), np.array(Ha_all)

    def mean_and_std_band(arr):
        mean = np.mean(arr, axis=0)
        std = np.zeros_like(mean) if is_single else np.std(arr, axis=0)
        return mean, std, mean - band_factor * std, mean + band_factor * std

    Bt_mean, Bt_std, Bt_lower, Bt_upper = mean_and_std_band(Bt_all)
    Ip_mean, Ip_std, Ip_lower, Ip_upper = mean_and_std_band(Ip_all)
    Ha_mean, Ha_std, Ha_lower, Ha_upper = mean_and_std_band(Ha_all)

    df_group = pd.DataFrame({
        'time_ms_from_Ip_start': ref_time_ip * 1000,
        # Backward-compatible aliases kept for older export readers.
        'time_bt_ms': ref_time_ip * 1000,
        'time_ip_ms': ref_time_ip * 1000,
        'Bt_mean_mT': Bt_mean,
        'Bt_std_mT': Bt_std,
        'Bt_lower_mT': Bt_lower,
        'Bt_upper_mT': Bt_upper,
        'Ip_mean_kA': Ip_mean / 1000,
        'Ip_std_kA': Ip_std / 1000,
        'Ip_lower_kA': Ip_lower / 1000,
        'Ip_upper_kA': Ip_upper / 1000,
        'Halpha_mean': Ha_mean,
        'Halpha_std': Ha_std,
        'Halpha_lower': Ha_lower,
        'Halpha_upper': Ha_upper,
    })

    return {
        'group_label': group_label,
        'ref_time_bt': ref_time_ip,
        'ref_time_ip': ref_time_ip,
        'Bt_mean': Bt_mean,
        'Bt_std': Bt_std,
        'Bt_lower': Bt_lower,
        'Bt_upper': Bt_upper,
        'Ip_mean': Ip_mean,
        'Ip_std': Ip_std,
        'Ip_lower': Ip_lower,
        'Ip_upper': Ip_upper,
        'Ha_mean': Ha_mean,
        'Ha_std': Ha_std,
        'Ha_lower': Ha_lower,
        'Ha_upper': Ha_upper,
        'df_group': df_group,
        'n_shots': len(processed_data),
        'is_single_shot': is_single,
        'shot_numbers': [d['shot_number'] for d in processed_data],
        'band_factor': band_factor,
        'smooth_bt_us': smooth_bt_us,
        'smooth_ip_us': smooth_ip_us,
        'smooth_halpha_us': smooth_halpha_us,
        'sync_reference': 'Ip_start',
    }

def compute_halpha_duration_official_style(Time, Halpha, level_percent=6.0, start_time_ms=4.0, stop_time_ms=18.0):
    """
    H-alpha based duration inspired by the recent MEPhIST/MephistDataKit notebooks.

    It is deliberately kept as an additional diagnostic, not as a replacement for
    the Ip-defined plasma duration used by the rest of this visualizer.
    """
    Time = np.asarray(Time, dtype=float)
    Halpha = np.asarray(Halpha, dtype=float)
    if Time.size < 5 or Halpha.size < 5 or Time.shape != Halpha.shape:
        return np.nan, np.nan, np.nan, np.nan

    t_ms = Time * 1000.0
    mask = (t_ms >= float(start_time_ms)) & (t_ms <= float(stop_time_ms))
    if np.sum(mask) < 5:
        return np.nan, np.nan, np.nan, np.nan

    t_cut_s = Time[mask]
    t_cut_ms = t_ms[mask]
    ha_abs = np.abs(Halpha[mask].astype(float))

    if ha_abs.size < 5 or not np.any(np.isfinite(ha_abs)):
        return np.nan, np.nan, np.nan, np.nan

    # Linear edge detrend like the notebook version. It helps remove slow offsets.
    try:
        t0, t1 = float(t_cut_s[0]), float(t_cut_s[-1])
        y0, y1 = float(ha_abs[0]), float(ha_abs[-1])
        if t1 > t0:
            a = (y1 - y0) / (t1 - t0)
            b = y0 - a * t0
            ha_work = ha_abs - (a * t_cut_s + b)
        else:
            ha_work = ha_abs.copy()
    except Exception:
        ha_work = ha_abs.copy()

    ha_work = positive_part(ha_work)

    # Savitzky-Golay smoothing when SciPy is available. Otherwise use a compact
    # moving-average fallback so the GUI does not depend on SciPy for loading.
    if savgol_filter is not None and ha_work.size >= 7:
        win = min(200, ha_work.size - 1)
        if win % 2 == 0:
            win -= 1
        if win >= 5:
            try:
                ha_smooth = savgol_filter(ha_work, window_length=win, polyorder=3)
            except Exception:
                ha_smooth = ha_work
        else:
            ha_smooth = ha_work
    else:
        win = min(101, ha_work.size)
        if win < 3:
            ha_smooth = ha_work
        else:
            if win % 2 == 0:
                win -= 1
            kernel = np.ones(win) / win
            ha_smooth = np.convolve(ha_work, kernel, mode="same")

    peak = float(np.nanmax(ha_smooth)) if ha_smooth.size else np.nan
    if not np.isfinite(peak) or peak <= 0:
        return np.nan, np.nan, np.nan, peak

    threshold = (float(level_percent) / 100.0) * peak

    start_idx = None
    t_start = np.nan
    for i in range(len(t_cut_s) - 1):
        if ha_smooth[i] <= threshold and ha_smooth[i + 1] > threshold:
            denom = ha_smooth[i + 1] - ha_smooth[i]
            frac = 0.0 if abs(denom) < 1e-15 else (threshold - ha_smooth[i]) / denom
            t_start = t_cut_s[i] + frac * (t_cut_s[i + 1] - t_cut_s[i])
            start_idx = i
            break

    if start_idx is None:
        return np.nan, np.nan, np.nan, peak

    t_end = np.nan
    for i in range(len(t_cut_s) - 1, start_idx, -1):
        if ha_smooth[i - 1] > threshold and ha_smooth[i] <= threshold:
            denom = ha_smooth[i] - ha_smooth[i - 1]
            frac = 0.0 if abs(denom) < 1e-15 else (threshold - ha_smooth[i - 1]) / denom
            t_end = t_cut_s[i - 1] + frac * (t_cut_s[i] - t_cut_s[i - 1])
            break

    if not np.isfinite(t_end):
        t_end = t_cut_s[-1]

    duration_ms = (t_end - t_start) * 1000.0 if t_end > t_start else np.nan
    return duration_ms, t_start * 1000.0, t_end * 1000.0, peak





def prepare_visible_emission_for_display(Time, t_raw_s, y_raw, baseline_end_ms=5.5):
    """
    Convert the visible-emission / H-alpha photodiode signal to the convention
    used by the official viewer: near-zero pre-plasma baseline and positive
    plasma emission.

    Why this is needed:
      - Old files can store H-alpha with a negative DC offset and positive burst.
      - Recent files can store the burst with opposite polarity.
      - Taking abs(raw) directly is wrong when the raw signal has a large DC
        offset: it creates an artificial flat high pre-plasma baseline.

    Procedure:
      1) Estimate a pre-plasma baseline from the first milliseconds.
      2) Subtract that baseline.
      3) Choose the polarity whose main 4-16 ms excursion is positive.
      4) Clip negative residuals to zero for the display/integral channel.
    """
    Time = np.asarray(Time, dtype=float)
    t_raw_s = np.asarray(t_raw_s, dtype=float)
    y_raw = np.asarray(y_raw, dtype=float)

    if Time.size == 0 or t_raw_s.size < 2 or y_raw.size < 2:
        return np.zeros_like(Time), np.zeros_like(Time), np.nan, 'missing'

    n = min(t_raw_s.size, y_raw.size)
    t = t_raw_s[:n]
    y = y_raw[:n]
    valid = np.isfinite(t) & np.isfinite(y)
    if np.sum(valid) < 2:
        return np.zeros_like(Time), np.zeros_like(Time), np.nan, 'invalid'
    t = t[valid]
    y = y[valid]
    order = np.argsort(t)
    t = t[order]
    y = y[order]

    t_ms = t * 1000.0
    base_mask = (t_ms >= 0.0) & (t_ms <= float(baseline_end_ms))
    if np.sum(base_mask) < 10:
        # fallback: first 5 percent of samples, capped to a reasonable range
        n_base = max(10, min(1000, int(0.05 * y.size)))
        base_values = y[:n_base]
    else:
        base_values = y[base_mask]
    baseline = float(np.nanmedian(base_values)) if base_values.size else 0.0
    y0 = y - baseline

    plasma_mask = (t_ms >= 4.0) & (t_ms <= 16.0)
    if np.sum(plasma_mask) < 10:
        plasma_mask = np.ones_like(y0, dtype=bool)

    y_win = y0[plasma_mask]
    pos_peak = float(np.nanpercentile(np.maximum(y_win, 0.0), 99.5)) if y_win.size else 0.0
    neg_peak = float(np.nanpercentile(np.maximum(-y_win, 0.0), 99.5)) if y_win.size else 0.0

    if neg_peak > 1.15 * max(pos_peak, 1e-15):
        y_oriented = -y0
        polarity = 'inverted_after_baseline'
    else:
        y_oriented = y0
        polarity = 'positive_after_baseline'

    # Remove small negative baseline/noise after orientation. This is the signal
    # that should be compared visually with the official H-alpha panel.
    y_positive = positive_part(y_oriented)

    photod = np.interp(Time, t, y_positive, left=0.0, right=0.0)
    signed_setzero = np.interp(Time, t, y_oriented, left=0.0, right=0.0)
    return photod, signed_setzero, baseline, polarity


def parse_shot_setpoints_from_text(text_value):
    """Extract CS, TF and requested pressure from free-text metadata/comment."""
    text_value = '' if text_value is None else str(text_value)
    out = {'CS_voltage_V': np.nan, 'TF_voltage_V': np.nan, 'pressure_requested_mPa': np.nan}

    # Examples found in files/comments:
    #   "H2 CS1000 TF340 18mPa"
    #   "norm TF340 before Li"
    patterns = {
        'CS_voltage_V': r'\bCS\s*[:=]?\s*([-+]?\d+(?:[\.,]\d+)?)\s*V?\b',
        'TF_voltage_V': r'\bTF\s*[:=]?\s*([-+]?\d+(?:[\.,]\d+)?)\s*V?\b',
        'pressure_requested_mPa': r'([-+]?\d+(?:[\.,]\d+)?)\s*mPa\b',
    }
    for key, pat in patterns.items():
        m = re.search(pat, text_value, flags=re.IGNORECASE)
        if m:
            try:
                out[key] = float(m.group(1).replace(',', '.'))
            except Exception:
                pass
    return out


def infer_default_setpoints(shot_id_int):
    """
    Last-resort setpoints used in the recent-shot notebook examples.
    These are only used when the HDF5 metadata/comment does not explicitly store
    the setpoint.
    """
    if shot_id_int >= 3800:
        return {'CS_voltage_V': 900.0, 'TF_voltage_V': 340.0}
    return {'CS_voltage_V': np.nan, 'TF_voltage_V': np.nan}

def choose_preferred_plasma_end_time(
    Time,
    t0_ip,
    t_end_ip,
    ip_end_method,
    halpha_official_end_ms=np.nan,
    halpha_official_duration_ms=np.nan,
    halpha_detector_end=None,
):
    """
    Keep the visualizer's own Ip-based plasma end as the preferred plasma end.

    The H-alpha/MEPhIST-style duration is still computed and exported as an
    alternative diagnostic, but it must not replace the main plasma window used
    for tau, normalization and shot-to-shot comparison. This avoids mixing two
    different definitions of plasma duration between old and recent files.
    """
    return t_end_ip, str(ip_end_method), False


def robust_mad_sigma(values):
    """Return a robust sigma estimate based on the median absolute deviation."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 3:
        return np.nan
    med = float(np.nanmedian(arr))
    mad = float(np.nanmedian(np.abs(arr - med)))
    return 1.4826 * mad


def refine_single_time_with_loop_voltage_edge(
    Time,
    Vloop,
    reference_time,
    before_ms,
    after_ms,
    smooth_us=LOOP_VOLTAGE_EDGE_SMOOTH_US,
    min_sigma=LOOP_VOLTAGE_EDGE_MIN_SIGMA,
    min_abs_dv_per_ms=LOOP_VOLTAGE_EDGE_MIN_ABS_DV_PER_MS,
    min_prominence_V=LOOP_VOLTAGE_FEATURE_MIN_PROMINENCE_V,
    side_window_ms=LOOP_VOLTAGE_FEATURE_SIDE_WINDOW_MS,
    max_shift_ms=LOOP_VOLTAGE_FEATURE_MAX_SHIFT_MS,
    label="edge",
    selection="best",
    use_falling_edge=False,
    fall_fraction=LOOP_VOLTAGE_END_FALL_FRACTION,
):
    """
    Refine one approximate time using a nearby loop-voltage extremum.

    This intentionally does NOT choose the maximum |dVloop/dt|.  The largest
    derivative often occurs on the early rising edge of the CS/loop-voltage ramp,
    before the plasma column is actually established.  Instead, the routine
    searches near the Ip-based reference for a local Vloop peak that has both:

      1) a fast rise before the candidate, and
      2) a fast fall or clear change of trend after the candidate.

    If no physically plausible local Vloop feature is found, the original
    Ip-based reference is kept.
    """
    Time = np.asarray(Time, dtype=float)
    Vloop = np.asarray(Vloop, dtype=float)

    def _fail(method, score=np.nan, noise=np.nan, t0=np.nan, t1=np.nan):
        return {
            'time': reference_time,
            'used': False,
            'method': f'{label}_{method}',
            'score_V_per_ms': score,
            'noise_sigma_V_per_ms': noise,
            'search_start_ms': t0 * 1000.0 if np.isfinite(t0) else np.nan,
            'search_end_ms': t1 * 1000.0 if np.isfinite(t1) else np.nan,
            'feature_prominence_V': np.nan,
            'feature_rise_V': np.nan,
            'feature_fall_V': np.nan,
            'peak_time': np.nan,
            'fall_end_time': np.nan,
            'time_definition': 'reference_fallback',
            'selected_peak_order': '',
        }

    if Time.size < 7 or Vloop.size < 7 or Time.shape != Vloop.shape:
        return _fail('loop_voltage_invalid_signal')

    if reference_time is None or not np.isfinite(reference_time):
        return _fail('loop_voltage_invalid_reference')

    t0 = float(reference_time) - float(before_ms) * 1e-3
    t1 = float(reference_time) + float(after_ms) * 1e-3
    mask = (Time >= t0) & (Time <= t1) & np.isfinite(Vloop)
    local_idx = np.where(mask)[0]

    if local_idx.size < 7:
        return _fail('loop_voltage_no_search_window', t0=t0, t1=t1)

    V_smooth = smooth_signal_time(Time, Vloop, window_us=smooth_us)
    t_ms = Time * 1000.0
    dV_dt = np.gradient(V_smooth, t_ms)  # V/ms
    abs_dV_dt = np.abs(dV_dt)

    local_abs = abs_dV_dt[local_idx]
    finite_abs = local_abs[np.isfinite(local_abs)]
    if finite_abs.size < 3:
        return _fail('loop_voltage_bad_derivative', t0=t0, t1=t1)

    # Estimate derivative noise from the quiet part of the local interval. Using
    # every sample would let the genuine peaks inflate their own noise estimate
    # and can incorrectly reject the final, smaller peak.
    quiet_limit = float(np.nanpercentile(finite_abs, 40.0))
    quiet_abs = finite_abs[finite_abs <= quiet_limit]
    noise_sigma = robust_mad_sigma(quiet_abs)
    if not np.isfinite(noise_sigma) or noise_sigma <= 1e-15:
        noise_sigma = float(np.nanstd(quiet_abs)) if quiet_abs.size else np.nan

    side_samples = max(int(round((float(side_window_ms) * 1e-3) / np.nanmedian(np.diff(Time)))), 3)
    max_shift_s = float(max_shift_ms) * 1e-3

    def _fall_end_time(peak_idx):
        """Return the first sample after a peak where the requested decay is reached."""
        right1 = min(local_idx[-1] + 1, peak_idx + side_samples + 1)
        right_indices = np.arange(peak_idx, right1, dtype=int)
        if right_indices.size < 3:
            return float(Time[peak_idx])
        right_values = V_smooth[right_indices]
        peak_value = float(V_smooth[peak_idx])
        # Estimate the post-feature level from a robust tail median. Using the
        # absolute minimum incorrectly pushes the end to the right when CS/eddy
        # pickup produces a slow global downward ramp after the local peak.
        tail_fraction = float(np.clip(
            LOOP_VOLTAGE_FALL_BASELINE_TAIL_FRACTION, 0.10, 0.50
        ))
        tail_samples = max(3, int(np.ceil(tail_fraction * right_values.size)))
        right_floor = float(np.nanmedian(right_values[-tail_samples:]))
        excursion = peak_value - right_floor
        if not np.isfinite(excursion) or excursion <= 0:
            return float(Time[peak_idx])
        fraction = float(np.clip(fall_fraction, 0.0, 1.0))
        target = peak_value - fraction * excursion
        below = np.asarray(V_smooth[right_indices] <= target, dtype=bool)
        dt_s = float(np.nanmedian(np.diff(Time)))
        hold_samples = max(
            2,
            int(round((LOOP_VOLTAGE_FALL_MIN_SUSTAINED_US * 1e-6) / dt_s))
            if np.isfinite(dt_s) and dt_s > 0 else 2,
        )
        first_sustained = None
        for local_pos in range(0, max(below.size - hold_samples + 1, 0)):
            if np.all(below[local_pos:local_pos + hold_samples]):
                first_sustained = int(local_pos)
                break
        if first_sustained is None:
            return float(Time[peak_idx])
        return float(Time[int(right_indices[first_sustained])])

    candidates = []
    # Keep away from the very edges of the search interval so that both sides
    # of the candidate can be inspected.
    for idx in local_idx[2:-2]:
        if idx <= 1 or idx >= len(Time) - 2:
            continue
        # Local positive peak.  For MEPhIST loop-voltage diagnostics this is the
        # physically useful feature around breakdown/termination in the examples.
        if not (V_smooth[idx] >= V_smooth[idx - 1] and V_smooth[idx] >= V_smooth[idx + 1]):
            continue

        left0 = max(local_idx[0], idx - side_samples)
        right1 = min(local_idx[-1] + 1, idx + side_samples + 1)
        left = V_smooth[left0:idx + 1]
        right = V_smooth[idx:right1]
        if left.size < 3 or right.size < 3:
            continue

        left_min = float(np.nanmin(left))
        right_min = float(np.nanmin(right))
        peak_val = float(V_smooth[idx])
        rise = peak_val - left_min
        fall = peak_val - right_min
        prominence = min(rise, fall)

        # Require a genuine rise-and-fall, not just a monotonic ramp edge.
        if not np.isfinite(prominence) or prominence < float(min_prominence_V):
            continue

        left_slope = float(np.nanmax(np.abs(dV_dt[left0:idx + 1])))
        right_slope = float(np.nanmax(np.abs(dV_dt[idx:right1])))
        local_slope = min(left_slope, right_slope)
        if local_slope < float(min_abs_dv_per_ms):
            continue
        if np.isfinite(noise_sigma) and noise_sigma > 1e-15 and local_slope < float(min_sigma) * noise_sigma:
            continue

        shift = abs(float(Time[idx]) - float(reference_time))
        if shift > max_shift_s:
            continue

        # Prefer strong, symmetric, nearby features.  The distance penalty avoids
        # jumping to an unrelated voltage feature when the Ip estimate is already good.
        distance_penalty = 1.0 + shift / max(max_shift_s, 1e-12)
        score = (prominence * local_slope) / distance_penalty
        candidates.append({
            'idx': int(idx),
            'time': float(Time[idx]),
            'score': float(score),
            'local_slope': float(local_slope),
            'rise': float(rise),
            'fall': float(fall),
            'prominence': float(prominence),
            'shift_ms': float(shift * 1000.0),
        })

    if not candidates:
        # As a conservative fallback, if the Ip reference itself is already close
        # to the local Vloop maximum, use that maximum only when it is close and
        # prominent enough. Otherwise keep the Ip-based reference.
        local_v = V_smooth[local_idx]
        best_idx = int(local_idx[int(np.nanargmax(local_v))])
        shift = abs(float(Time[best_idx]) - float(reference_time))
        if shift <= max_shift_s:
            left0 = max(local_idx[0], best_idx - side_samples)
            right1 = min(local_idx[-1] + 1, best_idx + side_samples + 1)
            peak_val = float(V_smooth[best_idx])
            rise = peak_val - float(np.nanmin(V_smooth[left0:best_idx + 1]))
            fall = peak_val - float(np.nanmin(V_smooth[best_idx:right1]))
            prominence = min(rise, fall)
            local_slope = min(
                float(np.nanmax(np.abs(dV_dt[left0:best_idx + 1]))),
                float(np.nanmax(np.abs(dV_dt[best_idx:right1]))),
            )
            if prominence >= float(min_prominence_V) and local_slope >= float(min_abs_dv_per_ms):
                peak_time = float(Time[best_idx])
                fall_end_time = _fall_end_time(best_idx)
                selected_time = fall_end_time if use_falling_edge else peak_time
                return {
                    'time': selected_time,
                    'used': True,
                    'method': (
                        f'{label}_loop_voltage_local_peak_falling_edge_fallback'
                        if use_falling_edge else f'{label}_loop_voltage_local_peak_fallback'
                    ),
                    'score_V_per_ms': local_slope,
                    'noise_sigma_V_per_ms': noise_sigma,
                    'search_start_ms': t0 * 1000.0,
                    'search_end_ms': t1 * 1000.0,
                    'feature_prominence_V': float(prominence),
                    'feature_rise_V': float(rise),
                    'feature_fall_V': float(fall),
                    'peak_time': peak_time,
                    'fall_end_time': fall_end_time,
                    'time_definition': 'falling_edge' if use_falling_edge else 'peak',
                    'selected_peak_order': 'fallback_local_maximum',
                }
        return _fail('loop_voltage_no_peak_with_rise_and_fall', score=float(np.nanmax(finite_abs)), noise=noise_sigma, t0=t0, t1=t1)

    # For plasma termination the requested convention is the last valid peak in
    # the Ip-anchored search interval.  Other callers can retain score selection.
    if str(selection).lower() == 'last':
        best = sorted(candidates, key=lambda c: (c['time'], c['prominence']))[-1]
        selected_peak_order = 'last_valid_peak'
    else:
        best = sorted(candidates, key=lambda c: (-c['score'], c['shift_ms']))[0]
        selected_peak_order = 'best_score'

    peak_time = best['time']
    fall_end_time = _fall_end_time(best['idx'])
    selected_time = fall_end_time if use_falling_edge else peak_time
    return {
        'time': selected_time,
        'used': True,
        'method': (
            f'{label}_loop_voltage_last_valid_peak_falling_edge'
            if str(selection).lower() == 'last' and use_falling_edge
            else f'{label}_loop_voltage_last_valid_peak'
            if str(selection).lower() == 'last'
            else f'{label}_loop_voltage_local_peak_rise_fall'
        ),
        'score_V_per_ms': best['local_slope'],
        'noise_sigma_V_per_ms': noise_sigma,
        'search_start_ms': t0 * 1000.0,
        'search_end_ms': t1 * 1000.0,
        'feature_prominence_V': best['prominence'],
        'feature_rise_V': best['rise'],
        'feature_fall_V': best['fall'],
        'peak_time': peak_time,
        'fall_end_time': fall_end_time,
        'time_definition': 'falling_edge' if use_falling_edge else 'peak',
        'selected_peak_order': selected_peak_order,
    }


def refine_plasma_window_with_loop_voltage(Time, Vloop, ip_start_time, ip_end_time):
    """
    Keep the Ip-based start and determine only the plasma end from Vloop.

    The selected feature is the last valid positive Vloop peak in a local window
    around the Ip-only end.  By default the reported end is the completion of its
    falling edge; both the peak and falling-edge times are returned for audit.
    """
    start_info = {
        'time': ip_start_time,
        'used': False,
        'method': 'start_ip_only_vloop_not_used',
        'score_V_per_ms': np.nan,
        'noise_sigma_V_per_ms': np.nan,
        'search_start_ms': np.nan,
        'search_end_ms': np.nan,
    }
    end_info = refine_single_time_with_loop_voltage_edge(
        Time, Vloop, ip_end_time,
        before_ms=LOOP_VOLTAGE_END_SEARCH_BEFORE_MS,
        after_ms=LOOP_VOLTAGE_END_SEARCH_AFTER_MS,
        label='end',
        selection='last',
        use_falling_edge=LOOP_VOLTAGE_END_USE_FALLING_EDGE,
        fall_fraction=LOOP_VOLTAGE_END_FALL_FRACTION,
    )

    start_t = start_info.get('time', ip_start_time)
    end_t = end_info.get('time', ip_end_time)

    # Guard against pathological inversions. Use Ip references when refinement
    # would make the duration non-physical.
    if not (np.isfinite(start_t) and np.isfinite(end_t) and end_t > start_t):
        start_t = ip_start_time
        end_t = ip_end_time
        start_info['used'] = False
        end_info['used'] = False
        start_info['method'] = str(start_info.get('method', '')) + '_duration_guard'
        end_info['method'] = str(end_info.get('method', '')) + '_duration_guard'

    return {
        'start_time': start_t,
        'end_time': end_t,
        'start_used': bool(start_info.get('used', False)),
        'end_used': bool(end_info.get('used', False)),
        'start_method': start_info.get('method', ''),
        'end_method': end_info.get('method', ''),
        'start_score_V_per_ms': start_info.get('score_V_per_ms', np.nan),
        'end_score_V_per_ms': end_info.get('score_V_per_ms', np.nan),
        'start_noise_sigma_V_per_ms': start_info.get('noise_sigma_V_per_ms', np.nan),
        'end_noise_sigma_V_per_ms': end_info.get('noise_sigma_V_per_ms', np.nan),
        'start_search_start_ms': start_info.get('search_start_ms', np.nan),
        'start_search_end_ms': start_info.get('search_end_ms', np.nan),
        'end_search_start_ms': end_info.get('search_start_ms', np.nan),
        'end_search_end_ms': end_info.get('search_end_ms', np.nan),
        'end_peak_time': end_info.get('peak_time', np.nan),
        'end_fall_time': end_info.get('fall_end_time', np.nan),
        'end_time_definition': end_info.get('time_definition', ''),
        'end_selected_peak_order': end_info.get('selected_peak_order', ''),
        'end_feature_prominence_V': end_info.get('feature_prominence_V', np.nan),
    }


def f_1_qa(kappa, delta):
    return (1.0 + kappa**2 * (1.0 + 2.0 * delta**2 - 1.2 * delta**3)) / 2.0


def f_2_qa(R, a):
    A = R / a
    return (1.17 - 0.65 / A) / (1.0 - A**(-2))**2


def compute_qa_profile_from_data(Time, Ip_A, B_phi_mT, a=0.10, R=0.25, kappa=1.7, delta=0.0):
    """Return q(a) profile using the same simple estimate used in the notebook."""
    Time = np.asarray(Time, dtype=float)
    Ip_A = np.asarray(Ip_A, dtype=float)
    B_phi_mT = np.asarray(B_phi_mT, dtype=float)
    if Time.size == 0 or Ip_A.size == 0 or B_phi_mT.size == 0:
        return np.array([]), np.array([])
    n = min(Time.size, Ip_A.size, B_phi_mT.size)
    Time = Time[:n]
    Ip_A = Ip_A[:n]
    B_phi_mT = B_phi_mT[:n]
    Bt_T = B_phi_mT / 1000.0
    Ip_MA = Ip_A / 1e6
    q = np.full_like(Time, np.nan, dtype=float)
    mask = np.isfinite(Ip_MA) & np.isfinite(Bt_T) & (np.abs(Ip_MA) > 1e-4)
    q[mask] = (5.0 * a**2 * Bt_T[mask] * f_1_qa(kappa, delta) * f_2_qa(R, a)) / (R * np.abs(Ip_MA[mask]))
    return Time, q


def compute_important_data_row(data):
    """Build one compact row with the same quantities shown in the official viewer/table."""
    Time = np.asarray(data.get('Time', np.array([])), dtype=float)
    Ip = np.asarray(data.get('Ip', np.array([])), dtype=float)
    Bt = np.asarray(data.get('B_phi', np.array([])), dtype=float)
    CS = np.asarray(data.get('CS_current_kA', np.array([])), dtype=float)
    TF = np.asarray(data.get('TF_current_kA', np.array([])), dtype=float)

    # q(a) must be evaluated only during the physical plasma interval.
    # If we take the minimum over the whole record, the early pre-plasma region
    # where Bt ~ 0 can produce artificial q ~ 0 values. This made new and old
    # shots incomparable. Therefore the Important data table reports q(a)_min
    # over the Ip-defined plasma window and with weak low-signal guard masks.
    _, q_profile = compute_qa_profile_from_data(Time, Ip, Bt)
    q_mask = np.isfinite(q_profile)
    if Time.size and Ip.size and Bt.size:
        t_start_q = data.get('Ip_start_time', np.nan)
        t_end_q = data.get('Ip_end_time', np.nan)
        if np.isfinite(t_start_q) and np.isfinite(t_end_q) and t_end_q > t_start_q:
            q_mask &= (Time >= t_start_q) & (Time <= t_end_q)
        ip_ref_q = np.nanmax(np.abs(Ip)) if Ip.size else np.nan
        if np.isfinite(ip_ref_q) and ip_ref_q > 0:
            q_mask &= (np.abs(Ip) >= max(0.05 * ip_ref_q, 1000.0))
        q_mask &= (np.abs(Bt) >= 20.0)
    q_min = float(np.nanmin(q_profile[q_mask])) if q_profile.size and np.any(q_mask) else np.nan

    row = {
        'shot': data.get('shot_number', ''),
        'gas': data.get('gas', ''),
        'pressure_measured_mPa': data.get('pressure_measured_mPa', np.nan),
        'pressure_requested_mPa': data.get('pressure_requested_mPa', np.nan),
        'CS_voltage_V': data.get('CS_voltage_V', np.nan),
        'TF_voltage_V': data.get('TF_voltage_V', np.nan),
        'I_max_kA': data.get('I_p_max_kA', np.nan),
        'I_min_kA': float(np.nanmin(Ip) / 1000.0) if Ip.size else np.nan,
        'Bt_max_mT': data.get('B_phi_max_mT', np.nan),
        'Bt_min_mT': float(np.nanmin(Bt)) if Bt.size else np.nan,
        'qa_min': q_min,
        'duration_preferred_my_method_ms': data.get('plasma_duration_sec', np.nan) * 1000.0,
        'duration_Ip_only_ms': data.get('plasma_duration_ip_only_sec', np.nan) * 1000.0,
        'duration_MEPhIST_Halpha_method_ms': data.get('Halpha_official_duration_ms', np.nan),
        'plasma_end_method_preferred': data.get('plasma_end_method', ''),
        'plasma_end_method_Ip_only': data.get('plasma_end_method_ip_only', ''),
        'plasma_end_halpha_guard_used': data.get('plasma_end_halpha_guard_used', False),
        'Ip_start_ms': data.get('Ip_start_time', np.nan) * 1000.0,
        'Ip_start_ms_Ip_only': data.get('Ip_start_time_Ip_only', np.nan) * 1000.0,
        'Ip_start_loop_refined': data.get('Ip_start_loop_refined', False),
        'Ip_start_loop_edge_score_V_per_ms': data.get('Ip_start_loop_edge_score_V_per_ms', np.nan),
        'Ip_start_loop_edge_method': data.get('Ip_start_loop_edge_method', ''),
        'Ip_end_ms_preferred': data.get('Ip_end_time', np.nan) * 1000.0,
        'Ip_end_ms_before_loop_refinement': data.get('Ip_end_time_before_loop_refinement', np.nan) * 1000.0,
        'Ip_end_loop_refined': data.get('Ip_end_loop_refined', False),
        'Ip_end_loop_edge_score_V_per_ms': data.get('Ip_end_loop_edge_score_V_per_ms', np.nan),
        'Ip_end_loop_edge_method': data.get('Ip_end_loop_edge_method', ''),
        'Ip_end_loop_last_peak_ms': data.get('Ip_end_loop_peak_time', np.nan) * 1000.0,
        'Ip_end_loop_falling_edge_ms': data.get('Ip_end_loop_fall_time', np.nan) * 1000.0,
        'Ip_end_loop_time_definition': data.get('Ip_end_loop_time_definition', ''),
        'Ip_end_loop_selected_peak_order': data.get('Ip_end_loop_selected_peak_order', ''),
        'Ip_end_loop_feature_prominence_V': data.get('Ip_end_loop_feature_prominence_V', np.nan),
        'Ip_end_ms_Ip_only': data.get('Ip_end_time_ip_only', np.nan) * 1000.0,
        'Halpha_official_start_ms': data.get('Halpha_official_start_ms', np.nan),
        'Halpha_official_end_ms': data.get('Halpha_official_end_ms', np.nan),
        'Halpha_end_ms_detector': data.get('Halpha_end_time', np.nan) * 1000.0,
        'Halpha_polarity_method': data.get('Halpha_polarity_method', ''),
        'Halpha_baseline_raw': data.get('Halpha_baseline_raw', np.nan),
        'CS_voltage_source': data.get('CS_voltage_source', ''),
        'TF_voltage_source': data.get('TF_voltage_source', ''),
        'CS_current_min_kA': float(np.nanmin(CS)) if CS.size and np.any(np.isfinite(CS)) else np.nan,
        'CS_current_max_kA': float(np.nanmax(CS)) if CS.size and np.any(np.isfinite(CS)) else np.nan,
        'TF_current_min_kA': float(np.nanmin(TF)) if TF.size and np.any(np.isfinite(TF)) else np.nan,
        'TF_current_max_kA': float(np.nanmax(TF)) if TF.size and np.any(np.isfinite(TF)) else np.nan,
        'PF1_current_max_kA': float(np.nanmax(np.asarray(data.get('PF1_current_kA', []), dtype=float))) if len(data.get('PF1_current_kA', [])) else np.nan,
        'PF2_current_max_kA': float(np.nanmax(np.asarray(data.get('PF2_current_kA', []), dtype=float))) if len(data.get('PF2_current_kA', [])) else np.nan,
        'PF3_current_max_kA': float(np.nanmax(np.asarray(data.get('PF3_current_kA', []), dtype=float))) if len(data.get('PF3_current_kA', [])) else np.nan,
        'PF4_current_max_kA': float(np.nanmax(np.asarray(data.get('PF4_current_kA', []), dtype=float))) if len(data.get('PF4_current_kA', [])) else np.nan,
        'spectrum_source': data.get('Avantes_intensity_source', ''),
        'available_spectrum_sources': data.get('available_spectrum_sources', ''),
        'default_spectrum_source': data.get('default_spectrum_source', ''),
        'loader_mode': data.get('loader_mode', ''),
        'missing_signals': ', '.join(map(str, data.get('missing_signals', []))),
    }

    # Add the H-alpha integrals directly to Important data so the separate
    # H-alpha-integral buttons are not needed. Two primary definitions are shown:
    #   1) H-alpha integrated over the Ip-defined plasma window.
    #   2) H-alpha integrated over its own detected optical window
    #      Halpha_start_5pct -> Halpha_end.
    # As a backup/comparison, the MEPhIST-style H-alpha duration window is also
    # integrated when available.
    try:
        hm = compute_halpha_integral_metrics(data)
    except Exception:
        hm = None

    if hm is not None:
        row.update({
            'Halpha_integral_my_Ip_window_positive': hm.get('Halpha_integral_plasma_time_positive', np.nan),
            'Halpha_mean_my_Ip_window': hm.get('Halpha_mean_over_plasma_duration', np.nan),
            'Halpha_duration_my_Ip_window_ms': hm.get('plasma_duration_ms_Ip', np.nan),
            'Halpha_integral_my_Halpha_window_positive': hm.get('Halpha_integral_real_time_positive', np.nan),
            'Halpha_mean_my_Halpha_window': hm.get('Halpha_mean_over_real_Halpha_duration', np.nan),
            'Halpha_duration_my_Halpha_window_ms': hm.get('Halpha_real_duration_ms_5pct_to_end', np.nan),
            'Halpha_start_my_Halpha_window_ms': hm.get('Halpha_start_5pct_ms', np.nan),
            'Halpha_end_my_Halpha_window_ms': hm.get('Halpha_end_ms', np.nan),
        })

    # Backup: integrate using the MEPhIST-style H-alpha start/end times, if the
    # loader found them. The main plasma duration still remains your Ip-based one.
    try:
        t0_ms = float(data.get('Halpha_official_start_ms', np.nan))
        t1_ms = float(data.get('Halpha_official_end_ms', np.nan))
        Halpha = np.asarray(data.get('Photod', np.array([])), dtype=float)
        if Time.size and Halpha.size and Halpha.shape == Time.shape and np.isfinite(t0_ms) and np.isfinite(t1_ms) and t1_ms > t0_ms:
            t0 = t0_ms * 1e-3
            t1 = t1_ms * 1e-3
            mask = (Time >= t0) & (Time <= t1)
            if np.sum(mask) >= 2:
                ha_pos = positive_part(Halpha[mask])
                integ = float(trapz_compat(ha_pos, Time[mask]))
                dur_s = float(t1 - t0)
                row.update({
                    'Halpha_integral_MEPhIST_window_positive': integ,
                    'Halpha_mean_MEPhIST_window': integ / dur_s if dur_s > 0 else np.nan,
                    'Halpha_duration_MEPhIST_window_ms': dur_s * 1000.0,
                    'Halpha_start_MEPhIST_window_ms': t0_ms,
                    'Halpha_end_MEPhIST_window_ms': t1_ms,
                })
    except Exception:
        pass

    return row


def compute_requested_discharge_summary_row(data):
    """Build a compact table row matching the requested discharge-summary columns.

    This summary deliberately uses the final Ip_start_time / Ip_end_time stored
    in each processed shot. In the current loader those times are the preferred
    plasma window, i.e. the Ip detector refined locally with loop-voltage edges
    when the loop-voltage refinement is accepted.
    """
    Time = np.asarray(data.get('Time', np.array([])), dtype=float)
    Ip = np.asarray(data.get('Ip', np.array([])), dtype=float)
    Bt = np.asarray(data.get('B_phi', np.array([])), dtype=float)
    Halpha = np.asarray(data.get('Photod', np.array([])), dtype=float)

    ip_start = float(data.get('Ip_start_time', np.nan))
    ip_end = float(data.get('Ip_end_time', np.nan))
    bt_start = float(data.get('Bt_sync_time', np.nan))

    pressure_group_label = data.get('folder_label') or data.get('pressure_group', '')
    pressure_group_mpa = np.nan
    try:
        group_text = str(pressure_group_label).strip().replace(',', '.')
        group_match = re.search(r"([-+]?\d+(?:\.\d+)?)\s*(mPa|Pa|mbar)?", group_text, re.IGNORECASE)
        if group_match:
            pressure_group_mpa = float(group_match.group(1))
            group_unit = (group_match.group(2) or 'mPa').lower()
            if group_unit == 'pa':
                pressure_group_mpa *= 1e3
            elif group_unit == 'mbar':
                pressure_group_mpa *= 1e5
    except Exception:
        pressure_group_mpa = np.nan

    row = {
        'Pressure_group_mPa': pressure_group_mpa,
        'pressure_group_from_folder': pressure_group_label,
        'shot': data.get('shot_number', ''),
        'Plasma_gas': data.get('gas', ''),
        'CS_cap_Ip_V': data.get('CS_voltage_V', np.nan),
        'TF_cap_Bt_V': data.get('TF_voltage_V', np.nan),
        'pWG_requested_mPa': data.get('pressure_requested_mPa', np.nan),
        'Vacuum_total_pressure_mPa': data.get('pressure_measured_mPa', np.nan),
        'Vacuum_total_pressure_mbar': (
            float(data.get('pressure_measured_mPa', np.nan)) * 1e-5
            if np.isfinite(float(data.get('pressure_measured_mPa', np.nan))) else np.nan
        ),
        'Pressure_measured_source': data.get('pressure_measured_source', ''),
        'Pressure_requested_source': data.get('pressure_requested_source', ''),
        'Pressure_working_gas': data.get('gas', ''),
        'MFC1_gasType': data.get('MFC1_gasType', np.nan),
        'MFC1_in_file_units': data.get('MFC1_in_file_units', np.nan),
        'MFC2_gasType': data.get('MFC2_gasType', np.nan),
        'MFC2_in_file_units': data.get('MFC2_in_file_units', np.nan),
        'MFC3_gasType': data.get('MFC3_gasType', np.nan),
        'MFC3_in_file_units': data.get('MFC3_in_file_units', np.nan),
        'FastValve_delay1_file_units': data.get('FastValve_delay1_file_units', np.nan),
        'FastValve_delay2_file_units': data.get('FastValve_delay2_file_units', np.nan),
        'FastValve_duration1_file_units': data.get('FastValve_duration1_file_units', np.nan),
        'FastValve_duration2_file_units': data.get('FastValve_duration2_file_units', np.nan),
        'FastValve_duration3_file_units': data.get('FastValve_duration3_file_units', np.nan),
        'MFC1_gasType_source': data.get('MFC1_gasType_source', ''),
        'MFC1_in_source': data.get('MFC1_in_source', ''),
        'MFC1_in_unit_from_file': data.get('MFC1_in_unit_from_file', ''),
        'MFC2_gasType_source': data.get('MFC2_gasType_source', ''),
        'MFC2_in_source': data.get('MFC2_in_source', ''),
        'MFC2_in_unit_from_file': data.get('MFC2_in_unit_from_file', ''),
        'MFC3_gasType_source': data.get('MFC3_gasType_source', ''),
        'MFC3_in_source': data.get('MFC3_in_source', ''),
        'MFC3_in_unit_from_file': data.get('MFC3_in_unit_from_file', ''),
        'FastValve_delay1_source': data.get('FastValve_delay1_source', ''),
        'FastValve_delay1_unit_from_file': data.get('FastValve_delay1_unit_from_file', ''),
        'FastValve_delay2_source': data.get('FastValve_delay2_source', ''),
        'FastValve_delay2_unit_from_file': data.get('FastValve_delay2_unit_from_file', ''),
        'FastValve_duration1_source': data.get('FastValve_duration1_source', ''),
        'FastValve_duration1_unit_from_file': data.get('FastValve_duration1_unit_from_file', ''),
        'FastValve_duration2_source': data.get('FastValve_duration2_source', ''),
        'FastValve_duration2_unit_from_file': data.get('FastValve_duration2_unit_from_file', ''),
        'FastValve_duration3_source': data.get('FastValve_duration3_source', ''),
        'FastValve_duration3_unit_from_file': data.get('FastValve_duration3_unit_from_file', ''),
        'Plasma_duration_ms_Vloop_refined': data.get('plasma_duration_sec', np.nan) * 1000.0,
        'Representative_max_Ip_kA': data.get('I_p_max_rep_kA', data.get('I_p_max_kA', np.nan)),
        'Ip_duration_window_ms': data.get('plasma_duration_sec', np.nan) * 1000.0,
        'I_max_kA_raw': data.get('I_p_max_kA', np.nan),
        'Ip_start_ms_Vloop_refined': ip_start * 1000.0 if np.isfinite(ip_start) else np.nan,
        'Ip_end_ms_Vloop_refined': ip_end * 1000.0 if np.isfinite(ip_end) else np.nan,
        'Ip_start_method': data.get('Ip_start_method', ''),
        'Ip_end_method': data.get('plasma_end_method', ''),
        'Ip_start_vs_Bt_start_ms': (ip_start - bt_start) * 1000.0 if np.isfinite(ip_start) and np.isfinite(bt_start) else np.nan,
    }

    # Window-based values during the preferred plasma interval.
    if Time.size and np.isfinite(ip_start) and np.isfinite(ip_end) and ip_end > ip_start:
        plasma_mask = (Time >= ip_start) & (Time <= ip_end)
    else:
        plasma_mask = np.zeros_like(Time, dtype=bool)

    if Time.size and Bt.size == Time.size and np.any(plasma_mask):
        row['Bt_mean_during_plasma_mT'] = float(np.nanmean(Bt[plasma_mask]))
        row['Bt_start_of_plasma_mT'] = float(np.interp(ip_start, Time, Bt)) if np.isfinite(ip_start) else np.nan
        row['Bt_end_of_plasma_mT'] = float(np.interp(ip_end, Time, Bt)) if np.isfinite(ip_end) else np.nan
    else:
        row['Bt_mean_during_plasma_mT'] = np.nan
        row['Bt_start_of_plasma_mT'] = np.nan
        row['Bt_end_of_plasma_mT'] = np.nan

    if Time.size and Halpha.size == Time.size:
        if np.any(plasma_mask):
            row['max_H_alpha_au'] = float(np.nanmax(Halpha[plasma_mask]))
        else:
            row['max_H_alpha_au'] = float(np.nanmax(Halpha)) if Halpha.size else np.nan
    else:
        row['max_H_alpha_au'] = np.nan

    # H-alpha integrals and H-alpha start/end diagnostics.
    try:
        hm = compute_halpha_integral_metrics(data)
    except Exception:
        hm = None
    if hm is not None:
        row.update({
            'H_alpha_duration_my_Halpha_window_ms': hm.get('Halpha_real_duration_ms_5pct_to_end', np.nan),
            'H_alpha_duration_Ip_window_ms': hm.get('plasma_duration_ms_Ip', np.nan),
            'H_alpha_duration_MEPhIST_ms': data.get('Halpha_official_duration_ms', np.nan),
            'Halpha_integral_Ip_window': hm.get('Halpha_integral_plasma_time_positive', np.nan),
            'Ip_integral_Ip_window_C': hm.get('Ip_integral_plasma_time_positive_C', np.nan),
            'Halpha_integral_over_Ip_integral_Ip_window': hm.get('Halpha_plasma_time_over_Ip_time', np.nan),
            'Halpha_integral_Halpha_window': hm.get('Halpha_integral_real_time_positive', np.nan),
            'Halpha_integral_Halpha_window_over_Ip_integral_plasma': hm.get('Halpha_real_time_over_Ip_plasma_time', np.nan),
            'Halpha_start_5pct_ms': hm.get('Halpha_start_5pct_ms', np.nan),
            'Halpha_end_ms': hm.get('Halpha_end_ms', np.nan),
            'Halpha_start_minus_Ip_start_ms': hm.get('Halpha_start_delay_from_Ip_ms', np.nan),
        })
    else:
        row.update({
            'H_alpha_duration_my_Halpha_window_ms': np.nan,
            'H_alpha_duration_Ip_window_ms': row.get('Plasma_duration_ms_Vloop_refined', np.nan),
            'H_alpha_duration_MEPhIST_ms': data.get('Halpha_official_duration_ms', np.nan),
            'Halpha_integral_Ip_window': np.nan,
            'Ip_integral_Ip_window_C': np.nan,
            'Halpha_integral_over_Ip_integral_Ip_window': np.nan,
            'Halpha_integral_Halpha_window': np.nan,
            'Halpha_integral_Halpha_window_over_Ip_integral_plasma': np.nan,
            'Halpha_start_5pct_ms': np.nan,
            'Halpha_end_ms': np.nan,
            'Halpha_start_minus_Ip_start_ms': np.nan,
        })

    # Maxima are searched inside the preferred plasma window.  The compact-table
    # times are relative to the detected plasma start so shots with different
    # absolute acquisition triggers can be compared directly.  Absolute times
    # are retained in the All data tab for traceability.
    try:
        if Time.size and Ip.size == Time.size and Halpha.size == Time.size and np.any(plasma_mask):
            idxs = np.where(plasma_mask)[0]
            ip_seg = Ip[idxs]
            ha_seg = Halpha[idxs]
            t_seg = Time[idxs]
            ip_idx = int(np.nanargmax(ip_seg))
            ha_idx = int(np.nanargmax(ha_seg))
            row['Ip_max_time_absolute_ms'] = float(t_seg[ip_idx] * 1000.0)
            row['Halpha_max_time_absolute_ms'] = float(t_seg[ha_idx] * 1000.0)
            row['Ip_max_time_ms'] = float((t_seg[ip_idx] - ip_start) * 1000.0)
            row['Halpha_max_time_ms'] = float((t_seg[ha_idx] - ip_start) * 1000.0)
            row['dt_Halpha_max_minus_Ip_max_ms'] = float((t_seg[ha_idx] - t_seg[ip_idx]) * 1000.0)
            row['max_time_reference'] = 'relative to detected plasma start (Ip_start_time)'
        else:
            row['Ip_max_time_absolute_ms'] = np.nan
            row['Halpha_max_time_absolute_ms'] = np.nan
            row['Ip_max_time_ms'] = np.nan
            row['Halpha_max_time_ms'] = np.nan
            row['dt_Halpha_max_minus_Ip_max_ms'] = np.nan
            row['max_time_reference'] = 'relative to detected plasma start (Ip_start_time)'
    except Exception:
        row['Ip_max_time_absolute_ms'] = np.nan
        row['Halpha_max_time_absolute_ms'] = np.nan
        row['Ip_max_time_ms'] = np.nan
        row['Halpha_max_time_ms'] = np.nan
        row['dt_Halpha_max_minus_Ip_max_ms'] = np.nan
        row['max_time_reference'] = 'relative to detected plasma start (Ip_start_time)'

    return row


def process_shot_data(file_path, save_to_csv=False):
    """
    Compatibility loader for old and recent MEPhIST-0 .nxs shots.

    Main changes relative to the older loader:
      - Supports old Rogowski names and new names (rog_TF, rog_CS, rog_PF*, rog_internal).
      - Uses the recent simplified Ip reconstruction for shots >= 3355.
      - Reads H-alpha like the official viewer/notebook: visible_emission as abs(signal).
      - Reads spectroscopy from both Avantes and Oceanfx.
      - Loads CS, PF coils, loop voltages and metadata for the important-data table.
    """
    missing_signals = []
    used_signal_paths = {}

    try:
        with h5py.File(file_path, 'r') as f:

            stem = os.path.basename(file_path).split('.')[0]
            shot_match = re.search(r"\d+", stem)
            shot_number = shot_match.group(0) if shot_match else stem
            try:
                shot_id_int = int(shot_number)
            except Exception:
                shot_id_int = -1

            pressure_group = os.path.basename(os.path.dirname(file_path))
            Time = np.linspace(0, 21e-3, 21000)

            def _decode_scalar_value(value):
                try:
                    if isinstance(value, bytes):
                        return value.decode('utf-8').strip('\x00').strip()
                    if hasattr(value, 'shape') and value.shape == ():
                        value = value[()]
                        return _decode_scalar_value(value)
                    if isinstance(value, np.ndarray):
                        if value.size == 1:
                            return _decode_scalar_value(value.flat[0])
                        return value
                    return value
                except Exception:
                    return value

            def _get_h5_object(root, path):
                obj = root
                for part in str(path).strip('/').split('/'):
                    if not part:
                        continue
                    if hasattr(obj, 'keys') and part in obj:
                        obj = obj[part]
                    else:
                        return None
                return obj

            def _read_dataset_from_group(group, names):
                if group is None:
                    return np.array([]), ''
                for name in names:
                    if name in group:
                        try:
                            return np.asarray(group[name][:]), name
                        except Exception:
                            try:
                                return np.asarray(group[name][()]), name
                            except Exception:
                                pass
                return np.array([]), ''

            def _normalize_time_units(t_raw):
                t = np.asarray(t_raw, dtype=float)
                if t.size == 0:
                    return t
                finite = np.isfinite(t)
                if not np.any(finite):
                    return t
                t_abs_max = float(np.nanmax(np.abs(t[finite])))
                if t_abs_max > 100.0:
                    return t / 1e6     # likely microseconds
                if t_abs_max > 0.5:
                    return t / 1000.0  # likely milliseconds
                return t               # likely seconds

            def _read_raw_channel(label, group_candidates, processor='set_zero', time_shift_s=0.0):
                for group_path in group_candidates:
                    group = _get_h5_object(f, group_path)
                    if group is None:
                        continue
                    y_raw, y_key = _read_dataset_from_group(group, ('data', 'Data', 'signal', 'Signal', 'values', 'Values'))
                    t_raw, t_key = _read_dataset_from_group(group, ('time', 'Time', 't', 'T'))
                    if y_raw.size == 0 or t_raw.size == 0:
                        continue
                    t = _normalize_time_units(t_raw) + float(time_shift_s)
                    y = np.asarray(y_raw, dtype=float)
                    n = min(t.size, y.size)
                    if n < 2:
                        continue
                    t, y = t[:n], y[:n]
                    valid = np.isfinite(t) & np.isfinite(y)
                    if np.sum(valid) < 2:
                        continue
                    t, y = t[valid], y[valid]
                    order = np.argsort(t)
                    t, y = t[order], y[order]
                    if processor == 'set_zero':
                        y = set_zero(y)
                    elif processor == 'preprocess':
                        y = preprocess(set_zero(y))
                    elif processor == 'abs':
                        y = np.abs(y)
                    elif processor == 'abs_set_zero':
                        y = np.abs(set_zero(y))
                    elif processor == 'none':
                        pass
                    used_signal_paths[label] = f"{group_path}/{y_key}"
                    return t, y
                missing_signals.append(label)
                used_signal_paths[label] = ''
                return np.array([]), np.array([])

            def _interp_channel(label, group_candidates, processor='set_zero', time_shift_s=0.0, default=0.0):
                t, y = _read_raw_channel(label, group_candidates, processor=processor, time_shift_s=time_shift_s)
                if t.size < 2 or y.size < 2:
                    return np.full_like(Time, default, dtype=float)
                return np.interp(Time, t, y, left=default, right=default)

            def _read_scalar_path(path):
                obj = _get_h5_object(f, path)
                if obj is None:
                    return None
                try:
                    return _decode_scalar_value(obj[()])
                except Exception:
                    return None

            def _read_first_scalar(paths):
                for path in paths:
                    value = _read_scalar_path(path)
                    if value is not None:
                        return value, path
                return None, ''

            def _normalize_metadata_scalar(value):
                """Return a Python scalar/string suitable for summary tables.

                NX/HDF5 metadata can be stored as scalar strings, bytes, one-item
                arrays or small character arrays.  This helper keeps strings as
                readable text and converts one-item numeric arrays to floats.
                """
                value = _decode_scalar_value(value)
                if isinstance(value, np.ndarray):
                    if value.size == 0:
                        return ''
                    if value.size == 1:
                        return _normalize_metadata_scalar(value.flat[0])
                    if value.dtype.kind in {'S', 'U', 'O'}:
                        parts = []
                        for item in value.flat:
                            item = _decode_scalar_value(item)
                            if isinstance(item, bytes):
                                item = item.decode('utf-8', errors='ignore')
                            parts.append(str(item))
                        joined = ''.join(parts).replace('\x00', '').strip()
                        return joined if joined else ', '.join(parts)
                    return ', '.join(map(str, value.flat))
                if isinstance(value, bytes):
                    return value.decode('utf-8', errors='ignore').replace('\x00', '').strip()
                if isinstance(value, (np.integer, np.floating)):
                    try:
                        return float(value)
                    except Exception:
                        return value
                if isinstance(value, str):
                    return value.replace('\x00', '').strip()
                return value

            def _read_first_metadata_scalar(paths):
                value, path = _read_first_scalar(paths)
                if value is None:
                    return np.nan, ''
                return _normalize_metadata_scalar(value), path

            def _read_scalar_unit(path):
                obj = _get_h5_object(f, path) if path else None
                if obj is None:
                    return ''
                for key in ('units', 'unit', 'Units', 'UNIT'):
                    try:
                        if key in obj.attrs:
                            return str(_normalize_metadata_scalar(obj.attrs[key]))
                    except Exception:
                        pass
                return ''

            def _read_numeric_metadata_by_keywords(keywords, exclude_keywords=()):
                keywords = tuple(k.lower() for k in keywords)
                exclude_keywords = tuple(k.lower() for k in exclude_keywords)
                matches = []
                def visitor(name, obj):
                    if len(matches) >= 1:
                        return
                    lname = name.lower()
                    if all(k in lname for k in keywords) and not any(k in lname for k in exclude_keywords):
                        try:
                            val = _decode_scalar_value(obj[()])
                            if isinstance(val, (int, float, np.integer, np.floating)) and np.isfinite(val):
                                matches.append((float(val), name))
                        except Exception:
                            pass
                try:
                    f.visititems(visitor)
                except Exception:
                    pass
                return matches[0] if matches else (np.nan, '')

            def _parse_pressure_from_folder(label):
                if not label:
                    return np.nan
                m = re.search(r"([-+]?\d+(?:[\.,]\d+)?)\s*m?pa", str(label), flags=re.IGNORECASE)
                if m:
                    return float(m.group(1).replace(',', '.'))
                m = re.search(r"([-+]?\d+(?:[\.,]\d+)?)", str(label))
                if m:
                    return float(m.group(1).replace(',', '.'))
                return np.nan

            # Metadata: gas and pressures. Measured pressure is usually in Pa in
            # total_pressure, hence Pa -> mPa is multiplication by 1e5.
            gas, gas_path = _read_first_scalar((
                'Vacuum/Pressure_fastValve/working_gas',
                'Vacuum/Pressure/working_gas',
                'META/Main/working_gas',
            ))
            gas = '' if gas is None else str(gas)

            main_description, main_description_path = _read_first_scalar((
                'META/Main/Description',
                'META/Main/comment',
                'META/Main/Comment',
                'META/Main/Experiment',
            ))
            main_description = '' if main_description is None else str(main_description)
            parsed_setpoints = parse_shot_setpoints_from_text(main_description)

            # Vacuum gas-injection metadata.  Recent MEPhIST-0 files can store
            # several MFC entries and several fast-valve pulses.  These values are
            # exported in the shot-summary table so repeated gas injections can be
            # correlated with plasma behavior.  The *_file_units suffix is used
            # because the raw NX tree does not always expose a reliable physical
            # unit for these control parameters.
            mfc_metadata = {}
            for _mfc_idx in (1, 2, 3):
                _gas_type, _gas_type_path = _read_first_metadata_scalar((
                    f'Vacuum/MFC/VAC:MFC{_mfc_idx}_gasType',
                    f'Vacuum/MFC/MFC{_mfc_idx}_gasType',
                    f'Vacuum/MFC/MFC{_mfc_idx}_gas_type',
                    f'Vacuum/MFC/MFC{_mfc_idx}/gasType',
                    f'Vacuum/MFC/MFC{_mfc_idx}/gas_type',
                ))
                _mfc_in, _mfc_in_path = _read_first_metadata_scalar((
                    f'Vacuum/MFC/VAC:MFC{_mfc_idx}_in',
                    f'Vacuum/MFC/MFC{_mfc_idx}_in',
                    f'Vacuum/MFC/MFC{_mfc_idx}/in',
                    f'Vacuum/MFC/MFC{_mfc_idx}/input',
                    f'Vacuum/MFC/MFC{_mfc_idx}/setpoint',
                ))
                mfc_metadata[_mfc_idx] = {
                    'gasType': _gas_type,
                    'gasType_source': _gas_type_path,
                    'in': _mfc_in,
                    'in_source': _mfc_in_path,
                    'in_unit': _read_scalar_unit(_mfc_in_path),
                }

            fastvalve_metadata = {}
            for _key in ('delay1', 'delay2', 'duration1', 'duration2', 'duration3'):
                _value, _path = _read_first_metadata_scalar((
                    f'Vacuum/Pressure_fastValve/{_key}',
                    f'Vacuum/Pressure_fastValve/VAC:{_key}',
                    f'Vacuum/Pressure_fastValve/fastValve_{_key}',
                    f'Vacuum/Pressure_fastValve/fast_valve_{_key}',
                ))
                fastvalve_metadata[_key] = {
                    'value': _value,
                    'source': _path,
                    'unit': _read_scalar_unit(_path),
                }

            p_meas_raw, p_meas_path = _read_first_scalar((
                'Vacuum/Pressure/total_pressure',
                'Vacuum/Pressure_fastValve/total_pressure',
                'Vacuum/Pressure/pressure',
                'Vacuum/Pressure_fastValve/pressure',
            ))
            try:
                pressure_measured_mPa = float(p_meas_raw) * 1e5
            except Exception:
                pressure_measured_mPa = np.nan

            p_req_raw, p_req_path = _read_first_scalar((
                'Vacuum/Pressure/requested_pressure',
                'Vacuum/Pressure/pressure_requested',
                'Vacuum/Pressure/set_pressure',
                'Vacuum/Pressure/target_pressure',
                'Vacuum/Pressure_fastValve/requested_pressure',
                'Vacuum/Pressure_fastValve/pressure_requested',
                'Vacuum/Pressure_fastValve/set_pressure',
                'Vacuum/Pressure_fastValve/target_pressure',
            ))
            try:
                pressure_requested_mPa = float(p_req_raw) * 1e5
            except Exception:
                pressure_requested_mPa = parsed_setpoints.get('pressure_requested_mPa', np.nan)
                if not np.isfinite(pressure_requested_mPa):
                    pressure_requested_mPa = _parse_pressure_from_folder(pressure_group)

            cs_voltage, cs_voltage_path = _read_numeric_metadata_by_keywords(('cs',), ('rog', 'current', 'time', 'data'))
            tf_voltage, tf_voltage_path = _read_numeric_metadata_by_keywords(('tf',), ('rog', 'current', 'time', 'data'))

            default_setpoints = infer_default_setpoints(shot_id_int)
            if not np.isfinite(cs_voltage):
                cs_voltage = parsed_setpoints.get('CS_voltage_V', np.nan)
                cs_voltage_path = 'META/Main/Description' if np.isfinite(cs_voltage) else cs_voltage_path
            if not np.isfinite(tf_voltage):
                tf_voltage = parsed_setpoints.get('TF_voltage_V', np.nan)
                tf_voltage_path = 'META/Main/Description' if np.isfinite(tf_voltage) else tf_voltage_path
            if not np.isfinite(cs_voltage):
                cs_voltage = default_setpoints.get('CS_voltage_V', np.nan)
                cs_voltage_path = 'recent-shot notebook fallback' if np.isfinite(cs_voltage) else cs_voltage_path
            if not np.isfinite(tf_voltage):
                tf_voltage = default_setpoints.get('TF_voltage_V', np.nan)
                tf_voltage_path = 'recent-shot notebook fallback' if np.isfinite(tf_voltage) else tf_voltage_path

            # Raw Rogowski diagnostics.
            U_rog_TF = _interp_channel('rog_TF_or_old_TF', (
                'rogowski_coils/rog_TF', 'rogowski_coils/rog_tf', 'rogowski_coils/TF',
                'rogowski_coils/rog_tor_coils', 'rogowski_coils/rog_tor_coil', 'rogowski_coils/rog_tor'
            ), processor='set_zero')

            U_rog_CS = _interp_channel('rog_CS_or_old_inductor', (
                'rogowski_coils/rog_CS', 'rogowski_coils/rog_cs', 'rogowski_coils/CS',
                'rogowski_coils/rog_inductor', 'rogowski_coils/inductor'
            ), processor='set_zero')

            U_rog_int = _interp_channel('rog_internal', (
                'rogowski_coils/rog_internal', 'rogowski_coils/rog_int',
                'rogowski_coils/internal', 'rogowski_coils/Ip', 'rogowski_coils/ip'
            ), processor='none', time_shift_s=(-8.6e-5 if shot_id_int < 3355 else 0.0))

            U_pf = {}
            for i in range(1, 7):
                U_pf[i] = _interp_channel(f'rog_PF{i}', (
                    f'rogowski_coils/rog_PF{i}', f'rogowski_coils/rog_pf{i}', f'rogowski_coils/PF{i}',
                    f'rogowski_coils/pf{i}', f'rogowski_coils/rog_pol_coils{i}', f'rogowski_coils/rog_pol_coil{i}'
                ), processor=('preprocess' if i == 2 else 'set_zero'))

            # Toroidal field. For new names use the current MephistDataKit/OceanFX
            # convention; for old tor_coils keep the legacy conversion.
            tf_source = used_signal_paths.get('rog_TF_or_old_TF', '')
            if any(s in tf_source for s in ('rog_TF', 'rog_tf', '/TF')):
                B_phi = K_TF * integrate(Time, U_rog_TF / 4.89) * 3.92e6
                if np.nanmax(B_phi) < abs(np.nanmin(B_phi)):
                    B_phi = -B_phi
                TF_current_kA = integrate(Time, U_rog_TF / 4.89) * 3.92e6 / 1000.0
            else:
                I_TF = abs(integrate(Time, U_rog_TF)) * K_ROG_TOR
                B_phi = I_TF * K_TF
                TF_current_kA = I_TF / 1000.0

            # CS/PF currents for the official-like diagnostics panel.
            if any(s in used_signal_paths.get('rog_CS_or_old_inductor', '') for s in ('rog_CS', 'rog_cs', '/CS')):
                CS_current_kA = K_ROG_IND * integrate(Time, U_rog_CS / 10.48) / 1000.0
            else:
                CS_current_kA = K_ROG_IND * integrate(Time, U_rog_CS) / 1000.0
            # Keep the official-style current orientation positive for the main CS ramp.
            if CS_current_kA.size and np.nanmax(CS_current_kA) < abs(np.nanmin(CS_current_kA)):
                CS_current_kA = -CS_current_kA

            pf_amp = {1: 19.05, 2: 19.05, 3: 42.86, 4: 42.86, 5: 32.14, 6: 32.14}
            PF_current_kA = {}
            for i in range(1, 7):
                PF_current_kA[i] = K_ROG_PF1 * integrate(Time, U_pf[i] / pf_amp[i]) / 1000.0

            # Plasma current. For shots after the Feb-2026 hardware change, use
            # the simple continuous-winding internal Rogowski reconstruction.
            if shot_id_int >= 3355:
                loader_mode = 'new_ge3355_internal_rogowski'
                Ip_raw = integrate(Time, -set_zero(U_rog_int)) * 2.8e3 * 1000.0  # kA -> A
                Ip, ip_baseline, ip_baseline_method = correct_ip_baseline_two_pass(Time, Ip_raw)
            else:
                loader_mode = 'legacy_synthetic_subtraction'
                synt_sig = -RC_transform(Time, U_rog_TF, 1, 1.8e-4) * 0.665
                synt_sig -= 0.515 * (
                    RC_transform(Time, U_rog_CS, 1, 8.6e-5) * 3
                    - RC_transform(Time, U_rog_CS, 1, 4.4e-4) * 1.67
                )
                synt_sig += 0.5 * 1.1 * (
                    RC_transform(Time, U_pf[1], 1, 5.5e-4) * 3.8
                    + RC_transform(Time, U_pf[1], 1, 5e-5) * 0.65
                )
                synt_sig += (
                    RC_transform(Time, U_pf[2], 1, 4.5e-4) * 3.2
                    + RC_transform(Time, U_pf[2], 1, 15e-4) * 0.45
                )
                synt_sig += 1.05 * (
                    RC_transform(Time, U_pf[3], 1, 60e-4) * 0.4
                    + RC_transform(Time, U_pf[3], 1, 6e-4) * 2.4
                )
                U_rog_int_filt = U_rog_int - synt_sig
                Ip_raw = integrate(Time, U_rog_int_filt) * 1.48e7 * 0.87
                Ip, ip_baseline, ip_baseline_method = correct_ip_baseline_two_pass(Time, Ip_raw)

            # Visible emission / H-alpha.
            # Important: do NOT use abs(raw) directly. Recent/old files can have
            # different polarity and a non-zero DC offset; abs(raw) turns that
            # offset into a false flat high H-alpha level. We first subtract the
            # pre-plasma baseline, then choose polarity, then clip to positive.
            t_vis, y_vis_raw = _read_raw_channel('visible_emission', (
                'spectroscopy/visible_emission', 'spectroscopy/H_alpha',
                'spectroscopy/halpha', 'spectroscopy/Halpha', 'spectroscopy/photod', 'spectroscopy/Photod'
            ), processor='none')
            if t_vis.size >= 2 and y_vis_raw.size >= 2:
                Photod, Photod_signed_setzero, halpha_baseline_raw, halpha_polarity_method = prepare_visible_emission_for_display(
                    Time, t_vis, y_vis_raw
                )
            else:
                Photod = np.zeros_like(Time)
                Photod_signed_setzero = np.zeros_like(Time)
                halpha_baseline_raw = np.nan
                halpha_polarity_method = 'missing'
            if HALPHA_DISPLAY_SMOOTH_US > 0:
                Photod = smooth_signal_time(Time, Photod, window_us=HALPHA_DISPLAY_SMOOTH_US)

            # Loop voltages. The official panel often shows (VL2 + VL7)/2.
            def _load_voltage_loop(num):
                return _interp_channel(f'VL{num}', (f'voltage_loops/VL{num}',), processor='set_zero')

            VL2 = _load_voltage_loop(2)
            VL3 = _load_voltage_loop(3)
            VL7 = _load_voltage_loop(7)
            Vloop_2_7 = 0.5 * (VL2 + VL7)
            Vloop_2_3_7 = 0.5 * (VL7 + 0.5 * (VL2 + VL3))

            # Main event times.
            t0_bt = find_bt_reference_time(Time, B_phi, BT_START_THRESHOLD_RATIO)
            ip_start_info = get_ip_start_backward_from_peak_info(Time, Ip)
            t0_ip_from_ip = ip_start_info['start_time']
            ip_start_method_ip_only = ip_start_info.get('method', '')

            ip_end_info = get_plasma_end_time(Time, Ip, t0_ip_from_ip, return_details=True)
            t_end_ip_only = ip_end_info['end_time']
            plasma_end_method_ip_only = ip_end_info['method']

            t_end_halpha_initial, halpha_end_method_initial = get_plasma_end_time_from_halpha(Time, Photod, Ip, start_time=t0_ip_from_ip)
            ip_crossings = find_ip_start_times(Time, Ip, IP_START_THRESHOLD_RATIO, IP_MIN_DURATION_US)

            ha_off_dur_ms, ha_off_start_ms, ha_off_end_ms, ha_off_peak = compute_halpha_duration_official_style(Time, Photod)

            # Preferred plasma window: start is always the original Ip detector.
            # Vloop is used only at the end, where the last valid local peak and
            # the completion of its falling edge are recorded.
            t_end_preferred_before_loop, plasma_end_method_before_loop, plasma_end_halpha_guard_used = choose_preferred_plasma_end_time(
                Time,
                t0_ip_from_ip,
                t_end_ip_only,
                plasma_end_method_ip_only,
                halpha_official_end_ms=ha_off_end_ms,
                halpha_official_duration_ms=ha_off_dur_ms,
                halpha_detector_end=t_end_halpha_initial,
            )

            if LOOP_VOLTAGE_EDGE_REFINEMENT_ENABLED:
                loop_edge_info = refine_plasma_window_with_loop_voltage(
                    Time,
                    Vloop_2_7,
                    t0_ip_from_ip,
                    t_end_preferred_before_loop
                )
                t0_ip = loop_edge_info.get('start_time', t0_ip_from_ip)
                t_end_ip = loop_edge_info.get('end_time', t_end_preferred_before_loop)
            else:
                loop_edge_info = {
                    'start_time': t0_ip_from_ip,
                    'end_time': t_end_preferred_before_loop,
                    'start_used': False,
                    'end_used': False,
                    'start_method': 'loop_voltage_refinement_disabled',
                    'end_method': 'loop_voltage_refinement_disabled',
                }
                t0_ip = t0_ip_from_ip
                t_end_ip = t_end_preferred_before_loop

            ip_start_method = ip_start_method_ip_only
            plasma_end_method = plasma_end_method_before_loop
            if loop_edge_info.get('end_used', False):
                plasma_end_method = f"{plasma_end_method_before_loop}+{loop_edge_info.get('end_method', 'loop_voltage')}"

            # Recompute the H-alpha detector using the final start time. This does
            # not define the plasma end, but it keeps H-alpha integrals consistent.
            t_end_halpha, halpha_end_method = get_plasma_end_time_from_halpha(Time, Photod, Ip, start_time=t0_ip)

            Time_sync_bt, Time_sync_ip = Time - t0_bt, Time - t0_ip
            tau_plasma, plasma_duration_tau = get_tau(Time, t0_ip, t_end_ip)
            plasma_duration_sec = max(t_end_ip - t0_ip, 0.0)
            plasma_duration_ip_only_sec = max(t_end_ip_only - t0_ip, 0.0) if np.isfinite(t_end_ip_only) else np.nan
            halpha_duration_sec = max(t_end_halpha - t0_ip, 0.0)
            ip_delay_ms = (t0_ip - t0_bt) * 1000.0

            I_p_max_kA = np.nanmax(Ip) / 1000.0 if Ip.size else np.nan
            I_p_max_rep_kA = representative_max(Time, Ip, smooth_us=IP_REPRESENTATIVE_SMOOTH_US) / 1000.0
            B_phi_max = np.nanmax(B_phi) if B_phi.size else np.nan

            # Spectrum: support both spectrometers when present.
            # Internally, old variable names are kept for backward compatibility,
            # but spectra_by_source stores each source separately so the GUI can
            # switch between OceanFX and Avantes.
            spectra_by_source = {}
            wavelengths_Avantes = np.array([])
            intensities_Avantes_raw = np.array([])
            intensities_Avantes_rw = np.array([])
            intensities_Avantes = np.array([])
            Avantes_intensity_source = ''

            def _store_spectrum_source(source_key, source_label, av_group):
                try:
                    if av_group is None:
                        return
                    wl_raw = av_group['Wavelength'][:] if 'Wavelength' in av_group else np.array([])
                    i_clean, clean_key = read_first_existing_dataset(
                        av_group,
                        ('CleanI', 'cleanI', 'clean_i', 'I', 'intensity', 'Intensity', 'Intensities')
                    )
                    i_rw, rw_key = read_first_existing_dataset(av_group, AVANTES_RW_DATASET_CANDIDATES)
                    if i_rw.size == 0:
                        i_rw = i_clean
                        rw_key = clean_key
                    if wl_raw.size > 0 and i_clean.size > 0 and wl_raw.shape == i_clean.shape:
                        raw = np.asarray(i_clean, dtype=float)
                        rw = np.asarray(i_rw, dtype=float) if i_rw.size == wl_raw.size else raw.copy()
                        max_int = np.nanmax(raw) if raw.size else np.nan
                        norm_max = raw / max_int if np.isfinite(max_int) and max_int > 0 else np.zeros_like(raw)
                        spectra_by_source[source_key] = {
                            'source_key': source_key,
                            'source_label': source_label,
                            'wavelengths': np.asarray(wl_raw, dtype=float),
                            'intensity_raw': raw,
                            'intensity_rw': rw,
                            'intensity_norm_max': norm_max,
                            'intensity_source': f'{source_label}/{rw_key or clean_key}',
                            'raw_dataset': clean_key,
                            'rw_dataset': rw_key or clean_key,
                        }
                except Exception:
                    pass

            if 'spectroscopy' in f:
                try:
                    spec_group = f['spectroscopy']
                    if 'Oceanfx' in spec_group:
                        _store_spectrum_source('Oceanfx', 'Oceanfx', spec_group['Oceanfx'])
                    if 'OceanFX' in spec_group and 'Oceanfx' not in spectra_by_source:
                        _store_spectrum_source('Oceanfx', 'OceanFX', spec_group['OceanFX'])
                    if 'Avantes' in spec_group:
                        _store_spectrum_source('Avantes', 'Avantes', spec_group['Avantes'])
                except Exception:
                    pass

            default_spectrum_source = 'Oceanfx' if 'Oceanfx' in spectra_by_source else ('Avantes' if 'Avantes' in spectra_by_source else '')
            if default_spectrum_source:
                chosen_spec = spectra_by_source[default_spectrum_source]
                wavelengths_Avantes = chosen_spec['wavelengths']
                intensities_Avantes_raw = chosen_spec['intensity_raw']
                intensities_Avantes_rw = chosen_spec['intensity_rw']
                intensities_Avantes = chosen_spec['intensity_norm_max']
                Avantes_intensity_source = chosen_spec['intensity_source']

            main_data_df = pd.DataFrame({
                'time_ms': Time * 1000,
                'time_sync_bt_ms': Time_sync_bt * 1000,
                'time_sync_ip_ms': Time_sync_ip * 1000,
                'tau_plasma': tau_plasma,
                'Bt_mT': B_phi,
                'Ip_kA': Ip / 1000,
                'H_alpha': Photod,
                'CS_current_kA': CS_current_kA,
                'TF_current_kA': TF_current_kA,
                'PF1_current_kA': PF_current_kA[1],
                'PF2_current_kA': PF_current_kA[2],
                'PF3_current_kA': PF_current_kA[3],
                'PF4_current_kA': PF_current_kA[4],
                'PF5_current_kA': PF_current_kA[5],
                'PF6_current_kA': PF_current_kA[6],
                'VL2_V': VL2,
                'VL3_V': VL3,
                'VL7_V': VL7,
                'Vloop_2_7_V': Vloop_2_7,
                'Vloop_2_3_7_V': Vloop_2_3_7,
            })

            spec_rows = []
            for _src_key, _src in spectra_by_source.items():
                _wl = np.asarray(_src.get('wavelengths', []), dtype=float)
                _raw = np.asarray(_src.get('intensity_raw', []), dtype=float)
                _rw = np.asarray(_src.get('intensity_rw', []), dtype=float)
                _norm = np.asarray(_src.get('intensity_norm_max', []), dtype=float)
                if _wl.size and _raw.size and _wl.shape == _raw.shape:
                    spec_rows.append(pd.DataFrame({
                        'spectrum_source_key': _src_key,
                        'wavelength_nm': _wl,
                        'intensity_raw': _raw,
                        'intensity_rw': _rw if _rw.shape == _wl.shape else _raw,
                        'intensity_norm_max': _norm if _norm.shape == _wl.shape else np.nan,
                        'intensity_source': _src.get('intensity_source', _src_key),
                    }))
            spec_data_df = pd.concat(spec_rows, ignore_index=True) if spec_rows else pd.DataFrame()

            if missing_signals:
                print(f"[WARN] Shot {shot_number}: missing optional signals {missing_signals}. Replaced with zeros where needed.")

            data = {
                'file_path': file_path,
                'pressure_group': pressure_group,
                'Time': Time,
                'Time_sync_bt': Time_sync_bt,
                'Time_sync_ip': Time_sync_ip,
                'tau_plasma': tau_plasma,
                'plasma_tau_duration': plasma_duration_tau,
                'B_phi': B_phi,
                'Ip': Ip,
                'Ip_raw_before_baseline': Ip_raw,
                'Photod': Photod,
                'wavelengths_Avantes': wavelengths_Avantes,
                'intensities_Avantes': intensities_Avantes,
                'intensities_Avantes_raw': intensities_Avantes_raw,
                'intensities_Avantes_rw': intensities_Avantes_rw,
                'Avantes_intensity_source': Avantes_intensity_source,
                'spectra_by_source': spectra_by_source,
                'available_spectrum_sources': ', '.join(spectra_by_source.keys()),
                'default_spectrum_source': default_spectrum_source,
                'shot_number': shot_number,
                'gas': gas,
                'main_description': main_description,
                'pressure_measured_mPa': pressure_measured_mPa,
                'pressure_measured_source': p_meas_path,
                'pressure_requested_mPa': pressure_requested_mPa,
                'pressure_requested_source': p_req_path if p_req_path else 'folder_label',
                'CS_voltage_V': cs_voltage,
                'CS_voltage_source': cs_voltage_path,
                'TF_voltage_V': tf_voltage,
                'TF_voltage_source': tf_voltage_path,
                'I_p_max_kA': I_p_max_kA,
                'I_p_max_rep_kA': I_p_max_rep_kA,
                'B_phi_max_mT': B_phi_max,
                'plasma_duration_sec': plasma_duration_sec,
                'halpha_duration_sec': halpha_duration_sec,
                'Halpha_official_duration_ms': ha_off_dur_ms,
                'Halpha_official_start_ms': ha_off_start_ms,
                'Halpha_official_end_ms': ha_off_end_ms,
                'Halpha_official_peak': ha_off_peak,
                'plasma_duration_ip_only_sec': plasma_duration_ip_only_sec,
                'Ip_end_time_ip_only': t_end_ip_only,
                'plasma_end_method_ip_only': plasma_end_method_ip_only,
                'plasma_end_halpha_guard_used': plasma_end_halpha_guard_used,
                'Photod_signed_setzero': Photod_signed_setzero,
                'Halpha_baseline_raw': halpha_baseline_raw,
                'Halpha_polarity_method': halpha_polarity_method,
                'Bt_sync_time': t0_bt,
                'Ip_start_time': t0_ip,
                'Ip_start_method': ip_start_method,
                'Ip_start_time_Ip_only': t0_ip_from_ip,
                'Ip_start_method_Ip_only': ip_start_method_ip_only,
                'Ip_start_loop_refined': bool(loop_edge_info.get('start_used', False)),
                'Ip_start_loop_edge_time': loop_edge_info.get('start_time', np.nan),
                'Ip_start_loop_edge_method': loop_edge_info.get('start_method', ''),
                'Ip_start_loop_edge_score_V_per_ms': loop_edge_info.get('start_score_V_per_ms', np.nan),
                'Ip_start_loop_edge_noise_sigma_V_per_ms': loop_edge_info.get('start_noise_sigma_V_per_ms', np.nan),
                'Ip_start_threshold_time': ip_start_info.get('threshold_start_time', np.nan),
                'Ip_start_peak_time': ip_start_info.get('ip_peak_time', np.nan),
                'Ip_start_threshold_A': ip_start_info.get('ip_start_threshold_A', np.nan),
                'Ip_start_ip_max_ref_A': ip_start_info.get('ip_start_ip_max_ref_A', np.nan),
                'Ip_start_idx': ip_start_info.get('ip_start_idx', np.nan),
                'Ip_start_5pct_method': ip_start_info.get('ip_start_5pct_method', ''),
                'Ip_start_5pct_time': ip_start_info.get('ip_start_5pct_time', np.nan),
                'Ip_start_behavior_score': ip_start_info.get('ip_start_behavior_score', np.nan),
                'Ip_start_behavior_pre_slope_kA_per_ms': ip_start_info.get('ip_start_behavior_pre_slope_kA_per_ms', np.nan),
                'Ip_start_behavior_post_slope_kA_per_ms': ip_start_info.get('ip_start_behavior_post_slope_kA_per_ms', np.nan),
                'Ip_start_behavior_post_rise_A': ip_start_info.get('ip_start_behavior_post_rise_A', np.nan),
                'Ip_start_behavior_pre_variation_A': ip_start_info.get('ip_start_behavior_pre_variation_A', np.nan),
                'Ip_start_behavior_slope_threshold_kA_per_ms': ip_start_info.get('ip_start_behavior_slope_threshold_kA_per_ms', np.nan),
                'Ip_start_behavior_quiet_slope_limit_kA_per_ms': ip_start_info.get('ip_start_behavior_quiet_slope_limit_kA_per_ms', np.nan),
                'Ip_end_time': t_end_ip,
                'Ip_end_time_before_loop_refinement': t_end_preferred_before_loop,
                'Ip_end_loop_refined': bool(loop_edge_info.get('end_used', False)),
                'Ip_end_loop_edge_time': loop_edge_info.get('end_time', np.nan),
                'Ip_end_loop_edge_method': loop_edge_info.get('end_method', ''),
                'Ip_end_loop_edge_score_V_per_ms': loop_edge_info.get('end_score_V_per_ms', np.nan),
                'Ip_end_loop_edge_noise_sigma_V_per_ms': loop_edge_info.get('end_noise_sigma_V_per_ms', np.nan),
                'Ip_end_loop_peak_time': loop_edge_info.get('end_peak_time', np.nan),
                'Ip_end_loop_fall_time': loop_edge_info.get('end_fall_time', np.nan),
                'Ip_end_loop_time_definition': loop_edge_info.get('end_time_definition', ''),
                'Ip_end_loop_selected_peak_order': loop_edge_info.get('end_selected_peak_order', ''),
                'Ip_end_loop_feature_prominence_V': loop_edge_info.get('end_feature_prominence_V', np.nan),
                'loop_voltage_edge_refinement_enabled': bool(LOOP_VOLTAGE_EDGE_REFINEMENT_ENABLED),
                'loop_voltage_edge_refinement_start_used': bool(loop_edge_info.get('start_used', False)),
                'loop_voltage_edge_refinement_end_used': bool(loop_edge_info.get('end_used', False)),
                'Halpha_end_time': t_end_halpha,
                'Ip_threshold_end_time': ip_end_info.get('threshold_end_time', np.nan),
                'Ip_plateau_end_time': ip_end_info.get('plateau_end_time', np.nan),
                'Ip_peak_time': ip_end_info.get('peak_time', np.nan),
                'Ip_end_ip_max_ref_A': ip_end_info.get('ip_max_ref_A', np.nan),
                'Ip_plateau_method': ip_end_info.get('plateau_method', ''),
                'Ip_step_plateau_end_time': ip_end_info.get('step_plateau_end_time', np.nan),
                'Ip_step_plateau_method': ip_end_info.get('step_plateau_method', ''),
                'Halpha_end_method': halpha_end_method,
                'plasma_end_method': plasma_end_method,
                'Ip_delay_ms': ip_delay_ms,
                'Ip_crossings': ip_crossings,
                'Ip_min_duration_us': IP_MIN_DURATION_US,
                'Ip_baseline_A': ip_baseline,
                'Ip_baseline_method': ip_baseline_method,
                'CS_current_kA': CS_current_kA,
                'TF_current_kA': TF_current_kA,
                'PF1_current_kA': PF_current_kA[1],
                'PF2_current_kA': PF_current_kA[2],
                'PF3_current_kA': PF_current_kA[3],
                'PF4_current_kA': PF_current_kA[4],
                'PF5_current_kA': PF_current_kA[5],
                'PF6_current_kA': PF_current_kA[6],
                'VL2_V': VL2,
                'VL3_V': VL3,
                'VL7_V': VL7,
                'Vloop_2_7_V': Vloop_2_7,
                'Vloop_2_3_7_V': Vloop_2_3_7,
                'MFC1_gasType': mfc_metadata.get(1, {}).get('gasType', np.nan),
                'MFC1_gasType_source': mfc_metadata.get(1, {}).get('gasType_source', ''),
                'MFC1_in_file_units': mfc_metadata.get(1, {}).get('in', np.nan),
                'MFC1_in_source': mfc_metadata.get(1, {}).get('in_source', ''),
                'MFC1_in_unit_from_file': mfc_metadata.get(1, {}).get('in_unit', ''),
                'MFC2_gasType': mfc_metadata.get(2, {}).get('gasType', np.nan),
                'MFC2_gasType_source': mfc_metadata.get(2, {}).get('gasType_source', ''),
                'MFC2_in_file_units': mfc_metadata.get(2, {}).get('in', np.nan),
                'MFC2_in_source': mfc_metadata.get(2, {}).get('in_source', ''),
                'MFC2_in_unit_from_file': mfc_metadata.get(2, {}).get('in_unit', ''),
                'MFC3_gasType': mfc_metadata.get(3, {}).get('gasType', np.nan),
                'MFC3_gasType_source': mfc_metadata.get(3, {}).get('gasType_source', ''),
                'MFC3_in_file_units': mfc_metadata.get(3, {}).get('in', np.nan),
                'MFC3_in_source': mfc_metadata.get(3, {}).get('in_source', ''),
                'MFC3_in_unit_from_file': mfc_metadata.get(3, {}).get('in_unit', ''),
                'FastValve_delay1_file_units': fastvalve_metadata.get('delay1', {}).get('value', np.nan),
                'FastValve_delay1_source': fastvalve_metadata.get('delay1', {}).get('source', ''),
                'FastValve_delay1_unit_from_file': fastvalve_metadata.get('delay1', {}).get('unit', ''),
                'FastValve_delay2_file_units': fastvalve_metadata.get('delay2', {}).get('value', np.nan),
                'FastValve_delay2_source': fastvalve_metadata.get('delay2', {}).get('source', ''),
                'FastValve_delay2_unit_from_file': fastvalve_metadata.get('delay2', {}).get('unit', ''),
                'FastValve_duration1_file_units': fastvalve_metadata.get('duration1', {}).get('value', np.nan),
                'FastValve_duration1_source': fastvalve_metadata.get('duration1', {}).get('source', ''),
                'FastValve_duration1_unit_from_file': fastvalve_metadata.get('duration1', {}).get('unit', ''),
                'FastValve_duration2_file_units': fastvalve_metadata.get('duration2', {}).get('value', np.nan),
                'FastValve_duration2_source': fastvalve_metadata.get('duration2', {}).get('source', ''),
                'FastValve_duration2_unit_from_file': fastvalve_metadata.get('duration2', {}).get('unit', ''),
                'FastValve_duration3_file_units': fastvalve_metadata.get('duration3', {}).get('value', np.nan),
                'FastValve_duration3_source': fastvalve_metadata.get('duration3', {}).get('source', ''),
                'FastValve_duration3_unit_from_file': fastvalve_metadata.get('duration3', {}).get('unit', ''),
                'loader_mode': loader_mode,
                'missing_signals': missing_signals,
                'used_signal_paths': used_signal_paths,
                'main_data_df': main_data_df,
                'spec_data_df': spec_data_df,
            }

            if save_to_csv:
                local_folder = f"shot_{shot_number}"
                os.makedirs(local_folder, exist_ok=True)
                main_data_df.to_csv(f"{local_folder}/main_data.csv", index=False)
                if not spec_data_df.empty:
                    spec_data_df.to_csv(f"{local_folder}/spectroscopy.csv", index=False)
                metadata = {k: v for k, v in data.items() if isinstance(v, (str, int, float, np.integer, np.floating)) or v is None}
                metadata['missing_signals'] = missing_signals
                metadata['used_signal_paths'] = used_signal_paths
                with open(f"{local_folder}/metadata.json", "w", encoding="utf-8") as fjson:
                    json.dump(metadata, fjson, default=str, indent=2)

            return data

    except Exception as e:
        messagebox.showerror("Data Load Error", f"Could not load or process file {file_path}:\n{e}")
        traceback.print_exc()
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




def nist_strength_from_row(row):
    """Return (text, numeric, source_column) for a NIST line strength.

    Many NIST exports use the `intens` column, but some files, especially the
    Li table, have empty `intens` and useful transition probabilities in
    `gA(s^-1)`.  This helper gives the quick/Voigt prefilters a numerical
    strength instead of treating such files as all-zero/unknown.
    """
    if row is None:
        return '', np.nan, ''
    for c in ['intens', 'Intensity', 'Rel.', 'rel_intensity', 'Aki', 'gA(s^-1)', 'gA', 'Einstein_A', 'A(s^-1)']:
        try:
            if c in getattr(row, 'index', []):
                raw = clean_nist_cell(row.get(c, ''))
                val = nist_cell_to_float(raw)
                if np.isfinite(val):
                    return str(raw), float(val), c
        except Exception:
            pass
    return '', np.nan, ''


def sp_num_to_roman_ion(value):
    """Convert NIST ASD sp_num to spectroscopic ion notation.

    ASD commonly uses sp_num=1 for neutral atoms (I), 2 for singly ionized
    (II), 3 for doubly ionized (III), etc.  The Li file supplied by the user
    uses `sp_num`, so without this mapping all Li rows appear as `unknown`.
    """
    try:
        s = clean_nist_cell(value)
        n = int(float(str(s).strip()))
    except Exception:
        return ''
    romans = {
        1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
        7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
    }
    return romans.get(n, '')

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

    # Prefer observed wavelength row-by-row, but fall back to Ritz for rows
    # where the observed wavelength is absent.  This matters for files such as
    # Li_290_1110_nm.csv: some Li transitions have observed wavelengths, while
    # many useful lines are Ritz-only.  The older logic chose the observed column
    # globally and accidentally dropped all Ritz-only rows.
    lambda_values = pd.Series(np.nan, index=df.index, dtype=float)
    lambda_source_values = pd.Series('unknown', index=df.index, dtype=object)

    for key, source in wavelength_preferences:
        if key in lower_cols:
            candidate = df[lower_cols[key]].map(nist_cell_to_float)
            fill = lambda_values.isna() & candidate.notna()
            if fill.any():
                lambda_values.loc[fill] = candidate.loc[fill].astype(float)
                lambda_source_values.loc[fill] = source

    # Last fallback: find any nm wavelength-like column not already used.
    if lambda_values.isna().all():
        for col in df.columns:
            col_l = col.lower()
            if 'wl' in col_l and '(nm)' in col_l:
                candidate = df[col].map(nist_cell_to_float)
                fill = lambda_values.isna() & candidate.notna()
                if fill.any():
                    lambda_values.loc[fill] = candidate.loc[fill].astype(float)
                    lambda_source_values.loc[fill] = col
                    break

    df['lambda_nm'] = lambda_values
    df['lambda_source'] = lambda_source_values
    df['source_file'] = file_path.name
    df['element_guess'] = guess_element_from_filename(file_path.name)

    # Store a generic numerical line-strength column.  This fixes files where
    # the visible `intens` column is empty but `gA(s^-1)` is populated, such as
    # Li_290_1110_nm.csv.
    strength_text = []
    strength_num = []
    strength_source = []
    for _, rr in df.iterrows():
        st, sn, ss = nist_strength_from_row(rr)
        strength_text.append(st)
        strength_num.append(sn)
        strength_source.append(ss)
    df['nist_strength'] = strength_text
    df['nist_relative_intensity_numeric'] = strength_num
    df['nist_strength_source'] = strength_source

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


def extract_ionization_state(element_label='', row=None, source_file=''):
    """Return (element_symbol, ionization_state, spectrum_label).

    Reads NIST `Spectrum`/`Species`/`Ion` columns when available and also
    infers ionization from filenames such as Fe_I_II_290_1110_nm.csv.
    The helper is intentionally conservative: if several states are encoded
    in the filename, it returns the first one unless the row itself provides a
    clearer Spectrum value.
    """
    texts = []
    if row is not None:
        try:
            for col in getattr(row, 'index', []):
                cl = str(col).strip().lower()
                if any(k in cl for k in ['spectrum', 'spectr', 'species', 'ion', 'element']):
                    val = clean_nist_cell(row.get(col, ''))
                    if str(val).strip():
                        texts.append(str(val).strip())
            # Preserve original per-row filename when grouped for Voigt.
            for col in ['__source_file_for_voigt__', 'source_file']:
                if col in getattr(row, 'index', []):
                    val = clean_nist_cell(row.get(col, ''))
                    if str(val).strip():
                        texts.append(Path(str(val).strip()).stem.replace('_', ' '))
        except Exception:
            pass
    if element_label:
        texts.append(str(element_label).strip())
    if source_file:
        texts.append(Path(str(source_file)).stem.replace('_', ' '))

    # Prefer explicit ASD sp_num when present.  This is essential for files like
    # Li_290_1110_nm.csv, where the filename has no roman state but each row has
    # sp_num = 1, 2, 3, ...
    if row is not None:
        try:
            for c in ['sp_num', 'spnum', 'ion_stage', 'ionization_stage']:
                if c in getattr(row, 'index', []):
                    ion = sp_num_to_roman_ion(row.get(c, ''))
                    if ion:
                        elem_from_row = ''
                        for ec in ['element', 'Element', 'elem']:
                            if ec in getattr(row, 'index', []):
                                elem_from_row = normalize_element_label(clean_nist_cell(row.get(ec, '')))
                                break
                        elem = elem_from_row or normalize_element_label(element_label or (texts[0] if texts else ''))
                        if elem:
                            return elem, ion, f"{elem} {ion}"
        except Exception:
            pass

    roman_re = r'(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)'
    for txt in texts:
        m = re.search(r'\b([A-Z][a-z]?)\s*[-_ ]*' + roman_re + r'\b', str(txt))
        if m:
            elem = normalize_element_label(m.group(1))
            ion = m.group(2)
            return elem, ion, f"{elem} {ion}"

    # Filename-only form like "Fe I II" after underscores were converted.
    for txt in texts:
        elem0 = normalize_element_label(txt)
        if elem0:
            m = re.search(r'\b' + re.escape(elem0) + r'\s+(' + roman_re + r')\b', str(txt))
            if m:
                ion = m.group(1)
                return elem0, ion, f"{elem0} {ion}"

    elem = normalize_element_label(element_label or (texts[0] if texts else ''))
    # Hydrogen Balmer files often do not include an explicit Spectrum/sp_num
    # column, but Balmer emission is neutral atomic hydrogen: H I.
    # Without this fallback the GUI labels the Balmer fits as `H unknown`.
    if elem == 'H':
        return elem, 'I', 'H I'
    return elem, 'unknown', elem


def voigt_unit_profile(x, center, sigma, gamma):
    """Unit-area Voigt profile evaluated at x."""
    x = np.asarray(x, dtype=float)
    sigma = max(float(sigma), 1e-6)
    gamma = max(float(gamma), 1e-9)
    if wofz is None:
        # Fallback pseudo-Voigt if scipy.special is unavailable.
        gauss = np.exp(-0.5 * ((x - center) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
        lorentz = (gamma / np.pi) / ((x - center) ** 2 + gamma ** 2)
        return 0.5 * gauss + 0.5 * lorentz
    z = ((x - center) + 1j * gamma) / (sigma * np.sqrt(2.0))
    return np.real(wofz(z)) / (sigma * np.sqrt(2.0 * np.pi))


def voigt_fwhm_nm(sigma, gamma):
    """Olivero-Longbothum approximation for Voigt FWHM."""
    sigma = max(float(sigma), 0.0)
    gamma = max(float(gamma), 0.0)
    f_g = 2.354820045 * sigma
    f_l = 2.0 * gamma
    return 0.5346 * f_l + np.sqrt(0.2166 * f_l ** 2 + f_g ** 2)


def voigt_single_model(x, area, center, sigma, gamma, b0, b1, x_ref=None):
    """Linear-background + one unit-area Voigt component."""
    x = np.asarray(x, dtype=float)
    if x_ref is None:
        x_ref = float(np.nanmedian(x)) if x.size else 0.0
    return b0 + b1 * (x - x_ref) + area * voigt_unit_profile(x, center, sigma, gamma)


def detect_saturation_mask(y):
    """Detect probable spectrometer saturation/flat-top clipping.

    This is conservative: a point is considered saturated mainly when values are
    near the 16-bit ADC ceiling, or when several adjacent points form an almost
    flat top at the global maximum. The flag is exported and changes the fit to
    a censored/wing-based residual.
    """
    y = np.asarray(y, dtype=float)
    mask = np.zeros_like(y, dtype=bool)
    finite = np.isfinite(y)
    if not np.any(finite):
        return mask, np.nan, 'no_finite_data'
    y_f = y[finite]
    y_max = float(np.nanmax(y_f))
    if not np.isfinite(y_max):
        return mask, np.nan, 'no_finite_max'

    adc_level = float(VOIGT_FIT_SATURATION_ADC_LEVEL)
    abs_thr = float(VOIGT_FIT_SATURATION_ABS_THRESHOLD)
    rel_thr = float(VOIGT_FIT_SATURATION_REL_THRESHOLD)

    if y_max >= abs_thr:
        level = adc_level if y_max > 0.92 * adc_level else y_max
        thr = min(rel_thr * level, y_max - 1e-9)
        mask = finite & (y >= thr)
        if np.sum(mask) >= 2:
            return mask, level, 'near_16bit_ceiling'

    # Secondary flat-top criterion, useful when data were clipped below 65535.
    high = finite & (y >= 0.998 * y_max)
    if np.sum(high) >= 4 and y_max > 20 * max(np.nanmedian(np.abs(y_f)), 1.0):
        return high, y_max, 'flat_top_at_maximum'

    return mask, y_max, 'not_saturated'


def fit_single_voigt_candidate(
    wavelengths_nm,
    intensities,
    lambda_nist_nm,
    element_label='',
    line_name='',
    ionization_state='',
    window_nm=VOIGT_FIT_DEFAULT_WINDOW_NM,
    force_saturated_reference=False,
    allow_weak_fit=False,
):
    """Fit one NIST candidate with a Voigt profile in a local window.

    Saturated samples are handled with a censored residual: for saturated points,
    the model is only penalized when it falls below the clipping level. This is
    important for H-alpha in Avantes-like saturated spectra.
    """
    wl = np.asarray(wavelengths_nm, dtype=float)
    y = np.asarray(intensities, dtype=float)
    lam0 = float(lambda_nist_nm)
    if wl.size != y.size or wl.size < VOIGT_FIT_MIN_POINTS or least_squares is None:
        return None

    finite = np.isfinite(wl) & np.isfinite(y)
    wl = wl[finite]
    y = y[finite]
    if wl.size < VOIGT_FIT_MIN_POINTS:
        return None
    order = np.argsort(wl)
    wl = wl[order]
    y = y[order]

    mask = (wl >= lam0 - window_nm) & (wl <= lam0 + window_nm)
    if np.sum(mask) < VOIGT_FIT_MIN_POINTS:
        return None
    x = wl[mask]
    yy = y[mask]

    baseline_global, noise_global = robust_noise_level(y)
    local_baseline = float(np.nanpercentile(yy, 15)) if yy.size else baseline_global
    local_max = float(np.nanmax(yy)) if yy.size else np.nan
    if not np.isfinite(local_max) or local_max <= local_baseline:
        return None
    min_peak_threshold = max(
        baseline_global + VOIGT_FIT_NOISE_SIGMA_FACTOR * noise_global,
        VOIGT_FIT_MIN_RELATIVE_HEIGHT * float(np.nanmax(y))
    )
    if allow_weak_fit:
        # For forced element overlays (e.g. "show me 3 Li fits no matter what"),
        # try a weaker local fit.  These rows are diagnostic candidates, not
        # automatically accepted global assignments.
        min_peak_threshold = max(
            baseline_global + 2.0 * noise_global,
            0.002 * float(np.nanmax(y))
        )
    if local_max < min_peak_threshold:
        return None

    sat_mask_local, sat_level, sat_reason = detect_saturation_mask(yy)
    is_saturated = bool(np.any(sat_mask_local)) or bool(force_saturated_reference)
    if force_saturated_reference and np.isfinite(local_max):
        # If H-alpha is expected saturated but the generic detector did not flag
        # it, use the upper samples as censored points.
        top = yy >= 0.985 * local_max
        if np.sum(top) >= 2:
            sat_mask_local = top
            sat_level = max(sat_level if np.isfinite(sat_level) else local_max, local_max)
            sat_reason = 'forced_H_balmer_reference_top'
            is_saturated = True

    # Initial center: midpoint of saturated plateau if present, else local max.
    if np.any(sat_mask_local):
        center0 = float(np.nanmean(x[sat_mask_local]))
    else:
        center0 = float(x[int(np.nanargmax(yy))])
    if not np.isfinite(center0):
        center0 = lam0
    center0 = float(np.clip(center0, lam0 - window_nm, lam0 + window_nm))

    amp0 = max(safe_area(x, positive_part(yy - local_baseline)), (local_max - local_baseline) * max(np.median(np.diff(x)), 0.05))
    sigma0 = 0.22
    gamma0 = 0.08
    b0 = local_baseline
    b1 = 0.0
    x_ref = float(np.nanmedian(x))

    y_scale = max(noise_global, 0.02 * max(local_max - local_baseline, 1.0), 1.0)
    x_span = max(float(np.nanmax(x) - np.nanmin(x)), 1e-6)
    y_range = max(float(np.nanmax(yy) - np.nanmin(yy)), 1.0)

    def residual(params):
        area, center, sigma, gamma, bb0, bb1 = params
        model = voigt_single_model(x, area, center, sigma, gamma, bb0, bb1, x_ref=x_ref)
        res = (model - yy) / y_scale
        if np.any(sat_mask_local) and np.isfinite(sat_level):
            # Censored residual: saturated points only require model >= sat_level.
            sat_res = np.minimum(model[sat_mask_local] - sat_level, 0.0) / y_scale
            res = res.copy()
            res[sat_mask_local] = sat_res
        return res

    lower = [0.0, lam0 - window_nm, 0.03, 0.001, np.nanmin(yy) - 2 * y_range, -20 * y_range / x_span]
    upper = [max(amp0 * 50, y_range * x_span * 50), lam0 + window_nm, 3.0, 5.0, np.nanmax(yy) + 2 * y_range, 20 * y_range / x_span]
    p0 = [amp0, center0, sigma0, gamma0, b0, b1]
    try:
        result = least_squares(residual, p0, bounds=(lower, upper), max_nfev=2500, loss='soft_l1')
    except Exception:
        return None
    if not result.success and result.cost <= 0:
        return None

    area, center, sigma, gamma, bb0, bb1 = [float(v) for v in result.x]
    model = voigt_single_model(x, area, center, sigma, gamma, bb0, bb1, x_ref=x_ref)
    component = area * voigt_unit_profile(x, center, sigma, gamma)
    unsat = ~sat_mask_local
    dof = max(int(np.sum(unsat)) - 6, 1)
    if np.sum(unsat) >= 3:
        chi2 = float(np.nansum(((model[unsat] - yy[unsat]) / y_scale) ** 2) / dof)
        rmse = float(np.sqrt(np.nanmean((model[unsat] - yy[unsat]) ** 2)))
    else:
        chi2 = np.nan
        rmse = np.nan

    delta = center - lam0
    fwhm = float(voigt_fwhm_nm(sigma, gamma))
    peak_height = float(np.nanmax(component)) if component.size else np.nan
    fit_quality = 1.0 / (1.0 + chi2) if np.isfinite(chi2) else 0.0

    return {
        'lambda_fit_nm': center,
        'lambda_nist_nm': lam0,
        'delta_nm': delta,
        'voigt_area': area,
        'voigt_amplitude_area': area,
        'voigt_peak_height': peak_height,
        'voigt_fwhm_nm': fwhm,
        'voigt_sigma_nm': sigma,
        'voigt_gamma_nm': gamma,
        'voigt_background_b0': bb0,
        'voigt_background_b1': bb1,
        'voigt_x_ref_nm': x_ref,
        'fit_window_start_nm': float(np.nanmin(x)),
        'fit_window_end_nm': float(np.nanmax(x)),
        'fit_window_half_width_nm': float(window_nm),
        'fit_rmse': rmse,
        'fit_reduced_chi2': chi2,
        'fit_quality_score': fit_quality,
        'fit_success': bool(result.success),
        'fit_message': str(result.message),
        'is_saturated': bool(is_saturated),
        'n_saturated_points': int(np.sum(sat_mask_local)),
        'saturation_level_estimated': float(sat_level) if np.isfinite(sat_level) else np.nan,
        'saturation_reason': sat_reason,
        'fit_saturation_method': 'censored_saturated_points' if bool(is_saturated) else 'ordinary_voigt',
        'area_reliability': 'estimated_from_wings_or_censored' if bool(is_saturated) else 'direct_fit',
        'intensity_reliable': not bool(is_saturated),
        'x_fit_nm_json': json.dumps([float(v) for v in x]),
        'y_fit_model_json': json.dumps([float(v) for v in model]),
        'y_fit_component_json': json.dumps([float(v) for v in component]),
    }


def estimate_voigt_hydrogen_wavelength_calibration(wavelengths_nm, intensities):
    """Robust H-Balmer wavelength calibration from Voigt-fitted alternatives.

    The previous calibration fitted one local Voigt per Balmer line and either
    accepted or rejected it.  That is fragile when H-alpha is saturated or when a
    weak Balmer line is blended with another feature.  This version does:

      1) For each Balmer line, find several local experimental alternatives.
      2) Fit each alternative with a Voigt profile, using censored residuals for
         saturated H-alpha-like peaks.
      3) Select the most self-consistent set of anchors with a weighted robust
         calibration fit lambda_NIST = f(lambda_raw).
      4) Export all alternatives, marking which anchors were used strongly,
         used weakly, or rejected.

    H lines are still expected physically; a rejected row means "this measured
    center was not reliable as a calibration anchor", not "hydrogen is absent".
    """
    wl = np.asarray(wavelengths_nm, dtype=float)
    y = np.asarray(intensities, dtype=float)
    finite = np.isfinite(wl) & np.isfinite(y)
    wl = wl[finite]
    y = y[finite]
    if wl.size < VOIGT_FIT_MIN_POINTS:
        return pd.DataFrame(), None
    order = np.argsort(wl)
    wl = wl[order]
    y = y[order]

    baseline, noise_sigma = robust_noise_level(y)
    y_max = float(np.nanmax(y)) if y.size else 0.0

    def local_peak_guesses(lam_nist, search_window, max_alts):
        mask = (wl >= lam_nist - search_window) & (wl <= lam_nist + search_window)
        if np.sum(mask) < VOIGT_FIT_MIN_POINTS:
            return [float(lam_nist)]
        xx = wl[mask]
        yy = y[mask]
        # Smooth only for locating alternative maxima.  Fits use the raw data.
        if savgol_filter is not None and yy.size >= 9:
            win = min(11, yy.size if yy.size % 2 else yy.size - 1)
            win = max(win, 5 if yy.size >= 5 else yy.size)
            if win % 2 == 0:
                win -= 1
            try:
                ys = savgol_filter(yy, win, 2)
            except Exception:
                ys = yy
        else:
            ys = yy
        loc_bg = float(np.nanpercentile(yy, 15)) if yy.size else baseline
        thr = max(loc_bg + 3.0 * noise_sigma, loc_bg + 0.015 * max(y_max - baseline, 1.0))
        ismax = np.zeros_like(ys, dtype=bool)
        if ys.size >= 3:
            ismax[1:-1] = (ys[1:-1] >= ys[:-2]) & (ys[1:-1] >= ys[2:]) & (ys[1:-1] > thr)
        idxs = np.where(ismax)[0]
        guesses = []
        for idx in idxs:
            c = float(xx[idx])
            local = (xx >= c - 0.45) & (xx <= c + 0.45)
            area = safe_area(xx[local], positive_part(yy[local] - loc_bg)) if np.sum(local) >= 2 else 0.0
            guesses.append((c, float(max(ys[idx] - loc_bg, 0.0)), area, abs(c - lam_nist)))
        # Always include the nominal raw NIST location as a fallback, but it will
        # only win if the fit is actually good and self-consistent.
        guesses.append((float(lam_nist), 0.0, 0.0, 0.0))
        guesses = sorted(guesses, key=lambda t: (t[1], t[2], -t[3]), reverse=True)
        accepted = []
        for c, h, area, d in guesses:
            if any(abs(c - a) < 0.35 for a in accepted):
                continue
            accepted.append(c)
            if len(accepted) >= max_alts:
                break
        return accepted or [float(lam_nist)]

    rows = []
    for line_name, lam_nist in HYDROGEN_BALMER_LINES_NM:
        base_window = VOIGT_FIT_SATURATED_BALMER_WINDOW_NM if line_name == 'H_alpha' else VOIGT_FIT_BALMER_WINDOW_NM
        search_window = max(base_window, VOIGT_BALMER_CALIBRATION_SEARCH_WINDOW_NM)
        guesses = local_peak_guesses(
            float(lam_nist),
            search_window,
            int(VOIGT_BALMER_CALIBRATION_MAX_ALTERNATIVES_PER_LINE),
        )
        local_rows = []
        for guess in guesses:
            # Fit around each measured alternative.  Delta is later computed
            # relative to the true NIST Balmer wavelength.
            fit_window = max(base_window, abs(float(guess) - float(lam_nist)) + 0.75)
            fit = fit_single_voigt_candidate(
                wl,
                y,
                lambda_nist_nm=float(guess),
                element_label='H',
                line_name=line_name,
                ionization_state='I',
                window_nm=fit_window,
                force_saturated_reference=(line_name == 'H_alpha'),
            )
            if fit is None:
                continue
            center_raw = float(fit.get('lambda_fit_nm', np.nan))
            if not np.isfinite(center_raw):
                continue
            raw_delta = center_raw - float(lam_nist)
            fwhm = float(fit.get('voigt_fwhm_nm', np.nan))
            fit_quality = float(fit.get('fit_quality_score', 0.0))
            area = float(fit.get('voigt_area', 0.0))
            saturated = bool(fit.get('is_saturated', False))
            # Metrological weight: H exists, but broad/saturated/weak fits should
            # not drag the whole wavelength calibration.
            delta_penalty = 1.0 / (1.0 + (abs(raw_delta) / max(VOIGT_BALMER_CALIBRATION_MAX_RAW_DELTA_SOFT_NM, 1e-6)) ** 2)
            fwhm_penalty = 1.0 / (1.0 + (max(fwhm, 0.0) / max(VOIGT_BALMER_CALIBRATION_GOOD_FWHM_NM, 1e-6)) ** 2) if np.isfinite(fwhm) else 0.15
            area_scale = np.sqrt(max(area, 0.0)) if np.isfinite(area) else 0.0
            area_weight = area_scale / (area_scale + 150.0) if area_scale > 0 else 0.15
            saturation_weight = 0.65 if saturated else 1.0
            # H-alpha is physically important, but saturation can bias its center;
            # it gets a prior boost without becoming automatically dominant.
            balmer_prior = 1.15 if line_name in ('H_alpha', 'H_beta') else 1.0
            anchor_weight = max(0.02, fit_quality) * delta_penalty * (0.35 + 0.65 * fwhm_penalty) * (0.35 + 0.65 * area_weight) * saturation_weight * balmer_prior
            local_rows.append({
                'line': line_name,
                'lambda_nist_nm': float(lam_nist),
                'lambda_fit_raw_nm': center_raw,
                'raw_delta_fit_minus_nist_nm': raw_delta,
                'voigt_area': area,
                'voigt_peak_height': fit.get('voigt_peak_height', np.nan),
                'voigt_fwhm_nm': fwhm,
                'voigt_sigma_nm': fit.get('voigt_sigma_nm', np.nan),
                'voigt_gamma_nm': fit.get('voigt_gamma_nm', np.nan),
                'is_saturated': saturated,
                'fit_saturation_method': fit.get('fit_saturation_method', ''),
                'fit_quality_score': fit_quality,
                'anchor_weight': float(anchor_weight),
                'anchor_candidate_center_guess_nm': float(guess),
                'anchor_candidate_score': float(anchor_weight),
                'anchor_status': 'candidate_not_selected',
                'used_for_calibration': False,
            })
        local_rows = sorted(local_rows, key=lambda r: r.get('anchor_candidate_score', 0.0), reverse=True)
        for k, r in enumerate(local_rows, start=1):
            r['anchor_candidate_rank_for_line'] = k
            rows.append(r)

    cal_df = pd.DataFrame(rows)
    if cal_df.empty:
        return cal_df, None

    # Keep only the top few alternatives per Balmer line for the combinatorial
    # robust selection.
    candidate_groups = []
    for line_name, grp in cal_df.groupby('line', sort=False):
        g = grp.sort_values('anchor_candidate_score', ascending=False).head(int(VOIGT_BALMER_CALIBRATION_MAX_ALTERNATIVES_PER_LINE))
        candidate_groups.append(g.to_dict('records'))

    # Generate combinations with one candidate per available Balmer line.  If
    # many lines are available this remains small: 3^6 = 729 combinations.
    best_combo = None
    best_score = np.inf
    for combo in itertools.product(*candidate_groups):
        combo = list(combo)
        # Prefer at least three anchors; allow two as fallback.
        if len(combo) < 2:
            continue
        x = np.asarray([r['lambda_fit_raw_nm'] for r in combo], dtype=float)
        z = np.asarray([r['lambda_nist_nm'] for r in combo], dtype=float)
        w = np.asarray([max(float(r.get('anchor_weight', 0.05)), 0.02) for r in combo], dtype=float)
        finite_combo = np.isfinite(x) & np.isfinite(z) & np.isfinite(w) & (w > 0)
        if np.sum(finite_combo) < 2:
            continue
        x = x[finite_combo]
        z = z[finite_combo]
        w = w[finite_combo]
        combo_valid = [r for r, ok in zip(combo, finite_combo) if ok]
        # Avoid quadratic fits with too few reliable anchors; linearly calibrated
        # axes are usually safer when anchors are sparse or doubtful.
        degree_eff = 2 if len(combo_valid) >= 5 else 1
        degree_eff = int(min(degree_eff, len(combo_valid) - 1))
        try:
            coeffs = np.polyfit(x, z, deg=degree_eff, w=np.sqrt(w))
            pred = np.polyval(coeffs, x)
        except Exception:
            continue
        residual = z - pred
        abs_res = np.abs(residual)
        robust_res = float(np.nanmedian(abs_res) + 0.35 * np.nanmax(abs_res))
        weak_penalty = float(np.nanmean(1.0 / np.maximum(w, 0.02))) * 0.015
        curvature_penalty = 0.0
        if degree_eff == 2:
            curvature_penalty = min(abs(float(coeffs[0])) * 1e4, 0.35)
        # Prefer more anchors, but only mildly: bad anchors should not win just
        # because there are many of them.
        n_bonus = -0.035 * len(combo_valid)
        score = robust_res + weak_penalty + curvature_penalty + n_bonus
        if score < best_score:
            best_score = score
            best_combo = (combo_valid, coeffs, degree_eff, residual, abs_res)

    if best_combo is None:
        return cal_df, None

    used_combo, coeffs, degree_eff, residual, abs_res = best_combo
    used_keys = set()
    for r, res in zip(used_combo, residual):
        used_keys.add((r['line'], round(float(r['lambda_fit_raw_nm']), 6)))

    cal_df['voigt_calibration_degree'] = degree_eff
    cal_df['lambda_fit_calibrated_nm'] = np.polyval(coeffs, cal_df['lambda_fit_raw_nm'].to_numpy(dtype=float))
    cal_df['residual_after_voigt_calibration_nm'] = cal_df['lambda_nist_nm'] - cal_df['lambda_fit_calibrated_nm']
    cal_df['voigt_calibration_coefficients_high_to_low'] = ', '.join(f'{c:.12g}' for c in coeffs)
    cal_df['used_for_calibration'] = False
    cal_df['anchor_status'] = 'candidate_not_used'

    for idx, row in cal_df.iterrows():
        key = (row.get('line', ''), round(float(row.get('lambda_fit_raw_nm', np.nan)), 6))
        if key in used_keys:
            res = abs(float(row.get('residual_after_voigt_calibration_nm', np.nan)))
            fwhm = float(row.get('voigt_fwhm_nm', np.nan))
            weight = float(row.get('anchor_weight', 0.0))
            cal_df.at[idx, 'used_for_calibration'] = True
            if (np.isfinite(res) and res <= VOIGT_BALMER_CALIBRATION_MAX_RESIDUAL_USED_NM and
                np.isfinite(fwhm) and fwhm <= VOIGT_BALMER_CALIBRATION_MAX_FWHM_STRONG_NM and
                weight >= 0.05):
                cal_df.at[idx, 'anchor_status'] = 'used_strong'
            else:
                cal_df.at[idx, 'anchor_status'] = 'used_weak'
        elif int(row.get('anchor_candidate_rank_for_line', 999)) == 1:
            cal_df.at[idx, 'anchor_status'] = 'best_local_alternative_not_used'

    # Order the table so the selected anchor and the best alternatives per line
    # are easy to inspect.
    cal_df = cal_df.sort_values(['line', 'used_for_calibration', 'anchor_candidate_rank_for_line'], ascending=[True, False, True]).reset_index(drop=True)
    return cal_df, coeffs


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
# FAST-CAMERA VIDEO LUMINOSITY
# =========================================================
def _parse_video_rate(rate_text):
    """Convert an ffprobe rate such as '7/1' to float."""
    try:
        text_value = str(rate_text)
        if '/' in text_value:
            numerator, denominator = text_value.split('/', 1)
            denominator = float(denominator)
            return float(numerator) / denominator if denominator else np.nan
        return float(text_value)
    except Exception:
        return np.nan


def extract_video_luminosity(video_path, return_display_frames=False):
    """
    Sum grayscale and RGB-channel intensities for every decoded video frame.

    OpenCV is used when available.  A streaming ffmpeg fallback keeps this
    feature usable without adding a mandatory Python package.  The returned fps
    is the *playback* rate only; it must not be confused with the physical fast-
    camera frame interval used by the synchronization plot. The red channel is
    retained separately because it is a closer camera proxy for H-alpha than
    broadband grayscale luminosity.
    """
    video_path = str(video_path)

    try:
        import cv2
        capture = cv2.VideoCapture(video_path)
        if capture.isOpened():
            playback_fps = float(capture.get(cv2.CAP_PROP_FPS))
            width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
            height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            frame_sums = []
            red_frame_sums = []
            green_frame_sums = []
            blue_frame_sums = []
            display_frames = []
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_sums.append(float(np.sum(gray, dtype=np.float64)))
                blue_frame_sums.append(float(np.sum(frame[:, :, 0], dtype=np.float64)))
                green_frame_sums.append(float(np.sum(frame[:, :, 1], dtype=np.float64)))
                red_frame_sums.append(float(np.sum(frame[:, :, 2], dtype=np.float64)))
                if return_display_frames:
                    frame_height, frame_width = frame.shape[:2]
                    scale = min(
                        VIDEO_DISPLAY_MAX_WIDTH / max(frame_width, 1),
                        VIDEO_DISPLAY_MAX_HEIGHT / max(frame_height, 1),
                        1.0,
                    )
                    if scale < 1.0:
                        frame = cv2.resize(
                            frame,
                            (max(1, int(round(frame_width * scale))),
                             max(1, int(round(frame_height * scale)))),
                            interpolation=cv2.INTER_AREA,
                        )
                    display_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            capture.release()
            if frame_sums:
                return {
                    'frame_sums': np.asarray(frame_sums, dtype=float),
                    'red_frame_sums': np.asarray(red_frame_sums, dtype=float),
                    'green_frame_sums': np.asarray(green_frame_sums, dtype=float),
                    'blue_frame_sums': np.asarray(blue_frame_sums, dtype=float),
                    'playback_fps': playback_fps,
                    'width': width,
                    'height': height,
                    'backend': 'opencv',
                    'display_frames': display_frames,
                }
    except Exception:
        # Try ffmpeg below.  Import/codec errors are reported only if both
        # decoders fail.
        pass

    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        raise RuntimeError(
            "The video could not be decoded. Install opencv-python or add "
            "ffmpeg/ffprobe to PATH."
        )

    probe_command = [
        ffprobe, '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,avg_frame_rate,r_frame_rate',
        '-of', 'json', video_path,
    ]
    try:
        probe = json.loads(subprocess.check_output(probe_command, stderr=subprocess.STDOUT, text=True))
        stream_info = probe['streams'][0]
        width = int(stream_info['width'])
        height = int(stream_info['height'])
        playback_fps = _parse_video_rate(
            stream_info.get('avg_frame_rate') or stream_info.get('r_frame_rate')
        )
    except Exception as exc:
        raise RuntimeError(f"ffprobe could not read the video: {exc}") from exc

    frame_size = width * height * 3
    decode_command = [
        ffmpeg, '-v', 'error', '-i', video_path, '-map', '0:v:0',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', 'pipe:1',
    ]
    process = subprocess.Popen(
        decode_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    def _read_exact(stream, byte_count):
        chunks = []
        received = 0
        while received < byte_count:
            chunk = stream.read(byte_count - received)
            if not chunk:
                break
            chunks.append(chunk)
            received += len(chunk)
        return b''.join(chunks)

    frame_sums = []
    red_frame_sums = []
    green_frame_sums = []
    blue_frame_sums = []
    display_frames = []
    try:
        while True:
            raw_frame = _read_exact(process.stdout, frame_size)
            if len(raw_frame) != frame_size:
                break
            rgb = np.frombuffer(raw_frame, dtype=np.uint8).reshape(height, width, 3)
            # Match the usual grayscale luma convention while retaining every
            # original colour channel for spectrally informed comparisons.
            gray = (
                0.299 * rgb[:, :, 0]
                + 0.587 * rgb[:, :, 1]
                + 0.114 * rgb[:, :, 2]
            )
            frame_sums.append(float(np.sum(gray, dtype=np.float64)))
            red_frame_sums.append(float(np.sum(rgb[:, :, 0], dtype=np.float64)))
            green_frame_sums.append(float(np.sum(rgb[:, :, 1], dtype=np.float64)))
            blue_frame_sums.append(float(np.sum(rgb[:, :, 2], dtype=np.float64)))
            if return_display_frames:
                display_height = min(height, VIDEO_DISPLAY_MAX_HEIGHT)
                display_width = min(width, VIDEO_DISPLAY_MAX_WIDTH)
                row_idx = np.linspace(0, height - 1, display_height).astype(int)
                col_idx = np.linspace(0, width - 1, display_width).astype(int)
                display_frames.append(rgb[np.ix_(row_idx, col_idx)].copy())
        stderr_text = process.stderr.read().decode('utf-8', errors='replace')
        return_code = process.wait()
    except Exception:
        process.kill()
        process.wait()
        raise

    if return_code != 0 or not frame_sums:
        raise RuntimeError(f"ffmpeg could not decode video frames: {stderr_text.strip()}")

    return {
        'frame_sums': np.asarray(frame_sums, dtype=float),
        'red_frame_sums': np.asarray(red_frame_sums, dtype=float),
        'green_frame_sums': np.asarray(green_frame_sums, dtype=float),
        'blue_frame_sums': np.asarray(blue_frame_sums, dtype=float),
        'playback_fps': playback_fps,
        'width': width,
        'height': height,
        'backend': 'ffmpeg',
        'display_frames': display_frames,
    }


def detect_video_light_window(
    frame_sums,
    frame_interval_ms=None,
    target_duration_ms=None,
    absolute_threshold_floor=0.0,
):
    """
    Subtract a robust dark-frame luminosity and find sustained luminous frames.

    The baseline is a low percentile over the complete video rather than the
    first frame only: this remains valid when recording begins during a flash.
    Short one-frame excursions are rejected, but separated sustained luminous
    episodes are retained so a disappearance/reappearance is visible.
    """
    frame_sums = np.asarray(frame_sums, dtype=float)
    finite = frame_sums[np.isfinite(frame_sums)]
    if finite.size < 3:
        raise ValueError("The signal does not contain enough valid samples.")

    baseline_sum = float(np.nanpercentile(finite, VIDEO_BASELINE_PERCENTILE))
    corrected = np.clip(frame_sums - baseline_sum, 0.0, None)
    signal_scale = float(np.nanpercentile(corrected, 95.0))

    dark_limit = float(np.nanpercentile(finite, 30.0))
    dark_values = finite[finite <= dark_limit]
    dark_sigma = robust_mad_sigma(dark_values)
    if not np.isfinite(dark_sigma):
        dark_sigma = float(np.nanstd(dark_values)) if dark_values.size else 0.0

    threshold = max(
        5.0 * max(dark_sigma, 0.0),
        VIDEO_LIGHT_THRESHOLD_FRACTION * max(signal_scale, 0.0),
        float(absolute_threshold_floor),
    )
    active = np.asarray(corrected >= threshold, dtype=bool)

    # Bridge a single missing frame inside an otherwise luminous episode.
    if active.size >= 3:
        bridged = active.copy()
        bridged[1:-1] |= active[:-2] & active[2:]
        active = bridged

    runs = []
    idx = 0
    while idx < active.size:
        if not active[idx]:
            idx += 1
            continue
        run_start = idx
        while idx + 1 < active.size and active[idx + 1]:
            idx += 1
        run_end = idx
        if run_end - run_start + 1 >= int(VIDEO_LIGHT_MIN_CONSECUTIVE_FRAMES):
            runs.append((int(run_start), int(run_end)))
        idx += 1

    sustained = np.zeros_like(active)
    for run_start, run_end in runs:
        sustained[run_start:run_end + 1] = True

    target_is_valid = (
        frame_interval_ms is not None
        and target_duration_ms is not None
        and np.isfinite(frame_interval_ms)
        and np.isfinite(target_duration_ms)
        and float(frame_interval_ms) > 0
        and float(target_duration_ms) > 0
    )
    duration_candidates = []

    if runs:
        dt_ms = (
            float(frame_interval_ms)
            if frame_interval_ms is not None and np.isfinite(frame_interval_ms)
            else np.nan
        )
        target_ms = float(target_duration_ms) if target_is_valid else np.nan
        total_light = max(float(np.nansum(corrected)), 1e-15)
        global_peak = max(float(np.nanmax(corrected)), 1e-15)

        # Use exactly the same episode-selection rule for camera luminosity and
        # H-alpha. Each sustained run remains an independent optical event: a
        # dark gap must never be filled just to imitate a long Ip duration.
        for run_index, (candidate_start, candidate_end) in enumerate(runs):
            duration_ms = (
                (candidate_end - candidate_start) * dt_ms
                if np.isfinite(dt_ms) else np.nan
            )
            relative_error = (
                abs(duration_ms - target_ms) / target_ms
                if target_is_valid else np.nan
            )
            local_values = corrected[candidate_start:candidate_end + 1]
            energy_fraction = float(np.nansum(local_values)) / total_light
            peak_fraction = float(np.nanmax(local_values)) / global_peak
            strength_score = 0.70 * energy_fraction + 0.30 * peak_fraction
            duration_candidates.append({
                'start_idx': int(candidate_start),
                'end_idx': int(candidate_end),
                'first_run': int(run_index),
                'last_run': int(run_index),
                'duration_ms': float(duration_ms),
                'relative_error': float(relative_error),
                'coverage': 1.0,
                'energy_fraction': float(energy_fraction),
                'peak_fraction': float(peak_fraction),
                'strength_score': float(strength_score),
                'score': (
                    float(relative_error - 0.25 * strength_score)
                    if target_is_valid else float(-strength_score)
                ),
            })

        strongest_score = max(
            candidate['strength_score'] for candidate in duration_candidates
        )
        duration_compatible = [
            candidate for candidate in duration_candidates
            if target_is_valid
            and candidate['relative_error'] <= VIDEO_DURATION_MATCH_TOLERANCE_RATIO
            and candidate['strength_score'] >= 0.50 * strongest_score
        ]
        if duration_compatible:
            selected_candidate = min(
                duration_compatible,
                key=lambda item: (
                    item['score'], item['relative_error'], -item['strength_score']
                ),
            )
            method = 'single_luminous_interval_matched_to_ip_only_duration'
        else:
            selected_candidate = max(
                duration_candidates,
                key=lambda item: (
                    item['strength_score'], item['energy_fraction'], -item['start_idx']
                ),
            )
            method = (
                'strongest_luminous_interval_duration_mismatch'
                if target_is_valid else 'strongest_sustained_luminous_interval'
            )
        start_idx = selected_candidate['start_idx']
        end_idx = selected_candidate['end_idx']
    else:
        start_idx = int(np.nanargmax(corrected))
        end_idx = start_idx
        selected_candidate = None
        method = 'brightest_frame_fallback'

    selected_mask = np.zeros_like(active)
    selected_mask[start_idx:end_idx + 1] = True
    selected_duration_ms = (
        (end_idx - start_idx) * float(frame_interval_ms)
        if frame_interval_ms is not None and np.isfinite(frame_interval_ms)
        else np.nan
    )
    duration_error_ratio = (
        abs(selected_duration_ms - float(target_duration_ms)) / float(target_duration_ms)
        if target_is_valid else np.nan
    )

    return {
        'baseline_sum': baseline_sum,
        'corrected_luminosity': corrected,
        'threshold': float(threshold),
        'active_mask': sustained,
        'active_runs': runs,
        'selected_mask': selected_mask,
        'start_idx': int(start_idx),
        'end_idx': int(end_idx),
        'method': method,
        'target_duration_ms': float(target_duration_ms) if target_is_valid else np.nan,
        'selected_duration_ms': float(selected_duration_ms),
        'duration_error_ratio': float(duration_error_ratio),
        'duration_match_within_tolerance': bool(
            np.isfinite(duration_error_ratio)
            and duration_error_ratio <= VIDEO_DURATION_MATCH_TOLERANCE_RATIO
        ),
        'duration_candidates': duration_candidates,
        'selected_candidate': selected_candidate,
    }


def detect_halpha_with_video_method(
    diagnostic_time_ms,
    halpha,
    frame_interval_ms,
    target_duration_ms=None,
):
    """Detect the main H-alpha burst at camera cadence.

    Thresholding, gap bridging, and minimum persistence are identical to the
    camera detector. The H-alpha episode is then anchored to its main peak near
    the Ip onset and traced backward/forward to the threshold boundaries. This
    prevents an earlier preionization flash from defining the synchronization.
    """
    diagnostic_time_ms = np.asarray(diagnostic_time_ms, dtype=float)
    halpha = np.asarray(halpha, dtype=float)
    n = min(diagnostic_time_ms.size, halpha.size)
    if n < 3 or not np.isfinite(frame_interval_ms) or frame_interval_ms <= 0:
        raise ValueError("H-alpha does not have enough data for comparable optical detection.")

    diagnostic_time_ms = diagnostic_time_ms[:n]
    halpha = halpha[:n]
    finite = np.isfinite(diagnostic_time_ms) & np.isfinite(halpha)
    if np.sum(finite) < 3:
        raise ValueError("H-alpha does not contain enough finite samples.")

    time_finite = diagnostic_time_ms[finite]
    halpha_finite = halpha[finite]
    order = np.argsort(time_finite)
    time_finite = time_finite[order]
    halpha_finite = halpha_finite[order]

    time_grid_ms = np.arange(
        time_finite[0],
        time_finite[-1] + 0.5 * float(frame_interval_ms),
        float(frame_interval_ms),
    )
    halpha_resampled = np.interp(time_grid_ms, time_finite, halpha_finite)
    detection = detect_video_light_window(
        halpha_resampled,
        frame_interval_ms=float(frame_interval_ms),
        target_duration_ms=target_duration_ms,
        absolute_threshold_floor=0.0,
    )

    corrected = np.asarray(detection['corrected_luminosity'], dtype=float)
    threshold = float(detection['threshold'])
    sustained = np.asarray(detection['active_mask'], dtype=bool)

    # Ip_start is t=0 in this time base. Find the dominant H-alpha peak in a
    # local post-breakdown window, allowing a small pre-Ip margin for timing
    # uncertainty. A late unrelated optical spike is therefore not eligible.
    peak_search_mask = (
        (time_grid_ms >= -float(HALPHA_MAIN_PEAK_SEARCH_BEFORE_IP_MS))
        & (time_grid_ms <= float(HALPHA_MAIN_PEAK_SEARCH_AFTER_IP_MS))
        & np.isfinite(corrected)
    )
    peak_search_indices = np.where(peak_search_mask)[0]
    peak_idx = None
    if peak_search_indices.size:
        local_peak_idx = int(np.nanargmax(corrected[peak_search_indices]))
        candidate_peak_idx = int(peak_search_indices[local_peak_idx])
        if corrected[candidate_peak_idx] >= threshold and sustained[candidate_peak_idx]:
            peak_idx = candidate_peak_idx

    if peak_idx is not None:
        # Walk backward from the main peak to the first threshold crossing of
        # this same sustained burst, exactly as a peak-anchored onset detector.
        start_idx = int(peak_idx)
        while start_idx > 0 and sustained[start_idx - 1]:
            start_idx -= 1

        end_idx = int(peak_idx)
        while end_idx + 1 < sustained.size and sustained[end_idx + 1]:
            end_idx += 1

        selected_mask = np.zeros_like(sustained)
        selected_mask[start_idx:end_idx + 1] = True
        selected_duration_ms = (end_idx - start_idx) * float(frame_interval_ms)
        target_is_valid = (
            target_duration_ms is not None
            and np.isfinite(target_duration_ms)
            and float(target_duration_ms) > 0
        )
        duration_error_ratio = (
            abs(selected_duration_ms - float(target_duration_ms)) / float(target_duration_ms)
            if target_is_valid else np.nan
        )
        detection.update({
            'start_idx': int(start_idx),
            'end_idx': int(end_idx),
            'selected_mask': selected_mask,
            'selected_duration_ms': float(selected_duration_ms),
            'duration_error_ratio': float(duration_error_ratio),
            'duration_match_within_tolerance': bool(
                np.isfinite(duration_error_ratio)
                and duration_error_ratio <= VIDEO_DURATION_MATCH_TOLERANCE_RATIO
            ),
            'method': 'main_halpha_peak_backward_to_sustained_threshold',
            'main_peak_idx': int(peak_idx),
            'main_peak_time_ms': float(time_grid_ms[peak_idx]),
        })
    else:
        detection['main_peak_idx'] = None
        detection['main_peak_time_ms'] = np.nan
        detection['method'] = f"{detection.get('method', 'optical_detector')}_peak_anchor_fallback"

    detection['time_grid_ms'] = time_grid_ms
    detection['signal_resampled'] = halpha_resampled
    detection['detector_name'] = 'same_as_video_resampled_to_camera_cadence'
    return detection


def estimate_halpha_video_shift(
    diagnostic_time_ms,
    halpha,
    base_video_time_ms,
    corrected_luminosity,
    selected_start_idx,
    selected_end_idx,
    halpha_start_relative_ms=0.0,
    halpha_end_relative_ms=None,
    max_extra_shift_ms=1.5,
):
    """Fine-tune a common-detector onset shift using constrained correlation.

    The same threshold detector supplies the coarse start for both optical
    signals. Correlation is then allowed to move the camera only inside a small
    neighbourhood of that start, and the main-peak lag is used as a weak prior.
    This aligns similar waveforms without jumping to a different video flash.
    """
    diagnostic_time_ms = np.asarray(diagnostic_time_ms, dtype=float)
    halpha = np.asarray(halpha, dtype=float)
    base_video_time_ms = np.asarray(base_video_time_ms, dtype=float)
    corrected_luminosity = np.asarray(corrected_luminosity, dtype=float)

    n_diag = min(diagnostic_time_ms.size, halpha.size)
    n_video = min(base_video_time_ms.size, corrected_luminosity.size)
    if n_diag < 5 or n_video < 3:
        return {
            'shift_ms': float(halpha_start_relative_ms) if np.isfinite(halpha_start_relative_ms) else 0.0,
            'correlation': np.nan,
            'method': 'halpha_onset_fallback_invalid_signal',
        }

    diagnostic_time_ms = diagnostic_time_ms[:n_diag]
    halpha = halpha[:n_diag]
    base_video_time_ms = base_video_time_ms[:n_video]
    corrected_luminosity = corrected_luminosity[:n_video]

    finite_diag = np.isfinite(diagnostic_time_ms) & np.isfinite(halpha)
    if np.sum(finite_diag) < 5:
        return {
            'shift_ms': float(halpha_start_relative_ms) if np.isfinite(halpha_start_relative_ms) else 0.0,
            'correlation': np.nan,
            'method': 'halpha_onset_fallback_no_finite_signal',
        }

    diagnostic_time_ms = diagnostic_time_ms[finite_diag]
    halpha = halpha[finite_diag]
    order = np.argsort(diagnostic_time_ms)
    diagnostic_time_ms = diagnostic_time_ms[order]
    halpha = halpha[order]

    baseline_mask = (diagnostic_time_ms >= -0.8) & (diagnostic_time_ms <= -0.05)
    if np.sum(baseline_mask) >= 3:
        halpha_baseline = float(np.nanmedian(halpha[baseline_mask]))
    else:
        halpha_baseline = float(np.nanpercentile(halpha, 10.0))
    halpha_positive = np.clip(halpha - halpha_baseline, 0.0, None)

    start_idx = min(max(int(selected_start_idx), 0), n_video - 1)
    end_idx = min(max(int(selected_end_idx), start_idx), n_video - 1)
    selected_indices = np.arange(start_idx, end_idx + 1, dtype=int)
    video_times = base_video_time_ms[selected_indices]
    video_values = corrected_luminosity[selected_indices]
    if video_values.size < 3 or np.nanstd(video_values) <= 0:
        return {
            'shift_ms': float(halpha_start_relative_ms) if np.isfinite(halpha_start_relative_ms) else 0.0,
            'correlation': np.nan,
            'method': 'halpha_onset_fallback_flat_video',
        }

    onset_shift = float(halpha_start_relative_ms) if np.isfinite(halpha_start_relative_ms) else 0.0
    max_extra_shift_ms = max(float(max_extra_shift_ms), 0.1)

    # Peak-to-peak displacement is not imposed directly; it is a weak prior for
    # the correlation score. Restrict the H-alpha peak to its selected optical
    # episode so a late isolated spike cannot become the synchronization target.
    halpha_event_mask = diagnostic_time_ms >= onset_shift
    if halpha_end_relative_ms is not None and np.isfinite(halpha_end_relative_ms):
        halpha_event_mask &= diagnostic_time_ms <= float(halpha_end_relative_ms)
    if np.sum(halpha_event_mask) >= 2:
        event_times = diagnostic_time_ms[halpha_event_mask]
        event_values = halpha_positive[halpha_event_mask]
        halpha_peak_time_ms = float(event_times[int(np.nanargmax(event_values))])
        video_peak_base_ms = float(video_times[int(np.nanargmax(video_values))])
        peak_shift_ms = halpha_peak_time_ms - video_peak_base_ms
        peak_prior_is_valid = bool(
            np.isfinite(peak_shift_ms)
            and abs(peak_shift_ms - onset_shift) <= 1.25 * max_extra_shift_ms
        )
    else:
        halpha_peak_time_ms = np.nan
        video_peak_base_ms = np.nan
        peak_shift_ms = np.nan
        peak_prior_is_valid = False

    video_values = (
        video_values - np.nanmean(video_values)
    ) / max(float(np.nanstd(video_values)), 1e-12)
    step_ms = max(float(np.nanmedian(np.diff(base_video_time_ms))) / 10.0, 0.01)
    shifts = np.arange(
        onset_shift - max_extra_shift_ms,
        onset_shift + max_extra_shift_ms + 0.5 * step_ms,
        step_ms,
    )

    candidates = []
    for shift_ms in shifts:
        sample_times = video_times + shift_ms
        inside = (
            (sample_times >= diagnostic_time_ms[0])
            & (sample_times <= diagnostic_time_ms[-1])
        )
        if np.sum(inside) < 3:
            continue
        h_values = np.interp(sample_times[inside], diagnostic_time_ms, halpha_positive)
        if np.nanstd(h_values) <= 0:
            continue
        h_values = (h_values - np.nanmean(h_values)) / max(float(np.nanstd(h_values)), 1e-12)
        correlation = float(np.nanmean(video_values[inside] * h_values))
        # The onset remains the hard neighbourhood constraint. Peak agreement
        # is a weak preference inside it, not an independent synchronization
        # rule, because camera and H-alpha can have different response shapes.
        onset_penalty = 0.04 * abs(shift_ms - onset_shift) / max_extra_shift_ms
        peak_penalty = (
            0.08 * abs(shift_ms - peak_shift_ms) / max_extra_shift_ms
            if peak_prior_is_valid else 0.0
        )
        score = correlation - onset_penalty - peak_penalty
        candidates.append((float(score), float(correlation), float(shift_ms)))

    if not candidates:
        return {
            'shift_ms': onset_shift,
            'correlation': np.nan,
            'method': 'halpha_onset_fallback_no_valid_correlation',
        }

    best_score, best_correlation, best_shift = max(candidates, key=lambda item: item[0])
    if not np.isfinite(best_correlation) or best_correlation < VIDEO_HALPHA_MIN_CORRELATION:
        return {
            'shift_ms': onset_shift,
            'correlation': best_correlation,
            'score': best_score,
            'halpha_peak_time_ms': halpha_peak_time_ms,
            'video_peak_base_ms': video_peak_base_ms,
            'peak_shift_ms': peak_shift_ms,
            'method': 'same_detector_onset_fallback_low_correlation',
        }
    return {
        'shift_ms': best_shift,
        'correlation': best_correlation,
        'score': best_score,
        'halpha_peak_time_ms': halpha_peak_time_ms,
        'video_peak_base_ms': video_peak_base_ms,
        'peak_shift_ms': peak_shift_ms,
        'method': 'same_detector_onset_plus_constrained_shape_correlation',
    }


def build_halpha_video_sync_candidates(
    diagnostic_time_ms,
    halpha,
    frame_interval_ms,
    total_corrected,
    light_info,
    halpha_start_relative_ms,
    halpha_end_relative_ms,
    halpha_duration_ms,
    red_corrected=None,
    max_candidates=VIDEO_MAX_SYNC_CANDIDATES,
):
    """Build and rank a small set of camera/H-alpha synchronizations.

    Every candidate represents a different sustained luminous episode in the
    video.  At most ``max_candidates`` episodes are evaluated, prioritizing
    durations similar to the detected H-alpha burst.  This prevents a second
    discharge or a preionization flash from silently becoming the only result,
    while keeping the correlation search inexpensive.

    The red channel is preferred as the H-alpha-like clock.  Broadband total
    luminosity is used as a fallback when the red-channel correlation is weak
    or unavailable.  The returned list is ordered by the selected correlation;
    duration error breaks ties and remains visible to the user.
    """
    total_corrected = np.asarray(total_corrected, dtype=float)
    red_corrected = (
        np.asarray(red_corrected, dtype=float)
        if red_corrected is not None else np.array([], dtype=float)
    )
    frame_interval_ms = float(frame_interval_ms)
    frame_count = total_corrected.size
    max_candidates = max(1, min(int(max_candidates), VIDEO_MAX_SYNC_CANDIDATES))
    if frame_count == 0 or not np.isfinite(frame_interval_ms) or frame_interval_ms <= 0:
        return []

    raw_episodes = [
        dict(item) for item in light_info.get('duration_candidates', [])
        if int(item.get('end_idx', -1)) >= int(item.get('start_idx', 0))
    ]
    if not raw_episodes:
        raw_episodes = [{
            'start_idx': int(light_info.get('start_idx', 0)),
            'end_idx': int(light_info.get('end_idx', light_info.get('start_idx', 0))),
            'strength_score': 0.0,
            'energy_fraction': np.nan,
            'peak_fraction': np.nan,
        }]

    target_duration_is_valid = bool(
        np.isfinite(halpha_duration_ms) and float(halpha_duration_ms) > 0
    )
    prepared_episodes = []
    for episode_number, episode in enumerate(raw_episodes, start=1):
        start_idx = min(max(int(episode.get('start_idx', 0)), 0), frame_count - 1)
        end_idx = min(max(int(episode.get('end_idx', start_idx)), start_idx), frame_count - 1)
        duration_ms = (end_idx - start_idx) * frame_interval_ms
        duration_error_ratio = (
            abs(duration_ms - float(halpha_duration_ms)) / float(halpha_duration_ms)
            if target_duration_is_valid else np.nan
        )
        prepared = dict(episode)
        prepared.update({
            'episode_number': int(episode_number),
            'start_idx': int(start_idx),
            'end_idx': int(end_idx),
            'duration_ms': float(duration_ms),
            'halpha_duration_error_ratio': float(duration_error_ratio),
        })
        prepared_episodes.append(prepared)

    # Correlation is evaluated only for the three most plausible durations.
    # Strength breaks duration ties so a weak noise burst is not preferred.
    prepared_episodes.sort(key=lambda item: (
        0 if (
            np.isfinite(item['halpha_duration_error_ratio'])
            and item['halpha_duration_error_ratio'] <= VIDEO_DURATION_MATCH_TOLERANCE_RATIO
        ) else 1,
        item['halpha_duration_error_ratio']
        if np.isfinite(item['halpha_duration_error_ratio']) else np.inf,
        -float(item.get('strength_score', 0.0)),
        item['start_idx'],
    ))
    prepared_episodes = prepared_episodes[:max_candidates]

    frame_index = np.arange(frame_count, dtype=float)
    evaluated = []
    for episode in prepared_episodes:
        start_idx = int(episode['start_idx'])
        end_idx = int(episode['end_idx'])
        base_video_time_ms = (frame_index - start_idx) * frame_interval_ms

        total_alignment = estimate_halpha_video_shift(
            diagnostic_time_ms,
            halpha,
            base_video_time_ms,
            total_corrected,
            start_idx,
            end_idx,
            halpha_start_relative_ms=halpha_start_relative_ms,
            halpha_end_relative_ms=halpha_end_relative_ms,
            max_extra_shift_ms=VIDEO_HALPHA_MAX_FINE_SHIFT_MS,
        )
        if red_corrected.size == frame_count:
            red_alignment = estimate_halpha_video_shift(
                diagnostic_time_ms,
                halpha,
                base_video_time_ms,
                red_corrected,
                start_idx,
                end_idx,
                halpha_start_relative_ms=halpha_start_relative_ms,
                halpha_end_relative_ms=halpha_end_relative_ms,
                max_extra_shift_ms=VIDEO_HALPHA_MAX_FINE_SHIFT_MS,
            )
        else:
            red_alignment = {
                'shift_ms': np.nan,
                'correlation': np.nan,
                'method': 'red_channel_unavailable',
            }

        red_correlation = float(red_alignment.get('correlation', np.nan))
        total_correlation = float(total_alignment.get('correlation', np.nan))
        if np.isfinite(red_correlation) and (
            red_correlation >= VIDEO_HALPHA_LOW_CORRELATION_WARNING
            or not np.isfinite(total_correlation)
        ):
            selected_alignment = red_alignment
            selected_signal = 'red-channel camera intensity'
        elif np.isfinite(total_correlation):
            selected_alignment = total_alignment
            selected_signal = 'total grayscale camera luminosity'
        elif np.isfinite(red_correlation):
            selected_alignment = red_alignment
            selected_signal = 'red-channel camera intensity'
        else:
            selected_alignment = total_alignment
            selected_signal = 'total grayscale camera luminosity'

        shift_ms = float(selected_alignment.get('shift_ms', halpha_start_relative_ms))
        if not np.isfinite(shift_ms):
            shift_ms = float(halpha_start_relative_ms) if np.isfinite(halpha_start_relative_ms) else 0.0
        correlation = float(selected_alignment.get('correlation', np.nan))
        candidate = dict(episode)
        candidate.update({
            'base_video_time_ms': base_video_time_ms,
            'video_time_ms': base_video_time_ms + shift_ms,
            'alignment_info': selected_alignment,
            'alignment_signal_label': selected_signal,
            'alignment_shift_ms': shift_ms,
            'correlation': correlation,
            'red_alignment_info': red_alignment,
            'total_alignment_info': total_alignment,
        })
        evaluated.append(candidate)

    evaluated.sort(key=lambda item: (
        -item['correlation'] if np.isfinite(item['correlation']) else np.inf,
        item['halpha_duration_error_ratio']
        if np.isfinite(item['halpha_duration_error_ratio']) else np.inf,
        -float(item.get('strength_score', 0.0)),
        item['start_idx'],
    ))
    for rank, candidate in enumerate(evaluated, start=1):
        candidate['rank'] = int(rank)
    return evaluated


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
        self.spanish_plots_var = None
        self.plot_font_var = None
        self.plot_text_scale_var = None
        self._video_comparison_windows = []

        # Bottom information panel shown inside the Matplotlib toolbar.
        # It can become very tall when many shots are loaded and a normalization
        # or cursor table is displayed, so the user can close/reopen it.
        self.data_box_visible = True
        self.data_box_text_cache = ""
        self.data_box_visible_var = None
        self.data_box_close_button = None

        # Spectroscopy source selection. Auto uses OceanFX when available,
        # otherwise Avantes. Raw-count display is the default because it is
        # closest to the official MEPhIST viewer. Matching/calibration can still
        # use the selected source with its own normalization internally.
        self.spectrum_source_mode = "Auto"
        self.spectrum_display_mode = "raw"
        # Display-axis controls for spectroscopy.
        # Spec λcal controls whether the experimental spectrum itself is drawn
        # against lambda_raw or lambda_calibrated. Fits/NIST λcal controls
        # whether NIST reference marks and Voigt curves are drawn in calibrated
        # wavelength coordinates or raw spectrometer coordinates.
        self.spectrum_x_calibrated_enabled = True
        self.overlay_x_calibrated_enabled = True

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

        # Voigt spectroscopy analysis state. This is intentionally separate from
        # the legacy NIST centroid/feature matcher so both workflows can be
        # compared during validation.
        self.voigt_fit_overlay_enabled = VOIGT_FIT_OVERLAY_DEFAULT
        # Overlay limits use a compact text syntax, e.g.
        #   default=4,H=6,Fe=8,W=5,O=3,N=3,Li=3
        # The limit is applied per shot and per element, so a loaded shot can
        # contribute up to N curves for each element.
        self.voigt_overlay_limits_text = (
            f"default={VOIGT_OVERLAY_DEFAULT_MAX_PER_ELEMENT},"
            "H=6,Fe=8,W=5,O=3,N=3,C=3,Li=3"
        )
        self.voigt_best_cache = None
        self.voigt_candidate_cache = None
        self.voigt_cache_key = None

        # Fast Voigt spectroscopy summary. This controls how many reliable
        # fitted lines per element are requested before the analysis stops moving
        # to the next selected element. Candidate/rejected fits are still stored.
        self.voigt_fit_top_n_per_element = VOIGT_FIT_TOP_N_PER_ELEMENT
        self.voigt_full_important_line_count = VOIGT_FIT_IMPORTANT_LINES_DEFAULT

        # Legacy non-Voigt quick summary is kept internally, but the visible fast
        # analysis now uses Voigt fits.
        self.quick_spectroscopy_top_n = 3
        self.quick_spectroscopy_cache = None
        self.quick_spectroscopy_cache_key = None

        # Main-plot panel selector. Defaults reproduce the previous main view
        # while allowing the user to add coils or hide panels to enlarge the rest.
        self.main_plot_panel_order = ["Ip", "LV", "Bt", "coils", "spectrum", "H_alpha"]
        self.main_plot_default_panels = {"Ip": True, "LV": False, "Bt": True, "coils": False, "spectrum": True, "H_alpha": True}
        self.main_plot_panel_vars = {}
        # Optional reference markers: show the plasma start/end used by the
        # current analysis on every temporal panel.  This is especially useful
        # in tau mode because Ip/H-alpha/LV should span tau=[0,1].
        self.show_ip_start_end_markers = True
        # Independent optical-window markers.  They are off by default to keep
        # multi-shot comparisons readable and can be enabled from the toolbar.
        self.show_halpha_start_end_markers = False

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

        # Hover labels for the main plot.  These are independent of the cursor
        # dynamics table: when enabled, moving the mouse close to a plotted line
        # shows the shot number, signal name and local value.
        self.hover_labels_enabled = True
        self.hover_label_var = None
        self.hover_cid = None
        self.hover_lines = []
        self.hover_annotation = None

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

        self.data_box_visible_var = tk.BooleanVar(value=bool(getattr(self, "data_box_visible", True)))
        tk.Checkbutton(
            self.top_button_frame1,
            text="Bottom info",
            variable=self.data_box_visible_var,
            command=self.on_data_box_visibility_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0
        ).pack(side=tk.LEFT, padx=(2, 5), pady=2)


        self.cursor_toggle_button = tk.Button(
            self.top_button_frame1,
            text="Enable cursor dynamics",
            command=self.toggle_cursor_dynamics,
            bg="#e0e0e0"
        )
        self.cursor_toggle_button.pack(side=tk.LEFT, padx=5, pady=2)

        self.hover_label_var = tk.BooleanVar(value=bool(getattr(self, "hover_labels_enabled", True)))
        tk.Checkbutton(
            self.top_button_frame1,
            text="Hover labels",
            variable=self.hover_label_var,
            command=self.on_hover_labels_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0
        ).pack(side=tk.LEFT, padx=(2, 5), pady=2)

        self.top_button_frame2 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame2.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        # Keep the spectrum source selector visible on the second toolbar.
        # On narrow screens it was hidden at the far right of the first toolbar.
        tk.Label(self.top_button_frame2, text="Spectrum:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(5, 2), pady=2)
        self.spectrum_source_var = tk.StringVar(value=self.spectrum_source_mode)
        self.spectrum_source_combo = ttk.Combobox(
            self.top_button_frame2,
            textvariable=self.spectrum_source_var,
            values=["Auto", "Oceanfx", "Avantes"],
            state="readonly",
            width=8
        )
        self.spectrum_source_combo.pack(side=tk.LEFT, padx=2, pady=2)
        self.spectrum_source_combo.bind("<<ComboboxSelected>>", self.on_spectrum_source_changed)

        self.spectrum_display_button = tk.Button(
            self.top_button_frame2,
            text="Spec: raw counts",
            command=self.toggle_spectrum_display_mode,
            bg="#eeeeee"
        )
        self.spectrum_display_button.pack(side=tk.LEFT, padx=2, pady=2)


        # Main panel selector. Compact checkbuttons avoid adding many extra
        # action buttons and let the user enlarge a subset of plots.
        tk.Label(self.top_button_frame2, text="Plots:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(8, 2), pady=2)
        self.main_plot_panel_vars = {}
        for _key, _label in [("Ip", "Ip"), ("LV", "LV"), ("Bt", "Bt"), ("coils", "coils"), ("spectrum", "spectrum"), ("H_alpha", "Hα")]:
            _var = tk.BooleanVar(value=bool(self.main_plot_default_panels.get(_key, False)))
            self.main_plot_panel_vars[_key] = _var
            tk.Checkbutton(
                self.top_button_frame2,
                text=_label,
                variable=_var,
                command=self.on_main_plot_panel_changed,
                bg="#f0f0f0",
                padx=1,
                pady=0
            ).pack(side=tk.LEFT, padx=1, pady=2)

        self.show_ip_window_var = tk.BooleanVar(value=bool(getattr(self, "show_ip_start_end_markers", True)))
        tk.Checkbutton(
            self.top_button_frame2,
            text="Ip start-end",
            variable=self.show_ip_window_var,
            command=self.on_ip_window_markers_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0
        ).pack(side=tk.LEFT, padx=(6, 2), pady=2)

        self.show_halpha_window_var = tk.BooleanVar(
            value=bool(getattr(self, "show_halpha_start_end_markers", False))
        )
        tk.Checkbutton(
            self.top_button_frame2,
            text="H-alpha start-end (-. / --)",
            variable=self.show_halpha_window_var,
            command=self.on_halpha_window_markers_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0
        ).pack(side=tk.LEFT, padx=(2, 2), pady=2)

        # The two old H-alpha integral buttons were removed. Their main
        # quantities are now included directly in Important data.
        tk.Button(self.top_button_frame2, text="Shot summary table", command=self.show_requested_discharge_summary, bg="#e7f4e4").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Official-style plots", command=self.plot_official_style_diagnostics, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Compute reproducibility", command=self.compute_reproducibility_gui, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Generate comparison", command=self.generate_group_comparison, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(self.top_button_frame2, text="Export full analysis", command=self.export_full_analysis, bg="#e0e0e0").pack(side=tk.LEFT, padx=5, pady=2)

        # Compact spectroscopy toolbar. Keep only the four high-level actions
        # visible in the main window; detailed controls live inside the
        # spectroscopy panel so the toolbar remains usable on narrow screens.
        self.top_button_frame3 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame3.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        tk.Label(self.top_button_frame3, text="Spectroscopy:", bg="#f0f0f0").pack(side=tk.LEFT, padx=(5, 2), pady=2)

        # Spectroscopy wavelength-axis controls live in the spectroscopy toolbar.
        # Spec λcal changes the x-axis of the experimental spectrum;
        # Fits/NIST λcal changes the coordinate system used to draw NIST marks
        # and Voigt fits.
        self.spectrum_x_calibrated_var = tk.BooleanVar(value=bool(getattr(self, "spectrum_x_calibrated_enabled", True)))
        tk.Checkbutton(
            self.top_button_frame3,
            text="Spec λcal",
            variable=self.spectrum_x_calibrated_var,
            command=self.on_spectrum_axis_mode_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0
        ).pack(side=tk.LEFT, padx=(6, 1), pady=2)

        self.overlay_x_calibrated_var = tk.BooleanVar(value=bool(getattr(self, "overlay_x_calibrated_enabled", True)))
        tk.Checkbutton(
            self.top_button_frame3,
            text="Fits/NIST λcal",
            variable=self.overlay_x_calibrated_var,
            command=self.on_overlay_axis_mode_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0
        ).pack(side=tk.LEFT, padx=(1, 10), pady=2)
        tk.Button(
            self.top_button_frame3,
            text="Quick candidates (NIST preview)",
            command=self.show_spectroscopy_filter_options,
            bg="#d9edf7"
        ).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(
            self.top_button_frame3,
            text="Voigt spectroscopy analysis",
            command=self.show_voigt_analysis_tools,
            bg="#d8f3dc"
        ).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(
            self.top_button_frame3,
            text="Calibrate H Balmer",
            command=self.calibrate_spectroscopy_gui,
            bg="#fff2cc"
        ).pack(side=tk.LEFT, padx=5, pady=2)
        tk.Button(
            self.top_button_frame3,
            text="Spectrum sources",
            command=self.plot_spectrum_sources,
            bg="#e0e0e0"
        ).pack(side=tk.LEFT, padx=5, pady=2)

        # Opciones generales de presentación.  El botón de video se mantiene en
        # esta fila inferior para despejar la barra de gráficos principal.
        self.top_button_frame4 = tk.Frame(self.main_frame, bg="#f0f0f0")
        self.top_button_frame4.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)

        tk.Label(self.top_button_frame4, text="General:", bg="#f0f0f0").pack(
            side=tk.LEFT, padx=(5, 4), pady=2
        )

        self.spanish_plots_var = tk.BooleanVar(value=bool(MOSTRAR_TEXTO_EN_ESPANOL))
        tk.Checkbutton(
            self.top_button_frame4,
            text="Plots in Spanish",
            variable=self.spanish_plots_var,
            command=self.on_plot_language_changed,
            bg="#f0f0f0",
            padx=1,
            pady=0,
        ).pack(side=tk.LEFT, padx=(2, 10), pady=2)

        tk.Label(self.top_button_frame4, text="Plot font:", bg="#f0f0f0").pack(
            side=tk.LEFT, padx=(4, 2), pady=2
        )
        self.plot_font_var = tk.StringVar(value=PLOT_FONT_FAMILY)
        self.plot_font_combo = ttk.Combobox(
            self.top_button_frame4,
            textvariable=self.plot_font_var,
            values=(
                "DejaVu Sans",
                "DejaVu Serif",
                "STIXGeneral",
                "Computer Modern Roman",
                "Arial",
            ),
            state="readonly",
            width=23,
        )
        self.plot_font_combo.pack(side=tk.LEFT, padx=(2, 10), pady=2)
        self.plot_font_combo.bind("<<ComboboxSelected>>", self.on_plot_font_changed)

        tk.Label(self.top_button_frame4, text="Text scale:", bg="#f0f0f0").pack(
            side=tk.LEFT, padx=(4, 2), pady=2
        )
        self.plot_text_scale_var = tk.StringVar(value="Informe (1.0×)")
        self.plot_text_scale_combo = ttk.Combobox(
            self.top_button_frame4,
            textvariable=self.plot_text_scale_var,
            values=(
                "Compacta (0.85×)",
                "Informe (1.0×)",
                "Grande (1.20×)",
                "Muy grande (1.40×)",
            ),
            state="readonly",
            width=19,
        )
        self.plot_text_scale_combo.pack(side=tk.LEFT, padx=(2, 12), pady=2)
        self.plot_text_scale_combo.bind("<<ComboboxSelected>>", self.on_plot_font_changed)

        tk.Button(
            self.top_button_frame4,
            text="Compare with video",
            command=self.compare_with_video,
            bg="#d9edf7",
        ).pack(side=tk.RIGHT, padx=(10, 6), pady=2)

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

        self.data_box_close_button = tk.Button(
            self.toolbar,
            text="×",
            command=lambda: self.set_data_box_visible(False),
            width=2,
            padx=1,
            pady=0,
            relief="flat",
            bg="#eeeeee"
        )
        self.data_box_close_button.pack(side=tk.LEFT, padx=(8, 0))

        self.data_box_label = tk.Label(
            self.toolbar,
            text="",
            anchor="w",
            justify="left",
            font=("Courier New", 8)
        )
        self.data_box_label.pack(side=tk.LEFT, padx=(4, 10))

        # Always connect the hover callback once; it returns immediately when
        # the checkbox is disabled. This keeps it compatible with redraws, zoom
        # and the existing cursor-dynamics callback.
        self.hover_cid = self.canvas.mpl_connect('motion_notify_event', self.on_line_hover_move)

        self.connect_xlim_sync_callbacks()
        self.canvas.draw()

    def on_plot_language_changed(self):
        """Alterna los textos visibles de los gráficos entre español e inglés."""
        global MOSTRAR_TEXTO_EN_ESPANOL
        try:
            MOSTRAR_TEXTO_EN_ESPANOL = bool(self.spanish_plots_var.get())
        except Exception:
            MOSTRAR_TEXTO_EN_ESPANOL = True

        # Actualiza los controles del panel y reconstruye la figura principal.
        # Las figuras secundarias se reconstruyen con el idioma elegido cuando
        # vuelven a abrirse.
        _actualizar_idioma_widgets(getattr(self, "main_frame", None))
        active_video_windows = []
        for video_window in list(getattr(self, "_video_comparison_windows", [])):
            try:
                if not video_window.winfo_exists():
                    continue
                _actualizar_idioma_widgets(video_window)
                refresh_language = getattr(
                    video_window, "_mephist_refresh_language", None
                )
                if callable(refresh_language):
                    refresh_language()
                active_video_windows.append(video_window)
            except Exception:
                continue
        self._video_comparison_windows = active_video_windows
        if hasattr(self, "fig"):
            self.plot_data()

    def on_plot_font_changed(self, event=None):
        """Aplica familia y escala tipográfica a todas las figuras posteriores."""
        global PLOT_FONT_FAMILY, PLOT_FONT_SCALE

        familia = str(
            self.plot_font_var.get() if self.plot_font_var is not None
            else PLOT_FONT_FAMILY
        ).strip() or "DejaVu Sans"
        escala_texto = str(
            self.plot_text_scale_var.get() if self.plot_text_scale_var is not None
            else "Informe (1.0×)"
        )
        escalas = {
            "Compacta (0.85×)": 0.85,
            "Informe (1.0×)": 1.00,
            "Grande (1.20×)": 1.20,
            "Muy grande (1.40×)": 1.40,
        }
        escala = float(escalas.get(escala_texto, 1.0))

        PLOT_FONT_FAMILY = familia
        PLOT_FONT_SCALE = escala
        plt.rcParams.update({
            "font.family": familia,
            "axes.titlesize": _tamano_plot(OVERLEAF_TITLE_SIZE),
            "axes.labelsize": _tamano_plot(OVERLEAF_AXIS_LABEL_SIZE),
            "xtick.labelsize": _tamano_plot(OVERLEAF_TICK_SIZE),
            "ytick.labelsize": _tamano_plot(OVERLEAF_TICK_SIZE),
            "legend.fontsize": _tamano_plot(OVERLEAF_LEGEND_SIZE),
            "legend.title_fontsize": _tamano_plot(OVERLEAF_LEGEND_TITLE_SIZE),
            "figure.titlesize": _tamano_plot(OVERLEAF_SUPTITLE_SIZE),
        })

        if hasattr(self, "fig"):
            self.plot_data()

    def get_selected_main_plot_keys(self):
        """Return selected main panels in a stable order."""
        selected = []
        vars_dict = getattr(self, "main_plot_panel_vars", {}) or {}
        for key in getattr(self, "main_plot_panel_order", ["Ip", "LV", "Bt", "coils", "spectrum", "H_alpha"]):
            var = vars_dict.get(key)
            try:
                is_on = bool(var.get()) if var is not None else bool(self.main_plot_default_panels.get(key, False))
            except Exception:
                is_on = bool(self.main_plot_default_panels.get(key, False))
            if is_on:
                selected.append(key)
        if not selected:
            selected = ["Ip"]
            try:
                vars_dict["Ip"].set(True)
            except Exception:
                pass
        return selected

    def on_main_plot_panel_changed(self):
        """Refresh the main figure when the user changes panel checkboxes."""
        # Make sure at least one panel remains visible.
        if not self.get_selected_main_plot_keys():
            try:
                self.main_plot_panel_vars["Ip"].set(True)
            except Exception:
                pass
        self.plot_data()

    def on_ip_window_markers_changed(self):
        """Toggle vertical start/end markers for the selected plasma window."""
        try:
            self.show_ip_start_end_markers = bool(self.show_ip_window_var.get())
        except Exception:
            self.show_ip_start_end_markers = True
        self.plot_data()

    def on_halpha_window_markers_changed(self):
        """Toggle vertical markers for the independently detected H-alpha window."""
        try:
            self.show_halpha_start_end_markers = bool(self.show_halpha_window_var.get())
        except Exception:
            self.show_halpha_start_end_markers = False
        self.plot_data()

    def rebuild_plot_axes(self):
        """
        Rebuild the Matplotlib axes according to selected panels and residual state.

        The normal view is dynamic: the user can select Ip, Bt, coils, spectrum
        and/or H-alpha. Residuals remain available for selected panels, but are
        arranged vertically to avoid hidden axes.
        """
        self.disconnect_xlim_sync_callbacks()
        self.fig.clear()
        self.hover_lines = []
        self.hover_annotation = None

        # Reset all known axes so code can safely test for None.
        self.ax_bt = None
        self.ax_ip = None
        self.ax_loop = None
        self.ax_halpha = None
        self.ax_avantes = None
        self.ax_coils = None
        self.ax_bt_residual = None
        self.ax_ip_residual = None
        self.ax_loop_residual = None
        self.ax_halpha_residual = None
        self.ax_avantes_residual = None
        self.ax_coils_residual = None

        selected = self.get_selected_main_plot_keys()

        def assign_axis(key, ax, residual=False):
            if key == "Bt":
                if residual:
                    self.ax_bt_residual = ax
                else:
                    self.ax_bt = ax
            elif key == "Ip":
                if residual:
                    self.ax_ip_residual = ax
                else:
                    self.ax_ip = ax
            elif key == "LV":
                if residual:
                    self.ax_loop_residual = ax
                else:
                    self.ax_loop = ax
            elif key == "H_alpha":
                if residual:
                    self.ax_halpha_residual = ax
                else:
                    self.ax_halpha = ax
            elif key == "spectrum":
                if residual:
                    self.ax_avantes_residual = ax
                else:
                    self.ax_avantes = ax
            elif key == "coils":
                if residual:
                    self.ax_coils_residual = ax
                else:
                    self.ax_coils = ax

        if self.show_residuals:
            # Vertical layout: each selected panel gets main + residual row.
            nrows = max(2 * len(selected), 2)
            height_ratios = []
            for _ in selected:
                height_ratios.extend([3.0, 1.0])
            gs = self.fig.add_gridspec(nrows, 1, height_ratios=height_ratios, hspace=0.42)
            for i, key in enumerate(selected):
                ax = self.fig.add_subplot(gs[2 * i, 0])
                ax_res = self.fig.add_subplot(gs[2 * i + 1, 0], sharex=ax)
                assign_axis(key, ax, residual=False)
                assign_axis(key, ax_res, residual=True)
        else:
            n = len(selected)
            ncols = 1 if n == 1 else 2
            nrows = int(np.ceil(n / ncols))
            gs = self.fig.add_gridspec(nrows, ncols, hspace=0.35, wspace=0.28)
            for i, key in enumerate(selected):
                r = i // ncols
                c = i % ncols
                ax = self.fig.add_subplot(gs[r, c])
                assign_axis(key, ax, residual=False)

        self.time_axes = [ax for ax in [self.ax_bt, self.ax_ip, self.ax_loop, self.ax_halpha, self.ax_coils] if ax is not None]
        self.time_residual_axes = [ax for ax in [self.ax_bt_residual, self.ax_ip_residual, self.ax_loop_residual, self.ax_halpha_residual, self.ax_coils_residual] if ax is not None]
        self.spec_axes = [ax for ax in [self.ax_avantes] if ax is not None]
        self.spec_residual_axes = [ax for ax in [self.ax_avantes_residual] if ax is not None]

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
        normalizations, Ip, Bt, loop voltage and H-alpha use the same tau axis
        defined by the Ip start/end window. Coils keep physical time.
        Spectroscopy is synchronized only with the spectroscopy residual axis
        because its x-axis is wavelength.
        """
        if source_ax in self.spec_axes or source_ax in self.spec_residual_axes:
            return [ax for ax in (self.spec_axes + self.spec_residual_axes) if ax is not None]

        if source_ax in self.time_axes or source_ax in self.time_residual_axes:
            if self.normalization_mode == NORMALIZATION_NONE:
                return [ax for ax in (self.time_axes + self.time_residual_axes) if ax is not None]

            # In tau modes, Ip, Bt, loop voltage and H-alpha use tau.
            # Coils keep their physical time axis.
            tau_axes = [
                self.ax_ip,
                self.ax_bt,
                self.ax_loop,
                self.ax_halpha,
                self.ax_ip_residual,
                self.ax_bt_residual,
                self.ax_loop_residual,
                self.ax_halpha_residual
            ]
            non_tau_time_axes = [
                self.ax_coils,
                self.ax_coils_residual
            ]

            if source_ax in tau_axes:
                return [ax for ax in tau_axes if ax is not None]
            return [ax for ax in non_tau_time_axes if ax is not None]

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


    def on_spectrum_source_changed(self, event=None):
        """Update selected spectrometer source and refresh plots/matching cache."""
        try:
            self.spectrum_source_mode = str(self.spectrum_source_var.get()).strip() or "Auto"
        except Exception:
            self.spectrum_source_mode = "Auto"
        self.nist_all_matches_cache = None
        self.nist_all_matches_cache_key = None
        self.nist_all_candidates_cache = None
        self.voigt_best_cache = None
        self.voigt_candidate_cache = None
        self.voigt_cache_key = None
        self.plot_data()

    def toggle_spectrum_display_mode(self):
        """Toggle the main spectrum panel between official raw counts and normalized spectrum."""
        self.spectrum_display_mode = "normalized" if getattr(self, "spectrum_display_mode", "raw") == "raw" else "raw"
        if hasattr(self, "spectrum_display_button"):
            self.spectrum_display_button.config(
                text="Spec: normalized" if self.spectrum_display_mode == "normalized" else "Spec: raw counts"
            )
        self.plot_data()

    def on_spectrum_axis_mode_changed(self):
        """Toggle the experimental spectrum x-axis: raw lambda or H-Balmer calibrated lambda."""
        try:
            self.spectrum_x_calibrated_enabled = bool(self.spectrum_x_calibrated_var.get())
        except Exception:
            self.spectrum_x_calibrated_enabled = True
        self.plot_data()

    def on_overlay_axis_mode_changed(self):
        """Toggle the NIST/Voigt overlay x-axis: raw/instrument or calibrated/NIST coordinates."""
        try:
            self.overlay_x_calibrated_enabled = bool(self.overlay_x_calibrated_var.get())
        except Exception:
            self.overlay_x_calibrated_enabled = True
        self.plot_data()

    def get_spectrum_display_wavelengths(self, data, wavelengths):
        """Return wavelengths for plotting the experimental spectrum.

        If Spec λcal is enabled, the spectrum itself is shifted to the
        H-Balmer calibrated wavelength axis. Otherwise the raw spectrometer
        wavelength is shown.
        """
        wl = np.asarray(wavelengths, dtype=float)
        if bool(getattr(self, "spectrum_x_calibrated_enabled", True)):
            return self.apply_spectroscopy_calibration_to_wavelengths(data, wl)
        return wl

    def overlay_uses_calibrated_axis(self):
        """Whether NIST markers and Voigt fit curves should be drawn in calibrated coordinates."""
        return bool(getattr(self, "overlay_x_calibrated_enabled", True))

    def get_spectrum_x_axis_label(self):
        return 'Calibrated wavelength [nm]' if bool(getattr(self, "spectrum_x_calibrated_enabled", True)) else 'Raw wavelength [nm]'

    def get_overlay_axis_label(self):
        return 'calibrated λ' if self.overlay_uses_calibrated_axis() else 'raw λ'

    def resolve_spectrum_source_key(self, data, requested=None):
        """Return the concrete spectrum source key to use for a shot."""
        spectra = data.get('spectra_by_source', {}) if isinstance(data, dict) else {}
        if not spectra:
            return ""
        mode = str(requested if requested is not None else getattr(self, "spectrum_source_mode", "Auto")).strip()
        if mode in spectra:
            return mode
        mode_low = mode.lower()
        for key in spectra.keys():
            if key.lower() == mode_low:
                return key
        if 'Oceanfx' in spectra:
            return 'Oceanfx'
        if 'Avantes' in spectra:
            return 'Avantes'
        return next(iter(spectra.keys()))

    def get_selected_spectrum_arrays(self, data, use_rw=False):
        """Return wl, intensity, source_label for the selected spectrometer source."""
        spectra = data.get('spectra_by_source', {}) if isinstance(data, dict) else {}
        key = self.resolve_spectrum_source_key(data)
        if key and key in spectra:
            s = spectra[key]
            wl = np.asarray(s.get('wavelengths', np.array([])), dtype=float)
            arr_key = 'intensity_rw' if use_rw else 'intensity_raw'
            intensity = np.asarray(s.get(arr_key, np.array([])), dtype=float)
            if intensity.size == 0 and use_rw:
                intensity = np.asarray(s.get('intensity_raw', np.array([])), dtype=float)
            label = s.get('intensity_source', key)
            return wl, intensity, label, key
        # Backward-compatible fallback
        wl = np.asarray(data.get('wavelengths_Avantes', np.array([])), dtype=float)
        intensity = np.asarray(data.get('intensities_Avantes_rw' if use_rw else 'intensities_Avantes_raw', np.array([])), dtype=float)
        if intensity.size == 0 and use_rw:
            intensity = np.asarray(data.get('intensities_Avantes_raw', np.array([])), dtype=float)
        return wl, intensity, data.get('Avantes_intensity_source', 'spectrum'), data.get('default_spectrum_source', '')

    def get_selected_spectroscopy_rw_normalized_arrays(self, data):
        """Return selected-source wavelength and RW intensity normalized for matching."""
        wl, rw, label, key = self.get_selected_spectrum_arrays(data, use_rw=True)
        wl = np.asarray(wl, dtype=float)
        rw = np.asarray(rw, dtype=float)
        if wl.size == 0 or rw.size == 0 or wl.shape != rw.shape:
            return wl, rw, {
                "spectrum_source": label,
                "spectrum_source_key": key,
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
        rw_norm = rw / factor if factor and factor > 0 else rw
        return wl, rw_norm, {
            "spectrum_source": label,
            "spectrum_source_key": key,
            "spectrum_normalization_factor": factor,
            "plasma_duration_s_for_spectrum": duration_s,
            "Ip_integral_plasma_tau_positive_A_for_spectrum": ip_integral_tau_A,
            "Ip_integral_plasma_time_positive_C_for_spectrum": ip_integral_time_C,
        }

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
    def show_dataframe_window(
        self,
        df,
        title,
        default_filename_base="analysis",
        plot_callback=None,
        extra_excel_tables=None,
        extra_display_tables=None,
        sort_buttons=None
    ):
        """Show a DataFrame and export it as CSV or Excel.

        extra_excel_tables is optional and is only used when the user exports an
        Excel workbook. It can be:
            dict[str, DataFrame]
            list[tuple[str, DataFrame]]

        extra_display_tables optionally adds read-only DataFrame tabs to the
        same window.  The first tab is always the primary DataFrame and is named
        "Summary"; additional items use their supplied names (for example,
        "All data").

        sort_buttons is optional. Each item can be a dict with:
            label: button text
            columns: one column name or a list of column names
            ascending: True/False
            numeric: True/False

        This lets a compact table be shown/exported as the first sheet while
        keeping a complete diagnostic table in additional Excel sheets. If the
        user sorts the visible table before exporting, the exported summary
        keeps the same sorted order.
        """
        win = tk.Toplevel(self.app)
        win.title(title)
        win.geometry("1150x560")

        original_df = df.copy()
        current_df = {"df": df.copy()}
        original_extra_excel_tables = extra_excel_tables
        current_extra_excel_tables = {"tables": extra_excel_tables}

        notebook = None
        if extra_display_tables:
            notebook = ttk.Notebook(win)
            notebook.pack(fill=tk.BOTH, expand=True)
            frame = ttk.Frame(notebook)
            notebook.add(frame, text="Summary")
        else:
            frame = tk.Frame(win)
            frame.pack(fill=tk.BOTH, expand=True)

        table_frame = tk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        style = ttk.Style(win)
        style.configure(
            "ReadableTable.Treeview.Heading",
            font=("Roboto", 9, "bold"),
            padding=(4, 10, 4, 10),
            anchor="center"
        )
        style.configure("ReadableTable.Treeview", rowheight=24)

        tree = ttk.Treeview(table_frame, style="ReadableTable.Treeview")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = tk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        x_scroll = tk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        def _format_table_value(v):
            return f"{v:.6g}" if isinstance(v, (float, np.floating)) else v

        def _sorted_dataframe(input_df, columns, ascending=True, numeric=True):
            if input_df is None or input_df.empty:
                return input_df

            cols = list(columns) if isinstance(columns, (list, tuple)) else [columns]
            cols = [c for c in cols if c in input_df.columns]
            if not cols:
                return input_df

            work = input_df.copy()
            sort_key_cols = []
            for i, col in enumerate(cols):
                key_col = f"__sort_key_{i}__"
                if numeric:
                    work[key_col] = pd.to_numeric(work[col], errors="coerce")
                else:
                    work[key_col] = work[col].astype(str).str.lower()
                sort_key_cols.append(key_col)

            sorted_df = work.sort_values(
                by=sort_key_cols,
                ascending=[ascending] * len(sort_key_cols),
                na_position="last",
                kind="mergesort"
            ).drop(columns=sort_key_cols)

            return sorted_df.reset_index(drop=True)

        def _normalized_extra_excel_tables(source=None):
            source_tables = current_extra_excel_tables["tables"] if source is None else source
            if not source_tables:
                return []
            if isinstance(source_tables, dict):
                return list(source_tables.items())
            return list(source_tables)

        def _sort_extra_tables(columns, ascending=True, numeric=True):
            sorted_tables = []
            for sheet_name, table_df in _normalized_extra_excel_tables(original_extra_excel_tables):
                if isinstance(table_df, pd.DataFrame):
                    sorted_tables.append((sheet_name, _sorted_dataframe(table_df, columns, ascending, numeric)))
                else:
                    sorted_tables.append((sheet_name, table_df))
            return sorted_tables

        def _render_table(display_df):
            tree.delete(*tree.get_children())
            tree["columns"] = list(display_df.columns)
            tree["show"] = "headings"

            for col in display_df.columns:
                header_text = format_table_column_header(col, multiline=True)
                header_lines = header_text.split("\n")
                max_line_len = max([len(x) for x in header_lines] + [8])
                width = min(max(max_line_len * 10 + 24, 95), 185)
                tree.heading(
                    col,
                    text=header_text,
                    command=lambda c=col: _apply_sort(c, ascending=True, numeric=True)
                )
                tree.column(col, width=width, anchor="center")

            for _, row in display_df.iterrows():
                values = [_format_table_value(v) for v in row]
                tree.insert("", tk.END, values=values)

        def _apply_sort(columns, ascending=True, numeric=True):
            current_df["df"] = _sorted_dataframe(
                current_df["df"],
                columns=columns,
                ascending=ascending,
                numeric=numeric
            )
            current_extra_excel_tables["tables"] = _sort_extra_tables(
                columns=columns,
                ascending=ascending,
                numeric=numeric
            )
            _render_table(current_df["df"])

        def _reset_order():
            current_df["df"] = original_df.copy()
            current_extra_excel_tables["tables"] = original_extra_excel_tables
            _render_table(current_df["df"])

        _render_table(current_df["df"])

        # Additional GUI tabs are intentionally independent of the compact
        # Summary view: each exposes every diagnostic column and supports
        # click-to-sort without changing the primary export order.
        if notebook is not None:
            display_tables = (
                list(extra_display_tables.items())
                if isinstance(extra_display_tables, dict)
                else list(extra_display_tables)
            )
            for tab_name, tab_df in display_tables:
                if not isinstance(tab_df, pd.DataFrame):
                    continue
                tab = ttk.Frame(notebook)
                notebook.add(tab, text=str(tab_name))
                tab_table_frame = tk.Frame(tab)
                tab_table_frame.pack(fill=tk.BOTH, expand=True)
                tab_tree = ttk.Treeview(tab_table_frame, style="ReadableTable.Treeview")
                tab_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                tab_y_scroll = tk.Scrollbar(tab_table_frame, orient=tk.VERTICAL, command=tab_tree.yview)
                tab_y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                tab_x_scroll = tk.Scrollbar(tab, orient=tk.HORIZONTAL, command=tab_tree.xview)
                tab_x_scroll.pack(side=tk.BOTTOM, fill=tk.X)
                tab_tree.configure(yscrollcommand=tab_y_scroll.set, xscrollcommand=tab_x_scroll.set)

                tab_state = {"df": tab_df.copy()}

                def _render_extra_table(display_df, target_tree=tab_tree):
                    target_tree.delete(*target_tree.get_children())
                    target_tree["columns"] = list(display_df.columns)
                    target_tree["show"] = "headings"
                    for extra_col in display_df.columns:
                        header_text = format_table_column_header(extra_col, multiline=True)
                        header_lines = header_text.split("\n")
                        max_line_len = max([len(x) for x in header_lines] + [8])
                        width = min(max(max_line_len * 10 + 24, 95), 185)
                        target_tree.heading(extra_col, text=header_text)
                        target_tree.column(extra_col, width=width, anchor="center")
                    for _, extra_row in display_df.iterrows():
                        target_tree.insert(
                            "",
                            tk.END,
                            values=[_format_table_value(v) for v in extra_row]
                        )

                def _sort_extra_column(column, state=tab_state, target_tree=tab_tree):
                    state["df"] = _sorted_dataframe(
                        state["df"], columns=column, ascending=True, numeric=True
                    )
                    _render_extra_table(state["df"], target_tree=target_tree)

                _render_extra_table(tab_state["df"])
                for extra_col in tab_state["df"].columns:
                    tab_tree.heading(
                        extra_col,
                        command=lambda c=extra_col, sorter=_sort_extra_column: sorter(c)
                    )

        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=8)

        if sort_buttons:
            for option in sort_buttons:
                label = option.get("label", "Sort")
                columns = option.get("columns", option.get("column", []))
                ascending = bool(option.get("ascending", True))
                numeric = bool(option.get("numeric", True))
                tk.Button(
                    btn_frame,
                    text=label,
                    command=lambda c=columns, a=ascending, n=numeric: _apply_sort(c, a, n)
                ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                btn_frame,
                text="Original order",
                command=_reset_order
            ).pack(side=tk.LEFT, padx=5)

        def _export_to_path(path, force_excel=False):
            p = Path(path)
            extra_tables = _normalized_extra_excel_tables()
            wants_excel = force_excel or p.suffix.lower() == ".xlsx"

            if wants_excel and extra_tables:
                tables = [("summary", current_df["df"])] + extra_tables
                return save_workbook_with_openpyxl_fallback(path, tables)

            return save_dataframe_with_openpyxl_fallback(current_df["df"], path, index=False)

        def _show_export_message(saved_path, mode, excel_requested=False):
            if mode == "csv_fallback":
                messagebox.showinfo(
                    "Exported as CSV",
                    "openpyxl is not installed, so the Excel file could not be created.\n"
                    "The table was saved as CSV instead:\n"
                    f"{saved_path}"
                )
            elif mode == "csv_folder":
                messagebox.showinfo(
                    "Exported as CSV folder",
                    "openpyxl is not installed, so the Excel workbook could not be created.\n"
                    "Each Excel sheet was saved as a separate CSV file in this folder:\n"
                    f"{saved_path}"
                )
            elif excel_requested or mode == "xlsx":
                messagebox.showinfo("Exported", f"Excel file exported successfully:\n{saved_path}")
            else:
                messagebox.showinfo("Exported", f"Table exported successfully:\n{saved_path}")

        def export_df():
            path = filedialog.asksaveasfilename(
                initialfile=default_filename_base,
                defaultextension=".csv",
                filetypes=[("CSV", "*.csv"), ("Excel", "*.xlsx")]
            )
            if not path:
                return
            try:
                saved_path, mode = _export_to_path(path)
                _show_export_message(saved_path, mode, excel_requested=Path(path).suffix.lower() == ".xlsx")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(btn_frame, text="Export table", command=export_df).pack(side=tk.RIGHT, padx=5)

        def export_df_excel():
            path = filedialog.asksaveasfilename(
                initialfile=f"{default_filename_base}.xlsx",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")]
            )
            if not path:
                return
            try:
                saved_path, mode = _export_to_path(path, force_excel=True)
                _show_export_message(saved_path, mode, excel_requested=True)
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(btn_frame, text="Export Excel", command=export_df_excel).pack(side=tk.RIGHT, padx=5)

        if plot_callback is not None:
            def plot_from_table():
                try:
                    plot_callback(current_df["df"].copy())
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

    def show_important_data(self):
        """Show a compact summary table compatible with old and new shots."""
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")
        rows = []
        for d in self.processed_data:
            try:
                rows.append(compute_important_data_row(d))
            except Exception as e:
                rows.append({
                    'shot': d.get('shot_number', 'unknown'),
                    'error': f'{type(e).__name__}: {e}'
                })
        df = pd.DataFrame(rows)
        preferred = [
            'shot', 'gas', 'pressure_measured_mPa', 'pressure_requested_mPa',
            'CS_voltage_V', 'TF_voltage_V', 'CS_voltage_source', 'TF_voltage_source', 'I_max_kA', 'I_min_kA',
            'Bt_max_mT', 'Bt_min_mT', 'qa_min',
            'duration_preferred_my_method_ms', 'duration_Ip_only_ms', 'duration_MEPhIST_Halpha_method_ms',
            'Halpha_integral_my_Ip_window_positive', 'Halpha_mean_my_Ip_window', 'Halpha_duration_my_Ip_window_ms',
            'Halpha_integral_my_Halpha_window_positive', 'Halpha_mean_my_Halpha_window', 'Halpha_duration_my_Halpha_window_ms',
            'Halpha_integral_MEPhIST_window_positive', 'Halpha_mean_MEPhIST_window', 'Halpha_duration_MEPhIST_window_ms',
            'plasma_end_method_preferred', 'plasma_end_method_Ip_only', 'plasma_end_halpha_guard_used',
            'Ip_start_loop_edge_method', 'Ip_end_loop_edge_method',
            'Ip_start_ms', 'Ip_start_ms_Ip_only', 'Ip_start_loop_refined', 'Ip_start_loop_edge_score_V_per_ms',
            'Ip_end_ms_preferred', 'Ip_end_ms_before_loop_refinement', 'Ip_end_loop_refined', 'Ip_end_loop_edge_score_V_per_ms',
            'Ip_end_ms_Ip_only', 'Halpha_start_my_Halpha_window_ms',
            'Halpha_end_my_Halpha_window_ms', 'Halpha_official_start_ms', 'Halpha_official_end_ms',
            'CS_current_min_kA', 'CS_current_max_kA',
            'TF_current_min_kA', 'TF_current_max_kA', 'loader_mode',
            'spectrum_source', 'available_spectrum_sources', 'default_spectrum_source', 'missing_signals'
        ]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        self.show_dataframe_window(
            df[cols],
            title="Important data",
            default_filename_base="important_data"
        )

    def _get_voigt_emission_summary_by_shot(self):
        """Return spectroscopy-emission summaries by shot from the cached Voigt table.

        The compact shot-summary table should not re-run the Voigt analysis. It
        only summarizes the accepted/best Voigt fits already cached by the
        spectroscopy tool.  The Voigt area is a property of the experimental
        fitted peak; here it is summed by element only to build compact emission
        indicators for the discharge-summary table.
        """
        best = getattr(self, 'voigt_best_cache', None)
        if best is None or not isinstance(best, pd.DataFrame) or best.empty:
            return {}

        df = best.copy()
        if 'shot' not in df.columns or 'type of element' not in df.columns:
            return {}
        df['shot'] = df['shot'].astype(str)
        df['type of element'] = df['type of element'].apply(normalize_element_label)

        # Use Voigt area as the default emission-strength proxy. If unavailable,
        # fall back to the measured feature intensity or local integrated signal.
        for col in ['voigt_area', 'feature_local_integrated_intensity', 'feature_peak_intensity', 'voigt_peak_height']:
            if col not in df.columns:
                df[col] = np.nan
            df[col] = pd.to_numeric(df[col], errors='coerce')
        strength = df['voigt_area'].copy()
        strength = strength.where(np.isfinite(strength), df['feature_local_integrated_intensity'])
        strength = strength.where(np.isfinite(strength), df['feature_peak_intensity'])
        strength = strength.where(np.isfinite(strength), df['voigt_peak_height'])
        df['_emission_strength'] = strength.fillna(0.0)

        top_map = {}

        for shot, sdf in df.groupby('shot', sort=False):
            g = (sdf.groupby('type of element', dropna=False)
                   .agg(n_lines=('type of element', 'size'),
                        total_strength=('_emission_strength', 'sum'),
                        max_strength=('_emission_strength', 'max'))
                   .reset_index())
            if g.empty:
                continue

            g = g.sort_values(['total_strength', 'n_lines', 'max_strength'], ascending=[False, False, False])
            labels = []
            shot_summary = {}
            for rank in range(1, 5):
                if len(g) >= rank:
                    ranked = g.iloc[rank - 1]
                    element_name = str(ranked['type of element'])
                    total_strength = float(ranked['total_strength'])
                    n_lines = int(ranked['n_lines'])
                    labels.append(f"{element_name} (n={n_lines}, sum={total_strength:.3g})")
                else:
                    element_name = ''
                    total_strength = np.nan
                    n_lines = 0
                # The compact columns are deliberately rank-based.  Element
                # identities remain separate in All data so no H/W/Fe/Li label
                # is assumed before the spectroscopy analysis is reviewed.
                shot_summary[f'Top{rank}_element_Voigt_area_counts_nm'] = total_strength
                shot_summary[f'top{rank}_element_by_Voigt_area'] = element_name
                shot_summary[f'Top{rank}_element_Voigt_n_lines'] = n_lines

            shot_summary['top4_elements_by_Voigt_area'] = '; '.join(labels)
            top_map[str(shot)] = shot_summary

        return top_map

    def show_requested_discharge_summary(self):
        """Show the requested compact shot table with loop-voltage-refined times."""
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")

        top_elements_by_shot = self._get_voigt_emission_summary_by_shot()
        rows = []
        for d in self.processed_data:
            try:
                row = compute_requested_discharge_summary_row(d)
                shot_key = str(d.get('shot_number', ''))
                row.update(top_elements_by_shot.get(shot_key, {
                    'top4_elements_by_Voigt_area': '',
                    'top1_element_by_Voigt_area': '',
                    'top2_element_by_Voigt_area': '',
                    'top3_element_by_Voigt_area': '',
                    'top4_element_by_Voigt_area': '',
                    'Top1_element_Voigt_area_counts_nm': np.nan,
                    'Top2_element_Voigt_area_counts_nm': np.nan,
                    'Top3_element_Voigt_area_counts_nm': np.nan,
                    'Top4_element_Voigt_area_counts_nm': np.nan,
                    'Top1_element_Voigt_n_lines': 0,
                    'Top2_element_Voigt_n_lines': 0,
                    'Top3_element_Voigt_n_lines': 0,
                    'Top4_element_Voigt_n_lines': 0,
                }))
                rows.append(row)
            except Exception as e:
                rows.append({
                    'shot': d.get('shot_number', 'unknown'),
                    'error': f'{type(e).__name__}: {e}'
                })

        df_full = pd.DataFrame(rows)

        # Compact catalog layout.  After the vacuum pressure, diagnostics are
        # grouped as requested: Ip, H-alpha, maximum-time difference, integrals,
        # Bt, rank-based spectroscopy, and finally fast-valve settings.
        requested_cols = [
            'Pressure_group_mPa',
            'shot',
            'Plasma_gas',
            'CS_cap_Ip_V',
            'TF_cap_Bt_V',
            'Vacuum_total_pressure_mPa',

            # Ip
            'Representative_max_Ip_kA',
            'Ip_max_time_ms',
            'Ip_duration_window_ms',

            # H-alpha
            'H_alpha_duration_my_Halpha_window_ms',
            'Halpha_max_time_ms',
            'Halpha_start_minus_Ip_start_ms',

            # Difference between the two maxima
            'dt_Halpha_max_minus_Ip_max_ms',

            # Integrals
            'Ip_integral_Ip_window_C',
            'Halpha_integral_Ip_window',
            'Halpha_integral_over_Ip_integral_Ip_window',

            # Toroidal field
            'Bt_mean_during_plasma_mT',

            # Spectroscopy (generic rank, no assumed element identity)
            'Top1_element_Voigt_area_counts_nm',
            'Top2_element_Voigt_area_counts_nm',
            'Top3_element_Voigt_area_counts_nm',
            'Top4_element_Voigt_area_counts_nm',

            # Fast-valve program
            'FastValve_delay1_file_units',
            'FastValve_delay2_file_units',
            'FastValve_duration1_file_units',
            'FastValve_duration2_file_units',
            'FastValve_duration3_file_units',
        ]

        # Keep the requested order even if a column is temporarily unavailable
        # for a failed shot or for files without spectroscopy information.
        for col in requested_cols:
            if col not in df_full.columns:
                df_full[col] = np.nan

        df_summary = df_full[requested_cols].copy()
        remaining_cols = [col for col in df_full.columns if col not in requested_cols]
        df_all_data = df_full[requested_cols + remaining_cols].copy()

        if not top_elements_by_shot:
            messagebox.showinfo(
                "Spectroscopy summary",
                "No accepted Voigt spectroscopy table is currently cached.\n"
                "The top-element columns will be empty until you run the Voigt spectroscopy analysis."
            )

        self.show_dataframe_window(
            df_summary,
            title="Shot summary table",
            default_filename_base="shot_summary_table",
            extra_excel_tables=[("all_data", df_all_data)],
            extra_display_tables=[("All data", df_all_data)],
            sort_buttons=[{
                "label": "Sort by pressure ↑",
                "columns": ["Vacuum_total_pressure_mPa", "pWG_requested_mPa"],
                "ascending": True,
                "numeric": True,
            }]
        )

    def toggle_voigt_fit_overlay(self):
        """Toggle Voigt-fit overlay in the Spectrum sources plot."""
        self.voigt_fit_overlay_enabled = not bool(getattr(self, "voigt_fit_overlay_enabled", False))
        if hasattr(self, "voigt_overlay_button"):
            self.voigt_overlay_button.config(text="Voigt fits: ON" if self.voigt_fit_overlay_enabled else "Voigt fits: OFF")
        # The main plot is not changed; this affects the separate Spectrum sources window.

    def configure_voigt_overlay_limits(self):
        """Ask the user how many Voigt curves to plot per element.

        Syntax examples:
            default=4,H=6,Fe=8,W=4,O=3,N=3,Li=3
            5

        The limits are applied per shot and per element. If fewer fits exist,
        only the available fits are drawn.
        """
        current = str(getattr(self, 'voigt_overlay_limits_text', 'default=5,H=6,Fe=8,W=5,O=3,N=3,Li=3'))
        txt = simpledialog.askstring(
            "Voigt overlay limits",
            "Max curves per element for the Spectrum sources overlay.\n"
            "Use e.g. default=4,H=6,Fe=8,W=5,O=3,N=3,Li=3\n"
            "A single number like 5 also works.",
            initialvalue=current,
            parent=self.master_frame
        )
        if txt is not None:
            self.voigt_overlay_limits_text = txt.strip() or current

    def _parse_voigt_overlay_limits(self):
        """Return (default_limit, dict[element] = limit) for overlay plotting."""
        txt = str(getattr(self, 'voigt_overlay_limits_text', '')).strip()
        default = int(VOIGT_OVERLAY_DEFAULT_MAX_PER_ELEMENT)
        limits = {}
        if not txt:
            return default, limits
        # Allow a single integer.
        try:
            if re.fullmatch(r"\d+", txt):
                return max(int(txt), 0), limits
        except Exception:
            pass
        for part in re.split(r"[,;]", txt):
            part = part.strip()
            if not part or '=' not in part:
                continue
            k, v = part.split('=', 1)
            k = k.strip()
            try:
                n = max(int(float(v.strip())), 0)
            except Exception:
                continue
            if k.lower() in ['default', '*', 'all']:
                default = n
            else:
                limits[normalize_element_label(k)] = n
        return default, limits

    def _voigt_cache_key(self):
        shots = tuple(str(d.get('shot_number', '')) for d in self.processed_data)
        all_files = tuple(sorted(str(x.get('file', '')) for _, x in get_nist_file_options().iterrows() if str(x.get('file', '')).strip()))
        return (
            shots,
            all_files,
            str(getattr(self, 'spectrum_source_mode', 'Auto')),
            float(getattr(self, 'nist_match_tolerance_nm', NIST_MATCH_TOLERANCE_NM)),
            float(getattr(self, 'nist_min_relative_peak_height', NIST_MIN_RELATIVE_PEAK_HEIGHT)),
            float(getattr(self, 'nist_noise_sigma_factor', NIST_NOISE_SIGMA_FACTOR)),
            int(getattr(self, 'voigt_fit_top_n_per_element', VOIGT_FIT_TOP_N_PER_ELEMENT)),
            bool(getattr(self, 'spectroscopy_calibration_enabled', False)),
        )

    def _get_nist_dataframes_for_voigt(self):
        """Return NIST data grouped by element for the Voigt top-N workflow.

        Important: unlike the quick vertical-line overlay, the Voigt analysis
        computes against ALL available local emission-line tables. This avoids
        false ownership caused by the current GUI selection. For example, if
        only Fe and Li are selected in the quick filter, H, W, O, N, etc. are
        still available as competitors in the Voigt fit. The top-N stop rule is
        then applied per chemical element, not per file.
        """
        all_nist = self.get_all_nist_dataframes()
        if not all_nist:
            return []

        grouped = {}
        for element_label, file_name, df in all_nist:
            if df is None or len(df) == 0:
                continue
            element = normalize_element_label(element_label)
            if not element:
                element = normalize_element_label(guess_element_from_filename(file_name))
            if not element:
                element = str(element_label).strip() or str(file_name)

            tmp = df.copy()
            tmp['__source_file_for_voigt__'] = str(file_name)
            tmp['__element_label_for_voigt__'] = str(element_label)
            grouped.setdefault(element, []).append(tmp)

        loaded = []
        for element, frames in sorted(grouped.items(), key=lambda x: x[0]):
            try:
                combined = pd.concat(frames, ignore_index=True)
                combined = combined.dropna(subset=['lambda_nm']).copy()
                # Keep the most intense/first row when duplicated exactly across files.
                if 'lambda_nm' in combined.columns:
                    combined['_lambda_round_for_voigt'] = pd.to_numeric(combined['lambda_nm'], errors='coerce').round(5)
                    combined = combined.drop_duplicates(subset=['_lambda_round_for_voigt', '__source_file_for_voigt__'], keep='first')
                    combined = combined.drop(columns=['_lambda_round_for_voigt'], errors='ignore')
                loaded.append((element, f'{element}_all_local_NIST_files', combined.reset_index(drop=True)))
            except Exception as exc:
                print(f'Could not group Voigt NIST files for {element}: {exc}')
        return loaded


    def configure_voigt_fit_top_n_per_element(self):
        """Ask how many reliable Voigt-fitted lines to keep per element."""
        current = int(getattr(self, 'voigt_fit_top_n_per_element', VOIGT_FIT_TOP_N_PER_ELEMENT))
        value = simpledialog.askinteger(
            "Voigt top N per element",
            "How many reliable Voigt-fitted lines should be found per element?\n"
            "The Voigt workflow computes all available local NIST elements, then stops after N accepted lines per element.\n"
            "Rejected/ambiguous attempts are still saved in the candidate table.",
            initialvalue=current,
            minvalue=1,
            maxvalue=50,
            parent=self.master_frame.winfo_toplevel()
        )
        if value is None:
            return
        self.voigt_fit_top_n_per_element = int(value)
        self.voigt_best_cache = None
        self.voigt_candidate_cache = None
        self.voigt_cache_key = None
        if hasattr(self, 'status_label'):
            self.status_label.config(text=f"Voigt fit target: top {value} reliable lines per element")

    def run_quick_voigt_spectroscopy(self):
        """Run the fast Voigt top-N spectroscopy workflow and show the accepted table.

        This is the main-window shortcut. It always uses the current Spectrum
        source selector (Auto/Oceanfx/Avantes) and the automatic Voigt H-Balmer
        calibration, with H-alpha treated as the high-priority anchor when it is
        present. The detailed panel exposes the same analysis plus candidates,
        export, fit diagnostics and tuning parameters.
        """
        if not self.processed_data:
            return messagebox.showinfo('No data', 'Load one or more shots first.')
        if not self.get_all_nist_dataframes():
            return messagebox.showinfo('No NIST files', 'No local emission-line tables were found in the emission-line folder.')
        try:
            best, candidates = self.compute_voigt_spectroscopy_tables(force=True)
        except Exception as exc:
            traceback.print_exc()
            return messagebox.showerror('Quick Voigt spectroscopy error', f'{type(exc).__name__}: {exc}')
        if best is None or best.empty:
            n_cand = 0 if candidates is None else len(candidates)
            return messagebox.showinfo(
                'Quick spectroscopy',
                'The Voigt top-N analysis finished, but no accepted global-best lines were found.\n'
                f'Candidate/attempted fits saved: {n_cand}\n'
                'Open Detailed spectroscopy tools and inspect the candidate table or relax thresholds.'
            )
        best = self._order_voigt_best_columns(best)
        self.show_dataframe_window(
            best,
            title=f'Quick spectroscopy: accepted Voigt top {getattr(self, "voigt_fit_top_n_per_element", VOIGT_FIT_TOP_N_PER_ELEMENT)} lines/element',
            default_filename_base='quick_voigt_topN_accepted_lines'
        )

    def _preselect_voigt_lines_for_element(
        self,
        wl_fit_axis,
        y_raw,
        nist_df,
        element_label,
        source_file,
        top_n=None,
        allow_weak=False,
    ):
        """Preselect NIST lines to fit with Voigt for one element.

        This is a fast, non-fitting prefilter. It ranks NIST wavelengths by the
        local measured excess in the experimental spectrum and returns only a
        limited set of promising candidates. The expensive Voigt fits then run in
        this order and stop once top_n reliable lines have been found.
        """
        if top_n is None:
            top_n = int(getattr(self, 'voigt_fit_top_n_per_element', VOIGT_FIT_TOP_N_PER_ELEMENT))
        top_n = max(int(top_n), 1)
        max_attempts = max(
            VOIGT_FIT_PREFILTER_MIN_ATTEMPTS_PER_ELEMENT,
            int(top_n * VOIGT_FIT_PREFILTER_ATTEMPTS_PER_TARGET),
        )

        wl = np.asarray(wl_fit_axis, dtype=float)
        yy = np.asarray(y_raw, dtype=float)
        if wl.size < VOIGT_FIT_MIN_POINTS or yy.size != wl.size or nist_df is None or len(nist_df) == 0:
            return pd.DataFrame()

        finite = np.isfinite(wl) & np.isfinite(yy)
        wl = wl[finite]
        yy = yy[finite]
        if wl.size < VOIGT_FIT_MIN_POINTS:
            return pd.DataFrame()

        try:
            baseline, noise_sigma = robust_noise_level(yy)
        except Exception:
            baseline = float(np.nanpercentile(yy, 20)) if yy.size else 0.0
            noise_sigma = float(np.nanstd(yy[:min(200, yy.size)])) if yy.size else 0.0
        y_max = float(np.nanmax(yy)) if yy.size else np.nan
        global_threshold = max(
            baseline + VOIGT_FIT_NOISE_SIGMA_FACTOR * noise_sigma,
            VOIGT_FIT_MIN_RELATIVE_HEIGHT * y_max if np.isfinite(y_max) else -np.inf,
        )

        rows = []
        wl_min = float(np.nanmin(wl))
        wl_max = float(np.nanmax(wl))
        for idx, line in nist_df.iterrows():
            try:
                lam = float(line.get('lambda_nm', np.nan))
            except Exception:
                continue
            if not np.isfinite(lam) or lam < wl_min - 6.0 or lam > wl_max + 6.0:
                continue

            elem, ion, spectrum_label = extract_ionization_state(element_label, line, source_file)
            elem = elem or normalize_element_label(element_label)
            balmer_info = get_hydrogen_balmer_match(lam) if elem == 'H' else None
            is_balmer = bool(balmer_info)

            half_width = max(float(getattr(self, 'nist_match_tolerance_nm', NIST_MATCH_TOLERANCE_NM)), 0.6)
            if is_balmer:
                half_width = max(half_width, SPECTROSCOPY_BALMER_MATCH_TOLERANCE_NM)
                if balmer_info and balmer_info[0] == 'H_alpha':
                    half_width = max(half_width, 1.2)

            local_mask = (wl >= lam - half_width) & (wl <= lam + half_width)
            if np.sum(local_mask) < 2:
                continue
            lx = wl[local_mask]
            ly = yy[local_mask]
            if ly.size == 0:
                continue
            peak_i = int(np.nanargmax(ly))
            local_peak = float(ly[peak_i])
            local_peak_wl = float(lx[peak_i])
            local_bg = float(np.nanpercentile(ly, 15))
            local_excess = max(local_peak - local_bg, 0.0)
            if local_peak < global_threshold and not is_balmer and not allow_weak:
                continue
            local_pos = np.maximum(ly - local_bg, 0.0)
            local_integral = float(trapz_compat(local_pos, lx)) if lx.size >= 2 else local_excess
            distance_to_local_peak = abs(local_peak_wl - lam)
            proximity = max(0.0, 1.0 - distance_to_local_peak / max(half_width, 1e-9))
            # This score is only for deciding which expensive fits to attempt.
            # The final Voigt tables are ranked later by the actual fit results.
            pre_score = local_excess * (0.35 + 0.65 * proximity)
            if is_balmer:
                pre_score += max(local_excess, np.nanmax(yy) * 0.02 if yy.size else 0.0) * 2.0
            peak_bin = int(np.round(local_peak_wl / max(VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM, 1e-6)))
            rows.append({
                '__nist_index__': idx,
                'prefit_score': pre_score,
                'prefit_local_peak': local_peak,
                'prefit_local_background': local_bg,
                'prefit_local_excess': local_excess,
                'prefit_local_integrated_intensity': local_integral,
                'prefit_peak_wavelength_nm': local_peak_wl,
                'prefit_distance_peak_to_nist_nm': distance_to_local_peak,
                'prefit_proximity_score': proximity,
                'prefit_peak_bin': peak_bin,
                'prefit_is_hydrogen_balmer': is_balmer,
                'prefit_hydrogen_balmer_name': balmer_info[0] if balmer_info else '',
            })

        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df = df.sort_values(['prefit_is_hydrogen_balmer', 'prefit_score', 'prefit_local_excess'], ascending=[False, False, False])
        # Avoid spending all fits on several NIST alternatives for the same
        # experimental spike. The non-kept alternatives can still appear in the
        # later candidate table when they are reached through another feature.
        df = df.drop_duplicates(subset=['prefit_peak_bin'], keep='first')
        df = df.head(max_attempts).copy()
        df['prefit_rank_for_element'] = np.arange(1, len(df) + 1)
        return df

    def _quick_spectroscopy_cache_key(self):
        """Cache key for the fast top-N spectroscopy summary."""
        shots = tuple(str(d.get('shot_number', '')) for d in self.processed_data)
        # The quick top-N candidate table intentionally uses all local elements
        # so physically plausible competitors such as H/Fe/W/N/O/Li are not
        # hidden merely because the visual overlay selection is incomplete.
        selected = ('__all_local_nist_files__',)
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
            selected,
            str(getattr(self, 'spectrum_source_mode', 'Auto')),
            float(getattr(self, 'nist_match_tolerance_nm', NIST_MATCH_TOLERANCE_NM)),
            float(getattr(self, 'nist_min_relative_peak_height', NIST_MIN_RELATIVE_PEAK_HEIGHT)),
            float(getattr(self, 'nist_noise_sigma_factor', NIST_NOISE_SIGMA_FACTOR)),
            int(getattr(self, 'quick_spectroscopy_top_n', 3)),
            calibration_key,
        )

    def _attach_ionization_to_match_rows(self, matched, nist_df, element_label, source_file):
        """Add ionization_state/spectrum_label to a matched-line dataframe."""
        if matched is None or matched.empty:
            return matched
        out = matched.copy()
        ions = []
        labels = []
        elems = []
        nist_lambda = pd.to_numeric(nist_df.get('lambda_nm', pd.Series([], dtype=float)), errors='coerce')
        for _, row in out.iterrows():
            line_row = None
            try:
                lam = float(row.get('wavelength', np.nan))
                if nist_lambda.size and np.isfinite(lam):
                    idx = (nist_lambda - lam).abs().idxmin()
                    if pd.notna(idx):
                        line_row = nist_df.loc[idx]
            except Exception:
                line_row = None
            elem, ion, spectrum_label = extract_ionization_state(element_label, line_row, source_file)
            elems.append(elem or normalize_element_label(element_label))
            ions.append(ion or 'unknown')
            labels.append(spectrum_label or (elem or normalize_element_label(element_label)))
        out['type of element'] = elems
        out['ionization_state'] = ions
        out['spectrum_label'] = labels
        return out

    def compute_quick_top3_spectroscopy_table(self, force=False, top_n=None):
        """Fast non-Voigt top-N lines per selected element and shot.

        This uses the existing centroid/window matcher and returns only the
        strongest measured lines for each selected element. It is much faster
        than fitting Voigt profiles for all NIST candidates and is intended as a
        first-pass diagnostic table.
        """
        if top_n is None:
            top_n = int(getattr(self, 'quick_spectroscopy_top_n', 3))
        else:
            top_n = int(top_n)
        top_n = max(top_n, 1)
        self.quick_spectroscopy_top_n = top_n

        cache_key = self._quick_spectroscopy_cache_key()
        if (not force and self.quick_spectroscopy_cache is not None
                and self.quick_spectroscopy_cache_key == cache_key):
            return self.quick_spectroscopy_cache.copy()

        if not self.processed_data:
            return pd.DataFrame()

        # Use all local NIST files for this quick table. The file-selection
        # tree in the quick window only controls the visual vertical-line overlay.
        # This avoids missing Li, W, N, O, etc. when they were not manually selected.
        selected = self.get_all_nist_dataframes()

        rows = []
        for shot_order, data in enumerate(self.processed_data):
            wl_raw_for_match, _, _ = self.get_selected_spectroscopy_rw_normalized_arrays(data)
            wl, intensity_norm, spec_meta = self.get_matching_spectrum_arrays(data)
            shot = data.get('shot_number', '')
            if len(wl) == 0 or len(intensity_norm) == 0:
                continue

            shot_rows = []
            for element_label, file_name, nist_df in selected:
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
                if matched is None or matched.empty:
                    continue
                matched = self._attach_ionization_to_match_rows(matched, nist_df, element_label, file_name)
                matched['source_file'] = file_name
                matched['shot_order'] = shot_order
                matched['spectrum_source'] = spec_meta.get('spectrum_source', '')
                matched['wavelength_calibration'] = spec_meta.get('wavelength_calibration', 'none')
                shot_rows.append(matched)

            if not shot_rows:
                continue
            sdf = pd.concat(shot_rows, ignore_index=True)
            # Keep one line per element and experimental feature first, so one
            # broad peak does not create many duplicated top entries for the same
            # element. Within a feature, prefer proximity, then local excess.
            if 'experimental_feature_id' in sdf.columns:
                sdf = sdf.sort_values(['type of element', 'experimental_feature_id', 'proximity_score', 'local_excess'], ascending=[True, True, False, False])
                sdf = sdf.drop_duplicates(subset=['type of element', 'experimental_feature_id'], keep='first')
            sdf['quick_rank_metric'] = pd.to_numeric(sdf.get('local_excess', sdf.get('intensity', 0)), errors='coerce').fillna(0.0)
            # H Balmer rows are kept if present, but ranking per element remains
            # based on measured intensity. This table does not decide global
            # ownership between elements; it is a quick per-element view.
            sdf = sdf.sort_values(['type of element', 'quick_rank_metric', 'proximity_score'], ascending=[True, False, False])
            sdf['quick_rank_for_element'] = sdf.groupby('type of element').cumcount() + 1
            sdf = sdf[sdf['quick_rank_for_element'] <= top_n].copy()
            rows.append(sdf)

        if not rows:
            df = pd.DataFrame()
        else:
            df = pd.concat(rows, ignore_index=True)
            preferred = [
                'shot', 'type of element', 'ionization_state', 'spectrum_label', 'quick_rank_for_element',
                'wavelength', 'experimental_raw_wavelength_nm', 'experimental_calibrated_wavelength_nm',
                'experimental_wavelength_nm', 'delta_nm', 'intensity', 'local_excess', 'local_integrated_intensity',
                'relative_intensity_in_shot', 'proximity_score', 'match_tolerance_used_nm',
                'hydrogen_balmer_name', 'is_hydrogen_balmer', 'source_file', 'spectrum_source', 'wavelength_calibration',
                'experimental_feature_id', 'feature_center_nm', 'feature_width_nm', 'feature_n_points'
            ]
            cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
            df = df[cols].sort_values(['shot', 'type of element', 'quick_rank_for_element']).reset_index(drop=True)

        self.quick_spectroscopy_cache = df.copy()
        self.quick_spectroscopy_cache_key = cache_key
        return df

    def show_quick_top3_spectroscopy_table(self):
        """Show the fast top-N candidate lines per element using all local NIST files."""
        if not self.processed_data:
            return messagebox.showinfo('No data', 'Load one or more shots first.')
        # The quick top-N table uses all local NIST files by default. Manual
        # selection only controls the quick vertical-line overlay on the main plot.
        try:
            df = self.compute_quick_top3_spectroscopy_table(force=True, top_n=getattr(self, 'quick_spectroscopy_top_n', 3))
        except Exception as exc:
            traceback.print_exc()
            return messagebox.showerror('Quick spectroscopy error', f'{type(exc).__name__}: {exc}')
        if df.empty:
            return messagebox.showinfo(
                'Quick spectroscopy',
                'No quick matches were found. Try selecting files, increasing tolerance, or lowering the relative threshold.'
            )
        self.show_dataframe_window(
            df,
            title=f'Quick top {getattr(self, "quick_spectroscopy_top_n", 3)} lines per element',
            default_filename_base='quick_top_lines_per_element'
        )

    def compute_voigt_spectroscopy_tables(self, force=False):
        """Compute Voigt-fit best and candidate spectroscopy tables.

        The fit is performed on raw counts from the selected spectrum source.
        Saturated points are treated with a censored residual. The accepted/best
        table contains one line per instrument-resolution band; the candidate
        table keeps all fitted NIST alternatives.
        """
        cache_key = self._voigt_cache_key()
        if (not force and self.voigt_best_cache is not None and self.voigt_candidate_cache is not None and self.voigt_cache_key == cache_key):
            return self.voigt_best_cache.copy(), self.voigt_candidate_cache.copy()

        nist_sets = self._get_nist_dataframes_for_voigt()
        if not self.processed_data or not nist_sets:
            best = pd.DataFrame()
            cand = pd.DataFrame()
            self.voigt_best_cache, self.voigt_candidate_cache, self.voigt_cache_key = best, cand, cache_key
            return best, cand

        candidate_rows = []
        for shot_order, data in enumerate(self.processed_data):
            shot = data.get('shot_number', '')
            wl_raw, y_raw, source_label, source_key = self.get_selected_spectrum_arrays(data, use_rw=False)
            wl_raw = np.asarray(wl_raw, dtype=float)
            y_raw = np.asarray(y_raw, dtype=float)
            if wl_raw.size < VOIGT_FIT_MIN_POINTS or wl_raw.shape != y_raw.shape:
                continue
            finite = np.isfinite(wl_raw) & np.isfinite(y_raw)
            wl_raw = wl_raw[finite]
            y_raw = y_raw[finite]
            if wl_raw.size < VOIGT_FIT_MIN_POINTS:
                continue
            order = np.argsort(wl_raw)
            wl_raw = wl_raw[order]
            y_raw = y_raw[order]

            voigt_calibration_df, voigt_calibration_coeffs = estimate_voigt_hydrogen_wavelength_calibration(wl_raw, y_raw)
            if voigt_calibration_coeffs is not None:
                wl_fit_axis = apply_wavelength_calibration(wl_raw, voigt_calibration_coeffs)
                voigt_calibration_label = f"Voigt H Balmer wavelength calibration degree {min(2, len(voigt_calibration_coeffs)-1)}"
            else:
                wl_fit_axis = wl_raw.copy()
                voigt_calibration_label = "none"
            wl_min = float(np.nanmin(wl_fit_axis))
            wl_max = float(np.nanmax(wl_fit_axis))
            baseline, noise_sigma = robust_noise_level(y_raw)
            y_max = float(np.nanmax(y_raw)) if y_raw.size else np.nan

            # Raw <-> calibrated approximate mapping for reporting. If no calibration
            # is enabled, both axes are identical.
            cal_order = np.argsort(wl_fit_axis)
            wl_cal_sorted = wl_fit_axis[cal_order]
            wl_raw_sorted = wl_raw[cal_order]

            rows_this_shot = []
            top_n_per_element = max(int(getattr(self, 'voigt_fit_top_n_per_element', VOIGT_FIT_TOP_N_PER_ELEMENT)), 1)
            for element_label, file_name, nist_df in nist_sets:
                if nist_df is None or len(nist_df) == 0:
                    continue
                source_file = str(file_name)
                lambda_source = str(nist_df['lambda_source'].iloc[0]) if 'lambda_source' in nist_df.columns and len(nist_df) else ''

                prefit_lines = self._preselect_voigt_lines_for_element(
                    wl_fit_axis,
                    y_raw,
                    nist_df,
                    element_label,
                    source_file,
                    top_n=top_n_per_element,
                )
                if prefit_lines is None or prefit_lines.empty:
                    continue

                accepted_centers_for_element = []
                for _, prefit_row in prefit_lines.iterrows():
                    try:
                        line = nist_df.loc[prefit_row.get('__nist_index__')]
                    except Exception:
                        continue
                    try:
                        lam_nist = float(line.get('lambda_nm', np.nan))
                    except Exception:
                        continue
                    if not np.isfinite(lam_nist) or lam_nist < wl_min - 6.0 or lam_nist > wl_max + 6.0:
                        continue
                    source_file_line = str(line.get('__source_file_for_voigt__', line.get('source_file', source_file)))
                    element_label_line = str(line.get('__element_label_for_voigt__', element_label))
                    lambda_source_line = str(line.get('lambda_source', lambda_source))
                    elem, ion, spectrum_label = extract_ionization_state(element_label_line, line, source_file_line)
                    balmer_info = get_hydrogen_balmer_match(lam_nist) if elem == 'H' else None
                    line_name = balmer_info[0] if balmer_info else spectrum_label
                    is_balmer = bool(balmer_info)

                    # Wider window for H-alpha if the local data show clipping; this is
                    # the line most likely to be saturated in MEPhIST spectra.
                    window = VOIGT_FIT_BALMER_WINDOW_NM if is_balmer else VOIGT_FIT_DEFAULT_WINDOW_NM
                    if is_balmer and balmer_info[0] == 'H_alpha':
                        rough_mask = (wl_fit_axis >= lam_nist - VOIGT_FIT_SATURATED_BALMER_WINDOW_NM) & (wl_fit_axis <= lam_nist + VOIGT_FIT_SATURATED_BALMER_WINDOW_NM)
                        if np.any(rough_mask):
                            sm, _, _ = detect_saturation_mask(y_raw[rough_mask])
                            if np.any(sm):
                                window = VOIGT_FIT_SATURATED_BALMER_WINDOW_NM

                    local_mask = (wl_fit_axis >= lam_nist - window) & (wl_fit_axis <= lam_nist + window)
                    if np.sum(local_mask) < VOIGT_FIT_MIN_POINTS:
                        continue
                    local_y = y_raw[local_mask]
                    if local_y.size == 0:
                        continue
                    local_peak = float(np.nanmax(local_y))
                    local_bg = float(np.nanpercentile(local_y, 15))
                    if local_peak < max(baseline + VOIGT_FIT_NOISE_SIGMA_FACTOR * noise_sigma, VOIGT_FIT_MIN_RELATIVE_HEIGHT * y_max):
                        continue
                    if local_peak - local_bg < max(VOIGT_FIT_NOISE_SIGMA_FACTOR * noise_sigma, 0.003 * max(y_max, 1.0)):
                        continue

                    force_sat = bool(is_balmer and balmer_info and balmer_info[0] == 'H_alpha')
                    fit = fit_single_voigt_candidate(
                        wl_fit_axis,
                        y_raw,
                        lambda_nist_nm=lam_nist,
                        element_label=elem,
                        line_name=line_name,
                        ionization_state=ion,
                        window_nm=window,
                        force_saturated_reference=force_sat,
                    )
                    if fit is None:
                        continue

                    center_cal = float(fit['lambda_fit_nm'])
                    if wl_cal_sorted.size >= 2:
                        center_raw = float(np.interp(center_cal, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan))
                    else:
                        center_raw = center_cal

                    # The fit is performed on the calibrated wavelength axis,
                    # because candidate matching is done against NIST. The raw
                    # Spectrum sources plot, however, is drawn with the original
                    # spectrometer wavelength array. Convert the fitted x-axis
                    # back to raw coordinates for visually aligned overlays.
                    x_fit_cal = np.asarray(json.loads(fit.get('x_fit_nm_json', '[]')), dtype=float)
                    if x_fit_cal.size and wl_cal_sorted.size >= 2:
                        x_fit_raw = np.interp(x_fit_cal, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)
                    else:
                        x_fit_raw = x_fit_cal.copy()

                    delta = center_cal - lam_nist
                    proximity = max(0.0, 1.0 - abs(delta) / max(VOIGT_FIT_CENTER_TOLERANCE_NM, 1e-9))
                    prior = get_element_prior_score(elem)
                    area = float(fit.get('voigt_area', np.nan))
                    fit_quality = float(fit.get('fit_quality_score', 0.0))
                    saturated = bool(fit.get('is_saturated', False))
                    fwhm_val = float(fit.get('voigt_fwhm_nm', np.nan))
                    max_fwhm_allowed = VOIGT_FIT_MAX_SATURATED_BALMER_FWHM_NM if (saturated and is_balmer) else VOIGT_FIT_MAX_FWHM_NM
                    voigt_quality_ok = (
                        np.isfinite(delta)
                        and abs(delta) <= VOIGT_FIT_CENTER_TOLERANCE_NM
                        and np.isfinite(fwhm_val)
                        and fwhm_val <= max_fwhm_allowed
                        and fit_quality >= VOIGT_FIT_MIN_QUALITY_ACCEPTED
                    )
                    balmer_boost = SPECTROSCOPY_BALMER_PRIORITY_BOOST if is_balmer else 0.0
                    saturation_penalty = 0.10 if (saturated and not is_balmer) else 0.0
                    # H Balmer is treated as a physically expected anchor for H shots.
                    # The boost does not delete Fe/W/O alternatives; it prevents them
                    # from stealing the main row when they share the same fitted feature.
                    score = 1.70 * proximity + 0.55 * fit_quality + 0.18 * prior + balmer_boost - saturation_penalty

                    nist_intensity = ''
                    nist_intensity_numeric = np.nan
                    for c in ['intens', 'Intensity', 'Rel.', 'rel_intensity']:
                        if c in nist_df.columns:
                            nist_intensity = clean_nist_cell(line.get(c, ''))
                            nist_intensity_numeric = nist_cell_to_float(nist_intensity)
                            break

                    row = {
                        'shot': shot,
                        'shot_order': shot_order,
                        'spectrum_source': source_label,
                        'spectrum_source_key': source_key,
                        'voigt_wavelength_calibration': voigt_calibration_label,
                        'voigt_calibration_n_anchors': int(len(voigt_calibration_df)) if voigt_calibration_df is not None else 0,
                        'type of element': elem,
                        'ionization_state': ion,
                        'spectrum_label': spectrum_label,
                        'line_name': line_name,
                        'wavelength': lam_nist,
                        'lambda_nist_nm': lam_nist,
                        'lambda_fit_calibrated_nm': center_cal,
                        'lambda_fit_raw_nm': center_raw,
                        'experimental_calibrated_wavelength_nm': center_cal,
                        'experimental_raw_wavelength_nm': center_raw,
                        'delta_nm': delta,
                        'voigt_area': area,
                        'voigt_peak_height': fit.get('voigt_peak_height', np.nan),
                        'voigt_fwhm_nm': fit.get('voigt_fwhm_nm', np.nan),
                        'voigt_sigma_nm': fit.get('voigt_sigma_nm', np.nan),
                        'voigt_gamma_nm': fit.get('voigt_gamma_nm', np.nan),
                        'voigt_background_b0': fit.get('voigt_background_b0', np.nan),
                        'voigt_background_b1': fit.get('voigt_background_b1', np.nan),
                        'voigt_x_ref_nm': fit.get('voigt_x_ref_nm', np.nan),
                        'fit_window_start_nm': fit.get('fit_window_start_nm', np.nan),
                        'fit_window_end_nm': fit.get('fit_window_end_nm', np.nan),
                        'fit_window_half_width_nm': fit.get('fit_window_half_width_nm', np.nan),
                        'fit_rmse': fit.get('fit_rmse', np.nan),
                        'fit_reduced_chi2': fit.get('fit_reduced_chi2', np.nan),
                        'fit_quality_score': fit_quality,
                        'candidate_score': score,
                        'proximity_score': proximity,
                        'voigt_quality_ok': bool(voigt_quality_ok),
                        'voigt_quality_reject_reason': '' if voigt_quality_ok else (
                            'large_delta' if abs(delta) > VOIGT_FIT_CENTER_TOLERANCE_NM else
                            'large_fwhm' if (np.isfinite(fwhm_val) and fwhm_val > max_fwhm_allowed) else
                            'low_quality'
                        ),
                        'element_prior_score': prior,
                        'is_hydrogen_balmer': is_balmer,
                        'hydrogen_balmer_name': balmer_info[0] if balmer_info else '',
                        'is_saturated': saturated,
                        'n_saturated_points': fit.get('n_saturated_points', 0),
                        'saturation_level_estimated': fit.get('saturation_level_estimated', np.nan),
                        'saturation_reason': fit.get('saturation_reason', ''),
                        'fit_saturation_method': fit.get('fit_saturation_method', ''),
                        'area_reliability': fit.get('area_reliability', ''),
                        'intensity_reliable': fit.get('intensity_reliable', True),
                        'source_file': source_file_line,
                        'wavelength_source': lambda_source_line,
                        'nist_relative_intensity': nist_intensity,
                        'nist_relative_intensity_numeric': nist_intensity_numeric,
                        'voigt_fit_top_n_per_element': top_n_per_element,
                        'prefit_rank_for_element': prefit_row.get('prefit_rank_for_element', np.nan),
                        'prefit_score': prefit_row.get('prefit_score', np.nan),
                        'prefit_local_peak': prefit_row.get('prefit_local_peak', np.nan),
                        'prefit_local_background': prefit_row.get('prefit_local_background', np.nan),
                        'prefit_local_excess': prefit_row.get('prefit_local_excess', np.nan),
                        'prefit_local_integrated_intensity': prefit_row.get('prefit_local_integrated_intensity', np.nan),
                        'prefit_peak_wavelength_nm': prefit_row.get('prefit_peak_wavelength_nm', np.nan),
                        'prefit_distance_peak_to_nist_nm': prefit_row.get('prefit_distance_peak_to_nist_nm', np.nan),
                        'x_fit_nm_json': fit.get('x_fit_nm_json', '[]'),
                        'x_fit_raw_nm_json': json.dumps([float(v) if np.isfinite(v) else None for v in x_fit_raw]),
                        'y_fit_model_json': fit.get('y_fit_model_json', '[]'),
                        'y_fit_component_json': fit.get('y_fit_component_json', '[]'),
                    }
                    rows_this_shot.append(row)

                    # Stop fitting this element once enough reliable, separated
                    # Voigt lines have been found. Rejected fits attempted before
                    # this point remain saved in rows_this_shot/candidate table.
                    if bool(voigt_quality_ok):
                        count_this_line = True
                        for acc_center in accepted_centers_for_element:
                            if np.isfinite(lam_nist) and np.isfinite(acc_center) and abs(lam_nist - acc_center) <= VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM:
                                count_this_line = False
                                break
                        if count_this_line:
                            accepted_centers_for_element.append(float(lam_nist))
                        if len(accepted_centers_for_element) >= top_n_per_element:
                            break

            if not rows_this_shot:
                continue
            shot_df = pd.DataFrame(rows_this_shot)
            # Normalize area inside shot for final ranking support.
            shot_df['voigt_area_norm_in_shot'] = normalize_01(shot_df['voigt_area'])
            shot_df['voigt_peak_height_norm_in_shot'] = normalize_01(shot_df.get('voigt_peak_height', 0.0))
            shot_df['candidate_score'] = pd.to_numeric(shot_df['candidate_score'], errors='coerce').fillna(0.0) + 0.10 * shot_df['voigt_peak_height_norm_in_shot']

            # Rank metric for the final best table. Use peak height and fit
            # quality rather than raw Voigt area alone, because a broad false
            # fit can have a huge area without being visually dominant. H Balmer
            # saturated lines keep a boost because their top can be clipped.
            _peak = pd.to_numeric(shot_df.get('voigt_peak_height', 0.0), errors='coerce').fillna(0.0)
            _area = pd.to_numeric(shot_df.get('voigt_area', 0.0), errors='coerce').fillna(0.0)
            _qual = pd.to_numeric(shot_df.get('fit_quality_score', 0.0), errors='coerce').fillna(0.0).clip(lower=0.0, upper=1.0)
            _prox = pd.to_numeric(shot_df.get('proximity_score', 0.0), errors='coerce').fillna(0.0).clip(lower=0.0, upper=1.0)
            _balmer = shot_df.get('is_hydrogen_balmer', False).astype(bool)
            _sat = shot_df.get('is_saturated', False).astype(bool)
            shot_df['voigt_rank_metric'] = (_peak * (0.25 + 0.75 * _qual) * (0.25 + 0.75 * _prox))
            shot_df.loc[_balmer & _sat, 'voigt_rank_metric'] = np.maximum(
                shot_df.loc[_balmer & _sat, 'voigt_rank_metric'],
                0.25 * _area.loc[_balmer & _sat] * (0.2 + 0.8 * _prox.loc[_balmer & _sat])
            )

            # Approximate feature grouping by fitted center and instrument resolution.
            shot_df = shot_df.sort_values(['lambda_fit_calibrated_nm']).reset_index(drop=True)
            feature_ids = []
            current_feature = -1
            last_center = None
            for center in shot_df['lambda_fit_calibrated_nm'].to_numpy(dtype=float):
                if last_center is None or abs(center - last_center) > VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM:
                    current_feature += 1
                    last_center = center
                feature_ids.append(current_feature)
            shot_df['voigt_feature_id'] = feature_ids

            shot_df = shot_df.sort_values(['voigt_feature_id', 'candidate_score', 'voigt_area'], ascending=[True, False, False])
            shot_df['candidate_rank_for_feature'] = shot_df.groupby('voigt_feature_id').cumcount() + 1
            candidate_rows.append(shot_df)

        if not candidate_rows:
            best = pd.DataFrame()
            cand = pd.DataFrame()
            self.voigt_best_cache, self.voigt_candidate_cache, self.voigt_cache_key = best, cand, cache_key
            return best, cand

        candidates = pd.concat(candidate_rows, ignore_index=True)
        candidates['is_global_best'] = False
        candidates['is_suppressed_by_exclusion_window'] = False
        candidates['suppression_reason'] = ''
        candidates['suppressed_by_element'] = ''
        candidates['suppressed_by_wavelength_nm'] = np.nan

        best_rows = []
        for shot, sdf in candidates.groupby('shot', sort=False):
            sdf = sdf.copy()

            # First choose one representative per fitted experimental feature.
            # If the feature contains a hydrogen Balmer candidate, keep that H
            # assignment as the representative. This reflects the fact that H
            # Balmer emission is expected and should not be overwritten by a
            # nearby dense Fe line in the same fitted structure. Alternatives
            # remain available in the candidate table.
            representative_indices = []
            candidates.loc[sdf.index, 'is_feature_representative'] = False
            candidates.loc[sdf.index, 'feature_representative_reason'] = ''
            for feature_id, g in sdf.groupby('voigt_feature_id', sort=True):
                if 'voigt_quality_ok' in g.columns:
                    g_quality = g[g['voigt_quality_ok'].astype(bool)].copy()
                else:
                    g_quality = g.copy()
                # Very poor fits remain in the candidate table but are not used
                # for the clean global ranking. This avoids false high-area lines
                # such as Li/Fe being ranked first when the curve is not credible.
                if g_quality.empty:
                    continue
                h = g_quality[g_quality['is_hydrogen_balmer'].astype(bool)]
                if not h.empty:
                    chosen_idx = h.sort_values(['candidate_score', 'voigt_rank_metric'], ascending=[False, False]).index[0]
                    reason = 'H_balmer_priority_within_feature'
                else:
                    chosen_idx = g_quality.sort_values(['candidate_score', 'voigt_rank_metric'], ascending=[False, False]).index[0]
                    reason = 'best_score_within_feature'
                representative_indices.append(chosen_idx)
                candidates.loc[chosen_idx, 'is_feature_representative'] = True
                candidates.loc[chosen_idx, 'feature_representative_reason'] = reason

            reps = candidates.loc[representative_indices].copy() if representative_indices else pd.DataFrame()
            if reps.empty:
                continue

            reps['__is_h_anchor'] = reps['is_hydrogen_balmer'].astype(bool)
            reps = reps.sort_values(['__is_h_anchor', 'candidate_score', 'voigt_area'], ascending=[False, False, False])

            accepted = []
            for idx, row in reps.iterrows():
                # Use NIST wavelength for the final instrumental-resolution
                # exclusion. The plot uses raw/calibrated fit centers, but final
                # ownership should block physically close tabulated lines, so Hα
                # is not stolen by a nearby Fe/Li/O candidate in the same band.
                center = float(row.get('lambda_nist_nm', row.get('lambda_fit_calibrated_nm', np.nan)))
                blocked = None
                for acc in accepted:
                    acc_center = float(acc.get('lambda_nist_nm', acc.get('lambda_fit_calibrated_nm', np.nan)))
                    if np.isfinite(center) and np.isfinite(acc_center) and abs(center - acc_center) <= VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM:
                        blocked = acc
                        break
                if blocked is None:
                    accepted.append(row.to_dict())
                    candidates.loc[idx, 'is_global_best'] = True
                else:
                    candidates.loc[idx, 'is_suppressed_by_exclusion_window'] = True
                    candidates.loc[idx, 'suppression_reason'] = 'within_voigt_fitted_resolution_band'
                    candidates.loc[idx, 'suppressed_by_element'] = blocked.get('type of element', '')
                    candidates.loc[idx, 'suppressed_by_wavelength_nm'] = blocked.get('lambda_nist_nm', np.nan)

            if accepted:
                bdf = pd.DataFrame(accepted)
                if '__is_h_anchor' in bdf.columns:
                    bdf = bdf.drop(columns=['__is_h_anchor'])
                if 'voigt_rank_metric' not in bdf.columns:
                    bdf['voigt_rank_metric'] = pd.to_numeric(bdf.get('voigt_peak_height', bdf.get('voigt_area', 0.0)), errors='coerce').fillna(0.0)
                bdf = bdf.sort_values('voigt_rank_metric', ascending=False).reset_index(drop=True)
                bdf['rank_in_shot'] = np.arange(1, len(bdf) + 1)
                best_rows.append(bdf)

        best = pd.concat(best_rows, ignore_index=True) if best_rows else pd.DataFrame()

        if not best.empty:
            best['rank_in_shot'] = pd.to_numeric(best['rank_in_shot'], errors='coerce')
            best['global_rank_in_shot'] = best['rank_in_shot']
            # Per-element rank is useful for the partial top-N Voigt workflow:
            # it estimates the strongest fitted lines of each selected element.
            if 'voigt_rank_metric' in best.columns:
                best['voigt_rank_for_element'] = (
                    best.groupby(['shot', 'type of element'])['voigt_rank_metric']
                    .rank(method='first', ascending=False)
                    .astype(int)
                )
            else:
                best['voigt_rank_for_element'] = (
                    best.groupby(['shot', 'type of element']).cumcount() + 1
                )
            best = best.sort_values(['shot_order', 'rank_in_shot']).reset_index(drop=True)

        if not candidates.empty:
            # Map each candidate feature to the global rank of the accepted/best
            # line representing that feature. Non-accepted features are left as NaN
            # instead of 0 so they are not confused with a valid global rank.
            if not best.empty and 'voigt_feature_id' in best.columns:
                rank_map = {
                    (str(r.get('shot', '')), int(r.get('voigt_feature_id'))): r.get('rank_in_shot', np.nan)
                    for _, r in best.iterrows()
                    if pd.notna(r.get('voigt_feature_id', np.nan))
                }
                candidates['global_rank_in_shot'] = [
                    rank_map.get((str(r.get('shot', '')), int(r.get('voigt_feature_id'))) if pd.notna(r.get('voigt_feature_id', np.nan)) else ('', -1), np.nan)
                    for _, r in candidates.iterrows()
                ]
            else:
                candidates['global_rank_in_shot'] = np.nan

            # Feature rank is a pure experimental-feature ordering within a shot.
            # It is useful in the candidate table even when the feature is not
            # accepted as a final global line.
            if 'feature_rank_in_shot' not in candidates.columns:
                candidates['feature_rank_in_shot'] = (
                    candidates.groupby('shot', sort=False)['voigt_feature_id']
                    .rank(method='dense')
                    .astype(float)
                )

            if 'voigt_rank_metric' in candidates.columns:
                candidates['voigt_candidate_rank_for_element'] = (
                    candidates.groupby(['shot', 'type of element'])['voigt_rank_metric']
                    .rank(method='first', ascending=False)
                    .astype(int)
                )

            candidates = candidates.sort_values(
                ['shot_order', 'global_rank_in_shot', 'feature_rank_in_shot', 'candidate_rank_for_feature'],
                na_position='last'
            ).reset_index(drop=True)

        self.voigt_best_cache = best
        self.voigt_candidate_cache = candidates
        self.voigt_cache_key = cache_key
        return best.copy(), candidates.copy()

    def fit_voigt_spectroscopy_gui(self):
        """Toolbar callback for the Voigt spectroscopy analysis."""
        if not self.processed_data:
            return messagebox.showinfo('No data', 'Load one or more shots first.')
        if not self.get_all_nist_dataframes():
            return messagebox.showinfo('No NIST files', 'No local emission-line tables were found.')
        # The Voigt top-N workflow intentionally computes all available local
        # NIST elements, regardless of the quick-filter selection. This gives a
        # more honest global competition among H/Fe/W/N/O/Li/etc., while still
        # stopping after N accepted lines per element.
        try:
            best, candidates = self.compute_voigt_spectroscopy_tables(force=True)
        except Exception as exc:
            traceback.print_exc()
            return messagebox.showerror('Voigt spectroscopy error', f'{type(exc).__name__}: {exc}')
        n_best = 0 if best is None else len(best)
        n_cand = 0 if candidates is None else len(candidates)
        messagebox.showinfo(
            'Voigt spectroscopy',
            f'Voigt top-N analysis completed using all available local NIST elements.\n'
            f'Target per element: {getattr(self, "voigt_fit_top_n_per_element", VOIGT_FIT_TOP_N_PER_ELEMENT)}\n'
            f'Best global fits: {n_best}\nCandidate/attempted fits: {n_cand}'
        )


    def _detect_exhaustive_voigt_features(self, wl_calibrated, intensity, n_features):
        """Detect the strongest experimental spectral features for exhaustive Voigt ownership.

        This is different from the per-element workflow.  Here the measured
        spectrum decides which peaks/features matter first.  Then every local
        NIST element competes for each of those experimental features.
        """
        wl = np.asarray(wl_calibrated, dtype=float)
        y = np.asarray(intensity, dtype=float)
        n_features = int(max(1, n_features))
        if wl.size != y.size or wl.size < 5:
            return []

        finite = np.isfinite(wl) & np.isfinite(y)
        wl = wl[finite]
        y = y[finite]
        if wl.size < 5:
            return []
        order = np.argsort(wl)
        wl = wl[order]
        y = y[order]

        baseline, noise_sigma = robust_noise_level(y)
        y_max = float(np.nanmax(y)) if y.size else np.nan
        if not np.isfinite(y_max):
            return []

        # Use a light smoothing only for peak finding.  The actual fit is still
        # performed on the raw counts.
        if savgol_filter is not None and len(y) >= 9:
            win = 9 if len(y) > 9 else (len(y) // 2) * 2 + 1
            try:
                y_s = savgol_filter(y, win, 2)
            except Exception:
                y_s = y.copy()
        else:
            y_s = smooth_signal_time(wl, y, window_us=0)

        min_peak = max(
            baseline + VOIGT_FIT_NOISE_SIGMA_FACTOR * noise_sigma,
            VOIGT_FIT_MIN_RELATIVE_HEIGHT * y_max,
        )

        # Local maxima.  Keep endpoints out to avoid edge artifacts.
        local_max = np.zeros_like(y_s, dtype=bool)
        local_max[1:-1] = (y_s[1:-1] >= y_s[:-2]) & (y_s[1:-1] >= y_s[2:]) & (y_s[1:-1] > min_peak)
        idxs = np.where(local_max)[0]
        if idxs.size == 0:
            # Fallback: use the strongest samples after threshold, still grouped
            # by instrumental resolution.
            idxs = np.where(y > min_peak)[0]
        if idxs.size == 0:
            return []

        # Build peak candidates with local integrated intensity around the peak.
        peak_rows = []
        half_width = max(float(VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM), 0.60)
        for idx in idxs:
            c = float(wl[idx])
            local = (wl >= c - half_width) & (wl <= c + half_width)
            if np.sum(local) < 2:
                continue
            yy = y[local]
            xx = wl[local]
            local_bg = float(np.nanpercentile(yy, 15))
            local_excess = float(max(y[idx] - local_bg, 0.0))
            local_area = float(safe_area(xx, positive_part(yy - local_bg)))
            # Estimate an experimental feature interval around the peak.
            # This is intentionally wider than the 0.5--0.6 nm instrumental
            # exclusion width: broad/saturated/blended peaks must be fitted over
            # the whole measured structure, not only over the NIST-centered half
            # window.
            thr = local_bg + max(0.08 * local_excess, 2.0 * noise_sigma)
            left = int(idx)
            while left > 0 and y_s[left] > thr:
                left -= 1
            right = int(idx)
            while right < len(y_s) - 1 and y_s[right] > thr:
                right += 1
            # Guard against extremely narrow or extremely wide intervals.
            feature_start = float(max(wl[left], c - 0.75))
            feature_end = float(min(wl[right], c + 3.50))
            if feature_end - feature_start < 0.90:
                feature_start = float(c - 0.75)
                feature_end = float(c + 0.75)
            peak_rows.append({
                'idx': int(idx),
                'center_calibrated_nm': c,
                'feature_start_nm': feature_start,
                'feature_end_nm': feature_end,
                'feature_width_nm': float(feature_end - feature_start),
                'peak_intensity': float(y[idx]),
                'local_background': local_bg,
                'local_excess': local_excess,
                'local_integrated_intensity': local_area,
            })

        if not peak_rows:
            return []

        # Sort by measured peak intensity/excess and merge peaks within the
        # instrument resolution.  This makes one experimental feature per peak
        # complex instead of one point per detector sample.
        peak_rows = sorted(peak_rows, key=lambda r: (r['local_excess'], r['peak_intensity']), reverse=True)
        accepted = []
        for row in peak_rows:
            c = row['center_calibrated_nm']
            if any(abs(c - a['center_calibrated_nm']) <= half_width for a in accepted):
                continue
            row = dict(row)
            row['feature_rank_by_intensity'] = len(accepted) + 1
            row['feature_id'] = len(accepted)
            accepted.append(row)
            if len(accepted) >= n_features:
                break
        return accepted

    def _flatten_nist_rows_for_exhaustive_voigt(self):
        """Return one dataframe with all local NIST rows and element metadata."""
        frames = []
        for element_label, file_name, nist_df in self._get_nist_dataframes_for_voigt():
            if nist_df is None or len(nist_df) == 0:
                continue
            tmp = nist_df.copy()
            tmp['__voigt_group_element__'] = str(element_label)
            tmp['__voigt_group_file__'] = str(file_name)
            frames.append(tmp)
        if not frames:
            return pd.DataFrame()
        out = pd.concat(frames, ignore_index=True)
        out['lambda_nm'] = pd.to_numeric(out.get('lambda_nm', np.nan), errors='coerce')
        out = out.dropna(subset=['lambda_nm']).reset_index(drop=True)
        return out

    def compute_exhaustive_topN_voigt_tables(self, n_lines=None, force=True):
        """Feature-based exhaustive Voigt analysis of the N strongest measured lines.

        Workflow:
          1) Calibrate wavelength with H Balmer Voigt anchors.
          2) Detect the N strongest experimental spectral features in raw counts.
          3) For each feature, test all local NIST candidates in the calibrated
             wavelength neighborhood.
          4) Keep exactly one best NIST owner per feature in the best table and
             store all tested alternatives in the candidate table.

        This is the mode intended for: "give me the best NIST assignment for the
        N most intense measured lines".
        """
        if n_lines is None:
            n_lines = int(max(1, getattr(self, 'voigt_full_important_line_count', VOIGT_FIT_IMPORTANT_LINES_DEFAULT)))
        n_lines = int(max(1, n_lines))

        nist_all = self._flatten_nist_rows_for_exhaustive_voigt()
        if nist_all.empty or not self.processed_data:
            self.voigt_best_cache = pd.DataFrame()
            self.voigt_candidate_cache = pd.DataFrame()
            self.voigt_cache_key = self._voigt_cache_key()
            return self.voigt_best_cache.copy(), self.voigt_candidate_cache.copy()

        best_rows = []
        cand_rows = []

        for shot_order, data in enumerate(self.processed_data):
            shot = data.get('shot_number', '')
            wl_raw, y_raw, source_label, source_key = self.get_selected_spectrum_arrays(data, use_rw=False)
            wl_raw = np.asarray(wl_raw, dtype=float)
            y_raw = np.asarray(y_raw, dtype=float)
            if wl_raw.size < VOIGT_FIT_MIN_POINTS or wl_raw.shape != y_raw.shape:
                continue
            finite = np.isfinite(wl_raw) & np.isfinite(y_raw)
            wl_raw = wl_raw[finite]
            y_raw = y_raw[finite]
            if wl_raw.size < VOIGT_FIT_MIN_POINTS:
                continue
            order = np.argsort(wl_raw)
            wl_raw = wl_raw[order]
            y_raw = y_raw[order]

            voigt_calibration_df, voigt_calibration_coeffs = estimate_voigt_hydrogen_wavelength_calibration(wl_raw, y_raw)
            if voigt_calibration_coeffs is not None:
                wl_fit_axis = apply_wavelength_calibration(wl_raw, voigt_calibration_coeffs)
                voigt_calibration_label = f"Voigt H Balmer wavelength calibration degree {min(2, len(voigt_calibration_coeffs)-1)}"
            else:
                wl_fit_axis = wl_raw.copy()
                voigt_calibration_label = "none"

            cal_order = np.argsort(wl_fit_axis)
            wl_cal_sorted = wl_fit_axis[cal_order]
            wl_raw_sorted = wl_raw[cal_order]
            wl_min = float(np.nanmin(wl_fit_axis))
            wl_max = float(np.nanmax(wl_fit_axis))

            features = self._detect_exhaustive_voigt_features(wl_fit_axis, y_raw, n_lines)
            if not features:
                continue

            for feature in features:
                feature_center = float(feature['center_calibrated_nm'])
                rank_by_intensity = int(feature['feature_rank_by_intensity'])

                # Search in calibrated wavelength space.  Start close to the
                # instrumental resolution and expand once so the mode returns a
                # candidate whenever the local NIST database supports it.
                search_radii = [max(VOIGT_FIT_CENTER_TOLERANCE_NM, 0.85), 1.25, 2.00]
                possible = pd.DataFrame()
                for radius in search_radii:
                    possible = nist_all[
                        (pd.to_numeric(nist_all['lambda_nm'], errors='coerce') >= feature_center - radius) &
                        (pd.to_numeric(nist_all['lambda_nm'], errors='coerce') <= feature_center + radius)
                    ].copy()
                    if not possible.empty:
                        possible['__search_radius_nm__'] = radius
                        break
                # Always append diagnostic coating-element candidates such as Li near the measured
                # feature.  These candidates compete normally if their fit is good, and even if
                # they do not win they remain available for dashed/x diagnostic overlays.
                # This prevents Li from disappearing just because Fe/W/H has denser or stronger
                # NIST tables around the same experimental feature.
                try:
                    diagnostic_elements = {normalize_element_label(e) for e in VOIGT_ALWAYS_DIAGNOSTIC_ELEMENTS}
                    _, _overlay_limits = self._parse_voigt_overlay_limits()
                    diagnostic_elements.update(
                        normalize_element_label(k) for k, v in _overlay_limits.items()
                        if normalize_element_label(k) in {normalize_element_label(e) for e in VOIGT_ALWAYS_DIAGNOSTIC_ELEMENTS}
                        and int(v) > 0
                    )
                    diag_frames = []
                    for _elem_diag in diagnostic_elements:
                        if not _elem_diag:
                            continue
                        _elem_series = nist_all.get('__voigt_group_element__', pd.Series('', index=nist_all.index)).map(normalize_element_label)
                        _elem_mask = _elem_series.eq(_elem_diag)
                        _lam_all = pd.to_numeric(nist_all.get('lambda_nm', np.nan), errors='coerce')
                        _diag = nist_all[_elem_mask & (_lam_all >= feature_center - VOIGT_DIAGNOSTIC_ELEMENT_RADIUS_NM) & (_lam_all <= feature_center + VOIGT_DIAGNOSTIC_ELEMENT_RADIUS_NM)].copy()
                        if _diag.empty:
                            continue
                        _diag['__distance_to_feature__'] = np.abs(pd.to_numeric(_diag['lambda_nm'], errors='coerce') - feature_center)
                        if 'nist_relative_intensity_numeric' not in _diag.columns:
                            _diag['nist_relative_intensity_numeric'] = np.nan
                        _diag['__rel_for_sort__'] = pd.to_numeric(_diag.get('nist_relative_intensity_numeric', np.nan), errors='coerce').fillna(0.0)
                        _diag['__search_radius_nm__'] = VOIGT_DIAGNOSTIC_ELEMENT_RADIUS_NM
                        _diag['__forced_exhaustive_diagnostic_element__'] = True
                        _diag = _diag.sort_values(['__distance_to_feature__', '__rel_for_sort__'], ascending=[True, False]).head(VOIGT_DIAGNOSTIC_CANDIDATES_PER_ELEMENT_PER_FEATURE)
                        diag_frames.append(_diag)
                    if diag_frames:
                        _diag_all = pd.concat(diag_frames, ignore_index=True)
                        if possible.empty:
                            possible = _diag_all.copy()
                        else:
                            possible['__forced_exhaustive_diagnostic_element__'] = False
                            possible = pd.concat([possible, _diag_all], ignore_index=True)
                        possible = possible.drop_duplicates(subset=['__voigt_group_element__', '__voigt_group_file__', 'lambda_nm'], keep='last')
                except Exception:
                    pass

                if possible.empty:
                    # Keep a diagnostic unresolved row so the user knows that the
                    # measured line was strong but no local NIST candidate was available.
                    unresolved = {
                        'shot': shot,
                        'shot_order': shot_order,
                        'spectrum_source': source_label,
                        'spectrum_source_key': source_key,
                        'voigt_wavelength_calibration': voigt_calibration_label,
                        'voigt_calibration_n_anchors': int(len(voigt_calibration_df)) if voigt_calibration_df is not None else 0,
                        'type of element': 'unassigned',
                        'ionization_state': 'unknown',
                        'spectrum_label': 'unassigned',
                        'line_name': 'no_local_NIST_candidate',
                        'lambda_nist_nm': np.nan,
                        'wavelength': np.nan,
                        'lambda_fit_calibrated_nm': feature_center,
                        'lambda_fit_raw_nm': float(np.interp(feature_center, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)) if wl_cal_sorted.size >= 2 else feature_center,
                        'experimental_calibrated_wavelength_nm': feature_center,
                        'experimental_raw_wavelength_nm': float(np.interp(feature_center, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)) if wl_cal_sorted.size >= 2 else feature_center,
                        'delta_nm': np.nan,
                        'voigt_area': np.nan,
                        'voigt_peak_height': feature.get('peak_intensity', np.nan),
                        'voigt_rank_metric': feature.get('local_excess', feature.get('peak_intensity', 0.0)),
                        'candidate_score': 0.0,
                        'fit_quality_score': 0.0,
                        'voigt_quality_ok': False,
                        'voigt_quality_reject_reason': 'no_local_NIST_candidate_in_search_window',
                        'is_global_best': True,
                        'global_rank_in_shot': rank_by_intensity,
                        'rank_in_shot': rank_by_intensity,
                        'voigt_feature_id': int(feature['feature_id']),
                        'feature_rank_in_shot': rank_by_intensity,
                        'feature_rank_by_intensity': rank_by_intensity,
                        'feature_center_calibrated_nm': feature_center,
                        'feature_peak_intensity': feature.get('peak_intensity', np.nan),
                        'feature_local_excess': feature.get('local_excess', np.nan),
                        'feature_local_integrated_intensity': feature.get('local_integrated_intensity', np.nan),
                        'candidate_rank_for_feature': 1,
                        'analysis_mode': 'exhaustive_topN_measured_features',
                    }
                    best_rows.append(unresolved)
                    cand_rows.append(unresolved.copy())
                    continue

                possible['__distance_to_feature__'] = np.abs(pd.to_numeric(possible['lambda_nm'], errors='coerce') - feature_center)
                # Do not try hundreds of essentially equivalent weak lines around
                # a very dense element.  Keep the nearest/strongest local NIST
                # candidates; the feature-based nature is preserved because every
                # element still competes inside this feature.
                if 'nist_relative_intensity_numeric' not in possible.columns:
                    rel_vals = []
                    for _, rr in possible.iterrows():
                        val = np.nan
                        for c in ['intens', 'Intensity', 'Rel.', 'rel_intensity']:
                            if c in possible.columns:
                                val = nist_cell_to_float(clean_nist_cell(rr.get(c, '')))
                                break
                        rel_vals.append(val)
                    possible['nist_relative_intensity_numeric'] = rel_vals
                possible['__rel_for_sort__'] = pd.to_numeric(possible.get('nist_relative_intensity_numeric', np.nan), errors='coerce').fillna(0.0)
                if '__forced_exhaustive_diagnostic_element__' not in possible.columns:
                    possible['__forced_exhaustive_diagnostic_element__'] = False
                _forced_possible = possible[possible['__forced_exhaustive_diagnostic_element__'].fillna(False).astype(bool)].copy()
                _regular_possible = possible[~possible['__forced_exhaustive_diagnostic_element__'].fillna(False).astype(bool)].copy()
                _regular_possible = _regular_possible.sort_values(['__distance_to_feature__', '__rel_for_sort__'], ascending=[True, False]).head(80)
                _forced_possible = _forced_possible.sort_values(['__distance_to_feature__', '__rel_for_sort__'], ascending=[True, False])
                possible = pd.concat([_regular_possible, _forced_possible], ignore_index=True).drop_duplicates(subset=['__voigt_group_element__', '__voigt_group_file__', 'lambda_nm'], keep='last')

                feature_candidate_indices = []
                for cand_rank, (_, line) in enumerate(possible.iterrows(), start=1):
                    lam_nist = float(line.get('lambda_nm', np.nan))
                    if not np.isfinite(lam_nist) or lam_nist < wl_min - 6.0 or lam_nist > wl_max + 6.0:
                        continue
                    source_file_line = str(line.get('__source_file_for_voigt__', line.get('source_file', line.get('__voigt_group_file__', ''))))
                    element_label_line = str(line.get('__element_label_for_voigt__', line.get('__voigt_group_element__', '')))
                    lambda_source_line = str(line.get('lambda_source', ''))
                    elem, ion, spectrum_label = extract_ionization_state(element_label_line, line, source_file_line)
                    balmer_info = get_hydrogen_balmer_match(lam_nist) if elem == 'H' else None
                    line_name = balmer_info[0] if balmer_info else spectrum_label
                    is_balmer = bool(balmer_info)

                    window = VOIGT_FIT_BALMER_WINDOW_NM if is_balmer else VOIGT_FIT_DEFAULT_WINDOW_NM
                    if is_balmer and balmer_info[0] == 'H_alpha':
                        window = VOIGT_FIT_SATURATED_BALMER_WINDOW_NM
                    # Ensure the local fit window covers the FULL detected experimental
                    # feature, not only a small interval around the NIST wavelength.
                    # This prevents diagnostic alternatives such as Li from being
                    # drawn as a half-Voigt when the Li NIST line lies on one side of
                    # a broad unresolved peak.
                    feature_start = float(feature.get('feature_start_nm', feature_center - 0.75))
                    feature_end = float(feature.get('feature_end_nm', feature_center + 0.75))
                    required_half_window = max(abs(lam_nist - feature_start), abs(lam_nist - feature_end)) + 0.20
                    window = max(window, abs(lam_nist - feature_center) + 0.75, required_half_window)

                    force_sat = bool(is_balmer and balmer_info and balmer_info[0] == 'H_alpha')
                    fit = fit_single_voigt_candidate(
                        wl_fit_axis,
                        y_raw,
                        lambda_nist_nm=lam_nist,
                        element_label=elem,
                        line_name=line_name,
                        ionization_state=ion,
                        window_nm=window,
                        force_saturated_reference=force_sat,
                    )
                    if fit is None:
                        continue

                    center_cal = float(fit['lambda_fit_nm'])
                    center_raw = float(np.interp(center_cal, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)) if wl_cal_sorted.size >= 2 else center_cal
                    x_fit_cal = np.asarray(json.loads(fit.get('x_fit_nm_json', '[]')), dtype=float)
                    if x_fit_cal.size and wl_cal_sorted.size >= 2:
                        x_fit_raw = np.interp(x_fit_cal, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)
                    else:
                        x_fit_raw = x_fit_cal.copy()

                    delta = center_cal - lam_nist
                    feature_delta = center_cal - feature_center
                    proximity = max(0.0, 1.0 - abs(delta) / max(VOIGT_FIT_CENTER_TOLERANCE_NM, 1e-9))
                    feature_proximity = max(0.0, 1.0 - abs(feature_delta) / max(VOIGT_FIT_EXCLUSION_HALF_WIDTH_NM, 1e-9))
                    prior = get_element_prior_score(elem)
                    fit_quality = float(fit.get('fit_quality_score', 0.0))
                    fwhm_val = float(fit.get('voigt_fwhm_nm', np.nan))
                    saturated = bool(fit.get('is_saturated', False))
                    max_fwhm_allowed = VOIGT_FIT_MAX_SATURATED_BALMER_FWHM_NM if (saturated and is_balmer) else VOIGT_FIT_MAX_FWHM_NM
                    voigt_quality_ok = (
                        np.isfinite(delta)
                        and abs(delta) <= max(VOIGT_FIT_CENTER_TOLERANCE_NM, float(line.get('__search_radius_nm__', VOIGT_FIT_CENTER_TOLERANCE_NM)))
                        and np.isfinite(fwhm_val)
                        and fwhm_val <= max_fwhm_allowed
                        and fit_quality >= VOIGT_FIT_MIN_QUALITY_ACCEPTED
                    )
                    balmer_boost = SPECTROSCOPY_BALMER_PRIORITY_BOOST if is_balmer else 0.0
                    saturation_penalty = 0.10 if (saturated and not is_balmer) else 0.0
                    # Carbon is kept as a possible contaminant, but it should not
                    # dominate a feature unless it is clearly better than Fe/W/H/N/O.
                    low_prior_contaminant_penalty = 0.48 if elem == 'C' else 0.0
                    peak_height = float(fit.get('voigt_peak_height', np.nan))
                    area = float(fit.get('voigt_area', np.nan))
                    rank_metric = peak_height * (0.25 + 0.75 * fit_quality) * (0.30 + 0.70 * proximity)
                    if is_balmer and saturated and np.isfinite(area):
                        rank_metric = max(rank_metric, 0.20 * area * (0.30 + 0.70 * proximity))
                    score = (
                        1.55 * proximity
                        + 0.75 * fit_quality
                        + 0.55 * feature_proximity
                        + 0.15 * prior
                        + balmer_boost
                        - saturation_penalty
                        - low_prior_contaminant_penalty
                    )

                    nist_intensity, nist_intensity_numeric, nist_intensity_source = nist_strength_from_row(line)

                    row = {
                        'shot': shot,
                        'shot_order': shot_order,
                        'spectrum_source': source_label,
                        'spectrum_source_key': source_key,
                        'voigt_wavelength_calibration': voigt_calibration_label,
                        'voigt_calibration_n_anchors': int(len(voigt_calibration_df)) if voigt_calibration_df is not None else 0,
                        'type of element': elem,
                        'ionization_state': ion,
                        'spectrum_label': spectrum_label,
                        'line_name': line_name,
                        'wavelength': lam_nist,
                        'lambda_nist_nm': lam_nist,
                        'lambda_fit_calibrated_nm': center_cal,
                        'lambda_fit_raw_nm': center_raw,
                        'experimental_calibrated_wavelength_nm': center_cal,
                        'experimental_raw_wavelength_nm': center_raw,
                        'delta_nm': delta,
                        'delta_fit_minus_feature_nm': feature_delta,
                        'voigt_area': area,
                        'voigt_peak_height': peak_height,
                        'voigt_fwhm_nm': fit.get('voigt_fwhm_nm', np.nan),
                        'voigt_sigma_nm': fit.get('voigt_sigma_nm', np.nan),
                        'voigt_gamma_nm': fit.get('voigt_gamma_nm', np.nan),
                        'voigt_background_b0': fit.get('voigt_background_b0', np.nan),
                        'voigt_background_b1': fit.get('voigt_background_b1', np.nan),
                        'voigt_x_ref_nm': fit.get('voigt_x_ref_nm', np.nan),
                        'fit_window_start_nm': fit.get('fit_window_start_nm', np.nan),
                        'fit_window_end_nm': fit.get('fit_window_end_nm', np.nan),
                        'fit_window_half_width_nm': fit.get('fit_window_half_width_nm', np.nan),
                        'fit_rmse': fit.get('fit_rmse', np.nan),
                        'fit_reduced_chi2': fit.get('fit_reduced_chi2', np.nan),
                        'fit_quality_score': fit_quality,
                        'candidate_score': score,
                        'proximity_score': proximity,
                        'feature_proximity_score': feature_proximity,
                        'voigt_quality_ok': bool(voigt_quality_ok),
                        'voigt_quality_reject_reason': '' if voigt_quality_ok else (
                            'large_delta' if abs(delta) > max(VOIGT_FIT_CENTER_TOLERANCE_NM, float(line.get('__search_radius_nm__', VOIGT_FIT_CENTER_TOLERANCE_NM))) else
                            'large_fwhm' if (np.isfinite(fwhm_val) and fwhm_val > max_fwhm_allowed) else
                            'low_quality'
                        ),
                        'element_prior_score': prior,
                        'is_hydrogen_balmer': is_balmer,
                        'hydrogen_balmer_name': balmer_info[0] if balmer_info else '',
                        'is_saturated': saturated,
                        'n_saturated_points': fit.get('n_saturated_points', 0),
                        'saturation_level_estimated': fit.get('saturation_level_estimated', np.nan),
                        'saturation_reason': fit.get('saturation_reason', ''),
                        'fit_saturation_method': fit.get('fit_saturation_method', ''),
                        'area_reliability': fit.get('area_reliability', ''),
                        'intensity_reliable': fit.get('intensity_reliable', True),
                        'source_file': source_file_line,
                        'wavelength_source': lambda_source_line,
                        'nist_relative_intensity': nist_intensity,
                        'nist_relative_intensity_numeric': nist_intensity_numeric,
                        'nist_intensity_source': nist_intensity_source,
                        'voigt_rank_metric': rank_metric,
                        'voigt_feature_id': int(feature['feature_id']),
                        'feature_rank_in_shot': rank_by_intensity,
                        'feature_rank_by_intensity': rank_by_intensity,
                        'feature_center_calibrated_nm': feature_center,
                        'feature_peak_intensity': feature.get('peak_intensity', np.nan),
                        'feature_local_background': feature.get('local_background', np.nan),
                        'feature_local_excess': feature.get('local_excess', np.nan),
                        'feature_local_integrated_intensity': feature.get('local_integrated_intensity', np.nan),
                        'feature_start_nm': feature.get('feature_start_nm', np.nan),
                        'feature_end_nm': feature.get('feature_end_nm', np.nan),
                        'feature_width_nm': feature.get('feature_width_nm', np.nan),
                        'candidate_rank_for_feature': cand_rank,
                        'analysis_mode': 'exhaustive_topN_measured_features',
                        'is_forced_diagnostic_element_candidate': bool(line.get('__forced_exhaustive_diagnostic_element__', False)),
                        'diagnostic_element_reason': 'required_element_near_feature' if bool(line.get('__forced_exhaustive_diagnostic_element__', False)) else '',
                        'x_fit_nm_json': fit.get('x_fit_nm_json', '[]'),
                        'x_fit_raw_nm_json': json.dumps([float(v) if np.isfinite(v) else None for v in x_fit_raw]),
                        'y_fit_model_json': fit.get('y_fit_model_json', '[]'),
                        'y_fit_component_json': fit.get('y_fit_component_json', '[]'),
                    }
                    cand_rows.append(row)
                    feature_candidate_indices.append(len(cand_rows) - 1)

                if not feature_candidate_indices:
                    continue

                # Pick the best candidate for THIS experimental feature.  H
                # Balmer receives priority only within the same feature; all other
                # elements remain in the candidate table.
                feature_df = pd.DataFrame([cand_rows[i] for i in feature_candidate_indices])
                quality = feature_df[feature_df['voigt_quality_ok'].astype(bool)].copy()
                pool = quality if not quality.empty else feature_df.copy()
                h_pool = pool[pool['is_hydrogen_balmer'].astype(bool)]
                if not h_pool.empty:
                    chosen = h_pool.sort_values(['candidate_score', 'voigt_rank_metric'], ascending=[False, False]).iloc[0].to_dict()
                    chosen_reason = 'H_balmer_priority_within_measured_feature'
                else:
                    chosen = pool.sort_values(['candidate_score', 'voigt_rank_metric'], ascending=[False, False]).iloc[0].to_dict()
                    chosen_reason = 'best_voigt_candidate_for_measured_feature'

                # Candidate ranks for this feature.
                feature_df = feature_df.sort_values(['candidate_score', 'voigt_rank_metric'], ascending=[False, False]).reset_index(drop=True)
                for rank0, (_, rr) in enumerate(feature_df.iterrows(), start=1):
                    # Update existing candidate rows in-place by matching on a few stable fields.
                    for j in feature_candidate_indices:
                        if (cand_rows[j].get('lambda_nist_nm') == rr.get('lambda_nist_nm') and
                            cand_rows[j].get('type of element') == rr.get('type of element') and
                            cand_rows[j].get('voigt_feature_id') == rr.get('voigt_feature_id')):
                            cand_rows[j]['candidate_rank_for_feature'] = rank0
                            cand_rows[j]['is_global_best'] = False
                            break

                chosen['is_global_best'] = True
                chosen['feature_representative_reason'] = chosen_reason
                chosen['rank_in_shot'] = rank_by_intensity
                chosen['global_rank_in_shot'] = rank_by_intensity
                best_rows.append(chosen)
                # Also mark the matching candidate row as global best.
                for j in feature_candidate_indices:
                    if (cand_rows[j].get('lambda_nist_nm') == chosen.get('lambda_nist_nm') and
                        cand_rows[j].get('type of element') == chosen.get('type of element') and
                        cand_rows[j].get('voigt_feature_id') == chosen.get('voigt_feature_id')):
                        cand_rows[j]['is_global_best'] = True
                        cand_rows[j]['global_rank_in_shot'] = rank_by_intensity
                        cand_rows[j]['rank_in_shot'] = rank_by_intensity
                        cand_rows[j]['feature_representative_reason'] = chosen_reason
                        break

        best = pd.DataFrame(best_rows)
        candidates = pd.DataFrame(cand_rows)
        if not best.empty:
            best = best.sort_values(['shot_order', 'rank_in_shot']).reset_index(drop=True)
            # In this mode rank_in_shot is deliberately the measured-intensity
            # rank of the experimental feature, not an element-specific rank.
            if 'voigt_rank_for_element' not in best.columns:
                best['voigt_rank_for_element'] = (
                    best.groupby(['shot', 'type of element'])['voigt_rank_metric']
                    .rank(method='first', ascending=False)
                    .astype(int)
                )
        if not candidates.empty:
            if 'global_rank_in_shot' not in candidates.columns:
                candidates['global_rank_in_shot'] = np.nan
            candidates = candidates.sort_values(
                ['shot_order', 'feature_rank_in_shot', 'candidate_rank_for_feature'],
                na_position='last'
            ).reset_index(drop=True)
            if 'voigt_candidate_rank_for_element' not in candidates.columns and 'voigt_rank_metric' in candidates.columns:
                candidates['voigt_candidate_rank_for_element'] = (
                    candidates.groupby(['shot', 'type of element'])['voigt_rank_metric']
                    .rank(method='first', ascending=False)
                    .astype(int)
                )

        self.voigt_best_cache = best.copy()
        self.voigt_candidate_cache = candidates.copy()
        self.voigt_cache_key = self._voigt_cache_key()
        return best.copy(), candidates.copy()

    def fit_voigt_important_lines_gui(self):
        """Run exhaustive feature-based Voigt assignment for the N strongest measured lines.

        Unlike the top-N-per-element mode, this mode starts from the measured
        spectrum itself: it finds the N strongest experimental features and, for
        each one, lets all local NIST lines compete through Voigt fits after
        H-Balmer wavelength calibration.  The accepted fits are then plotted on
        the Spectrum sources view.
        """
        if not self.processed_data:
            return messagebox.showinfo('No data', 'Load one or more shots first.')
        if not self.get_all_nist_dataframes():
            return messagebox.showinfo('No NIST files', 'No local emission-line tables were found.')
        n_lines = int(max(1, getattr(self, 'voigt_full_important_line_count', VOIGT_FIT_IMPORTANT_LINES_DEFAULT)))
        try:
            best, candidates = self.compute_exhaustive_topN_voigt_tables(n_lines=n_lines, force=True)
        except Exception as exc:
            traceback.print_exc()
            return messagebox.showerror('Exhaustive Voigt spectroscopy error', f'{type(exc).__name__}: {exc}')

        n_best = 0 if best is None else len(best)
        n_cand = 0 if candidates is None else len(candidates)
        if n_best == 0:
            return messagebox.showinfo(
                'Exhaustive Voigt spectroscopy',
                f'No accepted NIST assignments were found for the strongest measured features. Candidate/attempted fits: {n_cand}'
            )

        self.voigt_fit_overlay_enabled = True
        if hasattr(self, 'voigt_overlay_button'):
            self.voigt_overlay_button.config(text='Voigt fits: ON')

        messagebox.showinfo(
            'Exhaustive Voigt spectroscopy',
            f'Exhaustive top-N measured-line Voigt analysis completed.\n'
            f'Measured features requested per shot: {n_lines}\n'
            f'Accepted NIST assignments: {n_best}\n'
            f'Candidate/attempted fits: {n_cand}\n\n'
            f'The Spectrum sources window will open with the accepted fits overlaid.'
        )
        self.plot_spectrum_sources()

    def _order_voigt_best_columns(self, df):
        if df is None or df.empty:
            return df
        preferred = [
            'rank_in_shot', 'global_rank_in_shot', 'voigt_rank_for_element', 'shot', 'type of element', 'ionization_state', 'spectrum_label',
            'line_name', 'wavelength', 'lambda_nist_nm', 'lambda_fit_raw_nm', 'lambda_fit_calibrated_nm',
            'experimental_raw_wavelength_nm', 'experimental_calibrated_wavelength_nm', 'delta_nm',
            'voigt_area', 'voigt_peak_height', 'voigt_fwhm_nm', 'voigt_sigma_nm', 'voigt_gamma_nm',
            'candidate_score', 'fit_quality_score', 'voigt_quality_ok', 'voigt_quality_reject_reason',
            'is_hydrogen_balmer', 'hydrogen_balmer_name', 'is_saturated', 'n_saturated_points',
            'fit_saturation_method', 'area_reliability', 'intensity_reliable', 'spectrum_source', 'source_file',
            'wavelength_source', 'nist_relative_intensity', 'nist_relative_intensity_numeric'
        ]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        return df[cols]

    def _order_voigt_candidate_columns(self, df):
        if df is None or df.empty:
            return df
        preferred = [
            'global_rank_in_shot', 'feature_rank_in_shot', 'candidate_rank_for_feature', 'voigt_candidate_rank_for_element', 'prefit_rank_for_element', 'is_global_best',
            'shot', 'type of element', 'ionization_state', 'spectrum_label', 'line_name', 'wavelength',
            'lambda_nist_nm', 'lambda_fit_raw_nm', 'lambda_fit_calibrated_nm',
            'experimental_raw_wavelength_nm', 'experimental_calibrated_wavelength_nm', 'delta_nm',
            'voigt_area', 'candidate_score', 'fit_quality_score', 'voigt_quality_ok',
            'voigt_quality_reject_reason', 'is_hydrogen_balmer', 'hydrogen_balmer_name',
            'is_saturated', 'fit_saturation_method', 'source_file', 'wavelength_source'
        ]
        cols = [c for c in preferred if c in df.columns] + [c for c in df.columns if c not in preferred]
        return df[cols]

    def compute_voigt_best_table(self):
        best, _ = self.compute_voigt_spectroscopy_tables()
        return self._order_voigt_best_columns(best)

    def compute_voigt_candidate_table(self):
        _, candidates = self.compute_voigt_spectroscopy_tables()
        return self._order_voigt_candidate_columns(candidates)

    def show_voigt_best_table(self):
        best = self.compute_voigt_best_table()
        if best is None or best.empty:
            return messagebox.showinfo('No Voigt fits', 'No Voigt-fitted lines were found. Select NIST files or lower thresholds.')
        self.show_dataframe_window(best, title='Voigt best spectroscopy fits', default_filename_base='voigt_best_spectroscopy_fits')

    def show_voigt_candidate_table(self):
        candidates = self.compute_voigt_candidate_table()
        if candidates is None or candidates.empty:
            return messagebox.showinfo('No Voigt fits', 'No Voigt candidate fits were found. Select NIST files or lower thresholds.')
        self.show_dataframe_window(candidates, title='Voigt candidate spectroscopy fits', default_filename_base='voigt_candidate_spectroscopy_fits')

    def export_voigt_spectroscopy_analysis(self):
        best, candidates = self.compute_voigt_spectroscopy_tables()
        best = self._order_voigt_best_columns(best)
        candidates = self._order_voigt_candidate_columns(candidates)
        if (best is None or best.empty) and (candidates is None or candidates.empty):
            return messagebox.showinfo('No Voigt fits', 'No Voigt spectroscopy fits are available to export.')
        path = filedialog.asksaveasfilename(
            title='Export Voigt spectroscopy analysis',
            defaultextension='.xlsx',
            filetypes=[('Excel workbook', '*.xlsx'), ('CSV files fallback', '*.csv'), ('All files', '*.*')]
        )
        if not path:
            return
        out_path, kind = save_workbook_with_openpyxl_fallback(path, [
            ('voigt_best', best if best is not None else pd.DataFrame()),
            ('voigt_candidates', candidates if candidates is not None else pd.DataFrame()),
        ])
        messagebox.showinfo('Export complete', f'Voigt spectroscopy analysis saved as {kind}:\n{out_path}')

    def _get_spectrum_for_voigt_row(self, row):
        """Return (wavelength_raw, intensity_raw, label) matching a Voigt table row."""
        shot = str(row.get('shot', ''))
        source_key = str(row.get('spectrum_source_key', '')).lower()
        for d in self.processed_data:
            if str(d.get('shot_number', '')) != shot:
                continue
            spectra = d.get('spectra_by_source', {}) or {}
            if source_key:
                for key, spec in spectra.items():
                    if str(key).lower() == source_key:
                        wl = np.asarray(spec.get('wavelengths', np.array([])), dtype=float)
                        y = np.asarray(spec.get('intensity_raw', np.array([])), dtype=float)
                        return wl, y, str(key)
            wl, y, label, key = self.get_selected_spectrum_arrays(d, use_rw=False)
            return np.asarray(wl, dtype=float), np.asarray(y, dtype=float), str(label)
        return np.array([]), np.array([]), ''

    def _raw_nist_wavelength_from_fit_row(self, row):
        """Estimate where the NIST wavelength should appear on the raw axis."""
        try:
            lam_nist = float(row.get('lambda_nist_nm', np.nan))
        except Exception:
            return np.nan
        try:
            x_cal = np.asarray(json.loads(row.get('x_fit_nm_json', '[]')), dtype=float)
            x_raw = np.asarray(json.loads(row.get('x_fit_raw_nm_json', '[]')), dtype=float)
            if x_cal.size >= 2 and x_cal.size == x_raw.size:
                order = np.argsort(x_cal)
                return float(np.interp(lam_nist, x_cal[order], x_raw[order], left=np.nan, right=np.nan))
        except Exception:
            pass
        try:
            return float(row.get('lambda_fit_raw_nm', np.nan)) - float(row.get('delta_nm', 0.0))
        except Exception:
            return np.nan

    def plot_voigt_fit_diagnostics(self):
        """Plot accepted Voigt fits one by one in local windows.

        Each subplot shows the raw spectrum segment, the full Voigt fit, the
        component curve, and a vertical marker at the associated NIST line.  The
        fit and NIST marker share the element color. This is meant for checking
        whether the accepted assignment is visually credible, especially for
        blends or Avantes saturation.
        """
        best = self.compute_voigt_best_table()
        if best is None or best.empty:
            return messagebox.showinfo('No Voigt fits', 'Run Quick spectroscopy or Detailed spectroscopy → Run Voigt analysis first.')

        default_n = min(24, len(best))
        nmax = simpledialog.askinteger(
            'Plot Voigt fit diagnostics',
            'Maximum number of accepted fits to plot in this window.\n'
            'The table remains complete; this limit only keeps the figure readable.',
            initialvalue=default_n,
            minvalue=1,
            maxvalue=max(1, min(200, len(best))),
            parent=self.master_frame.winfo_toplevel()
        )
        if nmax is None:
            return

        df = best.copy()
        # Prefer reliable fits and stronger lines first. H Balmer anchors remain
        # early because they are physically expected and control calibration.
        if 'voigt_quality_ok' in df.columns:
            df['__quality_sort'] = df['voigt_quality_ok'].astype(bool).astype(int)
        else:
            df['__quality_sort'] = 1
        df['__h_sort'] = df.get('is_hydrogen_balmer', False).astype(bool).astype(int) if 'is_hydrogen_balmer' in df.columns else 0
        metric = pd.to_numeric(df.get('voigt_rank_metric', df.get('voigt_area', 0.0)), errors='coerce').fillna(0.0)
        df['__metric_sort'] = metric
        df = df.sort_values(['shot_order', '__h_sort', '__quality_sort', '__metric_sort'], ascending=[True, False, False, False]).head(int(nmax))
        if df.empty:
            return messagebox.showinfo('No Voigt fits', 'No fits remain after filtering.')

        n = len(df)
        ncols = 2 if n > 1 else 1
        nrows = int(np.ceil(n / ncols))
        win = tk.Toplevel(self.app)
        win.title('Voigt fit diagnostics: local windows')
        win.geometry('1250x850')
        fig = Figure(figsize=(12.5, max(4.0, 3.0 * nrows)), facecolor='white')

        for i, (_, row) in enumerate(df.iterrows(), start=1):
            ax = fig.add_subplot(nrows, ncols, i)
            wl, y, source_label = self._get_spectrum_for_voigt_row(row)
            elem = normalize_element_label(row.get('type of element', ''))
            color = VOIGT_ELEMENT_COLORS.get(elem, '#000000')
            try:
                x_raw = np.asarray(json.loads(row.get('x_fit_raw_nm_json', '[]')), dtype=float)
                x_cal = np.asarray(json.loads(row.get('x_fit_nm_json', '[]')), dtype=float)
                y_model = np.asarray(json.loads(row.get('y_fit_model_json', '[]')), dtype=float)
                y_comp = np.asarray(json.loads(row.get('y_fit_component_json', '[]')), dtype=float)
            except Exception:
                x_raw = x_cal = y_model = y_comp = np.array([])

            if wl.size == y.size and wl.size > 2 and x_raw.size > 0:
                x0 = float(np.nanmin(x_raw))
                x1 = float(np.nanmax(x_raw))
                pad = max(0.15, 0.15 * (x1 - x0))
                mask = np.isfinite(wl) & np.isfinite(y) & (wl >= x0 - pad) & (wl <= x1 + pad)
                if np.any(mask):
                    ax.plot(wl[mask], y[mask], color='0.35', linewidth=1.1, alpha=0.85, label=f'raw {source_label}')
            if x_raw.size == y_model.size and x_raw.size > 1:
                good = np.isfinite(x_raw) & np.isfinite(y_model)
                ax.plot(x_raw[good], y_model[good], color=color, linewidth=2.0, label=f'Voigt fit {elem}')
            if x_raw.size == y_comp.size and x_raw.size > 1:
                good = np.isfinite(x_raw) & np.isfinite(y_comp)
                ax.plot(x_raw[good], y_comp[good], color=color, linestyle='--', linewidth=1.5, alpha=0.85, label='Voigt component')
            raw_nist = self._raw_nist_wavelength_from_fit_row(row)
            if np.isfinite(raw_nist):
                ax.axvline(raw_nist, color=color, linestyle=':', linewidth=2.0, label='NIST λ')

            title = (
                f"Shot {row.get('shot','')} | {elem} {row.get('ionization_state','')} | "
                f"NIST {float(row.get('lambda_nist_nm', np.nan)):.3f} nm | "
                f"Δ {float(row.get('delta_nm', np.nan)):.3f} nm"
            )
            if bool(row.get('is_saturated', False)):
                title += ' | saturated/censored'
            ax.set_title(title, fontsize=9)
            ax.set_xlabel('raw wavelength [nm]')
            ax.set_ylabel('counts')
            ax.grid(True, alpha=0.25)
            ax.legend(fontsize=7, loc='best')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas.draw()


    def plot_voigt_candidate_fit_diagnostics(self):
        """Plot attempted/candidate Voigt fits, not only accepted best fits."""
        candidates = self.compute_voigt_candidate_table()
        if candidates is None or candidates.empty:
            return messagebox.showinfo('No Voigt candidates', 'Run a Voigt analysis first. The candidate table is empty.')

        default_n = min(30, len(candidates))
        nmax = simpledialog.askinteger(
            'Plot Voigt candidate fits',
            'Maximum number of candidate/attempted fits to plot.\n'
            'Use this to inspect rejected or ambiguous candidates before trusting the best table.',
            initialvalue=default_n,
            minvalue=1,
            maxvalue=max(1, min(300, len(candidates))),
            parent=self.master_frame.winfo_toplevel()
        )
        if nmax is None:
            return

        df = candidates.copy()
        if 'voigt_quality_ok' in df.columns:
            df['__quality_sort'] = df['voigt_quality_ok'].astype(bool).astype(int)
        else:
            df['__quality_sort'] = 1
        df['__h_sort'] = df.get('is_hydrogen_balmer', False).astype(bool).astype(int) if 'is_hydrogen_balmer' in df.columns else 0
        metric = pd.to_numeric(df.get('voigt_rank_metric', df.get('candidate_score', df.get('voigt_area', 0.0))), errors='coerce').fillna(0.0)
        df['__metric_sort'] = metric
        df = df.sort_values(['shot_order', '__h_sort', '__quality_sort', '__metric_sort'], ascending=[True, False, False, False]).head(int(nmax))
        if df.empty:
            return messagebox.showinfo('No Voigt candidates', 'No candidate fits remain after filtering.')

        n = len(df)
        ncols = 2 if n > 1 else 1
        nrows = int(np.ceil(n / ncols))
        win = tk.Toplevel(self.app)
        win.title('Voigt candidate fit diagnostics: local windows')
        win.geometry('1250x850')
        fig = Figure(figsize=(12.5, max(4.0, 3.0 * nrows)), facecolor='white')

        for i, (_, row) in enumerate(df.iterrows(), start=1):
            ax = fig.add_subplot(nrows, ncols, i)
            wl, y, source_label = self._get_spectrum_for_voigt_row(row)
            elem = normalize_element_label(row.get('type of element', ''))
            color = VOIGT_ELEMENT_COLORS.get(elem, '#000000')
            try:
                x_raw = np.asarray(json.loads(row.get('x_fit_raw_nm_json', '[]')), dtype=float)
                y_model = np.asarray(json.loads(row.get('y_fit_model_json', '[]')), dtype=float)
                y_comp = np.asarray(json.loads(row.get('y_fit_component_json', '[]')), dtype=float)
            except Exception:
                x_raw = y_model = y_comp = np.array([])

            if wl.size == y.size and wl.size > 2 and x_raw.size > 0:
                x0 = float(np.nanmin(x_raw)); x1 = float(np.nanmax(x_raw))
                pad = max(0.15, 0.15 * (x1 - x0))
                mask = np.isfinite(wl) & np.isfinite(y) & (wl >= x0 - pad) & (wl <= x1 + pad)
                if np.any(mask):
                    ax.plot(wl[mask], y[mask], color='0.35', linewidth=1.1, alpha=0.85, label=f'raw {source_label}')
            if x_raw.size == y_model.size and x_raw.size > 1:
                good = np.isfinite(x_raw) & np.isfinite(y_model)
                ax.plot(x_raw[good], y_model[good], color=color, linewidth=2.0, label=f'candidate Voigt {elem}')
            if x_raw.size == y_comp.size and x_raw.size > 1:
                good = np.isfinite(x_raw) & np.isfinite(y_comp)
                ax.plot(x_raw[good], y_comp[good], color=color, linestyle='--', linewidth=1.5, alpha=0.85, label='component')
            raw_nist = self._raw_nist_wavelength_from_fit_row(row)
            if np.isfinite(raw_nist):
                ax.axvline(raw_nist, color=color, linestyle=':', linewidth=2.0, label='NIST λ')
            title = (
                f"Shot {row.get('shot','')} | {elem} {row.get('ionization_state','')} | "
                f"NIST {float(row.get('lambda_nist_nm', np.nan)):.3f} nm | "
                f"Δ {float(row.get('delta_nm', np.nan)):.3f} nm | "
                f"candidate rank {row.get('candidate_rank_for_feature','')}"
            )
            if bool(row.get('is_global_best', False)):
                title += ' | accepted'
            if bool(row.get('is_saturated', False)):
                title += ' | saturated/censored'
            ax.set_title(title, fontsize=9)
            ax.set_xlabel('raw wavelength [nm]')
            ax.set_ylabel('counts')
            ax.grid(True, alpha=0.25)
            ax.legend(fontsize=7, loc='best')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.draw()


    def _compute_forced_element_overlay_rows(self, requested_elements=None):
        """Compute diagnostic Voigt fits that must be drawn for selected elements.

        This is intentionally separate from the accepted/global-best table.  It is
        used for cases such as Li coating: even when Li is not the best owner of
        any of the strongest measured features, the user can request Li=3 in the
        overlay limits and see the three best Li fits as dashed/x diagnostic
        candidates.
        """
        if not self.processed_data:
            return pd.DataFrame()
        if requested_elements is None:
            _, per_element_limits = self._parse_voigt_overlay_limits()
            requested_elements = [normalize_element_label(k) for k, v in per_element_limits.items() if int(v) > 0]
        requested_elements = [normalize_element_label(e) for e in requested_elements if normalize_element_label(e)]
        if not requested_elements:
            return pd.DataFrame()

        # Prefer feature-based candidates already produced by the exhaustive
        # analysis.  These fits were made over the full detected experimental
        # feature, so they are much more diagnostic than re-fitting each NIST line
        # independently in a narrow NIST-centered window.
        try:
            cand_cache = getattr(self, 'voigt_candidate_cache', pd.DataFrame())
            if cand_cache is not None and not cand_cache.empty and 'type of element' in cand_cache.columns:
                tmp = cand_cache.copy()
                tmp['__elem_norm__'] = tmp['type of element'].map(normalize_element_label)
                frames = []
                _, per_element_limits_tmp = self._parse_voigt_overlay_limits()
                for elem_req in requested_elements:
                    limit_tmp = int(per_element_limits_tmp.get(elem_req, VOIGT_OVERLAY_DEFAULT_MAX_PER_ELEMENT))
                    if limit_tmp <= 0:
                        continue
                    sub = tmp[tmp['__elem_norm__'].eq(elem_req)].copy()
                    if sub.empty:
                        continue
                    if 'is_global_best' in sub.columns:
                        # Prefer not-yet-accepted diagnostic candidates, but keep
                        # accepted rows if they are the only available ones.
                        not_best = sub[~sub['is_global_best'].fillna(False).astype(bool)].copy()
                        if not not_best.empty:
                            sub = not_best
                    for col in ['feature_peak_intensity', 'candidate_score', 'voigt_rank_metric']:
                        if col not in sub.columns:
                            sub[col] = np.nan
                    sub['__abs_delta__'] = pd.to_numeric(sub.get('delta_nm', np.nan), errors='coerce').abs()
                    sub = sub.sort_values(
                        ['feature_peak_intensity', 'candidate_score', 'voigt_rank_metric', '__abs_delta__'],
                        ascending=[False, False, False, True]
                    ).head(limit_tmp).copy()
                    if sub.empty:
                        continue
                    sub['is_forced_element_overlay_fit'] = True
                    sub['forced_overlay_reason'] = f'requested_{elem_req}_feature_based_candidate_overlay'
                    sub['forced_overlay_rank_for_element'] = np.arange(1, len(sub) + 1)
                    sub['analysis_mode'] = sub.get('analysis_mode', 'feature_based_candidate')
                    frames.append(sub)
                if frames:
                    out = pd.concat(frames, ignore_index=True)
                    return out.drop(columns=['__elem_norm__', '__abs_delta__'], errors='ignore')
        except Exception:
            pass

        nist_sets = self._get_nist_dataframes_for_voigt()
        nist_by_elem = {normalize_element_label(e): (e, f, df) for e, f, df in nist_sets}
        rows = []
        _, per_element_limits = self._parse_voigt_overlay_limits()

        for shot_order, data in enumerate(self.processed_data):
            shot = data.get('shot_number', '')
            wl_raw, y_raw, source_label, source_key = self.get_selected_spectrum_arrays(data, use_rw=False)
            wl_raw = np.asarray(wl_raw, dtype=float)
            y_raw = np.asarray(y_raw, dtype=float)
            if wl_raw.size < VOIGT_FIT_MIN_POINTS or wl_raw.shape != y_raw.shape:
                continue
            finite = np.isfinite(wl_raw) & np.isfinite(y_raw)
            wl_raw = wl_raw[finite]
            y_raw = y_raw[finite]
            if wl_raw.size < VOIGT_FIT_MIN_POINTS:
                continue
            order = np.argsort(wl_raw)
            wl_raw = wl_raw[order]
            y_raw = y_raw[order]

            voigt_calibration_df, voigt_calibration_coeffs = estimate_voigt_hydrogen_wavelength_calibration(wl_raw, y_raw)
            if voigt_calibration_coeffs is not None:
                wl_fit_axis = apply_wavelength_calibration(wl_raw, voigt_calibration_coeffs)
                voigt_calibration_label = f"Voigt H Balmer wavelength calibration degree {min(2, len(voigt_calibration_coeffs)-1)}"
            else:
                wl_fit_axis = wl_raw.copy()
                voigt_calibration_label = "none"
            cal_order = np.argsort(wl_fit_axis)
            wl_cal_sorted = wl_fit_axis[cal_order]
            wl_raw_sorted = wl_raw[cal_order]
            wl_min = float(np.nanmin(wl_fit_axis))
            wl_max = float(np.nanmax(wl_fit_axis))

            for elem_req in requested_elements:
                if elem_req not in nist_by_elem:
                    continue
                element_label, source_file, nist_df = nist_by_elem[elem_req]
                limit = int(per_element_limits.get(elem_req, VOIGT_OVERLAY_DEFAULT_MAX_PER_ELEMENT))
                if limit <= 0:
                    continue
                prefit_lines = self._preselect_voigt_lines_for_element(
                    wl_fit_axis, y_raw, nist_df, element_label, source_file,
                    top_n=max(limit * 20, 80), allow_weak=True
                )
                if prefit_lines is None or prefit_lines.empty:
                    continue
                accepted_lams = []
                rank_for_element = 0
                for _, prefit_row in prefit_lines.iterrows():
                    try:
                        line = nist_df.loc[prefit_row.get('__nist_index__')]
                        lam_nist = float(line.get('lambda_nm', np.nan))
                    except Exception:
                        continue
                    if not np.isfinite(lam_nist) or lam_nist < wl_min - 6.0 or lam_nist > wl_max + 6.0:
                        continue
                    if any(abs(lam_nist - old_lam) <= 0.12 for old_lam in accepted_lams):
                        continue
                    source_file_line = str(line.get('__source_file_for_voigt__', line.get('source_file', source_file)))
                    element_label_line = str(line.get('__element_label_for_voigt__', element_label))
                    lambda_source_line = str(line.get('lambda_source', ''))
                    elem, ion, spectrum_label = extract_ionization_state(element_label_line, line, source_file_line)
                    elem = normalize_element_label(elem or elem_req)
                    balmer_info = get_hydrogen_balmer_match(lam_nist) if elem == 'H' else None
                    is_balmer = bool(balmer_info)
                    line_name = balmer_info[0] if balmer_info else spectrum_label
                    window = VOIGT_FIT_BALMER_WINDOW_NM if is_balmer else VOIGT_FIT_DEFAULT_WINDOW_NM
                    if is_balmer and balmer_info[0] == 'H_alpha':
                        window = VOIGT_FIT_SATURATED_BALMER_WINDOW_NM
                    window = max(window, 0.85)
                    fit = fit_single_voigt_candidate(
                        wl_fit_axis, y_raw, lambda_nist_nm=lam_nist,
                        element_label=elem, line_name=line_name, ionization_state=ion,
                        window_nm=window, force_saturated_reference=bool(is_balmer and line_name == 'H_alpha'),
                        allow_weak_fit=True,
                    )
                    if fit is None:
                        continue
                    center_cal = float(fit.get('lambda_fit_nm', np.nan))
                    center_raw = float(np.interp(center_cal, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)) if wl_cal_sorted.size >= 2 else center_cal
                    x_fit_cal = np.asarray(json.loads(fit.get('x_fit_nm_json', '[]')), dtype=float)
                    if x_fit_cal.size and wl_cal_sorted.size >= 2:
                        x_fit_raw = np.interp(x_fit_cal, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan)
                    else:
                        x_fit_raw = x_fit_cal.copy()
                    delta = center_cal - lam_nist
                    fit_quality = float(fit.get('fit_quality_score', 0.0))
                    fwhm_val = float(fit.get('voigt_fwhm_nm', np.nan))
                    proximity = max(0.0, 1.0 - abs(delta) / max(VOIGT_FIT_CENTER_TOLERANCE_NM, 1e-9))
                    nist_intensity, nist_intensity_numeric, nist_intensity_source = nist_strength_from_row(line)
                    rank_for_element += 1
                    accepted_lams.append(lam_nist)
                    rows.append({
                        'shot': shot,
                        'shot_order': shot_order,
                        'spectrum_source': source_label,
                        'spectrum_source_key': source_key,
                        'voigt_wavelength_calibration': voigt_calibration_label,
                        'voigt_calibration_n_anchors': int(len(voigt_calibration_df)) if voigt_calibration_df is not None else 0,
                        'type of element': elem,
                        'ionization_state': ion,
                        'spectrum_label': spectrum_label,
                        'line_name': line_name,
                        'wavelength': lam_nist,
                        'lambda_nist_nm': lam_nist,
                        'lambda_fit_calibrated_nm': center_cal,
                        'lambda_fit_raw_nm': center_raw,
                        'experimental_calibrated_wavelength_nm': center_cal,
                        'experimental_raw_wavelength_nm': center_raw,
                        'delta_nm': delta,
                        'voigt_area': float(fit.get('voigt_area', np.nan)),
                        'voigt_peak_height': float(fit.get('voigt_peak_height', np.nan)),
                        'voigt_fwhm_nm': fwhm_val,
                        'fit_quality_score': fit_quality,
                        'candidate_score': 0.75 * proximity + 0.25 * fit_quality,
                        'proximity_score': proximity,
                        'voigt_quality_ok': bool(np.isfinite(delta) and np.isfinite(fwhm_val) and fit_quality >= 0.001),
                        'voigt_quality_reject_reason': 'forced_overlay_diagnostic_candidate',
                        'is_global_best': False,
                        'is_forced_element_overlay_fit': True,
                        'forced_overlay_reason': f'requested_{elem}_top_{limit}_diagnostic_fit',
                        'forced_overlay_rank_for_element': rank_for_element,
                        'global_rank_in_shot': np.nan,
                        'rank_in_shot': np.nan,
                        'voigt_rank_for_element': rank_for_element,
                        'candidate_rank_for_feature': np.nan,
                        'source_file': source_file_line,
                        'wavelength_source': lambda_source_line,
                        'nist_relative_intensity': nist_intensity,
                        'nist_relative_intensity_numeric': nist_intensity_numeric,
                        'nist_intensity_source': nist_intensity_source,
                        'analysis_mode': 'forced_required_element_overlay',
                        'x_fit_nm_json': fit.get('x_fit_nm_json', '[]'),
                        'x_fit_raw_nm_json': json.dumps([float(v) if np.isfinite(v) else None for v in x_fit_raw]),
                        'y_fit_model_json': fit.get('y_fit_model_json', '[]'),
                        'y_fit_component_json': fit.get('y_fit_component_json', '[]'),
                        'is_saturated': bool(fit.get('is_saturated', False)),
                        'fit_saturation_method': fit.get('fit_saturation_method', ''),
                    })
                    if rank_for_element >= limit:
                        break
        return pd.DataFrame(rows)

    def _plot_voigt_overlays_on_axis(self, ax, spectrum_source_filter=None):
        """Overlay accepted Voigt fits and the two best alternatives on a spectrum axis.

        Solid lines are accepted/best assignments.  Dashed lines are the next two
        NIST candidates for the same measured experimental feature.  This makes
        the exhaustive 2B plot diagnostic: the user sees both the chosen owner of
        a peak and the nearest plausible competitors.
        """
        best = self.compute_voigt_best_table()
        if best is None or best.empty:
            return []

        default_limit, per_element_limits = self._parse_voigt_overlay_limits()
        overlay_lines = []
        plotted_counts = {}
        legend_seen = set()
        self._forced_overlay_plot_counts_tmp = {}

        df = best.copy()
        # Plot only usable accepted fits. Candidate tables still keep rejected
        # fits, but drawing all of them would make the spectrum unreadable.
        if 'voigt_quality_ok' in df.columns:
            df = df[df['voigt_quality_ok'].astype(bool)]
        if 'delta_nm' in df.columns:
            df = df[pd.to_numeric(df['delta_nm'], errors='coerce').abs() <= VOIGT_OVERLAY_MAX_ABS_DELTA_NM]
        if 'fit_quality_score' in df.columns:
            df = df[pd.to_numeric(df['fit_quality_score'], errors='coerce').fillna(0.0) >= VOIGT_OVERLAY_MIN_QUALITY]
        if 'voigt_fwhm_nm' in df.columns:
            df = df[pd.to_numeric(df['voigt_fwhm_nm'], errors='coerce').fillna(np.inf) <= VOIGT_OVERLAY_MAX_FWHM_NM]

        if df.empty:
            return []

        cand = getattr(self, 'voigt_candidate_cache', pd.DataFrame())
        if cand is None:
            cand = pd.DataFrame()

        df = df.sort_values(['shot_order', 'rank_in_shot', 'type of element', 'voigt_area'], ascending=[True, True, True, False])

        def draw_row(row, *, linestyle='-', linewidth=2.1, alpha=0.92, label_prefix='Voigt', alternative=False, marker=None, markevery=None, role=None):
            try:
                source_key = str(row.get('spectrum_source_key', ''))
                if spectrum_source_filter and source_key and source_key != spectrum_source_filter:
                    return None
                elem = normalize_element_label(row.get('type of element', ''))
                x_raw_json = row.get('x_fit_raw_nm_json', '')
                x_cal_json = row.get('x_fit_nm_json', '[]')
                if self.overlay_uses_calibrated_axis():
                    x_json = x_cal_json if x_cal_json else x_raw_json
                else:
                    x_json = x_raw_json if x_raw_json else x_cal_json
                x = np.asarray(json.loads(x_json), dtype=float)
                y = np.asarray(json.loads(row.get('y_fit_model_json', '[]')), dtype=float)
                if x.size < 2 or x.size != y.size:
                    return None
                finite = np.isfinite(x) & np.isfinite(y)
                x = x[finite]
                y = y[finite]
                if x.size < 2:
                    return None
                color = VOIGT_ELEMENT_COLORS.get(elem, '#000000')
                legend_key = (label_prefix, elem, row.get('ionization_state', ''), linestyle)
                if legend_key in legend_seen:
                    label = '_nolegend_'
                else:
                    ion = str(row.get('ionization_state', '')).strip()
                    if role == 'forced_required_element_candidate':
                        label = f"Req. {elem} {ion}".strip()
                    elif alternative:
                        label = f"Alt. {elem} {ion}".strip()
                    else:
                        label = f"{label_prefix} {elem} {ion}".strip()
                    legend_seen.add(legend_key)
                line, = ax.plot(
                    x, y,
                    color=color,
                    linestyle=linestyle,
                    linewidth=linewidth,
                    alpha=alpha,
                    label=label,
                    marker=marker if marker else None,
                    markevery=markevery,
                    markersize=5 if marker else None,
                )
                line.set_picker(6)
                info = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
                info['overlay_role'] = role or ('alternative_candidate' if alternative else 'accepted_best')
                line._voigt_info = info
                overlay_lines.append(line)
                return line
            except Exception:
                return None

        for _, row in df.iterrows():
            try:
                elem = normalize_element_label(row.get('type of element', ''))
                shot = str(row.get('shot', ''))
                limit = per_element_limits.get(elem, default_limit)
                key = (shot, elem)
                if plotted_counts.get(key, 0) >= limit:
                    continue
                main_line = draw_row(row, linestyle='-', linewidth=2.2, alpha=0.94, label_prefix='Voigt', alternative=False)
                if main_line is None:
                    continue
                plotted_counts[key] = plotted_counts.get(key, 0) + 1

                # In exhaustive mode, also show the next two candidate NIST fits
                # for the same measured feature as dashed alternatives.
                if cand is not None and not cand.empty and 'voigt_feature_id' in cand.columns:
                    try:
                        feature_id = row.get('voigt_feature_id', np.nan)
                        shot_val = row.get('shot', '')
                        alt = cand[
                            (cand.get('shot', '') == shot_val) &
                            (pd.to_numeric(cand.get('voigt_feature_id', np.nan), errors='coerce') == float(feature_id))
                        ].copy()
                        if 'candidate_rank_for_feature' in alt.columns:
                            alt['__rank__'] = pd.to_numeric(alt['candidate_rank_for_feature'], errors='coerce')
                            alt = alt[(alt['__rank__'] >= 2) & (alt['__rank__'] <= 3)]
                            alt = alt.sort_values('__rank__')
                        else:
                            alt = alt[alt.get('is_global_best', False) != True].sort_values('candidate_score', ascending=False).head(2)
                        # Always try to show the two best alternatives.  Do not
                        # hide them with strict quality filters: their purpose is
                        # diagnostic, so the user can see what else could explain
                        # the same measured feature.
                        if 'is_global_best' in alt.columns:
                            alt = alt[~alt['is_global_best'].fillna(False).astype(bool)].copy()
                        if 'candidate_score' in alt.columns:
                            alt = alt.sort_values('candidate_score', ascending=False)
                        # Draw the two best alternatives, and additionally keep the best Li
                        # alternative visible when present.  This is useful for lithium-coated
                        # shots: Li may not be top-2 by the generic score, but it is physically
                        # important to inspect.
                        alt_top = alt.head(2).copy()
                        try:
                            full_alt = cand[
                                (cand.get('shot', '') == shot_val) &
                                (pd.to_numeric(cand.get('voigt_feature_id', np.nan), errors='coerce') == float(feature_id))
                            ].copy()
                            if 'is_global_best' in full_alt.columns:
                                full_alt = full_alt[~full_alt['is_global_best'].fillna(False).astype(bool)].copy()
                            full_alt['__elem_norm__'] = full_alt.get('type of element', '').map(normalize_element_label)
                            li_alt = full_alt[full_alt['__elem_norm__'].eq('Li')].copy()
                            if not li_alt.empty:
                                li_alt = li_alt.sort_values(['candidate_score', 'voigt_rank_metric'], ascending=[False, False]).head(1)
                                alt_top = pd.concat([alt_top, li_alt], ignore_index=True)
                                alt_top = alt_top.drop_duplicates(subset=['shot', 'voigt_feature_id', 'type of element', 'lambda_nist_nm'], keep='first')
                        except Exception:
                            pass
                        for _, arow in alt_top.iterrows():
                            is_li_alt = normalize_element_label(arow.get('type of element', '')) == 'Li'
                            draw_row(
                                arow,
                                linestyle='--',
                                linewidth=1.9 if is_li_alt else 1.7,
                                alpha=0.86 if is_li_alt else 0.78,
                                label_prefix='Voigt',
                                alternative=True,
                                marker='x' if is_li_alt else None,
                                markevery=max(1, 14) if is_li_alt else None,
                            )
                    except Exception:
                        pass
            except Exception:
                continue

        # Finally, force requested element diagnostics such as Li=3 in the overlay
        # limits.  These are not accepted global owners; they are drawn as dotted
        # curves with x markers so the user can inspect whether a coating element
        # may be present even when Fe/W/H wins the main assignment.
        try:
            required = self._compute_forced_element_overlay_rows()
            if required is not None and not required.empty:
                required = required.sort_values(['shot_order', 'type of element', 'forced_overlay_rank_for_element'])
                for _, rrow in required.iterrows():
                    elem = normalize_element_label(rrow.get('type of element', ''))
                    shot = str(rrow.get('shot', ''))
                    limit = per_element_limits.get(elem, default_limit)
                    if not hasattr(self, '_forced_overlay_plot_counts_tmp'):
                        self._forced_overlay_plot_counts_tmp = {}
                    key = (shot, elem)
                    # Required diagnostic overlays are counted separately from
                    # accepted/alternative fits.  If the user asks for Li=3,
                    # show up to three Li diagnostic fits even if Li already
                    # appeared elsewhere or did not win any feature.
                    if self._forced_overlay_plot_counts_tmp.get(key, 0) >= limit:
                        continue
                    line = draw_row(
                        rrow, linestyle=':', linewidth=1.9, alpha=0.82,
                        label_prefix='Req.', alternative=False, marker='x', markevery=max(1, 12),
                        role='forced_required_element_candidate'
                    )
                    if line is not None:
                        self._forced_overlay_plot_counts_tmp[key] = self._forced_overlay_plot_counts_tmp.get(key, 0) + 1
        except Exception:
            traceback.print_exc()

        return overlay_lines

    def _attach_voigt_hover(self, fig, ax, canvas, overlay_lines):
        if not overlay_lines:
            return
        annot = ax.annotate(
            '', xy=(0, 0), xytext=(12, 12), textcoords='offset points',
            bbox=dict(boxstyle='round', fc='white', alpha=0.88),
            arrowprops=dict(arrowstyle='->')
        )
        annot.set_visible(False)

        def fmt(row):
            def fval(k):
                try:
                    v = float(row.get(k, np.nan))
                    return f'{v:.4f}' if np.isfinite(v) else 'nan'
                except Exception:
                    return 'nan'
            return (
                f"Shot: {row.get('shot', '')}\n"
                f"Element: {row.get('type of element', '')} {row.get('ionization_state', '')}\n"
                f"Line: {row.get('line_name', '')}\n"
                f"NIST λ: {fval('lambda_nist_nm')} nm\n"
                f"Fit λ raw: {fval('lambda_fit_raw_nm')} nm\n"
                f"Fit λ calibrated: {fval('lambda_fit_calibrated_nm')} nm\n"
                f"Δλ: {fval('delta_nm')} nm\n"
                f"Area: {fval('voigt_area')}\n"
                f"Saturated: {row.get('is_saturated', False)} ({row.get('fit_saturation_method', '')})"
            )

        def on_move(event):
            if event.inaxes != ax:
                if annot.get_visible():
                    annot.set_visible(False)
                    canvas.draw_idle()
                return
            for line in overlay_lines:
                try:
                    contains, _ = line.contains(event)
                except Exception:
                    contains = False
                if contains:
                    row = getattr(line, '_voigt_info', {})
                    annot.xy = (event.xdata, event.ydata)
                    annot.set_text(fmt(row))
                    annot.set_visible(True)
                    canvas.draw_idle()
                    return
            if annot.get_visible():
                annot.set_visible(False)
                canvas.draw_idle()

        fig.canvas.mpl_connect('motion_notify_event', on_move)

    def plot_spectrum_sources(self):
        """Show Avantes and OceanFX spectra separately for loaded shots.

        When many shots are loaded, the Matplotlib legend can become so large
        that tight_layout compresses the spectrum axes into a very thin strip.
        The spectrum window now uses a fixed subplot layout and hides large
        legends by default.  The full legend can still be opened in a separate
        scrollable table, and a compact in-plot legend can be toggled on when
        needed.
        """
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")

        win = tk.Toplevel(self.app)
        win.title("Available spectrum sources")
        win.geometry("1200x750")

        fig = Figure(figsize=(12, 7), facecolor='white')
        ax = fig.add_subplot(111)

        for idx, d in enumerate(self.processed_data):
            base_color = self.get_color_for_data(d, fallback_index=idx)
            label = self.get_plot_label_for_data(d)
            spectra = d.get('spectra_by_source', {})
            for j, (key, s) in enumerate(spectra.items()):
                wl = np.asarray(s.get('wavelengths', np.array([])), dtype=float)
                raw = np.asarray(s.get('intensity_raw', np.array([])), dtype=float)
                if wl.size == raw.size and wl.size > 2:
                    xwl = self.get_spectrum_display_wavelengths(d, wl)
                    mask = np.isfinite(xwl) & np.isfinite(raw) & (xwl >= 350.0) & (xwl <= 900.0)
                    if np.any(mask):
                        order = np.argsort(xwl[mask])
                        linestyle = '-' if key.lower().startswith('ocean') else '--'
                        alpha = 0.95 if key.lower().startswith('ocean') else 0.75
                        ax.plot(
                            xwl[mask][order],
                            raw[mask][order],
                            linestyle=linestyle,
                            alpha=alpha,
                            label=f'{label} {key}'
                        )

        overlay_lines = []
        if bool(getattr(self, 'voigt_fit_overlay_enabled', False)):
            overlay_lines = self._plot_voigt_overlays_on_axis(ax)

        ax.set_title(
            'Available spectra: OceanFX and Avantes'
            + (' + Voigt fits' if overlay_lines else '')
            + f' | spectrum {self.get_spectrum_x_axis_label()} | overlay {self.get_overlay_axis_label()}'
        )
        ax.set_xlabel(self.get_spectrum_x_axis_label())
        ax.set_ylabel('intensity [counts]')
        ax.grid(True, alpha=0.3)

        # Do not call fig.tight_layout() here.  With many legend entries,
        # tight_layout tries to reserve space for the legend and can squash the
        # spectrum into a narrow band at the top of the window.
        fig.subplots_adjust(left=0.08, right=0.985, bottom=0.12, top=0.90)

        def _unique_legend_entries():
            handles, labels = ax.get_legend_handles_labels()
            entries = []
            seen = set()
            for handle, text in zip(handles, labels):
                text = str(text)
                if not text or text.startswith('_') or text in seen:
                    continue
                seen.add(text)
                entries.append((handle, text))
            return entries

        legend_entries = _unique_legend_entries()
        legend_count = len(legend_entries)
        # Small legends are useful; large legends are the failure mode shown by
        # the user, so they start hidden and can be opened separately.
        show_legend_var = tk.BooleanVar(value=(legend_count <= 12))
        status_var = tk.StringVar()
        legend_state = {'legend': None}

        controls = tk.Frame(win, bg='white')
        controls.pack(side=tk.TOP, fill=tk.X)

        plot_frame = tk.Frame(win, bg='white')
        plot_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = FigureCanvasTkAgg(fig, master=plot_frame)

        def _handle_color(handle):
            try:
                color = handle.get_color()
                if isinstance(color, (list, tuple, np.ndarray)):
                    return str(color)
                return str(color)
            except Exception:
                return ''

        def _handle_style(handle):
            try:
                return str(handle.get_linestyle())
            except Exception:
                return ''

        def open_legend_window():
            legend_win = tk.Toplevel(win)
            legend_win.title(f"Spectrum legend ({legend_count} entries)")
            legend_win.geometry("650x500")

            top = tk.Frame(legend_win)
            top.pack(side=tk.TOP, fill=tk.X, padx=6, pady=4)

            tk.Label(
                top,
                text="Full legend. Use this instead of a very large in-plot legend.",
                anchor='w'
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)

            def copy_labels():
                try:
                    pyperclip.copy("\n".join(text for _, text in legend_entries))
                    messagebox.showinfo("Copied", "Legend labels copied to clipboard.")
                except Exception as exc:
                    messagebox.showerror("Copy error", f"Could not copy labels:\n{exc}")

            tk.Button(top, text="Copy labels", command=copy_labels).pack(side=tk.RIGHT, padx=4)

            table_frame = tk.Frame(legend_win)
            table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

            columns = ('label', 'color', 'style')
            tree = ttk.Treeview(table_frame, columns=columns, show='headings')
            tree.heading('label', text='Label')
            tree.heading('color', text='Color')
            tree.heading('style', text='Line style')
            tree.column('label', width=420, anchor='w')
            tree.column('color', width=100, anchor='center')
            tree.column('style', width=80, anchor='center')

            yscroll = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
            xscroll = ttk.Scrollbar(table_frame, orient='horizontal', command=tree.xview)
            tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

            tree.grid(row=0, column=0, sticky='nsew')
            yscroll.grid(row=0, column=1, sticky='ns')
            xscroll.grid(row=1, column=0, sticky='ew')
            table_frame.rowconfigure(0, weight=1)
            table_frame.columnconfigure(0, weight=1)

            for handle, text in legend_entries:
                tree.insert('', tk.END, values=(text, _handle_color(handle), _handle_style(handle)))

        def update_legend():
            old_legend = legend_state.get('legend')
            if old_legend is not None:
                try:
                    old_legend.remove()
                except Exception:
                    pass
                legend_state['legend'] = None

            if show_legend_var.get() and legend_entries:
                max_inside_entries = 24
                entries_to_show = legend_entries[:max_inside_entries]
                handles_to_show = [h for h, _ in entries_to_show]
                labels_to_show = [t for _, t in entries_to_show]
                ncol = 1 if len(labels_to_show) <= 10 else min(4, int(np.ceil(len(labels_to_show) / 10)))
                title = 'Legend'
                if legend_count > max_inside_entries:
                    title = f'Legend, first {max_inside_entries}/{legend_count}'
                legend_state['legend'] = ax.legend(
                    handles_to_show,
                    labels_to_show,
                    fontsize=7,
                    loc='upper right',
                    ncol=ncol,
                    title=title,
                    frameon=True,
                    borderaxespad=0.3
                )
                status_var.set(f"Legend shown inside plot ({min(legend_count, max_inside_entries)}/{legend_count} entries).")
            else:
                if legend_count > 12:
                    status_var.set(f"Legend hidden to keep the spectrum readable ({legend_count} entries). Use 'Open legend'.")
                else:
                    status_var.set(f"Legend hidden ({legend_count} entries).")

            canvas.draw_idle()

        legend_check = tk.Checkbutton(
            controls,
            text="Show compact legend",
            variable=show_legend_var,
            command=update_legend,
            bg='white'
        )
        legend_check.pack(side=tk.LEFT, padx=(8, 4), pady=4)

        tk.Button(
            controls,
            text="Open legend",
            command=open_legend_window
        ).pack(side=tk.LEFT, padx=4, pady=4)

        tk.Label(
            controls,
            textvariable=status_var,
            bg='white',
            anchor='w'
        ).pack(side=tk.LEFT, padx=8, fill=tk.X, expand=True)

        if overlay_lines:
            self._attach_voigt_hover(fig, ax, canvas, overlay_lines)

        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        update_legend()
        canvas.draw()

    def plot_official_style_diagnostics(self):
        """Plot official-style diagnostics including raw OceanFX/Avantes spectrum."""
        if not self.processed_data:
            return messagebox.showinfo("No data", "Load one or more shots first.")

        win = tk.Toplevel(self.app)
        win.title("Official-style diagnostics")
        win.geometry("1350x950")

        fig = Figure(figsize=(13, 9), facecolor='white')
        gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 1.05])
        ax_ip = fig.add_subplot(gs[0, 0])
        ax_ha = fig.add_subplot(gs[0, 1])
        ax_coils = fig.add_subplot(gs[1, 0])
        ax_bt = fig.add_subplot(gs[1, 1])
        ax_spec = fig.add_subplot(gs[2, :])

        for idx, d in enumerate(self.processed_data):
            color = self.get_color_for_data(d, fallback_index=idx)
            label = self.get_plot_label_for_data(d)
            Time_ms = np.asarray(d.get('Time', np.array([])), dtype=float) * 1000.0
            if Time_ms.size == 0:
                continue

            # Panel 1: Ip and loop voltage.
            Ip_kA = np.asarray(d.get('Ip', np.zeros_like(Time_ms)), dtype=float) / 1000.0
            ax_ip.plot(Time_ms, Ip_kA, color=color, label=f'Ip {label}')
            vloop = np.asarray(d.get('Vloop_2_7_V', np.array([])), dtype=float)
            if vloop.size == Time_ms.size and np.any(np.isfinite(vloop)):
                ax_ip_2 = getattr(ax_ip, '_right_axis', None)
                if ax_ip_2 is None:
                    ax_ip_2 = ax_ip.twinx()
                    ax_ip._right_axis = ax_ip_2
                    ax_ip_2.set_ylabel('(VL2+VL7)/2 [V]')
                ax_ip_2.plot(Time_ms, vloop, color=color, linestyle='--', alpha=0.7, label=f'(VL2+VL7)/2 {label}')

            # Panel 2: H-alpha/visible emission. Use positive official-style signal.
            ha = np.asarray(d.get('Photod', np.zeros_like(Time_ms)), dtype=float)
            ax_ha.plot(Time_ms, ha, color=color, label=label)

            # Panel 3: CS and PF currents.
            cs = np.asarray(d.get('CS_current_kA', np.array([])), dtype=float)
            if cs.size == Time_ms.size:
                ax_coils.plot(Time_ms, cs, color=color, label=f'CS {label}')
            pf1 = np.asarray(d.get('PF1_current_kA', np.array([])), dtype=float)
            pf2 = np.asarray(d.get('PF2_current_kA', np.array([])), dtype=float)
            pf3 = np.asarray(d.get('PF3_current_kA', np.array([])), dtype=float)
            pf4 = np.asarray(d.get('PF4_current_kA', np.array([])), dtype=float)
            if pf1.size == Time_ms.size and pf2.size == Time_ms.size:
                ax_coils.plot(Time_ms, 5.0 * (pf1 + pf2) / 2.0, color=color, linestyle='--', alpha=0.75, label=f'PF1/2 x5 {label}')
            if pf3.size == Time_ms.size and pf4.size == Time_ms.size:
                ax_coils.plot(Time_ms, 5.0 * (pf3 + pf4) / 2.0, color=color, linestyle=':', alpha=0.85, label=f'PF3/4 x5 {label}')

            # Panel 4: toroidal magnetic field.
            bt = np.asarray(d.get('B_phi', np.array([])), dtype=float)
            if bt.size == Time_ms.size:
                ax_bt.plot(Time_ms, bt, color=color, label=label)

            # Panel 5: raw survey visible spectrum. This intentionally does NOT
            # use tau/current normalization, so it resembles the official viewer.
            wl, spec_raw, spec_label, spec_key = self.get_selected_spectrum_arrays(d, use_rw=False)
            if wl.size == spec_raw.size and wl.size > 2:
                mask = np.isfinite(wl) & np.isfinite(spec_raw) & (wl >= 350.0) & (wl <= 900.0)
                if np.any(mask):
                    ax_spec.plot(wl[mask], spec_raw[mask], color=color, label=f'{label} ({spec_label})')

        ax_ip.set_title('Plasma current and loop voltage')
        ax_ip.set_xlabel('time [ms]')
        ax_ip.set_ylabel('Ip [kA]')
        ax_ip.grid(True, alpha=0.3)
        ax_ip.legend(fontsize=8, loc='best')
        if getattr(ax_ip, '_right_axis', None) is not None:
            ax_ip._right_axis.legend(fontsize=8, loc='upper right')

        ax_ha.set_title('H-alpha / visible emission')
        ax_ha.set_xlabel('time [ms]')
        ax_ha.set_ylabel('relative intensity [a.u.]')
        ax_ha.grid(True, alpha=0.3)
        ax_ha.legend(fontsize=8, loc='best')

        ax_coils.set_title('CS and PF coils currents')
        ax_coils.set_xlabel('time [ms]')
        ax_coils.set_ylabel('current [kA]')
        ax_coils.grid(True, alpha=0.3)
        ax_coils.legend(fontsize=8, loc='best')

        ax_bt.set_title('Toroidal magnetic field')
        ax_bt.set_xlabel('time [ms]')
        ax_bt.set_ylabel('Bt [mT]')
        ax_bt.grid(True, alpha=0.3)
        ax_bt.legend(fontsize=8, loc='best')

        ax_spec.set_title(f'Survey visible spectrum, raw counts ({getattr(self, "spectrum_source_mode", "Auto")})')
        ax_spec.set_xlabel('wavelength [nm]')
        ax_spec.set_ylabel('intensity [counts]')
        ax_spec.grid(True, alpha=0.3)
        ax_spec.legend(fontsize=8, loc='best')

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=win)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        canvas.draw()

    def show_spectroscopy_filter_options(self):
        """Compact quick spectroscopy candidate window.

        This is intentionally the fast/visual stage only: it does not run Voigt.
        It lets the user select local NIST files, draw quick candidate marks on
        the main spectrum panel, and inspect candidate tables that indicate which
        lines are worth fitting later in the detailed Voigt analysis.
        """
        options = get_nist_file_options()
        if options.empty:
            self.show_dataframe_window(
                list_local_nist_files(),
                title="Quick spectroscopy candidates - local NIST files",
                default_filename_base="nist_emission_line_options"
            )
            return

        win = tk.Toplevel(self.app)
        win.title("Quick spectroscopy candidates - NIST preview")
        win.geometry("900x560")

        info = tk.Label(
            win,
            text=(
                "Fast preview only: select NIST element files and draw possible line candidates on the spectrum.\n"
                "This does not decide the final element identity; use Spectroscopy analysis (Voigt) for fitted lines."
            ),
            justify="left",
            anchor="w"
        )
        info.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(8, 4))

        columns = ("selected", "element", "file", "n_lines", "range", "source")
        tree = ttk.Treeview(win, columns=columns, show="headings", height=14)
        for col, label, width in [
            ("selected", "Use", 55),
            ("element", "Element", 80),
            ("file", "NIST file", 260),
            ("n_lines", "Lines", 70),
            ("range", "λ range [nm]", 150),
            ("source", "λ source", 120),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="center" if col in {"selected", "element", "n_lines"} else "w")
        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=4)

        def row_values(row):
            file_name = str(row.get("file", ""))
            selected = "✓" if file_name in self.selected_nist_files else ""
            lam_min = row.get("lambda_min_nm", np.nan)
            lam_max = row.get("lambda_max_nm", np.nan)
            if pd.notna(lam_min) and pd.notna(lam_max):
                r = f"{float(lam_min):.1f}–{float(lam_max):.1f}"
            else:
                r = ""
            return (
                selected,
                str(row.get("element_guess", "")),
                file_name,
                str(row.get("n_lines", "")),
                r,
                str(row.get("wavelength_source", "")),
            )

        def refresh_tree():
            for item in tree.get_children():
                tree.delete(item)
            for i, row in options.reset_index(drop=True).iterrows():
                tree.insert("", tk.END, iid=str(i), values=row_values(row))

        def selected_iids():
            return list(tree.selection())

        def toggle_selected():
            for iid in selected_iids():
                try:
                    file_name = str(options.iloc[int(iid)].get("file", ""))
                except Exception:
                    continue
                if not file_name:
                    continue
                if file_name in self.selected_nist_files:
                    self.selected_nist_files.remove(file_name)
                else:
                    self.selected_nist_files.add(file_name)
            self.nist_last_matches = pd.DataFrame()
            self.nist_all_matches_cache = None
            self.nist_all_matches_cache_key = None
            self.nist_all_candidates_cache = None
            self.quick_spectroscopy_cache = None
            self.quick_spectroscopy_cache_key = None
            refresh_tree()

        tree.bind("<Double-1>", lambda _event: toggle_selected())
        refresh_tree()

        params_frame = tk.LabelFrame(win, text="Quick candidate parameters")
        params_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=6)

        tol_var = tk.StringVar(value=str(self.nist_match_tolerance_nm))
        rel_var = tk.StringVar(value=str(self.nist_min_relative_peak_height))
        sigma_var = tk.StringVar(value=str(self.nist_noise_sigma_factor))
        max_lines_var = tk.StringVar(value=str(getattr(self, "nist_display_max_lines", 10)))
        quick_n_var = tk.StringVar(value=str(getattr(self, "quick_spectroscopy_top_n", 3)))

        for label, var, width in [
            ("Tolerance [nm]", tol_var, 7),
            ("Min rel. intensity", rel_var, 7),
            ("Noise σ factor", sigma_var, 7),
            ("Marks/shot", max_lines_var, 5),
            ("Table top N/element", quick_n_var, 5),
        ]:
            tk.Label(params_frame, text=label).pack(side=tk.LEFT, padx=(8, 2), pady=6)
            tk.Entry(params_frame, textvariable=var, width=width).pack(side=tk.LEFT, padx=(0, 8), pady=6)

        def read_params():
            try:
                new_tolerance = float(tol_var.get())
                new_rel_height = float(rel_var.get())
                new_sigma = float(sigma_var.get())
                new_max_lines = int(float(max_lines_var.get()))
                new_quick_n = int(float(quick_n_var.get()))
                if new_max_lines < 1 or new_quick_n < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid parameters",
                    "Tolerance, relative height, sigma factor, marks/shot and table top N must be valid numbers."
                )
                return False

            if (
                new_tolerance != getattr(self, "nist_match_tolerance_nm", NIST_MATCH_TOLERANCE_NM)
                or new_rel_height != getattr(self, "nist_min_relative_peak_height", NIST_MIN_RELATIVE_PEAK_HEIGHT)
                or new_sigma != getattr(self, "nist_noise_sigma_factor", NIST_NOISE_SIGMA_FACTOR)
            ):
                self.nist_all_matches_cache = None
                self.nist_all_matches_cache_key = None
                self.nist_all_candidates_cache = None
                self.quick_spectroscopy_cache = None
                self.quick_spectroscopy_cache_key = None

            self.nist_match_tolerance_nm = new_tolerance
            self.nist_min_relative_peak_height = new_rel_height
            self.nist_noise_sigma_factor = new_sigma
            self.nist_display_max_lines = new_max_lines
            self.quick_spectroscopy_top_n = new_quick_n
            return True

        def run_gui_action(action):
            try:
                action()
            except Exception as exc:
                messagebox.showerror(
                    "Quick spectroscopy error",
                    f"The requested quick spectroscopy action failed:\n{type(exc).__name__}: {exc}\n\nCheck the terminal for the full traceback."
                )
                traceback.print_exc()

        def apply_quick_marks():
            if read_params():
                self.plot_data()

        def select_all_quick_files():
            self.selected_nist_files = set(str(x) for x in options['file'].dropna().astype(str).tolist())
            self.nist_last_matches = pd.DataFrame()
            self.nist_all_matches_cache = None
            self.nist_all_matches_cache_key = None
            self.nist_all_candidates_cache = None
            refresh_tree()

        def clear_quick_marks():
            self.selected_nist_files.clear()
            self.nist_last_matches = pd.DataFrame()
            self.nist_all_matches_cache = None
            self.nist_all_matches_cache_key = None
            self.nist_all_candidates_cache = None
            self.quick_spectroscopy_cache = None
            self.quick_spectroscopy_cache_key = None
            refresh_tree()
            self.plot_data()

        def show_quick_candidates_table():
            if read_params():
                self.show_quick_top3_spectroscopy_table()

        def show_quick_global_best_table():
            if not read_params():
                return
            df = self.compute_spectroscopy_best_global_table()
            if df.empty:
                messagebox.showinfo("No quick candidates", "No quick NIST best candidates were found.")
                return
            self.show_dataframe_window(
                df,
                title="Quick NIST best candidate marks",
                default_filename_base="quick_nist_best_candidate_marks",
                plot_callback=self.show_matched_spectroscopy_figure
            )

        def show_all_quick_candidates():
            if not read_params():
                return
            df = self.compute_spectroscopy_candidate_table()
            if df.empty:
                messagebox.showinfo("No quick candidates", "No quick NIST candidates were found.")
                return
            self.show_dataframe_window(
                df,
                title="Quick NIST candidate alternatives",
                default_filename_base="quick_nist_candidate_alternatives"
            )

        btn_frame = tk.Frame(win)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        tk.Button(btn_frame, text="Toggle selected overlay files", command=lambda: run_gui_action(toggle_selected)).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Select all overlay files", command=lambda: run_gui_action(select_all_quick_files)).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Draw selected NIST reference marks", command=lambda: run_gui_action(apply_quick_marks), bg="#d9edf7").pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Clear marks", command=lambda: run_gui_action(clear_quick_marks)).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="List all local NIST files", command=lambda: run_gui_action(lambda: self.show_dataframe_window(list_local_nist_files(), title="Local NIST line files", default_filename_base="nist_emission_line_options"))).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text="Show top N candidates/element (all local files)", command=lambda: run_gui_action(show_quick_candidates_table), bg="#d9edf7").pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="Show quick best marks table", command=lambda: run_gui_action(show_quick_global_best_table)).pack(side=tk.RIGHT, padx=4)
        tk.Button(btn_frame, text="Show all quick candidates", command=lambda: run_gui_action(show_all_quick_candidates)).pack(side=tk.RIGHT, padx=4)

    def show_voigt_analysis_tools(self):
        """Detailed Voigt spectroscopy analysis window.

        This panel contains the slower, physics-oriented spectroscopy workflow:
        H-Balmer calibrated Voigt fits, accepted-line tables, candidate tables,
        and diagnostic plots of the best accepted fits.
        """
        win = tk.Toplevel(self.app)
        win.title("Spectroscopy analysis - Voigt fits")
        win.geometry("820x430")

        info = tk.Label(
            win,
            text=(
                "Detailed spectroscopy analysis uses Voigt fits and H-Balmer calibration.\n"
                "Top-N per element finds the strongest lines of each element. Exhaustive mode starts from the N strongest measured peaks and assigns the best NIST candidate to each one."
            ),
            justify="left",
            anchor="w"
        )
        info.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 4))

        param_frame = tk.LabelFrame(win, text="Voigt fit controls")
        param_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        n_var = tk.StringVar(value=str(getattr(self, "voigt_fit_top_n_per_element", VOIGT_FIT_TOP_N_PER_ELEMENT)))
        important_var = tk.StringVar(value=str(getattr(self, "voigt_full_important_line_count", VOIGT_FIT_IMPORTANT_LINES_DEFAULT)))
        overlay_var = tk.StringVar(value=str(getattr(self, "voigt_overlay_limits_text", "default=5,H=6,Fe=8,W=5,O=3,N=3,C=3,Li=3")))

        tk.Label(param_frame, text="Top-N per element").pack(side=tk.LEFT, padx=(8, 2), pady=8)
        tk.Entry(param_frame, textvariable=n_var, width=5).pack(side=tk.LEFT, padx=(0, 12), pady=8)
        tk.Label(param_frame, text="Exhaustive: strongest measured lines/shot").pack(side=tk.LEFT, padx=(8, 2), pady=8)
        tk.Entry(param_frame, textvariable=important_var, width=6).pack(side=tk.LEFT, padx=(0, 12), pady=8)
        tk.Label(param_frame, text="Overlay limits").pack(side=tk.LEFT, padx=(8, 2), pady=8)
        tk.Entry(param_frame, textvariable=overlay_var, width=42).pack(side=tk.LEFT, padx=(0, 8), pady=8)

        def read_voigt_params():
            try:
                n = int(float(n_var.get()))
                m = int(float(important_var.get()))
                if n < 1 or m < 1:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Invalid Voigt parameters", "Top-N per element and important lines/shot must be integers >= 1.")
                return False
            self.voigt_fit_top_n_per_element = n
            self.voigt_full_important_line_count = m
            self.voigt_overlay_limits_text = overlay_var.get().strip() or self.voigt_overlay_limits_text
            return True

        def run_gui_action(action):
            try:
                action()
            except Exception as exc:
                messagebox.showerror(
                    "Voigt spectroscopy error",
                    f"The requested Voigt spectroscopy action failed:\n{type(exc).__name__}: {exc}\n\nCheck the terminal for the full traceback."
                )
                traceback.print_exc()

        def run_voigt_fit():
            if read_voigt_params():
                self.fit_voigt_spectroscopy_gui()

        def run_full_important_fit():
            if read_voigt_params():
                self.fit_voigt_important_lines_gui()

        def plot_best_fits():
            if read_voigt_params():
                self.plot_voigt_fit_diagnostics()

        def plot_candidate_fits():
            if read_voigt_params():
                self.plot_voigt_candidate_fit_diagnostics()

        def show_overlay_in_sources():
            if not read_voigt_params():
                return
            self.voigt_fit_overlay_enabled = True
            self.plot_spectrum_sources()

        def toggle_overlay_state():
            if read_voigt_params():
                self.toggle_voigt_fit_overlay()
                state = 'ON' if getattr(self, 'voigt_fit_overlay_enabled', False) else 'OFF'
                messagebox.showinfo('Voigt overlay', f'Voigt overlay is now {state}. Use "Show accepted fits on Spectrum sources" to open/redraw the spectrum window.')

        table_frame = tk.LabelFrame(win, text="Tables and exports")
        table_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)
        plot_frame = tk.LabelFrame(win, text="Fit diagnostics")
        plot_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)

        tk.Button(param_frame, text="1) Apply parameters", command=lambda: run_gui_action(read_voigt_params), bg="#fff2cc").pack(side=tk.LEFT, padx=6)
        tk.Button(param_frame, text="2A) Run top-N per element Voigt fit", command=lambda: run_gui_action(run_voigt_fit), bg="#d8f3dc").pack(side=tk.LEFT, padx=6)
        tk.Button(param_frame, text="2B) Exhaustive top measured lines + plot", command=lambda: run_gui_action(run_full_important_fit), bg="#cdeffd").pack(side=tk.LEFT, padx=6)

        tk.Button(table_frame, text="Show accepted/best Voigt lines table", command=lambda: run_gui_action(self.show_voigt_best_table), bg="#d8f3dc").pack(side=tk.LEFT, padx=6, pady=8)
        tk.Button(table_frame, text="Show attempted candidate fits table", command=lambda: run_gui_action(self.show_voigt_candidate_table), bg="#d8f3dc").pack(side=tk.LEFT, padx=6, pady=8)
        tk.Button(table_frame, text="Export accepted + candidate Voigt tables", command=lambda: run_gui_action(self.export_voigt_spectroscopy_analysis)).pack(side=tk.LEFT, padx=6, pady=8)

        tk.Button(plot_frame, text="Plot accepted best fits", command=lambda: run_gui_action(plot_best_fits), bg="#d8f3dc").pack(side=tk.LEFT, padx=6, pady=8)
        tk.Button(plot_frame, text="Plot attempted candidate fits", command=lambda: run_gui_action(plot_candidate_fits), bg="#cdeffd").pack(side=tk.LEFT, padx=6, pady=8)
        tk.Button(plot_frame, text="Show current accepted fits on Spectrum sources", command=lambda: run_gui_action(show_overlay_in_sources), bg="#d8f3dc").pack(side=tk.LEFT, padx=6, pady=8)
        tk.Button(plot_frame, text="Overlay state ON/OFF", command=lambda: run_gui_action(toggle_overlay_state)).pack(side=tk.LEFT, padx=6, pady=8)

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
            str(getattr(self, 'spectrum_source_mode', 'Auto')),
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
        wl, intensity_norm, spec_meta = self.get_selected_spectroscopy_rw_normalized_arrays(data)
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
        wl_raw, intensity_norm, spec_meta = self.get_selected_spectroscopy_rw_normalized_arrays(data)
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
        """Calibrate spectra with Voigt-fitted H Balmer anchors.

        The calibration used by the detailed Voigt workflow is always based on
        H Balmer lines because H emission is expected in H2 discharges.  This
        GUI callback also stores the same calibration coefficients for the quick
        NIST overlay tables, so both workflows use the same wavelength reference.
        """
        if not self.processed_data:
            messagebox.showinfo("No shots", "Load at least one shot before calibrating spectroscopy.")
            return

        all_rows = []
        calibrated_count = 0
        for data in self.processed_data:
            wl_raw, y_raw, source_label, source_key = self.get_selected_spectrum_arrays(data, use_rw=False)
            wl_raw = np.asarray(wl_raw, dtype=float)
            y_raw = np.asarray(y_raw, dtype=float)
            if wl_raw.size < VOIGT_FIT_MIN_POINTS or wl_raw.shape != y_raw.shape:
                continue
            finite = np.isfinite(wl_raw) & np.isfinite(y_raw)
            wl_raw = wl_raw[finite]
            y_raw = y_raw[finite]
            if wl_raw.size < VOIGT_FIT_MIN_POINTS:
                continue
            order = np.argsort(wl_raw)
            wl_raw = wl_raw[order]
            y_raw = y_raw[order]

            cal_df, coeffs = estimate_voigt_hydrogen_wavelength_calibration(wl_raw, y_raw)
            if cal_df is not None and not cal_df.empty:
                cal_df = cal_df.copy()
                cal_df.insert(0, 'shot', data.get('shot_number', ''))
                cal_df.insert(1, 'spectrum_source', source_label)
                all_rows.append(cal_df)

            if coeffs is not None and len(coeffs) >= 2:
                data['spectroscopy_calibration_coefficients'] = [float(c) for c in coeffs]
                data['spectroscopy_calibration_enabled'] = True
                data['spectroscopy_calibration_label'] = (
                    f"Voigt H-Balmer wavelength calibration degree {min(2, len(coeffs)-1)} ({source_label})"
                )
                data['spectroscopy_calibration_anchors'] = cal_df.to_dict(orient='records') if cal_df is not None else []
                calibrated_count += 1
            else:
                data['spectroscopy_calibration_coefficients'] = None
                data['spectroscopy_calibration_enabled'] = False
                data['spectroscopy_calibration_label'] = 'not enough H Balmer Voigt anchors'
                data['spectroscopy_calibration_anchors'] = []

        self.spectroscopy_calibration_enabled = calibrated_count > 0
        self.nist_all_matches_cache = None
        self.nist_all_matches_cache_key = None
        self.nist_all_candidates_cache = None
        self.voigt_best_cache = None
        self.voigt_candidate_cache = None
        self.voigt_cache_key = None

        result_df = pd.concat(all_rows, ignore_index=True) if all_rows else pd.DataFrame()
        self.spectroscopy_last_calibration_table = result_df

        if result_df.empty:
            messagebox.showwarning(
                "H-Balmer calibration",
                "No usable H Balmer lines were found with the current spectrum source.\n"
                "Try Spectrum: Oceanfx/Avantes/Auto and check Spectrum sources."
            )
            return

        messagebox.showinfo(
            "H-Balmer calibration",
            f"Voigt H-Balmer calibration applied to {calibrated_count} shot(s).\n"
            "H-alpha is fitted with the saturated/censored treatment when needed."
        )
        self.show_dataframe_window(
            result_df,
            title="Voigt H-Balmer wavelength calibration",
            default_filename_base="voigt_h_balmer_wavelength_calibration"
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
            wl_raw_for_match, _, _ = self.get_selected_spectroscopy_rw_normalized_arrays(data)
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

    def _compute_selected_nist_reference_overlay_rows(self):
        """Return direct NIST reference marks for the selected quick-overlay files.

        This routine is for drawing reference marks, not for deciding the final
        element identity.  Therefore it must not require that a local peak is
        already detected within the tolerance window.  Earlier versions ranked
        reference marks by the measured local intensity around each NIST line;
        this made important lines such as H-alpha disappear when the calibration
        was slightly offset, when switching between OceanFX/Avantes, or when the
        local peak was just outside the tolerance.  The new logic draws selected
        NIST reference wavelengths directly and only uses the spectrum to choose
        the plotted coordinate system and to provide optional diagnostic columns.
        """
        if not self.selected_nist_files or not self.processed_data:
            return pd.DataFrame()

        selected = self.get_selected_nist_dataframes()
        if not selected:
            return pd.DataFrame()

        rows = []
        max_lines = int(max(1, getattr(self, 'nist_display_max_lines', 10)))
        tol = float(max(getattr(self, 'nist_match_tolerance_nm', NIST_MATCH_TOLERANCE_NM), 0.60))
        balmer_priority = {name: 10_000 - i for i, (name, _) in enumerate(HYDROGEN_BALMER_LINES_NM)}

        for shot_order, data in enumerate(self.processed_data):
            shot = data.get('shot_number', '')
            wl_raw, y_raw, source_label, source_key = self.get_selected_spectrum_arrays(data, use_rw=False)
            wl_raw = np.asarray(wl_raw, dtype=float)
            y_raw = np.asarray(y_raw, dtype=float)
            if wl_raw.size < 3 or wl_raw.shape != y_raw.shape:
                continue
            finite = np.isfinite(wl_raw) & np.isfinite(y_raw)
            wl_raw = wl_raw[finite]
            y_raw = y_raw[finite]
            if wl_raw.size < 3:
                continue
            order = np.argsort(wl_raw)
            wl_raw = wl_raw[order]
            y_raw = y_raw[order]

            coeffs = data.get('spectroscopy_calibration_coefficients', None)
            if coeffs is not None:
                wl_match_axis = apply_wavelength_calibration(wl_raw, coeffs)
                cal_order = np.argsort(wl_match_axis)
                wl_cal_sorted = wl_match_axis[cal_order]
                wl_raw_sorted = wl_raw[cal_order]
                calibration_label = 'calibrated'
            else:
                wl_match_axis = wl_raw.copy()
                wl_cal_sorted = wl_raw.copy()
                wl_raw_sorted = wl_raw.copy()
                calibration_label = 'raw'

            finite_cal = wl_match_axis[np.isfinite(wl_match_axis)]
            if finite_cal.size:
                axis_min = float(np.nanmin(finite_cal))
                axis_max = float(np.nanmax(finite_cal))
            else:
                axis_min, axis_max = float(np.nanmin(wl_raw)), float(np.nanmax(wl_raw))
            margin_nm = max(5.0, 2.0 * tol)

            for element_label, file_name, nist_df in selected:
                elem_norm_file = normalize_element_label(element_label)
                local_rows = []

                def add_reference_row(line, lam, forced_balmer_name=''):
                    if not np.isfinite(lam):
                        return
                    # Keep only reference lines that can appear in the displayed
                    # spectrometer range, with a small margin for calibration shifts.
                    if lam < axis_min - margin_nm or lam > axis_max + margin_nm:
                        return

                    elem, ion, spectrum_label = extract_ionization_state(element_label, line, file_name)
                    elem = elem or elem_norm_file
                    nist_intensity, nist_num, nist_src = nist_strength_from_row(line)
                    strength_num = float(nist_num) if np.isfinite(nist_num) else 0.0

                    # Optional local diagnostics only.  These values no longer
                    # decide whether the reference line is drawn.
                    local_peak = np.nan
                    local_peak_wl_cal = np.nan
                    local_bg = np.nan
                    local_excess = np.nan
                    local_area = np.nan
                    local_has_samples = False
                    mask = (wl_match_axis >= lam - tol) & (wl_match_axis <= lam + tol)
                    if np.sum(mask) >= 1:
                        xx = wl_match_axis[mask]
                        yy = y_raw[mask]
                        if yy.size:
                            local_has_samples = True
                            peak_idx = int(np.nanargmax(yy))
                            local_peak = float(yy[peak_idx])
                            local_peak_wl_cal = float(xx[peak_idx])
                            local_bg = float(np.nanpercentile(yy, 15)) if yy.size >= 3 else float(np.nanmin(yy))
                            local_excess = max(local_peak - local_bg, 0.0)
                            local_area = float(safe_area(xx, positive_part(yy - local_bg))) if xx.size >= 2 else local_excess

                    balmer = get_hydrogen_balmer_match(lam, tolerance_nm=0.20) if elem == 'H' else None
                    balmer_name = forced_balmer_name or (balmer[0] if balmer else '')
                    is_balmer = bool(balmer_name)
                    # H-alpha/H-beta/etc. are forced to the top for H overlays.
                    # Other lines are ordered mostly by NIST line strength, with
                    # a small measured-signal diagnostic tiebreaker when present.
                    if is_balmer:
                        priority = balmer_priority.get(balmer_name, 9000)
                    else:
                        priority = 0
                    # Reference marks should be deterministic catalogue marks.
                    # Do not let the measured local spectrum decide whether a
                    # line is drawn; the local values are diagnostic only.  This
                    # avoids different behavior between OceanFX/Avantes or
                    # between shots when the same NIST file is selected.
                    strength_term = np.log10(max(strength_num, 0.0) + 1.0)
                    score = priority + 10.0 * strength_term

                    lam_plot_raw = (
                        float(np.interp(lam, wl_cal_sorted, wl_raw_sorted, left=np.nan, right=np.nan))
                        if wl_cal_sorted.size >= 2 else float(lam)
                    )
                    local_rows.append({
                        'shot': shot,
                        'shot_order': shot_order,
                        'type of element': elem,
                        'ionization_state': ion,
                        'spectrum_label': spectrum_label,
                        'source_file': file_name,
                        'wavelength': float(lam),
                        'lambda_nist_nm': float(lam),
                        'lambda_plot_raw_nm': lam_plot_raw,
                        'lambda_plot_calibrated_nm': float(lam),
                        'experimental_peak_calibrated_nm': local_peak_wl_cal,
                        'local_peak_intensity': local_peak,
                        'local_background': local_bg,
                        'local_excess': local_excess,
                        'local_integrated_intensity': local_area,
                        'quick_overlay_score': score,
                        'quick_overlay_priority': priority,
                        'is_forced_balmer_reference': is_balmer,
                        'balmer_reference_name': balmer_name,
                        'local_samples_in_tolerance': local_has_samples,
                        'wavelength_source': line.get('lambda_source', '') if line is not None else 'canonical_balmer',
                        'nist_relative_intensity': nist_intensity,
                        'nist_relative_intensity_numeric': nist_num,
                        'nist_intensity_source': nist_src,
                        'spectrum_source': source_label,
                        'spectrum_source_key': source_key,
                        'wavelength_calibration': calibration_label,
                    })

                # Add all NIST lines in range.  This is a true reference overlay:
                # line selection is independent of whether the measured peak was
                # detected locally for this shot/source.
                for _, line in nist_df.iterrows():
                    lam = nist_cell_to_float(line.get('lambda_nm', np.nan))
                    add_reference_row(line, lam)

                # Extra safety: if the selected file is hydrogen, always include
                # canonical Balmer references even if the local file is incomplete
                # or if NIST labels/strengths are unusual.  This guarantees H-alpha
                # is drawn in the preview.
                if elem_norm_file == 'H':
                    existing_lams = []
                    for rr in local_rows:
                        try:
                            existing_lams.append(float(rr.get('lambda_nist_nm', np.nan)))
                        except Exception:
                            pass
                    for balmer_name, balmer_lam in HYDROGEN_BALMER_LINES_NM:
                        if not any(abs(float(balmer_lam) - x) <= 0.08 for x in existing_lams if np.isfinite(x)):
                            synthetic = pd.Series({
                                'lambda_nm': float(balmer_lam),
                                'lambda_source': 'canonical_balmer_air',
                                'nist_strength': '',
                                'nist_relative_intensity_numeric': np.nan,
                            })
                            add_reference_row(synthetic, float(balmer_lam), forced_balmer_name=balmer_name)

                if not local_rows:
                    continue
                edf = pd.DataFrame(local_rows)
                # Remove exact/near duplicates within a selected file, keeping the
                # physically privileged Balmer row or the strongest reference row.
                edf['_lambda_round_for_overlay'] = edf['lambda_nist_nm'].round(3)
                edf = (edf.sort_values(
                        ['quick_overlay_priority', 'quick_overlay_score', 'lambda_nist_nm'],
                        ascending=[False, False, True]
                    )
                    .drop_duplicates(subset=['type of element', 'source_file', '_lambda_round_for_overlay'], keep='first')
                    .drop(columns=['_lambda_round_for_overlay'])
                )
                edf = edf.sort_values(
                    ['quick_overlay_priority', 'quick_overlay_score', 'lambda_nist_nm'],
                    ascending=[False, False, True]
                )

                # Hydrogen special case: the Balmer series is not optional for
                # this preview.  Always draw the canonical Balmer references
                # that are inside the spectrometer range, including H-alpha,
                # and then fill the remaining Marks/shot slots with the
                # strongest extra H catalogue lines.  This fixes the case where
                # Marks/shot=10 still showed only H-gamma/H-beta because the
                # previous top-N truncation or catalogue ranking hid the rest.
                if elem_norm_file == 'H' and 'is_forced_balmer_reference' in edf.columns:
                    balmer_order = {name: i for i, (name, _) in enumerate(HYDROGEN_BALMER_LINES_NM)}
                    balmer_mask = edf['is_forced_balmer_reference'].astype(bool)
                    balmer_df = edf[balmer_mask].copy()
                    extra_df = edf[~balmer_mask].copy()
                    if not balmer_df.empty:
                        balmer_df['_balmer_order_for_overlay'] = balmer_df['balmer_reference_name'].map(balmer_order).fillna(999).astype(int)
                        balmer_df = balmer_df.sort_values(['_balmer_order_for_overlay', 'lambda_nist_nm'])
                        balmer_df = balmer_df.drop(columns=['_balmer_order_for_overlay'])
                    extra_limit = max(int(max_lines) - len(balmer_df), 0)
                    edf_to_draw = pd.concat([balmer_df, extra_df.head(extra_limit)], ignore_index=True)
                else:
                    edf_to_draw = edf.head(max_lines).copy()

                edf_to_draw['quick_overlay_rank_for_file'] = np.arange(1, len(edf_to_draw) + 1)
                rows.append(edf_to_draw)

        if not rows:
            return pd.DataFrame()
        out = pd.concat(rows, ignore_index=True)
        out = out.sort_values(['shot_order', 'type of element', 'quick_overlay_rank_for_file']).reset_index(drop=True)
        return out

    def plot_selected_nist_lines(self):
        """Overlay selected NIST reference/candidate lines on the spectrum panel.

        This preview is deliberately not restricted to the globally accepted
        candidate.  If Li is selected, it draws the strongest Li local reference
        lines even when H/Fe/W wins the physical assignment.
        """
        if not self.selected_nist_files or not self.processed_data:
            self.nist_last_matches = pd.DataFrame()
            return

        df = self._compute_selected_nist_reference_overlay_rows()
        self.nist_last_matches = df
        if df.empty:
            return

        ymax = self.ax_avantes.get_ylim()[1] if self.ax_avantes.has_data() else 1.0
        shown_labels = set()
        max_labels = 45
        label_count = 0

        for _, row in df.iterrows():
            try:
                lam_nist = float(row.get('lambda_nist_nm', row.get('wavelength', np.nan)))
                if self.overlay_uses_calibrated_axis():
                    lam_plot = float(row.get('lambda_plot_calibrated_nm', lam_nist))
                else:
                    lam_plot = float(row.get('lambda_plot_raw_nm', row.get('wavelength', np.nan)))
            except Exception:
                continue
            if not np.isfinite(lam_plot):
                continue
            elem = normalize_element_label(row.get('type of element', ''))
            ion = str(row.get('ionization_state', '')).strip()
            color = VOIGT_ELEMENT_COLORS.get(elem, 'black')
            self.ax_avantes.axvline(
                lam_plot,
                linestyle='--',
                linewidth=1.15 if elem == 'H' else 0.9,
                alpha=0.90 if elem == 'H' else 0.65,
                color=color,
                zorder=30,
            )
            if label_count < max_labels:
                label = f"{elem} {ion} {lam_nist:.2f}".strip()
                key = (elem, ion, round(lam_nist, 3))
                if key not in shown_labels:
                    self.ax_avantes.text(
                        lam_plot,
                        0.96,
                        label,
                        rotation=90,
                        transform=self.ax_avantes.get_xaxis_transform(),
                        fontsize=7,
                        va='top',
                        ha='center',
                        alpha=0.86,
                        color=color,
                    )
                    shown_labels.add(key)
                    label_count += 1

        self.ax_avantes.text(
            0.01,
            0.98,
            f"Quick NIST preview: {', '.join(sorted({str(x) for x in df['type of element'].unique()}))} | top {getattr(self, 'nist_display_max_lines', 10)} lines/file | overlay {self.get_overlay_axis_label()}",
            transform=self.ax_avantes.transAxes,
            fontsize=8,
            va='top',
            ha='left',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none')
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
                "Bt and coils keep physical time; Ip, H-alpha and loop voltage use tau.\n"
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
        """Set axis labels safely for selected panels and residual layouts."""
        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            if ax is not None:
                ax.set_facecolor('white')

        mode = self.normalization_mode

        if self.display_time_mode == DISPLAY_RAW:
            bt_time_label = "Time [ms]"
            ip_time_label = "Time [ms]"
            ha_time_label = "Time [ms]"
            loop_time_label = "Time [ms]"
            coils_time_label = "Time [ms]"
        else:
            bt_time_label = "Time - t_Ip,start [ms]"
            ip_time_label = "Time - t_Ip,start [ms]"
            ha_time_label = "Time - t_Ip,start [ms]"
            loop_time_label = "Time - t_Ip,start [ms]"
            coils_time_label = "Time - t_Ip,start [ms]"

        if mode == NORMALIZATION_NONE:
            ip_label = "Ip [kA]"
            ha_label = "H-alpha [a.u.]"
            spec_label = "S_raw [a.u.]"
        elif mode == NORMALIZATION_TAU:
            bt_time_label = "tau [-]"
            ip_time_label = "tau [-]"
            ha_time_label = "tau [-]"
            loop_time_label = "tau [-]"
            ip_label = "Ip(tau) [kA]"
            ha_label = "H-alpha(tau) [a.u.]"
            spec_label = "S_raw / Δt_p [a.u./ms]"
        elif mode == NORMALIZATION_TAU_MAX:
            bt_time_label = "tau [-]"
            ip_time_label = "tau [-]"
            ha_time_label = "tau [-]"
            loop_time_label = "tau [-]"
            ip_label = "Ip(tau) / Ip,max_rep"
            ha_label = "H-alpha(tau) / Ip,max_rep"
            spec_label = "(S_raw/Δt_p) / Ip,max_rep"
        elif mode == NORMALIZATION_TAU_AREA:
            bt_time_label = "tau [-]"
            ip_time_label = "tau [-]"
            ha_time_label = "tau [-]"
            loop_time_label = "tau [-]"
            ip_label = "Ip_pos(tau) / int(Ip_pos(tau)dtau)"
            ha_label = "H-alpha(tau) / int(Ip_pos(tau)dtau)"
            spec_label = "S_raw / (dt_p * int(Ip_pos(tau)dtau))"
        else:
            ip_label = "Ip [kA]"
            ha_label = "H-alpha [a.u.]"
            spec_label = "S_raw [a.u.]"

        if self.ax_bt is not None:
            self.ax_bt.set_ylabel('Bt [mT]')
        if self.ax_ip is not None:
            self.ax_ip.set_ylabel(ip_label)
        if self.ax_loop is not None:
            if mode == NORMALIZATION_NONE:
                self.ax_loop.set_ylabel("(VL2+VL7)/2 [V]")
            else:
                self.ax_loop.set_ylabel("Vloop(tau) [V]")
        if self.ax_halpha is not None:
            self.ax_halpha.set_ylabel(ha_label)
        if self.ax_avantes is not None:
            self.ax_avantes.set_ylabel(spec_label)
        if self.ax_coils is not None:
            self.ax_coils.set_ylabel('coil current [kA]')

        if self.show_residuals:
            if self.ax_bt_residual is not None:
                self.ax_bt_residual.set_ylabel('Delta Bt [mT]')
                self.ax_bt_residual.set_xlabel(bt_time_label)
            if self.ax_ip_residual is not None:
                self.ax_ip_residual.set_ylabel('Delta Ip')
                self.ax_ip_residual.set_xlabel(ip_time_label)
            if self.ax_loop_residual is not None:
                self.ax_loop_residual.set_ylabel("Delta LV")
                self.ax_loop_residual.set_xlabel(loop_time_label)
            if self.ax_halpha_residual is not None:
                self.ax_halpha_residual.set_ylabel('Delta H-alpha')
                self.ax_halpha_residual.set_xlabel(ha_time_label)
            if self.ax_avantes_residual is not None:
                self.ax_avantes_residual.set_ylabel('Delta intensity')
                self.ax_avantes_residual.set_xlabel(self.get_spectrum_x_axis_label())
            if self.ax_coils_residual is not None:
                self.ax_coils_residual.set_ylabel('Delta coils')
                self.ax_coils_residual.set_xlabel(coils_time_label)

            for ax in [self.ax_bt, self.ax_ip, self.ax_loop, self.ax_halpha, self.ax_avantes, self.ax_coils]:
                if ax is not None:
                    ax.tick_params(labelbottom=False)
        else:
            if self.ax_bt is not None:
                self.ax_bt.set_xlabel(bt_time_label)
            if self.ax_ip is not None:
                self.ax_ip.set_xlabel(ip_time_label)
            if self.ax_loop is not None:
                self.ax_loop.set_xlabel(loop_time_label)
            if self.ax_halpha is not None:
                self.ax_halpha.set_xlabel(ha_time_label)
            if self.ax_avantes is not None:
                self.ax_avantes.set_xlabel(self.get_spectrum_x_axis_label())
            if self.ax_coils is not None:
                self.ax_coils.set_xlabel(coils_time_label)

            for ax in [self.ax_bt, self.ax_ip, self.ax_loop, self.ax_halpha, self.ax_avantes, self.ax_coils]:
                if ax is not None:
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

    @staticmethod
    def _normalized_shot_id(value):
        match = re.search(r'\d+', str(value))
        return str(int(match.group(0))) if match else str(value).strip()

    def _video_search_directories(self):
        """Return portable candidates for the repository's shots_s1/videos."""
        module_dir = Path(__file__).resolve().parent
        seeds = [module_dir, Path.cwd().resolve()]
        try:
            seeds.append(Path(sys.argv[0]).resolve().parent)
        except Exception:
            pass
        for data in getattr(self, 'processed_data', []):
            file_path = data.get('file_path', '')
            if file_path:
                try:
                    seeds.append(Path(file_path).resolve().parent)
                except Exception:
                    pass

        directories = []
        configured_directory = os.environ.get('MEPHIST_VIDEO_DIR', '').strip()
        if configured_directory:
            directories.append(Path(configured_directory).expanduser())

        for seed in seeds:
            ancestors = [seed] + list(seed.parents)[:8]
            for base in ancestors:
                directories.extend([
                    base / 'shots_s1' / 'videos',
                    base / 'rto-mephist-main' / 'shots_s1' / 'videos',
                ])
                # Support repositories extracted with a repeated directory name,
                # e.g. rto-mephist-main/rto-mephist-main/shots_s1/videos, without
                # encoding a user-specific Documents path.
                if base.parent != base:
                    try:
                        directories.extend(base.glob('*/shots_s1/videos'))
                        directories.extend(base.glob('*/*/shots_s1/videos'))
                    except OSError:
                        pass
        # A same-directory fallback is convenient for a single downloaded test
        # video, but the project video directory above always has priority.
        directories.append(module_dir)

        unique = []
        seen = set()
        for directory in directories:
            key = os.path.normcase(os.path.abspath(str(directory)))
            if key not in seen:
                seen.add(key)
                unique.append(directory)
        return unique

    def _find_video_for_shot(self, shot_id):
        allowed_extensions = {'.webm', '.mp4', '.avi', '.mov', '.mkv', '.mpeg', '.mpg'}
        shot_text = self._normalized_shot_id(shot_id)
        token_pattern = re.compile(rf'(?<!\d){re.escape(shot_text)}(?!\d)')
        candidates = []
        searched = []

        for directory in self._video_search_directories():
            searched.append(str(directory))
            if not directory.is_dir():
                continue
            for path in directory.iterdir():
                if path.is_file() and path.suffix.lower() in allowed_extensions:
                    if token_pattern.search(path.stem):
                        candidates.append(path)

        candidates = sorted(
            set(candidates),
            key=lambda path: (path.stem != shot_text, len(path.stem), path.name.lower())
        )
        if not candidates:
            return None, searched
        if len(candidates) == 1 or candidates[0].stem == shot_text:
            return candidates[0], searched

        options = '\n'.join(f'{idx + 1}: {path.name}' for idx, path in enumerate(candidates))
        selected = simpledialog.askinteger(
            "Multiple videos",
            f"Multiple videos were found for shot {shot_text}:\n\n{options}\n\nSelect a number:",
            initialvalue=1,
            minvalue=1,
            maxvalue=len(candidates),
            parent=self.master_frame,
        )
        return (candidates[selected - 1] if selected is not None else None), searched

    def compare_with_video(self):
        """Synchronize a shot with its summed fast-camera luminosity curve."""
        if not self.processed_data:
            return messagebox.showinfo(
                "No shots loaded",
                "Load the .nxs file for the shot you want to compare first.",
                parent=self.master_frame,
            )

        loaded_ids = [self._normalized_shot_id(d.get('shot_number', '')) for d in self.processed_data]
        initial_shot = loaded_ids[0] if len(loaded_ids) == 1 else ''
        shot_text = simpledialog.askstring(
            "Compare with video",
            "Shot number (for example, 2621):",
            initialvalue=initial_shot,
            parent=self.master_frame,
        )
        if shot_text is None:
            return
        shot_id = self._normalized_shot_id(shot_text)

        data = next(
            (d for d in self.processed_data
             if self._normalized_shot_id(d.get('shot_number', '')) == shot_id),
            None,
        )
        if data is None:
            return messagebox.showwarning(
                "Shot not loaded",
                f"Shot {shot_id} is not loaded in Shot comparison.",
                parent=self.master_frame,
            )

        video_path, searched = self._find_video_for_shot(shot_id)
        if video_path is None:
            use_manual = messagebox.askyesno(
                "Video not found",
                "No video whose filename contains the exact shot number "
                f"{shot_id} was found in shots_s1/videos.\n\nSelect it manually?",
                parent=self.master_frame,
            )
            if not use_manual:
                return
            manual_path = filedialog.askopenfilename(
                title=f"Select video for shot {shot_id}",
                filetypes=[
                    ("Videos", "*.webm *.mp4 *.avi *.mov *.mkv *.mpeg *.mpg"),
                    ("All files", "*.*"),
                ],
                parent=self.master_frame,
            )
            if not manual_path:
                return
            video_path = Path(manual_path)

        frame_interval_us = simpledialog.askfloat(
            "Physical camera timing",
            "Physical interval between frames [µs].\n\n"
            "Do not use the WebM playback frame rate. In video 2621, "
            "for example, each frame represents 100 µs:",
            initialvalue=VIDEO_DEFAULT_FRAME_INTERVAL_US,
            minvalue=1e-6,
            parent=self.master_frame,
        )
        if frame_interval_us is None:
            return

        sync_with_halpha = messagebox.askyesnocancel(
            "Time reference",
            "Synchronize camera luminosity with H-alpha?\n\n"
            "Yes: common-detector onset followed by a constrained "
            "camera–H-alpha shape correlation.\n"
            "No: selected luminosity start = Ip_start_Ip_only "
            "(physically independent comparison).",
            default=messagebox.NO,
            parent=self.master_frame,
        )
        if sync_with_halpha is None:
            return

        Time = np.asarray(data.get('Time', np.array([])), dtype=float)
        Ip = np.asarray(data.get('Ip', np.array([])), dtype=float)
        Halpha = np.asarray(data.get('Photod', np.array([])), dtype=float)
        Vloop = np.asarray(data.get('Vloop_2_7_V', np.array([])), dtype=float)
        ip_start = float(data.get('Ip_start_time_Ip_only', data.get('Ip_start_time', np.nan)))
        ip_only_end_absolute = float(data.get('Ip_end_time_ip_only', np.nan))
        target_ip_duration_ms = (
            (ip_only_end_absolute - ip_start) * 1000.0
            if np.isfinite(ip_only_end_absolute) and np.isfinite(ip_start)
            and ip_only_end_absolute > ip_start
            else np.nan
        )
        frame_interval_ms = float(frame_interval_us) * 1e-3
        diagnostic_time_ms = (Time - ip_start) * 1000.0

        try:
            self.main_frame.configure(cursor='watch')
            self.main_frame.update_idletasks()
            video_info = extract_video_luminosity(video_path, return_display_frames=True)
            # Total grayscale luminosity always defines the optical episodes and
            # their duration. The red channel is an optional, more H-alpha-like
            # clock signal only; it must not replace broadband duration.
            video_signal_label = 'total grayscale camera luminosity'
            light_info = detect_video_light_window(
                video_info['frame_sums'],
                frame_interval_ms=frame_interval_ms,
                target_duration_ms=target_ip_duration_ms,
            )
            red_frame_sums = np.asarray(
                video_info.get('red_frame_sums', np.array([])), dtype=float
            )
            red_light_info = (
                detect_video_light_window(
                    red_frame_sums,
                    frame_interval_ms=frame_interval_ms,
                    target_duration_ms=target_ip_duration_ms,
                )
                if red_frame_sums.size else None
            )
            halpha_light_info = detect_halpha_with_video_method(
                diagnostic_time_ms,
                Halpha,
                frame_interval_ms=frame_interval_ms,
                target_duration_ms=target_ip_duration_ms,
            )
        except Exception as exc:
            return messagebox.showerror(
                "Video processing error",
                f"The luminosity curve could not be generated:\n{exc}",
                parent=self.master_frame,
            )
        finally:
            try:
                self.main_frame.configure(cursor='')
            except Exception:
                pass

        frame_sums = np.asarray(video_info['frame_sums'], dtype=float)
        corrected = np.asarray(light_info['corrected_luminosity'], dtype=float)
        frame_index = np.arange(frame_sums.size, dtype=float)

        halpha_time_grid_ms = np.asarray(halpha_light_info['time_grid_ms'], dtype=float)
        halpha_corrected = np.asarray(halpha_light_info['corrected_luminosity'], dtype=float)
        halpha_start_idx = int(halpha_light_info['start_idx'])
        halpha_end_idx = int(halpha_light_info['end_idx'])
        halpha_start_relative_ms = float(halpha_time_grid_ms[halpha_start_idx])
        halpha_end_relative_ms = float(halpha_time_grid_ms[halpha_end_idx])
        halpha_duration_ms = max(
            halpha_end_relative_ms - halpha_start_relative_ms, 0.0
        )

        if sync_with_halpha:
            red_corrected = (
                np.asarray(red_light_info['corrected_luminosity'], dtype=float)
                if red_light_info is not None else np.array([], dtype=float)
            )
            synchronization_candidates = build_halpha_video_sync_candidates(
                halpha_time_grid_ms,
                halpha_corrected,
                frame_interval_ms,
                corrected,
                light_info,
                halpha_start_relative_ms,
                halpha_end_relative_ms,
                halpha_duration_ms,
                red_corrected=red_corrected,
                max_candidates=VIDEO_MAX_SYNC_CANDIDATES,
            )
            if not synchronization_candidates:
                return messagebox.showerror(
                    "Video processing error",
                    "No valid camera/H-alpha synchronization candidate could be generated.",
                    parent=self.master_frame,
                )
        else:
            start_idx = int(light_info['start_idx'])
            end_idx = int(light_info['end_idx'])
            base_video_time_ms = (frame_index - start_idx) * frame_interval_ms
            ip_alignment_info = {
                'shift_ms': 0.0,
                'correlation': np.nan,
                'method': 'ip_only_start_alignment',
            }
            synchronization_candidates = [{
                'rank': 1,
                'episode_number': 1,
                'start_idx': start_idx,
                'end_idx': end_idx,
                'duration_ms': (end_idx - start_idx) * frame_interval_ms,
                'halpha_duration_error_ratio': np.nan,
                'base_video_time_ms': base_video_time_ms,
                'video_time_ms': base_video_time_ms,
                'alignment_info': ip_alignment_info,
                'alignment_signal_label': 'Ip-only reference (no optical correlation)',
                'alignment_shift_ms': 0.0,
                'correlation': np.nan,
                'red_alignment_info': {
                    'shift_ms': np.nan,
                    'correlation': np.nan,
                    'method': 'not_requested',
                },
                'total_alignment_info': ip_alignment_info,
            }]

        selected_sync = synchronization_candidates[0]
        start_frame = int(selected_sync['start_idx'])
        end_frame = int(selected_sync['end_idx'])
        base_video_time_ms = np.asarray(selected_sync['base_video_time_ms'], dtype=float)
        video_time_ms = np.asarray(selected_sync['video_time_ms'], dtype=float)
        alignment_info = selected_sync['alignment_info']
        alignment_signal_label = selected_sync['alignment_signal_label']
        total_alignment_info = selected_sync['total_alignment_info']
        red_alignment_info = selected_sync['red_alignment_info']
        video_alignment_shift_ms = float(selected_sync['alignment_shift_ms'])
        video_alignment_label = (
            f'constrained H-alpha correlation using {alignment_signal_label}'
            if sync_with_halpha else 'Ip-only start'
        )

        def _relative_ms(absolute_time):
            try:
                absolute_time = float(absolute_time)
                return (absolute_time - ip_start) * 1000.0 if np.isfinite(absolute_time) else np.nan
            except Exception:
                return np.nan

        ip_only_end_ms = _relative_ms(data.get('Ip_end_time_ip_only', np.nan))
        loop_peak_ms = _relative_ms(data.get('Ip_end_loop_peak_time', np.nan))
        loop_fall_ms = _relative_ms(data.get('Ip_end_loop_fall_time', data.get('Ip_end_time', np.nan)))
        selected_end_ms = _relative_ms(data.get('Ip_end_time', np.nan))
        video_start_ms = float(video_time_ms[start_frame])
        video_end_ms = float(video_time_ms[end_frame])
        display_frames = list(video_info.get('display_frames', []))
        delta_end_ms = video_end_ms - selected_end_ms if np.isfinite(selected_end_ms) else np.nan
        delta_video_peak_ms = (
            video_end_ms - loop_peak_ms if np.isfinite(loop_peak_ms) else np.nan
        )
        delta_video_fall_ms = (
            video_end_ms - loop_fall_ms if np.isfinite(loop_fall_ms) else np.nan
        )
        finite_ip = (
            np.isfinite(diagnostic_time_ms) & np.isfinite(Ip)
            if diagnostic_time_ms.size == Ip.size and Ip.size >= 2
            else np.array([], dtype=bool)
        )
        if finite_ip.size:
            if np.sum(finite_ip) >= 2:
                ip_at_video_end_kA = float(np.interp(
                    video_end_ms,
                    diagnostic_time_ms[finite_ip],
                    Ip[finite_ip],
                )) / 1000.0
                ip_peak_kA = float(np.nanmax(np.abs(Ip[finite_ip]))) / 1000.0
                ip_at_video_end_ratio = (
                    abs(ip_at_video_end_kA) / ip_peak_kA
                    if np.isfinite(ip_peak_kA) and ip_peak_kA > 0 else np.nan
                )
            else:
                ip_at_video_end_kA = np.nan
                ip_at_video_end_ratio = np.nan
        else:
            ip_at_video_end_kA = np.nan
            ip_at_video_end_ratio = np.nan
        duration_error_percent = 100.0 * float(light_info.get('duration_error_ratio', np.nan))
        vloop_fall_percent = 100.0 * float(LOOP_VOLTAGE_END_FALL_FRACTION)
        total_active_runs = list(light_info.get('active_runs', []))
        active_run_duration_text = ', '.join(
            f"#{run_number}: {(run_end - run_start) * frame_interval_ms:.3f} ms"
            for run_number, (run_start, run_end) in enumerate(total_active_runs, start=1)
        ) or 'none'
        red_correlation_value = float(red_alignment_info.get('correlation', np.nan))
        total_correlation_value = float(total_alignment_info.get('correlation', np.nan))
        red_quality_text = (
            'LOW' if np.isfinite(red_correlation_value)
            and red_correlation_value < VIDEO_HALPHA_LOW_CORRELATION_WARNING
            else 'unavailable' if not np.isfinite(red_correlation_value) else 'acceptable'
        )
        total_quality_text = (
            'LOW' if np.isfinite(total_correlation_value)
            and total_correlation_value < VIDEO_HALPHA_LOW_CORRELATION_WARNING
            else 'unavailable' if not np.isfinite(total_correlation_value) else 'acceptable'
        )

        details_text = (
            f"Shot: {shot_id}\n"
            f"Video: {video_path.name}\n"
            f"Decoded frames: {frame_sums.size}\n"
            f"Physical frame interval: {frame_interval_us:g} µs\n"
            f"Playback frame rate: {video_info.get('playback_fps', np.nan):g} fps (not used for timing)\n"
            f"Decoder: {video_info.get('backend', '')}\n\n"
            f"Camera duration signal: {video_signal_label}\n"
            f"Camera alignment signal selected: {alignment_signal_label}\n\n"
            f"Alignment mode: {video_alignment_label}\n"
            f"Alignment method: {alignment_info.get('method', '')}\n"
            f"Camera time shift: {video_alignment_shift_ms:+.3f} ms\n"
            f"Selected camera–H-alpha correlation: "
            f"{alignment_info.get('correlation', np.nan):.3f}\n"
            f"Red-channel correlation: {red_correlation_value:.3f} "
            f"({red_quality_text}); shift={red_alignment_info.get('shift_ms', np.nan):+.3f} ms\n"
            f"Total-luminosity correlation: {total_correlation_value:.3f} "
            f"({total_quality_text}); shift={total_alignment_info.get('shift_ms', np.nan):+.3f} ms\n"
            f"Low-correlation warning threshold: "
            f"{VIDEO_HALPHA_LOW_CORRELATION_WARNING:.2f}\n\n"
            f"H-alpha peak used by alignment: "
            f"{alignment_info.get('halpha_peak_time_ms', np.nan):.3f} ms\n"
            f"Camera peak before alignment: "
            f"{alignment_info.get('video_peak_base_ms', np.nan):.3f} ms\n"
            f"Peak-to-peak suggested shift: "
            f"{alignment_info.get('peak_shift_ms', np.nan):+.3f} ms\n\n"
            f"Ip-only duration: {target_ip_duration_ms:.3f} ms\n"
            f"Selected camera duration: {light_info.get('selected_duration_ms', np.nan):.3f} ms\n"
            f"Total-luminosity episode selection: {light_info.get('method', '')}\n"
            f"Total-luminosity episodes detected: {len(total_active_runs)}\n"
            f"Episode durations: {active_run_duration_text}\n"
            f"Selected total-luminosity frames: {start_frame}–{end_frame}\n"
            f"Selected H-alpha duration: {halpha_light_info.get('selected_duration_ms', np.nan):.3f} ms\n"
            f"H-alpha episode detector: {halpha_light_info.get('method', '')}\n"
            f"Main H-alpha peak: {halpha_light_info.get('main_peak_time_ms', np.nan):.3f} ms\n"
            f"Camera duration mismatch: {duration_error_percent:.1f} %\n\n"
            f"Ip-only start: 0.000 ms\n"
            f"Ip-only end: {ip_only_end_ms:.3f} ms\n"
            f"Camera start: {video_start_ms:.3f} ms\n"
            f"Camera end: {video_end_ms:.3f} ms\n"
            f"H-alpha start: {halpha_start_relative_ms:.3f} ms\n"
            f"H-alpha end: {halpha_end_relative_ms:.3f} ms\n"
            f"Current-quench Vloop peak: {loop_peak_ms:.3f} ms\n"
            f"Vloop {vloop_fall_percent:.0f}% decay end: {loop_fall_ms:.3f} ms\n"
            f"Selected plasma end: {selected_end_ms:.3f} ms\n"
            f"Selected plasma-end method: {data.get('plasma_end_method', '')}\n"
            f"Camera end − Vloop end: {delta_end_ms:+.3f} ms\n\n"
            f"Camera end − Vloop peak: {delta_video_peak_ms:+.3f} ms\n"
            f"Camera end − Vloop {vloop_fall_percent:.0f}% decay: "
            f"{delta_video_fall_ms:+.3f} ms\n"
            f"Ip at camera end: {ip_at_video_end_kA:+.3f} kA "
            f"({100.0 * ip_at_video_end_ratio:.1f}% of |Ip|max)\n\n"
            f"Electrical-end convention: first point after the selected final "
            f"Vloop peak where {100.0 * LOOP_VOLTAGE_END_FALL_FRACTION:.0f}% "
            f"of its local peak-to-right-floor excursion has decayed.\n\n"
            f"Camera threshold: {light_info.get('threshold', np.nan):.6g}\n"
            f"H-alpha threshold: {halpha_light_info.get('threshold', np.nan):.6g}"
        )

        sync_state = {'candidate': selected_sync}

        def _dynamic_details_text(candidate):
            candidate_time = np.asarray(candidate['video_time_ms'], dtype=float)
            candidate_start = int(candidate['start_idx'])
            candidate_end = int(candidate['end_idx'])
            candidate_video_start = float(candidate_time[candidate_start])
            candidate_video_end = float(candidate_time[candidate_end])
            selected_alignment = candidate['alignment_info']
            red_alignment = candidate['red_alignment_info']
            total_alignment = candidate['total_alignment_info']
            duration_error_percent_candidate = 100.0 * float(
                candidate.get('halpha_duration_error_ratio', np.nan)
            )
            if finite_ip.size and np.sum(finite_ip) >= 2:
                candidate_ip_end_kA = float(np.interp(
                    candidate_video_end,
                    diagnostic_time_ms[finite_ip],
                    Ip[finite_ip],
                )) / 1000.0
            else:
                candidate_ip_end_kA = np.nan
            return (
                f"Shot: {shot_id}\n"
                f"Video: {video_path.name}\n"
                f"Synchronization rank: {candidate.get('rank', 1)} "
                f"of {len(synchronization_candidates)}\n"
                f"Evaluated luminous episode: {candidate.get('episode_number', 1)}\n"
                f"Selected frames: {candidate_start}–{candidate_end}\n"
                f"Camera duration: {candidate.get('duration_ms', np.nan):.3f} ms\n"
                f"H-alpha duration: {halpha_duration_ms:.3f} ms\n"
                f"H-alpha duration error: {duration_error_percent_candidate:.1f}%\n\n"
                f"Alignment signal: {candidate['alignment_signal_label']}\n"
                f"Selected correlation: {candidate.get('correlation', np.nan):.3f}\n"
                f"Red-channel correlation: "
                f"{red_alignment.get('correlation', np.nan):.3f}\n"
                f"Total-luminosity correlation: "
                f"{total_alignment.get('correlation', np.nan):.3f}\n"
                f"Alignment method: {selected_alignment.get('method', '')}\n"
                f"Camera time shift: {candidate.get('alignment_shift_ms', np.nan):+.3f} ms\n\n"
                f"Camera start: {candidate_video_start:.3f} ms\n"
                f"Camera end: {candidate_video_end:.3f} ms\n"
                f"H-alpha start: {halpha_start_relative_ms:.3f} ms\n"
                f"H-alpha end: {halpha_end_relative_ms:.3f} ms\n"
                f"Ip at camera end: {candidate_ip_end_kA:+.3f} kA\n"
                f"Camera end − selected plasma end: "
                f"{candidate_video_end - selected_end_ms:+.3f} ms\n\n"
                f"Decoded frames: {frame_sums.size}\n"
                f"Physical frame interval: {frame_interval_us:g} µs\n"
                f"Playback frame rate: {video_info.get('playback_fps', np.nan):g} fps "
                f"(not used for timing)\n"
                f"Detector: {halpha_light_info.get('method', '')}\n"
                f"Candidates evaluated: {len(synchronization_candidates)} "
                f"(maximum {VIDEO_MAX_SYNC_CANDIDATES})"
            )

        def _normalize_positive(values):
            values = np.asarray(values, dtype=float)
            if values.size == 0:
                return values
            positive = np.clip(values, 0.0, None)
            scale = float(np.nanpercentile(positive, 99.0))
            return positive / scale if np.isfinite(scale) and scale > 0 else positive

        window = tk.Toplevel(self.master_frame)
        window.title(f"Shot {shot_id}: diagnostics vs video")
        window.geometry("1500x840")

        info_frame = tk.Frame(window, bg="#f0f0f0")
        info_frame.pack(side=tk.TOP, fill=tk.X)
        compact_summary_var = tk.StringVar()
        tk.Label(info_frame, textvariable=compact_summary_var, bg="#f0f0f0", anchor='w').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=4
        )

        event_marker_artists = []
        event_legend_ref = {'artist': None}
        show_event_markers_var = tk.BooleanVar(value=True)
        show_event_labels_var = tk.BooleanVar(value=False)

        def _toggle_event_labels():
            if bool(show_event_labels_var.get()) and not bool(show_event_markers_var.get()):
                show_event_markers_var.set(True)
                for artist in event_marker_artists:
                    artist.set_visible(True)
            legend = event_legend_ref.get('artist')
            if legend is not None:
                legend.set_visible(
                    bool(show_event_labels_var.get())
                    and bool(show_event_markers_var.get())
                )
            try:
                canvas.draw_idle()
            except NameError:
                pass

        def _toggle_event_markers():
            visible = bool(show_event_markers_var.get())
            for artist in event_marker_artists:
                artist.set_visible(visible)
            if not visible:
                show_event_labels_var.set(False)
            _toggle_event_labels()
            try:
                canvas.draw_idle()
            except NameError:
                pass

        def _show_comparison_details():
            messagebox.showinfo(
                "Comparison details",
                texto_es(_dynamic_details_text(sync_state['candidate'])),
                parent=window,
            )

        tk.Button(
            info_frame,
            text="Details...",
            command=_show_comparison_details,
            bg="#e0e0e0",
        ).pack(side=tk.RIGHT, padx=6, pady=3)
        tk.Checkbutton(
            info_frame,
            text="Show start/end markers",
            variable=show_event_markers_var,
            command=_toggle_event_markers,
            bg="#f0f0f0",
        ).pack(side=tk.RIGHT, padx=6, pady=3)
        tk.Checkbutton(
            info_frame,
            text="Show event labels",
            variable=show_event_labels_var,
            command=_toggle_event_labels,
            bg="#f0f0f0",
        ).pack(side=tk.RIGHT, padx=6, pady=3)

        synchronization_frame = tk.Frame(window, bg="#f0f0f0")
        synchronization_frame.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        tk.Label(
            synchronization_frame,
            text="Synchronization:",
            bg="#f0f0f0",
        ).pack(side=tk.LEFT, padx=(8, 4), pady=(0, 4))

        synchronization_var = tk.StringVar()
        synchronization_combo = ttk.Combobox(
            synchronization_frame,
            textvariable=synchronization_var,
            state="readonly",
            width=38,
        )
        synchronization_combo.pack(side=tk.LEFT, padx=(0, 8), pady=(0, 4))

        synchronization_table_windows = []

        def _synchronization_option_label(candidate):
            correlation = float(candidate.get('correlation', np.nan))
            correlation_text = f"r={correlation:.3f}" if np.isfinite(correlation) else "r=N/A"
            raw_label = (
                f"Synchronization {candidate.get('rank', 1)} — "
                f"frames {candidate['start_idx']}–{candidate['end_idx']} — "
                f"{correlation_text}"
            )
            return texto_es(raw_label)

        def _populate_synchronization_table(tree):
            for item_id in tree.get_children():
                tree.delete(item_id)
            for candidate in synchronization_candidates:
                correlation = float(candidate.get('correlation', np.nan))
                duration_error = 100.0 * float(
                    candidate.get('halpha_duration_error_ratio', np.nan)
                )
                tree.insert('', tk.END, values=(
                    texto_es(f"Synchronization {candidate.get('rank', 1)}"),
                    f"{correlation:.3f}" if np.isfinite(correlation) else "N/A",
                    candidate.get('rank', 1),
                    texto_es(candidate.get('alignment_signal_label', '')),
                    f"{candidate.get('duration_ms', np.nan):.3f}",
                    f"{duration_error:.1f}" if np.isfinite(duration_error) else "N/A",
                    f"{candidate['start_idx']}–{candidate['end_idx']}",
                    f"{candidate.get('alignment_shift_ms', np.nan):+.3f}",
                ))

        def _show_synchronization_table():
            table_window = tk.Toplevel(window)
            table_window.title("Synchronization ranking")
            table_window.geometry("1080x300")

            columns = (
                'synchronization', 'correlation', 'top', 'signal',
                'duration', 'duration_error', 'frames', 'shift',
            )
            tree = ttk.Treeview(
                table_window,
                columns=columns,
                show='headings',
                height=max(3, len(synchronization_candidates)),
            )
            headings = {
                'synchronization': 'Synchronization',
                'correlation': 'Correlation',
                'top': 'Top',
                'signal': 'Signal',
                'duration': 'Video duration [ms]',
                'duration_error': 'H-alpha duration error [%]',
                'frames': 'Frames',
                'shift': 'Shift [ms]',
            }
            widths = {
                'synchronization': 145,
                'correlation': 95,
                'top': 70,
                'signal': 265,
                'duration': 135,
                'duration_error': 180,
                'frames': 95,
                'shift': 100,
            }
            for column in columns:
                tree.heading(column, text=headings[column])
                tree.column(column, width=widths[column], anchor='center')
            tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)
            _populate_synchronization_table(tree)

            tk.Button(
                table_window,
                text="Close",
                command=table_window.destroy,
                bg="#e0e0e0",
            ).pack(side=tk.BOTTOM, pady=(0, 8))

            def _refresh_table_language():
                table_window.title("Synchronization ranking")
                _actualizar_idioma_widgets(table_window)
                _populate_synchronization_table(tree)

            table_window._mephist_refresh_language = _refresh_table_language
            synchronization_table_windows.append(table_window)

        tk.Button(
            synchronization_frame,
            text="Compare synchronizations",
            command=_show_synchronization_table,
            bg="#d9edf7",
        ).pack(side=tk.LEFT, padx=(0, 8), pady=(0, 4))

        cursor_control_frame = tk.Frame(window, bg="#f0f0f0")
        cursor_control_frame.pack(side=tk.TOP, fill=tk.X)
        cursor_status_var = tk.StringVar(
            value="Enable the cursor to inspect Ip, H-alpha, Vloop, and video frames."
        )
        tk.Label(
            cursor_control_frame,
            textvariable=cursor_status_var,
            bg="#f0f0f0",
            anchor='w',
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8, pady=(0, 4))

        figure = Figure(figsize=(14.5, 7.5), facecolor='white')
        grid = figure.add_gridspec(
            2, 4,
            width_ratios=[1.0, 1.0, 1.0, 0.86],
            hspace=0.20,
            wspace=0.34,
        )
        ax_ip = figure.add_subplot(grid[0, :3])
        ax_optical = figure.add_subplot(grid[1, :3], sharex=ax_ip)
        ax_camera = figure.add_subplot(grid[:, 3])
        ax_loop = ax_ip.twinx()

        if display_frames:
            initial_display_frame = min(max(start_frame, 0), len(display_frames) - 1)
            first_frame = display_frames[initial_display_frame]
            camera_image = ax_camera.imshow(
                first_frame,
                cmap='gray' if np.asarray(first_frame).ndim == 2 else None,
                vmin=0 if np.asarray(first_frame).ndim == 2 else None,
                vmax=255 if np.asarray(first_frame).ndim == 2 else None,
            )
            ax_camera.set_title(
                f"Video frame {initial_display_frame}\nt={video_time_ms[initial_display_frame]:+.3f} ms"
            )
        else:
            camera_image = None
            ax_camera.text(
                0.5, 0.5, 'Video frames unavailable',
                ha='center', va='center', transform=ax_camera.transAxes
            )
        ax_camera.set_axis_off()

        if diagnostic_time_ms.size == Ip.size and Ip.size:
            ip_line, = ax_ip.plot(diagnostic_time_ms, Ip / 1000.0, color='#003f5c', label='Ip')
        else:
            ip_line = None
        if diagnostic_time_ms.size == Vloop.size and Vloop.size:
            loop_line, = ax_loop.plot(
                diagnostic_time_ms, Vloop, color='#d95f02', linestyle='--',
                alpha=0.9, label='(VL2+VL7)/2'
            )
        else:
            loop_line = None

        halpha_norm = _normalize_positive(halpha_corrected)
        video_norm = _normalize_positive(corrected)
        if halpha_time_grid_ms.size == halpha_norm.size and halpha_norm.size:
            ax_optical.plot(
                halpha_time_grid_ms, halpha_norm,
                color='#7a5195', label='Normalized H-alpha'
            )
            halpha_scale = float(np.nanpercentile(np.clip(halpha_corrected, 0.0, None), 99.0))
            if np.isfinite(halpha_scale) and halpha_scale > 0:
                ax_optical.axhline(
                    halpha_light_info['threshold'] / halpha_scale,
                    color='#7a5195', linestyle=':', alpha=0.55,
                    label='H-alpha threshold'
                )
        video_line, = ax_optical.plot(
            video_time_ms, video_norm, color='#118ab2',
            label=f'Normalized {video_signal_label}'
        )
        video_scale = float(np.nanpercentile(np.clip(corrected, 0.0, None), 99.0))
        if np.isfinite(video_scale) and video_scale > 0:
            ax_optical.axhline(
                light_info['threshold'] / video_scale,
                color='#118ab2', linestyle=':', alpha=0.55,
                label=f'{video_signal_label.capitalize()} threshold'
            )

        video_active_spans = []
        for run_start, run_end in light_info['active_runs']:
            video_active_spans.append(ax_optical.axvspan(
                video_time_ms[run_start], video_time_ms[run_end],
                color='#118ab2', alpha=0.06, linewidth=0
            ))

        # The green band is the interval chosen by the Ip-duration constraint.
        # Blue bands still show every detected luminous episode, including a
        # possible preionization flash before the selected plasma interval.
        selected_video_span_ref = {'artist': ax_optical.axvspan(
            video_start_ms, video_end_ms, color='#1a9850', alpha=0.07,
            linewidth=1.0, edgecolor='#1a9850', label='_nolegend_'
        )}
        ax_optical.axvspan(
            halpha_start_relative_ms, halpha_end_relative_ms,
            color='#7a5195', alpha=0.055, linewidth=1.0,
            edgecolor='#7a5195', label='_nolegend_'
        )

        marker_specs = [
            ('ip_start', 0.0, 'black', ':', 'Ip-only start'),
            ('video_start', video_start_ms, '#2c7fb8', '-.', 'Selected camera start'),
            ('halpha_start', halpha_start_relative_ms, '#7a5195', ':', 'H-alpha start'),
            ('halpha_end', halpha_end_relative_ms, '#7a5195', '--', 'H-alpha end'),
            ('ip_end', ip_only_end_ms, '#777777', ':', 'Ip-only end'),
            ('vloop_peak', loop_peak_ms, '#fdae61', '--', 'Current-quench Vloop peak'),
            (
                'vloop_end', loop_fall_ms, '#d73027', '--',
                f'Vloop {vloop_fall_percent:.0f}% decay end'
            ),
            ('video_end', video_end_ms, '#1a9850', '-.', f'{video_signal_label.capitalize()} end'),
        ]
        event_marker_by_key = {}
        for axis in (ax_ip, ax_optical):
            for marker_key, marker_time, color, style, label in marker_specs:
                if np.isfinite(marker_time):
                    marker_line = axis.axvline(
                        marker_time, color=color, linestyle=style, linewidth=1.2,
                        alpha=0.9, label='_nolegend_'
                    )
                    marker_line._mephist_event_label = label
                    event_marker_artists.append(marker_line)
                    event_marker_by_key.setdefault(marker_key, []).append(marker_line)

        event_legend_handles = [
            Line2D(
                [0], [0], color=color, linestyle=style,
                linewidth=1.4, label=label,
            )
            for marker_key, marker_time, color, style, label in marker_specs
            if np.isfinite(marker_time)
        ]
        event_legend = figure.legend(
            handles=event_legend_handles,
            loc='lower center',
            bbox_to_anchor=(0.5, 0.01),
            ncol=4,
            fontsize=8,
            title='Event markers',
            frameon=True,
        )
        event_legend.set_visible(False)
        event_legend_ref['artist'] = event_legend

        ax_ip.set_ylabel('Ip [kA]')
        ax_loop.set_ylabel('Vloop [V]', color='#d95f02')
        ax_optical.set_ylabel('Normalized intensity')
        ax_optical.set_xlabel('Time relative to Ip-only start [ms]')
        for axis in (ax_ip, ax_optical):
            axis.grid(True, alpha=0.30)
        ax_optical.set_ylim(bottom=-0.03)

        top_handles = [line for line in (ip_line, loop_line) if line is not None]
        if top_handles:
            ax_ip.legend(top_handles, [line.get_label() for line in top_handles], loc='best')
        ax_optical.legend(loc='best', ncol=2, fontsize=8)
        figure.suptitle(f"Shot {shot_id} — H-alpha and camera comparison", fontsize=12)
        figure.tight_layout(rect=[0.03, 0.11, 0.99, 0.94])

        canvas = FigureCanvasTkAgg(figure, master=window)
        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        def _update_compact_summary():
            candidate = sync_state['candidate']
            correlation = float(candidate.get('correlation', np.nan))
            correlation_text = (
                f"{correlation:.3f}" if np.isfinite(correlation) else "N/A"
            )
            raw_summary = (
                f"Video: {video_path.name} | Δt={frame_interval_us:g} µs | "
                f"Synchronization {candidate.get('rank', 1)}/{len(synchronization_candidates)} | "
                f"Correlation: {correlation_text} | "
                f"Signal: {candidate.get('alignment_signal_label', '')}"
            )
            compact_summary_var.set(texto_es(raw_summary))

        def _refresh_synchronization_combo():
            candidate = sync_state['candidate']
            labels = [
                _synchronization_option_label(item)
                for item in synchronization_candidates
            ]
            synchronization_combo.configure(values=labels)
            selected_index = next(
                (
                    index for index, item in enumerate(synchronization_candidates)
                    if item is candidate
                ),
                0,
            )
            if labels:
                synchronization_combo.current(selected_index)
            synchronization_combo.configure(
                state="readonly" if len(labels) > 1 else "disabled"
            )

        def _refresh_video_window_language():
            window.title(f"Shot {shot_id}: diagnostics vs video")
            _refresh_synchronization_combo()
            _update_compact_summary()
            for table_window in list(synchronization_table_windows):
                try:
                    if not table_window.winfo_exists():
                        continue
                    refresh_table = getattr(
                        table_window, '_mephist_refresh_language', None
                    )
                    if callable(refresh_table):
                        refresh_table()
                except Exception:
                    continue

        def _apply_synchronization_candidate(candidate):
            sync_state['candidate'] = candidate
            candidate_time = np.asarray(candidate['video_time_ms'], dtype=float)
            candidate_start = int(candidate['start_idx'])
            candidate_end = int(candidate['end_idx'])

            video_line.set_xdata(candidate_time)
            for span in list(video_active_spans):
                try:
                    span.remove()
                except Exception:
                    pass
            video_active_spans.clear()
            for run_start, run_end in light_info['active_runs']:
                video_active_spans.append(ax_optical.axvspan(
                    candidate_time[run_start], candidate_time[run_end],
                    color='#118ab2', alpha=0.06, linewidth=0,
                ))

            previous_selected_span = selected_video_span_ref.get('artist')
            if previous_selected_span is not None:
                try:
                    previous_selected_span.remove()
                except Exception:
                    pass
            selected_video_span_ref['artist'] = ax_optical.axvspan(
                candidate_time[candidate_start], candidate_time[candidate_end],
                color='#1a9850', alpha=0.07, linewidth=1.0,
                edgecolor='#1a9850', label='_nolegend_',
            )

            for marker_key, marker_time in (
                ('video_start', candidate_time[candidate_start]),
                ('video_end', candidate_time[candidate_end]),
            ):
                for marker_line in event_marker_by_key.get(marker_key, []):
                    marker_line.set_xdata([marker_time, marker_time])

            if camera_image is not None and display_frames:
                display_idx = min(max(candidate_start, 0), len(display_frames) - 1)
                camera_image.set_data(display_frames[display_idx])
                ax_camera.set_title(
                    f"Video frame {display_idx}\n"
                    f"t={candidate_time[display_idx]:+.3f} ms"
                )

            finite_times = [
                values[np.isfinite(values)]
                for values in (diagnostic_time_ms, candidate_time)
                if np.asarray(values).size
            ]
            finite_times = [values for values in finite_times if values.size]
            if finite_times:
                x_min = min(float(np.nanmin(values)) for values in finite_times)
                x_max = max(float(np.nanmax(values)) for values in finite_times)
                if np.isfinite(x_min) and np.isfinite(x_max) and x_max > x_min:
                    ax_ip.set_xlim(x_min, x_max)

            _refresh_synchronization_combo()
            _update_compact_summary()
            cursor_state['last_frame'] = None
            if cursor_state['enabled']:
                _update_cursor_at(candidate_time[candidate_start])
            canvas.draw_idle()

        def _on_synchronization_selected(event=None):
            selected_index = synchronization_combo.current()
            if 0 <= selected_index < len(synchronization_candidates):
                _apply_synchronization_candidate(
                    synchronization_candidates[selected_index]
                )

        cursor_state = {'enabled': False, 'last_frame': None}
        cursor_lines = [
            axis.axvline(
                0.0, color='#c51b8a', linestyle='-', linewidth=1.1,
                alpha=0.9, visible=False, zorder=1000, label='_nolegend_'
            )
            for axis in (ax_ip, ax_optical)
        ]

        def _update_cursor_at(x_ms):
            if not np.isfinite(x_ms):
                return
            for cursor_line in cursor_lines:
                cursor_line.set_xdata([x_ms, x_ms])
                cursor_line.set_visible(True)

            candidate = sync_state['candidate']
            candidate_shift_ms = float(candidate.get('alignment_shift_ms', 0.0))
            candidate_start_frame = int(candidate['start_idx'])
            candidate_video_time_ms = np.asarray(candidate['video_time_ms'], dtype=float)
            video_frame = int(round(
                (x_ms - candidate_shift_ms) / frame_interval_ms
                + candidate_start_frame
            ))
            video_frame = min(max(video_frame, 0), frame_sums.size - 1)
            if camera_image is not None and display_frames:
                display_idx = min(video_frame, len(display_frames) - 1)
                if cursor_state['last_frame'] != display_idx:
                    camera_image.set_data(display_frames[display_idx])
                    cursor_state['last_frame'] = display_idx
                ax_camera.set_title(
                    f"Video frame {display_idx}\n"
                    f"Relative time={candidate_video_time_ms[display_idx]:+.3f} ms | "
                    f"Video time={display_idx * frame_interval_ms:.3f} ms"
                )

            if diagnostic_time_ms.size and np.any(np.isfinite(diagnostic_time_ms)):
                diagnostic_idx = int(np.nanargmin(np.abs(diagnostic_time_ms - x_ms)))
                ip_value = Ip[diagnostic_idx] / 1000.0 if diagnostic_idx < Ip.size else np.nan
                halpha_value = Halpha[diagnostic_idx] if diagnostic_idx < Halpha.size else np.nan
                vloop_value = Vloop[diagnostic_idx] if diagnostic_idx < Vloop.size else np.nan
            else:
                ip_value = halpha_value = vloop_value = np.nan
            luminosity_value = corrected[video_frame] / 1e6
            cursor_status_var.set(
                f"t={x_ms:+.3f} ms | frame={video_frame} | "
                f"Ip={ip_value:.3f} kA | H-alpha={halpha_value:.4g} | "
                f"Vloop={vloop_value:.3f} V | "
                f"{video_signal_label.capitalize()}={luminosity_value:.3f}×10⁶"
            )
            canvas.draw_idle()

        def _on_video_cursor_motion(event):
            if not cursor_state['enabled'] or event.xdata is None:
                return
            if event.inaxes not in (ax_ip, ax_loop, ax_optical):
                return
            _update_cursor_at(float(event.xdata))

        cursor_connection_id = canvas.mpl_connect('motion_notify_event', _on_video_cursor_motion)

        def _toggle_video_cursor():
            cursor_state['enabled'] = not cursor_state['enabled']
            if cursor_state['enabled']:
                cursor_toggle_button.configure(text='Disable cursor dynamics')
                _update_cursor_at(0.0)
            else:
                cursor_toggle_button.configure(text='Enable cursor dynamics')
                for cursor_line in cursor_lines:
                    cursor_line.set_visible(False)
                cursor_status_var.set(
                    "Enable the cursor to inspect Ip, H-alpha, Vloop, and video frames."
                )
                canvas.draw_idle()

        cursor_toggle_button = tk.Button(
            cursor_control_frame,
            text='Enable cursor dynamics',
            command=_toggle_video_cursor,
            bg='#e0e0e0',
        )
        cursor_toggle_button.pack(side=tk.RIGHT, padx=8, pady=(0, 4))

        synchronization_combo.bind(
            "<<ComboboxSelected>>", _on_synchronization_selected
        )
        window._mephist_refresh_language = _refresh_video_window_language
        self._video_comparison_windows.append(window)
        _refresh_video_window_language()

        canvas.draw()

        # Keep Tk/Matplotlib objects alive for the lifetime of the comparison window.
        window._video_figure = figure
        window._video_canvas = canvas
        window._video_toolbar = toolbar
        window._video_cursor_connection_id = cursor_connection_id

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
    # MAIN-PLOT HOVER LABELS
    # -----------------------------------------------------
    def on_hover_labels_changed(self):
        """Enable/disable local shot labels when the mouse is near a line."""
        try:
            self.hover_labels_enabled = bool(self.hover_label_var.get())
        except Exception:
            self.hover_labels_enabled = True

        if not self.hover_labels_enabled:
            self.hide_hover_annotation()
            if hasattr(self, "canvas"):
                self.canvas.draw_idle()

    def get_current_time_axis_label(self):
        """Return the x-axis label used by temporal hover tags."""
        if self.normalization_mode != NORMALIZATION_NONE:
            return "tau [-]"
        if self.display_time_mode == DISPLAY_RAW:
            return "Time [ms]"
        return "Time - t_Ip,start [ms]"

    def get_hover_y_unit(self, signal_key):
        """Return compact y-unit text for hover labels."""
        if signal_key == "Ip":
            return "kA" if self.normalization_mode in [NORMALIZATION_NONE, NORMALIZATION_TAU] else "normalized"
        if signal_key == "H_alpha":
            return "a.u." if self.normalization_mode in [NORMALIZATION_NONE, NORMALIZATION_TAU] else "normalized"
        if signal_key == "spectrum":
            return "a.u." if getattr(self, "spectrum_display_mode", "raw") == "raw" else "normalized"
        return ""

    def register_hover_line(self, line, data, signal_name, y_unit="", x_label=""):
        """Attach metadata to a Matplotlib line so it can show a hover tag."""
        if line is None:
            return
        try:
            line.set_picker(8)
            line.set_pickradius(8)
        except Exception:
            pass

        line._mephist_hover_info = {
            "shot": str(data.get("shot_number", "")),
            "label": self.get_plot_label_for_data(data),
            "signal": str(signal_name),
            "y_unit": str(y_unit or ""),
            "x_label": str(x_label or ""),
        }
        self.hover_lines.append(line)

    def hide_hover_annotation(self):
        """Hide the current hover annotation, if it exists."""
        annot = getattr(self, "hover_annotation", None)
        if annot is not None:
            try:
                annot.set_visible(False)
            except Exception:
                pass

    def _get_hover_annotation(self, ax):
        """Create or reuse the annotation object for the current axis."""
        if getattr(self, "hover_annotation", None) is not None:
            try:
                if self.hover_annotation.axes is ax:
                    return self.hover_annotation
                self.hover_annotation.remove()
            except Exception:
                pass

        self.hover_annotation = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            fontsize=9,
            color="black",
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.35", alpha=0.92),
            arrowprops=dict(arrowstyle="->", color="0.35", lw=0.8),
            zorder=1000,
        )
        self.hover_annotation.set_visible(False)
        return self.hover_annotation

    def _format_hover_value(self, value):
        try:
            v = float(value)
        except Exception:
            return ""
        if not np.isfinite(v):
            return "nan"
        if abs(v) >= 1000 or (0 < abs(v) < 1e-3):
            return f"{v:.4e}"
        return f"{v:.5g}"

    def find_nearest_hover_line(self, event):
        """Return the nearest registered line point to the mouse event."""
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return None

        max_dist_px = 12.0
        best = None

        for line in getattr(self, "hover_lines", []):
            try:
                if line.axes is not event.inaxes or not line.get_visible():
                    continue

                xdata = np.asarray(line.get_xdata(), dtype=float)
                ydata = np.asarray(line.get_ydata(), dtype=float)
                if xdata.size < 2 or ydata.size < 2 or xdata.size != ydata.size:
                    continue

                finite = np.isfinite(xdata) & np.isfinite(ydata)
                if not np.any(finite):
                    continue

                # For the plotted MEPhIST traces x is normally monotonic.  Use
                # searchsorted for speed and only inspect a small neighborhood.
                if xdata[0] <= xdata[-1]:
                    idx0 = int(np.searchsorted(xdata, event.xdata))
                else:
                    idx0 = int(np.searchsorted(xdata[::-1], event.xdata))
                    idx0 = len(xdata) - idx0 - 1

                lo = max(0, idx0 - 4)
                hi = min(len(xdata), idx0 + 5)
                inds = np.arange(lo, hi)
                inds = inds[finite[inds]]
                if inds.size == 0:
                    continue

                xy_pixels = event.inaxes.transData.transform(
                    np.column_stack([xdata[inds], ydata[inds]])
                )
                distances = np.hypot(xy_pixels[:, 0] - event.x, xy_pixels[:, 1] - event.y)
                j = int(np.argmin(distances))
                dist = float(distances[j])

                if dist <= max_dist_px and (best is None or dist < best[0]):
                    idx = int(inds[j])
                    best = (dist, line, float(xdata[idx]), float(ydata[idx]))
            except Exception:
                continue

        return best

    def on_line_hover_move(self, event):
        """Show shot/signal/value when the mouse is close to a main plotted line."""
        if not bool(getattr(self, "hover_labels_enabled", True)):
            return
        if event.inaxes is None:
            if getattr(self, "hover_annotation", None) is not None and self.hover_annotation.get_visible():
                self.hide_hover_annotation()
                self.canvas.draw_idle()
            return

        target = self.find_nearest_hover_line(event)
        if target is None:
            if getattr(self, "hover_annotation", None) is not None and self.hover_annotation.get_visible():
                self.hide_hover_annotation()
                self.canvas.draw_idle()
            return

        _, line, x, y = target
        info = getattr(line, "_mephist_hover_info", {}) or {}
        shot = info.get("shot", "")
        signal = info.get("signal", "signal")
        y_unit = info.get("y_unit", "")
        x_label = info.get("x_label", "x")

        y_unit_text = f" {y_unit}" if y_unit else ""
        text = (
            f"Shot {shot}\n"
            f"{signal}: {self._format_hover_value(y)}{y_unit_text}\n"
            f"{x_label}: {self._format_hover_value(x)}"
        )

        annot = self._get_hover_annotation(event.inaxes)
        annot.xy = (x, y)
        annot.set_text(text)
        annot.set_visible(True)
        self.canvas.draw_idle()

    # -----------------------------------------------------
    # BOTTOM INFO PANEL
    # -----------------------------------------------------
    def set_data_box_text(self, text):
        """Set the bottom information text, respecting the visibility toggle."""
        text = "" if text is None else str(text)
        self.data_box_text_cache = text

        if not hasattr(self, 'data_box_label'):
            return

        if bool(getattr(self, 'data_box_visible', True)):
            self._pack_data_box_widgets()
            self.data_box_label.config(text=text)
        else:
            self.data_box_label.config(text="")

    def _pack_data_box_widgets(self):
        """Ensure the close button and label are visible in the toolbar."""
        if hasattr(self, 'data_box_close_button') and self.data_box_close_button is not None:
            if not self.data_box_close_button.winfo_ismapped():
                self.data_box_close_button.pack(side=tk.LEFT, padx=(8, 0))
        if hasattr(self, 'data_box_label'):
            if not self.data_box_label.winfo_ismapped():
                self.data_box_label.pack(side=tk.LEFT, padx=(4, 10))

    def set_data_box_visible(self, visible):
        """Show or hide the large bottom information panel."""
        self.data_box_visible = bool(visible)

        if getattr(self, 'data_box_visible_var', None) is not None:
            try:
                self.data_box_visible_var.set(self.data_box_visible)
            except Exception:
                pass

        if not hasattr(self, 'data_box_label'):
            return

        if self.data_box_visible:
            self._pack_data_box_widgets()
            self.data_box_label.config(text=getattr(self, 'data_box_text_cache', ""))
        else:
            self.data_box_label.config(text="")
            try:
                self.data_box_label.pack_forget()
            except Exception:
                pass
            try:
                if getattr(self, 'data_box_close_button', None) is not None:
                    self.data_box_close_button.pack_forget()
            except Exception:
                pass

    def on_data_box_visibility_changed(self):
        visible = True
        try:
            visible = bool(self.data_box_visible_var.get())
        except Exception:
            pass
        self.set_data_box_visible(visible)

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
            self.set_data_box_text("")

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

        self.set_data_box_text("\n".join(rows))
        self.canvas.draw_idle()

    def on_right_click(self, event):
        if not event.inaxes or not self.cursor_dynamics_enabled or event.button != 3:
            return
        pyperclip.copy(getattr(self, "data_box_text_cache", self.data_box_label.cget("text")))
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
            self.set_data_box_text("")
            return

        if self.normalization_mode == NORMALIZATION_NONE:
            self.set_data_box_text("Normalization: none")
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

        self.set_data_box_text("\n".join(rows))

    # -----------------------------------------------------
    # DISPLAY DATA
    # -----------------------------------------------------
    def get_display_coil_arrays(self, data):
        """Return x-axis and coil-current arrays for the selected time mode."""
        Time = np.asarray(data.get('Time', np.array([])), dtype=float)
        if Time.size == 0:
            return np.array([]), {}
        if self.display_time_mode == DISPLAY_RAW:
            x = Time * 1000.0
        else:
            x = (Time - data.get('Ip_start_time', 0.0)) * 1000.0
        coils = {}
        for key, label in [
            ('CS_current_kA', 'CS'),
            ('PF1_current_kA', 'PF1'),
            ('PF2_current_kA', 'PF2'),
            ('PF3_current_kA', 'PF3'),
            ('PF4_current_kA', 'PF4'),
        ]:
            arr = np.asarray(data.get(key, np.array([])), dtype=float)
            if arr.size == Time.size:
                coils[label] = arr
        return x, coils

    def get_display_loop_arrays(self, data):
        """Return x-axis and loop voltage for display.

        In tau normalizations the loop voltage is plotted against tau so the
        selected plasma interval is visible on the same 0..1 scale as Ip and
        H-alpha. Its amplitude is kept in volts because dividing voltage by the
        Ip normalization factor is not physically meaningful for this diagnostic.
        """
        Time = np.asarray(data.get('Time', np.array([])), dtype=float)
        vloop = np.asarray(data.get('Vloop_2_7_V', np.array([])), dtype=float)
        if Time.size == 0 or Time.size != vloop.size:
            return np.array([]), np.array([])

        if self.normalization_mode != NORMALIZATION_NONE:
            tau, _duration = get_tau(
                Time,
                data.get('Ip_start_time', Time[0] if Time.size else 0.0),
                data.get('Ip_end_time', Time[-1] if Time.size else 0.0)
            )
            active = (tau >= 0.0) & (tau <= 1.0)
            return tau[active], vloop[active]

        if self.display_time_mode == DISPLAY_RAW:
            x = Time * 1000.0
        else:
            x = (Time - data.get('Ip_start_time', 0.0)) * 1000.0
        return x, vloop

    def get_display_time_arrays(self, data):
        m = self.normalization_mode
        start_time = data['Ip_start_time']
        end_time = data['Ip_end_time']

        # Bt is now referenced to the same plasma window as Ip.
        # In synchronized time, t=0 is t_Ip,start, not t_Bt,start.
        # In tau normalizations, Bt is plotted over tau in the active plasma
        # interval so its value at plasma start/end can be compared directly
        # with Ip, loop voltage and H-alpha.  Its amplitude stays in mT.
        xb, yb = get_normalized_temporal_signal(
            data['Time'], data['B_phi'], data['Ip'], NORMALIZATION_NONE,
            signal_kind="bt", display_mode=self.display_time_mode,
            sync_time=start_time, force_tau=(m != NORMALIZATION_NONE),
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
        wl_raw, spec_raw, source_label, source_key = self.get_selected_spectrum_arrays(data, use_rw=False)
        wl_raw = np.asarray(wl_raw, dtype=float)
        spec_raw = np.asarray(spec_raw, dtype=float)

        if getattr(self, "spectrum_display_mode", "raw") == "raw":
            wl = self.get_spectrum_display_wavelengths(data, wl_raw)
            return wl, spec_raw

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
            wl_raw,
            spec_raw,
            plasma_duration,
            self.normalization_mode,
            ip_norm
        )
        wl = self.get_spectrum_display_wavelengths(data, wl)
        return wl, spec_y

    def get_plasma_window_marker_x(self, data, panel_key):
        """Return display x positions for plasma start/end on a temporal panel.

        Spectrum panels use wavelength on x and are intentionally skipped.
        """
        start = float(data.get('Ip_start_time', np.nan))
        end = float(data.get('Ip_end_time', np.nan))
        if not np.isfinite(start) or not np.isfinite(end):
            return None

        if panel_key in ("Ip", "LV", "Bt", "H_alpha") and self.normalization_mode != NORMALIZATION_NONE:
            return 0.0, 1.0

        # Ip, LV, Bt, coils and H-alpha in synchronized time are referenced to
        # Ip start. In raw display they use absolute time.
        if self.display_time_mode == DISPLAY_RAW:
            return start * 1000.0, end * 1000.0
        return 0.0, (end - start) * 1000.0

    def draw_plasma_window_markers_for_data(self, data, color):
        """Draw start/end vertical lines in the shot color on temporal panels."""
        if not bool(getattr(self, "show_ip_start_end_markers", True)):
            return

        panels = [
            ("Ip", self.ax_ip),
            ("LV", self.ax_loop),
            ("Bt", self.ax_bt),
            ("coils", self.ax_coils),
            ("H_alpha", self.ax_halpha),
            ("Ip", self.ax_ip_residual),
            ("LV", self.ax_loop_residual),
            ("Bt", self.ax_bt_residual),
            ("coils", self.ax_coils_residual),
            ("H_alpha", self.ax_halpha_residual),
        ]

        for key, ax in panels:
            if ax is None:
                continue
            xs = self.get_plasma_window_marker_x(data, key)
            if xs is None:
                continue
            x0, x1 = xs
            for x in (x0, x1):
                if np.isfinite(x):
                    ax.axvline(
                        x,
                        color=color,
                        linestyle=":",
                        linewidth=1.0,
                        alpha=0.80,
                        zorder=1,
                        label="_nolegend_"
                    )

    def get_halpha_window_marker_x(self, data, panel_key):
        """Return displayed H-alpha start/end positions for one temporal panel.

        The start is recomputed with the same detector used by the H-alpha
        integral table: first sustained 5%-of-maximum crossing after Ip start.
        The end is the independently stored optical-emission end time.
        """
        Time = np.asarray(data.get('Time', np.array([])), dtype=float)
        Halpha = np.asarray(data.get('Photod', np.array([])), dtype=float)
        ip_start = float(data.get('Ip_start_time', np.nan))
        ip_end = float(data.get('Ip_end_time', np.nan))
        halpha_end = float(data.get('Halpha_end_time', np.nan))

        if (
            Time.size < 2
            or Halpha.size != Time.size
            or not np.isfinite(ip_start)
            or not np.isfinite(halpha_end)
        ):
            return None

        halpha_start, _threshold, _method = get_halpha_start_5pct_time(
            Time,
            Halpha,
            ip_start,
            halpha_end,
            threshold_ratio=0.05,
            smooth_us=HALPHA_END_SMOOTH_US,
            min_active_us=HALPHA_END_MIN_ACTIVE_US
        )

        def _display_x(event_time):
            if not np.isfinite(event_time):
                return np.nan
            if panel_key in ("Ip", "LV", "Bt", "H_alpha") and self.normalization_mode != NORMALIZATION_NONE:
                duration = ip_end - ip_start
                if not np.isfinite(duration) or duration <= 0:
                    return np.nan
                return (event_time - ip_start) / duration
            if self.display_time_mode == DISPLAY_RAW:
                return event_time * 1000.0
            return (event_time - ip_start) * 1000.0

        return _display_x(halpha_start), _display_x(halpha_end)

    def draw_halpha_window_markers_for_data(self, data, color):
        """Draw the independently detected optical H-alpha start/end markers."""
        if not bool(getattr(self, "show_halpha_start_end_markers", False)):
            return

        panels = [
            ("Ip", self.ax_ip),
            ("LV", self.ax_loop),
            ("Bt", self.ax_bt),
            ("coils", self.ax_coils),
            ("H_alpha", self.ax_halpha),
            ("Ip", self.ax_ip_residual),
            ("LV", self.ax_loop_residual),
            ("Bt", self.ax_bt_residual),
            ("coils", self.ax_coils_residual),
            ("H_alpha", self.ax_halpha_residual),
        ]

        for key, ax in panels:
            if ax is None:
                continue
            xs = self.get_halpha_window_marker_x(data, key)
            if xs is None:
                continue
            halpha_start_x, halpha_end_x = xs
            for x, linestyle in (
                (halpha_start_x, "-."),
                (halpha_end_x, "--"),
            ):
                if np.isfinite(x):
                    ax.axvline(
                        x,
                        color=color,
                        linestyle=linestyle,
                        linewidth=1.35,
                        alpha=0.90,
                        zorder=2,
                        label="_nolegend_"
                    )

    def plot_data(self):
        self.rebuild_plot_axes()

        for ax in self.time_axes + self.time_residual_axes + self.spec_axes + self.spec_residual_axes:
            if ax is not None:
                ax.clear()

        self.hover_lines = []
        self.hover_annotation = None

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

            if self.ax_bt is not None:
                line_bt, = self.ax_bt.plot(xb, yb, label=plot_label, color=c)
                self.register_hover_line(line_bt, d, "Bt", "mT", x_label=self.get_current_time_axis_label())

            if self.ax_ip is not None:
                line_ip, = self.ax_ip.plot(xi, yi, label=f"Ip {plot_label}", color=c)
                self.register_hover_line(line_ip, d, "Ip", self.get_hover_y_unit("Ip"), x_label=self.get_current_time_axis_label())

            if self.ax_loop is not None:
                xvl, vloop = self.get_display_loop_arrays(d)
                if xvl.size == vloop.size and vloop.size > 2 and np.any(np.isfinite(vloop)):
                    line_loop, = self.ax_loop.plot(xvl, vloop, color=c, linestyle='--', alpha=0.85, label=f"LV {plot_label}")
                    self.register_hover_line(line_loop, d, "Vloop", "V", x_label=self.get_current_time_axis_label())

            if self.ax_halpha is not None:
                line_ha, = self.ax_halpha.plot(xh, yh, label=plot_label, color=c)
                self.register_hover_line(line_ha, d, "H-alpha", self.get_hover_y_unit("H_alpha"), x_label=self.get_current_time_axis_label())

            if self.ax_coils is not None:
                xc, coils = self.get_display_coil_arrays(d)
                if xc.size:
                    if 'CS' in coils:
                        line_cs, = self.ax_coils.plot(xc, coils['CS'], color=c, linestyle='-', label=f"CS {plot_label}")
                        self.register_hover_line(line_cs, d, "CS", "kA", x_label=self.get_current_time_axis_label())
                    if 'PF1' in coils and 'PF2' in coils:
                        line_pf12, = self.ax_coils.plot(xc, 5.0 * 0.5 * (coils['PF1'] + coils['PF2']), color=c, linestyle='--', alpha=0.8, label=f"PF1/2 x5 {plot_label}")
                        self.register_hover_line(line_pf12, d, "PF1/2 x5", "kA", x_label=self.get_current_time_axis_label())
                    elif 'PF1' in coils:
                        line_pf1, = self.ax_coils.plot(xc, 5.0 * coils['PF1'], color=c, linestyle='--', alpha=0.8, label=f"PF1 x5 {plot_label}")
                        self.register_hover_line(line_pf1, d, "PF1 x5", "kA", x_label=self.get_current_time_axis_label())
                    if 'PF3' in coils and 'PF4' in coils:
                        line_pf34, = self.ax_coils.plot(xc, 5.0 * 0.5 * (coils['PF3'] + coils['PF4']), color=c, linestyle=':', alpha=0.9, label=f"PF3/4 x5 {plot_label}")
                        self.register_hover_line(line_pf34, d, "PF3/4 x5", "kA", x_label=self.get_current_time_axis_label())
                    elif 'PF3' in coils:
                        line_pf3, = self.ax_coils.plot(xc, 5.0 * coils['PF3'], color=c, linestyle=':', alpha=0.9, label=f"PF3 x5 {plot_label}")
                        self.register_hover_line(line_pf3, d, "PF3 x5", "kA", x_label=self.get_current_time_axis_label())

            if self.ax_avantes is not None and wl.size > 0 and sy.size > 0 and wl.shape == sy.shape:
                line_spec, = self.ax_avantes.plot(wl, sy, label=plot_label, color=c)
                self.register_hover_line(line_spec, d, "Spectrum", self.get_hover_y_unit("spectrum"), x_label="Wavelength [nm]")

            self.draw_plasma_window_markers_for_data(d, c)
            self.draw_halpha_window_markers_for_data(d, c)

        # Overlay selected local NIST lines only after experimental spectra exist.
        if self.ax_avantes is not None:
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
        legend_source_ax = next((ax for ax in [self.ax_bt, self.ax_ip, self.ax_loop, self.ax_halpha, self.ax_coils, self.ax_avantes] if ax is not None and ax.has_data()), None)
        if legend_source_ax is not None:
            handles, labels = legend_source_ax.get_legend_handles_labels()
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

        if self.ax_avantes is not None:
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
            # Ip, Bt, loop voltage and H-alpha are in tau. Coils keep time.
            for ax in [self.ax_ip, self.ax_ip_residual, self.ax_bt, self.ax_bt_residual, self.ax_loop, self.ax_loop_residual, self.ax_halpha, self.ax_halpha_residual]:
                if ax is not None:
                    ax.set_xlim(0, 1)

        if self.normalization_mode == NORMALIZATION_TAU_AREA:
            if self.ax_ip is not None:
                self.ax_ip.set_title("NORMALIZED: Ip_pos(tau) / int(Ip_pos(tau)dtau)")
            if self.ax_loop is not None:
                self.ax_loop.set_title("TAU DISPLAY: Vloop(tau), amplitude kept in V")
            if self.ax_halpha is not None:
                self.ax_halpha.set_title("NORMALIZED: H-alpha / int(Ip_pos(tau)dtau)")
            if self.ax_avantes is not None:
                self.ax_avantes.set_title("NORMALIZED: spectrum / (dt_p * int(Ip_pos(tau)dtau))")
            for ax in [self.ax_ip, self.ax_halpha, self.ax_avantes]:
                if ax is not None and ax.has_data():
                    try:
                        ax.ticklabel_format(axis='y', style='sci', scilimits=(-2, 3))
                    except Exception:
                        pass
        else:
            for ax in [self.ax_ip, self.ax_loop, self.ax_halpha, self.ax_avantes, self.ax_coils, self.ax_bt]:
                if ax is not None:
                    ax.set_title("")

        if self.ax_ip is not None and getattr(self.ax_ip, '_right_axis', None) is not None:
            try:
                self.ax_ip._right_axis.legend(fontsize='x-small', loc='upper right')
            except Exception:
                pass
        if self.ax_coils is not None and self.ax_coils.has_data():
            try:
                self.ax_coils.legend(fontsize='x-small', loc='best')
            except Exception:
                pass

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
                "Synchronization is fixed: Ip and H-alpha with Ip start. Bt is exported but not plotted here."
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
        tk.Button(button_frame, text="Generate Ip/H-alpha plot", command=generate_plot).pack(side=tk.RIGHT, padx=5)
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
        win.geometry("1500x900")

        # Only show the plasma-current and H-alpha panels. Bt is still kept in
        # the exported comparison tables, but it is not plotted here so the main
        # plasma behavior is easier to read.
        # Tamaño y tipografías pensados para que la figura siga siendo legible
        # al insertarla a ancho completo en un informe de dos columnas.
        fig = Figure(figsize=(13.2, 8.4), facecolor='white')
        ax_ip = fig.add_subplot(2, 1, 1)
        ax_ha = fig.add_subplot(2, 1, 2, sharex=ax_ip)

        report_label_size = _tamano_plot(17)
        report_tick_size = _tamano_plot(14)
        report_legend_size = _tamano_plot(13)
        report_legend_title_size = _tamano_plot(14)
        report_title_size = _tamano_plot(16)
        report_line_width = 2.2

        color_cycle = itertools.cycle(self.color_palette)

        for result in results:
            color = next(color_cycle)
            label = result['group_label']
            band_factor = result['band_factor']
            n_shots = result['n_shots']
            is_single = result.get('is_single_shot', False)

            if is_single:
                label_mean = f"{label} | 1 shot"
            else:
                label_mean = f"{label} mean | N={n_shots}"

            # Both displayed panels use the same reference time:
            # t = 0 is the plasma-current start used by the main page.
            t_ms = result['ref_time_ip'] * 1000

            # Put labels only on the Ip axis. H-alpha uses _nolegend_ so there
            # is one single legend, not duplicated legends in both panels.
            ax_ip.plot(
                t_ms, result['Ip_mean'] / 1000, color=color,
                linewidth=report_line_width, label=label_mean
            )
            ax_ha.plot(
                t_ms, result['Ha_mean'], color=color,
                linewidth=report_line_width, label='_nolegend_'
            )

            if not is_single:
                ax_ip.fill_between(
                    t_ms,
                    result['Ip_lower'] / 1000,
                    result['Ip_upper'] / 1000,
                    color=color,
                    alpha=0.18,
                    label='_nolegend_',
                )
                ax_ha.fill_between(
                    t_ms,
                    result['Ha_lower'],
                    result['Ha_upper'],
                    color=color,
                    alpha=0.18,
                    label='_nolegend_',
                )

        ax_ip.set_ylabel("Ip [kA]", fontsize=report_label_size)
        ax_ip.set_xlabel("Time - t_Ip,start [ms]", fontsize=report_label_size)
        ax_ha.set_ylabel("H-alpha [a.u.]", fontsize=report_label_size)
        ax_ha.set_xlabel("Time - t_Ip,start [ms]", fontsize=report_label_size)

        for ax in [ax_ip, ax_ha]:
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.tick_params(axis='both', which='major', labelsize=report_tick_size)

        # One shared legend, drawn only on the Ip panel and placed outside the
        # plotting area. This avoids overlapping the title/suptitle.
        handles, labels = ax_ip.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if by_label:
            ax_ip.legend(
                by_label.values(),
                by_label.keys(),
                title="Group",
                loc='center left',
                bbox_to_anchor=(1.015, 0.5),
                fontsize=report_legend_size,
                title_fontsize=report_legend_title_size,
                frameon=True,
                borderaxespad=0.0,
                handlelength=2.8,
                handletextpad=0.8,
                labelspacing=0.65,
            )

        smooth_ip_us = results[0]['smooth_ip_us']
        smooth_halpha_us = results[0]['smooth_halpha_us']
        band_factor = results[0]['band_factor']
        fig.suptitle(
            (
                "Group comparison | panels synchronized to t_Ip,start\n"
                f"If N >= 2: band = mean ± {band_factor:g} std | "
                f"Ip smoothing = {smooth_ip_us:g} us | "
                f"H-alpha smoothing = {smooth_halpha_us:g} us"
            ),
            fontsize=report_title_size,
            y=0.982,
        )
        # Reserve space at the right for the side legend and at the top for the
        # title. Avoid tight_layout because it can pull the legend into the plot
        # when there are many groups.
        fig.subplots_adjust(left=0.105, right=0.75, top=0.86, bottom=0.105, hspace=0.40)

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
                        'smooth_bt_us': result['smooth_bt_us'],
                        'sync_reference': result.get('sync_reference', 'Ip_start')
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

        def export_multi_group_figure():
            path = filedialog.asksaveasfilename(
                title="Export comparison figure",
                defaultextension=".pdf",
                filetypes=[
                    ("PDF vectorial", "*.pdf"),
                    ("PNG 300 dpi", "*.png"),
                    ("SVG vectorial", "*.svg"),
                ],
            )
            if not path:
                return
            try:
                extension = Path(path).suffix.lower()
                opciones = {
                    "bbox_inches": "tight",
                    "facecolor": "white",
                }
                if extension == ".png":
                    opciones["dpi"] = 300
                fig.savefig(path, **opciones)
                messagebox.showinfo(
                    "Figure exported",
                    f"The figure was saved successfully to:\n{path}"
                )
            except Exception as exc:
                messagebox.showerror("Export error", str(exc))

        tk.Button(
            toolbar,
            text="Export data",
            command=export_multi_group_comparison,
        ).pack(side=tk.LEFT, padx=(10, 4))
        tk.Button(
            toolbar,
            text="Export figure",
            command=export_multi_group_figure,
        ).pack(side=tk.LEFT, padx=4)
        self.connect_multi_axis_xlim_sync(fig, canvas, [ax_ip, ax_ha])
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
