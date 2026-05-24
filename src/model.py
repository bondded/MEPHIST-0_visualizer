import h5py
from pathlib import Path
from mephistdatakit.client import Client
from mephistdatakit.shot import Shot 
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

class DataEngine:
    def __init__(self):
        try:
            self.client = Client()
        except Exception as e:
            print(f"Error crítico al iniciar el motor: {e}")
            
        self.shot_actual = None
        self.shot_h5py = None

    def test_conexion(self):
        try:
            self.client.test_connection()
            return True, "✅ Conexión exitosa"
        except Exception as e:
            return False, "❌ No se puede conectar al servidor."


    def descargar_datos(self, id_shot: int):
        """
        Descarga de datos desde el servidor u obtención desde la carpeta caché
        """
        print(f"Intentando descargar el shot con ID: {id_shot}...")
        
        try:
            archivo_hdf5 = self.client.get_shot(id_shot)
            
            if archivo_hdf5 is not None:
                self.shot_actual = archivo_hdf5
                return True, "Descarga exitosa."
            else:
                return False, "El archivo no se encontró en el servidor o en la caché."
                
        except Exception as e:
            return False, f"❌ Error de conexión: Verifica tu internet o el servidor. Detalle: {e}"


    def obtener_lista_shots(self):
        """
        Obtiene la lista completa de shots hechos
        """
        
        lista_disparos = self.client.get_shots_list()

        if not lista_disparos:
            return False, "No se pudo obtener la lista de shots o está vacía"
            
        return True, lista_disparos


    def cargar_shot(self, id_shot: int):

        carpeta = Path("./MephistDataKit/.cache")
        nombre_archivo = f"{id_shot}MD.nxs"
        
        archivo_encontrado = next(carpeta.rglob(nombre_archivo), None)

        if not archivo_encontrado:

            self.descargar_datos(id_shot)

            path = carpeta / nombre_archivo
            
        else:
            path = archivo_encontrado
            

        f = h5py.File(path, 'r')
        shot = Shot(f)
        self.shot_actual = shot
        self.shot_h5py = f

        return shot

    def informacion_shot(self, id_shot: int):
        """
        Obtiene meta data del shot escogido, si no encuentra el shot, lo descarga
        """

        shot = self.cargar_shot(id_shot)

        shot_comment = shot.get_comment()
        shot_time = shot.get_shot_time()
        shot_gas = shot.get_gas()
        shot_pressure = shot.get_pressure()

        informacion = {
            "shot_id" : id_shot,
            "comentario" : shot_comment,
            "fecha_shot" : shot_time,
            "gas_trabajo" : shot_gas,
            "presion_maxima" : shot_pressure      
        }

        encabezado = [
            "INFORMACIÓN DEL SHOT CON ID", 
            "COMENTARIO", 
            "FECHA", 
            "GAS DE TRABAJO", 
            "PRESIÓN MÁXIMA"
        ]

        mensaje = (
            f"{"=" * 50} \n"
            f"{encabezado[0]:28s}: {id_shot}\n"
            f"{encabezado[1]:28s}: {shot_comment}\n"
            f"{encabezado[2]:28s}: {shot_time}\n"
            f"{encabezado[3]:28s}: {shot_gas}\n"
            f"{encabezado[4]:28s}: {shot_pressure:.2e} mBar\n"
            f"{"=" * 50}"
        )
        return informacion, mensaje


    def obtener_estructura_archivo(self, id_shot):
        """
        Imprime la estructura del archivo usado
        """

        shot = self.cargar_shot(id_shot)
        try:
            estructura = shot.get_hdf5_structure()
            return estructura

        except Exception as e:
            return "No se ha podido obtener la estructura del shot"    

    def obtener_corriente_plasma(self):
        if self.shot_actual == None:
            return "No se ha cargado ningún shot"

        tiempo, corriente_plasma = self.shot_actual.get_plasma_current()

        return tiempo, corriente_plasma

    def obtener_voltaje_loop(self, loop=1):
        if self.shot_actual == None:
            return "No se ha cargado ningún shot"        

        tiempo, voltaje_loop = self.shot_actual.get_voltage_loop(loop)

        return tiempo, voltaje_loop

    def obtener_corriente_inductor(self):
        tiempo, corriente_inductor = self.shot_actual.get_inductor_current()

        return tiempo, corriente_inductor

    def obtener_corriente_pol_coil(self, coil_num=1):
        tiempo, corriente_bobina_poloidal = self.shot_actual.get_pol_coils_current(coil_num)
        return tiempo, corriente_bobina_poloidal

    # Puede tener problemas, aveces no accede a los archivos
    def obtener_torfield(self):
        try:
            tiempo = self.shot_h5py["Postprocess"]["tor_field"]["time"][:]
            data   = self.shot_h5py["Postprocess"]["tor_field"]["data"][:]

            return tiempo, data

        except:
            return np.array([]), np.array([])


    def obtener_Ha(self):
        tiempo, intensidad = self.shot_actual.get_emission()

        # Corrección de datos: OFFSET
        mask = tiempo < 2.0
        base = np.mean(intensidad[mask])
        intensidad_corregida = intensidad - base

        # Corrección de datos: orientación
        if abs(np.min(intensidad_corregida)) > np.max(intensidad_corregida):
            intensidad_corregida *= -1

        intensidad = np.where(intensidad_corregida < 0, 0, intensidad_corregida)

        return tiempo, intensidad

    def obtener_espectro_emision(self):

        longitud_onda, intensidad = self.shot_actual.get_emission_spectrum()

        return longitud_onda, intensidad

    # No todas las descargas la tienen   
    def obtener_densidad_plasma(self):
        tiempo, densidad_electronica = self.shot_actual.get_plasma_density()

        return tiempo, densidad_electronica

    def obtener_mirnov(self, mirnov_num):
        try:
            tiempo = self.shot_h5py["magnetic_probes"][f"MP{mirnov_num}"]["time"][:]
            data = self.shot_h5py["magnetic_probes"][f"MP{mirnov_num}"]["data"][:]
            return tiempo, data
        except:
            return np.array(), np.array()

