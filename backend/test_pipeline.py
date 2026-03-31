import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.file_classifier import clasificar_archivos
from app.parsers.siirfe_parser import parse_siirfe_file

ruta = "data"

print("Iniciando pipeline...\n")

archivos = clasificar_archivos(ruta)

for archivo_info in archivos:
    archivo_nombre = archivo_info["archivo"]
    tipo = archivo_info["tipo"]
    mac = archivo_info["mac"]

    print(f"Archivo encontrado: {archivo_nombre}")
    print(f"MAC: {mac}")
    print(f"Tipo: {tipo}")

    if tipo == "TIEMPOS":
        ruta_archivo = os.path.join(ruta, archivo_nombre)
        resultado = parse_siirfe_file(ruta_archivo)

        if resultado["success"]:
            df = resultado["data"]
            print(f"Lectura exitosa: {len(df)} filas, {len(df.columns)} columnas")
        else:
            print(f"Error al parsear: {resultado['error']}")

    print("-" * 50)