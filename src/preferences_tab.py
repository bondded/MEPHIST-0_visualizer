import tkinter as tk
from tkinter import filedialog, messagebox, ttk 

class PreferencesTab:
	"""
	Por ahora solo tiene la función de guardar la inspeción de archivos
	para saber en qué lugar mi programa debería leer mi archivo del diag
	nostico, así podemos manejar d emejor manera las entradas y el manejo
	de archivos crudos y centralizar su procesamiento.

	Funciones actuales: 

		1. (proximamente) Obtener la ruta de todos los archivos //
		2. (proximamente) Seleccionar el mapa de colores
		3. (proximamente) Seleccionar el tipo de archivo para la
			exportación de datos. 
		4. (proximamente) Seleccionar la carpeta de shots //
		5. (proximamente) Seleccionar la carpeta de exportación//
	"""

	def __init__(self, master_frame, app_instance):
		self.master_frame = master_frame
		self.app = app_instance
		self.setup_ui_preferences()

	def setup_ui_preferences(self):
		"""
		Dibuja el panel de control de las preferencias
		"""
		main_form = tk.Frame(self.master_frame, bg="white", padx=30, pady=30)
		main_form.pack(anchor="w")

		self.ip_path_var = tk.StringVar()
		self.ip_path_var.set("Ejemplo: rogowski_coils/rog_pol_coils1")
		self.shot_path_var = tk.StringVar()
		self.shot_path_var.set("C:/Ejemplo/Tu_nombre/MEPHIST/shots")
		self.export_path_var = tk.StringVar()
		self.export_path_var.set("C:/Ejemplo/name/MEPHIST/export")
		self.extension_var = tk.StringVar()
		self.extension_var.set(".png, .pdf, .jpg")

		title = tk.Label(main_form, text='Path manager', font=self.app.fuente_negrita, bg="white", fg="black")
		title.grid(row=0, column=0, sticky='w', padx=10, pady=10)
		
		keys = [
			"Description",
			"ID",
			"Shot time",
			"RF",
			"Total pressure",
			"Working gas",
			"Microwave",
			"Rogowski coils",
			"Visible emission",
			"Voltage loops",
			"Diamagnetic loops",
			"Interferometry",
			"AXUV",
			"Langmuir probes",
			"Magnetic probes"
		]
		for i, key in enumerate(keys):
			index = i + 1
			lbl_path = tk.Label(main_form, text=f"{key} dir: ", bg="white", fg="black")
			lbl_path.grid(row=index, column=0, sticky='e', padx=10, pady=10)
			ent_path = tk.Entry(main_form, textvariable=self.ip_path_var, width=60)
			ent_path.grid(row=index, column=1, sticky='e', padx=10, pady=10)

		lbl_shot_path = tk.Label(main_form, text=f"Shot dir: ", bg="white", fg="black")
		lbl_shot_path.grid(row=index + 1, column=0, sticky='e', padx=10, pady=10)
		ent_shot_path = tk.Entry(main_form, textvariable=self.shot_path_var, width=60)
		ent_shot_path.grid(row=index + 1, column=1, sticky='e', padx=10, pady=10)

		lbl_export_path = tk.Label(main_form, text=f"Export dir: ", bg="white", fg="black")
		lbl_export_path.grid(row=index + 2, column=0, sticky='e', padx=10, pady=10)
		ent_export_path = tk.Entry(main_form, textvariable=self.export_path_var, width=60)
		ent_export_path.grid(row=index + 2, column=1, sticky='e', padx=10, pady=10)

		lbl_extension = tk.Label(main_form, text=f"image format: ", bg="white", fg="black")
		lbl_extension.grid(row=index + 3, column=0, sticky='e', padx=10, pady=10)
		ent_extension = tk.Entry(main_form, textvariable=self.extension_var, width=60)
		ent_extension.grid(row=index + 3, column=1, sticky='e', padx=10, pady=10)

		btn_load = tk.Button(main_form, text="Load",bg="black", fg="white", command=self.cargar_preferencias)
		btn_load.grid(row=index + 4, column=1, sticky="e", padx=10, pady=10)

	def cargar_preferencias(self):
		print('Cargando preferencias...')