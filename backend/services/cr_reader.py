from pathlib import Path

from app.parsers.siirfe_parser_cr import parse_siirfe_cr_file
from backend.services.cr_cleaner import limpiar_reporte_cr
from backend.services.cr_metrics import calcular_metricas_cr


BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"


def _buscar_ultimo_archivo_cr():
    archivos = sorted(
        UPLOADS_DIR.glob("*Rep_nom_TiemAten_CR*.xls"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    if not archivos:
        return None

    return archivos[0]


def obtener_metricas_cr():
    archivo = _buscar_ultimo_archivo_cr()

    if not archivo:
        return {
            "success": False,
            "error": "No se encontró archivo CR en uploads",
            "metricas": None,
            "archivo": None,
        }

    resultado = parse_siirfe_cr_file(str(archivo))

    if not resultado["success"]:
        return {
            "success": False,
            "error": resultado["error"],
            "metricas": None,
            "archivo": archivo.name,
        }

    df = limpiar_reporte_cr(resultado["data"])
    metricas = calcular_metricas_cr(df)

    return {
        "success": True,
        "error": None,
        "metricas": metricas,
        "archivo": archivo.name,
    }