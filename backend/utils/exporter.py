import os
from datetime import datetime
import pandas as pd


def formatear_tiempo(valor):
    if not valor:
        return ""

    texto = str(valor).strip()

    if texto.lower() == "sin datos":
        return ""

    if "days" in texto:
        partes = texto.split()
        if len(partes) >= 3:
            hora = partes[2]
        else:
            hora = texto
    else:
        hora = texto

    if "." in hora:
        hora = hora.split(".")[0]

    return hora


def exportar_metricas_csv(metricas, nombre_archivo_origen, tipo):
    nombre_base = os.path.splitext(nombre_archivo_origen)[0]

    carpeta_salida = os.path.join("output", tipo.lower())
    os.makedirs(carpeta_salida, exist_ok=True)

    ruta_salida = os.path.join(
        carpeta_salida,
        f"{nombre_base}_reporte_funcionarios.csv"
    )

    filas = []
    total_registros = metricas.get("total_registros", 0)

    for item in metricas.get("por_funcionario", []):
        tramites = item.get("tramites_reales", 0)
        entregas = item.get("entregas", 0)
        total_funcionario = item.get("total_registros", tramites + entregas)
        atipicos = item.get("tramites_atipicos", 0)

        porcentaje_tramites = round((tramites / total_registros) * 100, 2) if total_registros else 0

        fila = {
            "funcionario": item.get("funcionario", ""),
            "tramites_reales": tramites,
            "entregas": entregas,
            "total_registros": total_funcionario,
            "porcentaje_tramites": f"{porcentaje_tramites}%",
            "promedio_general": formatear_tiempo(item.get("promedio_general", "")),
            "promedio_tramites": formatear_tiempo(item.get("promedio_tramites", "")),
            "promedio_entregas": formatear_tiempo(item.get("promedio_entregas", "")),
            "tiempo_minimo": formatear_tiempo(item.get("tiempo_minimo", "")),
            "tiempo_maximo": formatear_tiempo(item.get("tiempo_maximo", "")),
            "tramites_atipicos": atipicos,
            "porcentaje_atipicos": item.get("porcentaje_atipicos", 0),
            "terminales": item.get("terminales", "")
        }

        filas.append(fila)

    df = pd.DataFrame(filas)

    try:
        df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
        return ruta_salida
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_salida_alterna = os.path.join(
            carpeta_salida,
            f"{nombre_base}_reporte_funcionarios_{timestamp}.csv"
        )
        df.to_csv(ruta_salida_alterna, index=False, encoding="utf-8-sig")
        return ruta_salida_alterna