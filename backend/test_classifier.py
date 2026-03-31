import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.file_classifier import clasificar_archivos

ruta = "data"

print("Analizando archivos...\n")

resultados = clasificar_archivos(ruta)

for r in resultados:
    print(f"Archivo: {r['archivo']}")
    print(f"MAC: {r['mac']}")
    print(f"Tipo: {r['tipo']}")
    print("-" * 40)