
# :dart: Visualizador MEPHIST

## :clipboard: Indice
* [Descripción General](#descripción-general)
* [Instalación](#instalación)
* [Caracteríticas principales](#características-principales)

## :globe_with_meridians: Descripción General
Este visualizador es una herramienta para el análisis de datos de las descargas hechas en el proyecto MEPHIST-0; un tokamak esférico dedicado principalmente a la formación y capacitación de estudiantes en la Física de Fusión Nuclear.

La herramienta cuenta funciones tales como la inspección de parametros como la corriente de plasma Ip, el campo toroidal Bt, el espectro de emisión y la emisión de la línea de hidrógeno H-alpha. Además permite la comparación estadística de descargas y la visualización de diagnosticos magnéticos, entre otras cosas.

## :hammer: Instalación
1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/bondded/MEPHIST-0_visualizer.git
   cd MEPHIST-0_visualizer
   ```
2. **Instalar las dependencias**
   ```bash
   uv pip install -r requirements.txt
   ```
3. **Instalar MephistDataKit en la raíz del proyecto y obtener una llave de acceso**
4. **Ejecutar**
   ```bash
   uv run src/main.py
   ```

## :chart_with_upwards_trend: Características principales
* Visualización rápida de descargas
* Comparación de shots 
* Análisis MHD y detección de inestabilidades
* EqReq
* FastCamera

## :page_with_curl: Tareas pendientes (24 de mayo, 2026)
- [X] Creación del repositorio de github
- [ ] Unificar el código en un solo visualizador
- [ ] Revisión de bugs
- [ ] Relacionar parametros controlados con el desarrollo de las descargas
- [ ] Realizazión del reporte

## :page_with_curl: Documentación visualizador de datos (apuntes)

Pedir una llave de acceso en MEPHIST e ingresarla en el archivo config.yaml-

Hay que tomar los datos del post procesado de manera manual para evitar errores. 

La función de corriente funciona bien, pero las demas debería hacerlas de manera manual.				
