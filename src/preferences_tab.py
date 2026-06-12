import tkinter as tk
from tkinter import filedialog, messagebox, ttk 

class PreferencesTab:
	"""
	Por ahora solo tiene la función de guardar la inspeción de archivos
	para saber en qué lugar mi programa debería leer mi archivo del diag
	nostico, así podemos manejar d emejor manera las entradas y el manejo
	de archivos crudos y centralizar su procesamiento.

	Funciones actuales: 

		1. (proximamente) Obtener la ruta de todos los archivos
		2. (proximamente) Seleccionar el mapa de colores
		3. (proximamente) Seleccionar el tipo de archivo para la
			exportación de datos.
		4. (proximamente) Seleccionar la carpeta de shots
		5. (proximamente) Seleccionar la carpeta de exportación
		6. (proximamente) Seleccionar el tamaño de letra para las 
			anotaciones 
	"""

	def __init__(self, master_frame, app_instance):
		self.master_frame = master_frame
		self.app = app_instance
		self.setup_ui_preferences()

	def setup_ui_preferences(self):
		"""
		Dibuja el panel de control de las preferencias
		"""

		main_form = tk.Frame(self.master_frame, bg="black", padx=30, pady=30)
		main_form.pack(anchor="center")