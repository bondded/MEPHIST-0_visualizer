import customtkinter as ctk
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class PantallaPrincipal(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)

