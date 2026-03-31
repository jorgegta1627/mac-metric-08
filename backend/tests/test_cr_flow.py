import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(BASE_DIR))

print("BASE_DIR:", BASE_DIR)
print("INICIANDO PRUEBA CR...")

from app.parsers.siirfe_parser_cr import parse_siirfe_cr_file
from backend.services.cr_cleaner import limpiar_reporte_cr
from backend.services.cr_metrics import calcular_metricas_cr

ruta = r"C:\Users\jorge.pizano\OneDrive - Instituto Nacional Electoral\2_VOCALIA DEL RFE\MAC-METRIC-08\uploads\20260326_200213_Rep_nom_TiemAten_CR_090853_25032026_081233.xls"

resultado = parse_siirfe_cr_file(ruta)

if not resultado["success"]:
    print("ERROR PARSER:", resultado["error"])
    raise SystemExit

df = resultado["data"]

print("=== COLUMNAS ORIGINALES ===")
print(df.columns.tolist())

df_limpio = limpiar_reporte_cr(df)

print("\n=== PRIMEROS REGISTROS LIMPIOS ===")
print(df_limpio.head())

metricas = calcular_metricas_cr(df_limpio)

print("\n=== METRICAS CR ===")
for k, v in metricas.items():
    if k != "por_terminal":
        print(f"{k}: {v}")

print("\n=== POR TERMINAL ===")
for item in metricas["por_terminal"]:
    print(item)