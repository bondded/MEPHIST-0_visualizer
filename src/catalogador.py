import pandas as pd
import h5py
import os
import glob
from model import DataEngine

modelo = DataEngine()
carpeta_descargas =  "./MephistDataKit/.cache"
metadatos_totales = []

lista_de_shots = range(2194, 4102)
for shot_id in lista_de_shots:
    modelo.descargar_datos(shot_id)
    ruta_temporal = carpeta_descargas + f"/{shot_id}MD.nxs"

    if not os.path.exists(ruta_temporal):
        print(f"  -> Shot {shot_id} no encontrado. Saltando...")
        continue
    info_shot = {
        "shot_id": shot_id,
        "peso_mb": round(os.path.getsize(ruta_temporal) / (1024 * 1024), 2)
    }

    def rastrear_estructura(nombre_ruta, objeto_interno):
        if isinstance(objeto_interno, h5py.Dataset):
            info_shot[f"has_{nombre_ruta}"] = True

    try:
            with h5py.File(ruta_temporal, 'r') as f:
                f.visititems(rastrear_estructura)
                
    except Exception as e:
        print(f"  -> Error: Archivo {shot_id} corrupto o ilegible ({e})")
        info_shot["corrupto"] = True
        
    # Guardamos la fila en nuestra lista maestra
    metadatos_totales.append(info_shot)
    
    # 3. DESTRUIR
    # Eliminamos el archivo físico para liberar el disco duro inmediatamente
    try:
        os.remove(ruta_temporal)
    except OSError as e:
        print(f"  -> Advertencia: No se pudo eliminar el archivo temporal: {e}")

    # Al terminar el bucle de las 2000 descargas, ensamblamos el mapa maestro
print("\nEnsamblando mapa maestro de metadatos...")
df_catalogo = pd.DataFrame(metadatos_totales)

# Rellenamos con False los sensores que no existían en descargas antiguas
df_catalogo.fillna(False, inplace=True)

df_catalogo.to_csv("mephist_mapa_maestro.csv", index=False)
print(f"¡Éxito! Catálogo creado con {len(df_catalogo.columns)} columnas distintas.")