import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.parsers.siirfe_parser import parse_siirfe_file
from backend.services.file_classifier import clasificar_archivos
from backend.services.time_cleaner import limpiar_reporte_tiempos
from backend.services.time_metrics import calcular_metricas_tiempos
from backend.utils.exporter import exportar_metricas_csv


def imprimir_resumen_terminal(metricas):
    print("\nResumen por terminal:")
    por_terminal = metricas.get("por_terminal", {})
    porcentaje_terminal = metricas.get("porcentaje_terminal", {})

    if not por_terminal:
        print("  Sin datos")
        return

    for terminal, total in por_terminal.items():
        porcentaje = porcentaje_terminal.get(terminal, 0)
        print(f"  {terminal}: {total} registros ({porcentaje:.2f}%)")


def imprimir_resumen_categoria(metricas):
    print("\nResumen general por tipo:")
    por_categoria = metricas.get("por_categoria", {})

    if not por_categoria:
        print("  Sin datos")
        return

    for categoria, total in por_categoria.items():
        print(f"  {categoria}: {total}")


def imprimir_resumen_funcionarios(metricas):
    print("\nResumen por funcionario:")
    por_funcionario = metricas.get("por_funcionario", [])

    if not por_funcionario:
        print("  Sin datos")
        return

    for item in por_funcionario[:20]:
        funcionario = item.get("funcionario", "SIN NOMBRE")
        total_registros = item.get(
            "total_registros",
            item.get("tramites_reales", 0) + item.get("entregas", 0)
        )
        entregas = item.get("entregas", 0)
        tramites_reales = item.get("tramites_reales", 0)
        promedio_general = item.get(
            "promedio_general",
            item.get("promedio_tramites", "Sin datos")
        )
        promedio_entregas = item.get("promedio_entregas", "Sin datos")
        promedio_tramites = item.get("promedio_tramites", "Sin datos")
        tramites_atipicos = item.get("tramites_atipicos", 0)

        print(
            f"  {funcionario}: "
            f"Total={total_registros} | "
            f"Entregas={entregas} | "
            f"Trámites reales={tramites_reales} | "
            f"Prom. general={promedio_general} | "
            f"Prom. entregas={promedio_entregas} | "
            f"Prom. trámites={promedio_tramites} | "
            f"Atípicos={tramites_atipicos}"
        )


def imprimir_valores_tipo_tramite(df):
    print("\nValores detectados en la columna de tipo:")
    posibles_columnas = [
        "TIPO DE TRAMITE",
        "TIPO_TRAMITE",
        "TRAMITE",
        "TIPO"
    ]

    columna_encontrada = None
    for col in posibles_columnas:
        if col in df.columns:
            columna_encontrada = col
            break

    if not columna_encontrada:
        print("  No se encontró columna de tipo de trámite.")
        return

    valores = (
        df[columna_encontrada]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .unique()
        .tolist()
    )

    if not valores:
        print(f"  La columna {columna_encontrada} no tiene valores útiles.")
        return

    print(f"  Columna encontrada: {columna_encontrada}")
    for valor in valores[:50]:
        print(f"    - {valor}")


if __name__ == "__main__":
    import pandas as pd

    print("Iniciando prueba de métricas...\n")

    ruta = "data"

    if not os.path.exists(ruta):
        print(f"No existe la carpeta: {ruta}")
        sys.exit(1)

    archivos = clasificar_archivos(ruta)

    if not archivos:
        print("No se detectaron archivos para procesar.")
        sys.exit(0)

    for archivo_info in archivos:
        archivo_nombre = archivo_info["archivo"]
        tipo_archivo = archivo_info["tipo"]
        mac = archivo_info["mac"]

        print(f"Archivo detectado: {archivo_nombre}")
        print(f"Tipo detectado: {tipo_archivo}")

        if tipo_archivo != "TIEMPOS_SOL":
            print("  Archivo omitido: no corresponde a TIEMPOS_SOL")
            print("-" * 60)
            continue

        ruta_archivo = os.path.join(ruta, archivo_nombre)

        print(f"Archivo: {archivo_nombre}")
        print(f"MAC: {mac}")
        print(f"Tipo: {tipo_archivo}")

        print("Leyendo archivo...")
        resultado = parse_siirfe_file(ruta_archivo)

        if not resultado.get("success"):
            print(f"Error al procesar archivo: {resultado.get('error', 'Error desconocido')}")
            print("-" * 60)
            continue

        df = resultado.get("data")

        if df is None or df.empty:
            print("El parser no devolvió datos útiles.")
            print("-" * 60)
            continue

        print("Encabezados leídos")

        df = limpiar_reporte_tiempos(df)

        if df is None or df.empty:
            print("El archivo quedó sin registros después de la limpieza.")
            print("-" * 60)
            continue

        print("Datos procesados")

        metricas = calcular_metricas_tiempos(df)

        if not metricas:
            print("No se pudieron calcular métricas.")
            print("-" * 60)
            continue

        print("LLAVES RESULTADO:", metricas.keys())
        print("Total de registros:", metricas.get("total_registros"))
        print("Promedio tiempo de atención:", metricas.get("promedio_tiempo_atencion"))
        print("Columna tipo detectada:", metricas.get("columna_tipo_detectada"))
        print("Resumen por categoría:", metricas.get("por_categoria"))
        print("Umbral de trámites atípicos:", metricas.get("umbral_atipico"))
        print("Criterio:", metricas.get("criterio_atipico"))

        imprimir_resumen_terminal(metricas)
        imprimir_resumen_categoria(metricas)
        imprimir_resumen_funcionarios(metricas)
        imprimir_valores_tipo_tramite(df)

        try:
            ruta_exportada = exportar_metricas_csv(
                metricas,
                nombre_archivo_origen=archivo_nombre,
                tipo=tipo_archivo
            )
            print(f"\nArchivo exportado en: {ruta_exportada}")
        except Exception as e:
            print(f"\nNo se pudo exportar el CSV: {e}")

        print("-" * 60)