import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.parsers.siirfe_parser import parse_siirfe_file

file_path = "data/Rep_nom_TiemAten_SOL_090852_14032026_030434.xls"

result = parse_siirfe_file(file_path)

if result["success"]:
    df = result["data"]
    print("Columnas:")
    print(df.columns)
    print("\nPrimeras filas:")
    print(df.head())
else:
    print("Error:", result["error"])