import os
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data"

def detectar_modulo(nombre_archivo):
    if "090852" in nombre_archivo:
        return "090852"
    elif "090853" in nombre_archivo:
        return "090853"
    else:
        return "DESCONOCIDO"

def leer_archivos():
    if not DATA_PATH.exists():
        print(f"❌ No existe la carpeta de datos: {DATA_PATH}")
        return

    archivos = os.listdir(DATA_PATH)

    if not archivos:
        print("⚠️ La carpeta data está vacía")
        return

    for archivo in archivos:
        ruta = DATA_PATH / archivo

        print(f"\n📂 Procesando: {archivo}")
        modulo = detectar_modulo(archivo)
        print(f"🏢 MAC detectado: {modulo}")

        try:
            if archivo.endswith(".xlsx"):
                df = pd.read_excel(ruta, engine="openpyxl", header=None)
            elif archivo.endswith(".xls"):
                df = pd.read_excel(ruta, engine="xlrd", header=None)
            elif archivo.endswith(".csv"):
                df = pd.read_csv(ruta, header=None)
            else:
                print("⚠️ Formato no soportado")
                continue

            print("📊 Dimensiones del archivo:")
            print(df.shape)

            print("\n🔎 Filas 20 a 60 del archivo:")
            print(df.iloc[20:60].to_string())

        except Exception as e:
            print("❌ Error leyendo archivo:")
            print(e)

if __name__ == "__main__":
    leer_archivos()