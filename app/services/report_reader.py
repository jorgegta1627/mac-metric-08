from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "output"


def _buscar_ultimo_archivo(patrones):
    archivos = []

    for patron in patrones:
        archivos.extend(OUTPUT_DIR.glob(patron))

    archivos = [a for a in archivos if a.is_file()]

    if not archivos:
        return None

    return max(archivos, key=lambda x: x.stat().st_mtime)


def _leer_reporte_sol(path_archivo):
    if not path_archivo or not path_archivo.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(path_archivo)
    except Exception:
        return pd.DataFrame()

    df = df.loc[:, ~df.columns.duplicated()]
    df.columns = [str(col).strip().lower() for col in df.columns]

    if df.empty or "funcionario" not in df.columns:
        return pd.DataFrame()

    df = df.copy()

    mapa_columnas = {
        "funcionario": "funcionario",
        "tramites_reales": "sol_tramites",
        "entregas": "sol_entregas",
        "total_registros": "sol_total",
        "promedio_general": "sol_promedio_general",
        "promedio_tramites": "sol_promedio_tramites",
        "promedio_entregas": "sol_promedio_entregas",
        "tiempo_minimo": "sol_minimo",
        "tiempo_maximo": "sol_maximo",
        "tramites_atipicos": "sol_atipicos",
        "porcentaje_atipicos": "sol_porcentaje_atipicos",
        "terminales": "sol_terminales",
    }

    columnas_disponibles = {
        original: nuevo
        for original, nuevo in mapa_columnas.items()
        if original in df.columns
    }

    if "funcionario" not in columnas_disponibles:
        return pd.DataFrame()

    df = df.rename(columns=columnas_disponibles)
    df = df[list(columnas_disponibles.values())]

    columnas_numericas = [
        "sol_tramites",
        "sol_entregas",
        "sol_total",
        "sol_atipicos",
        "sol_porcentaje_atipicos",
    ]

    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in [
        "sol_promedio_general",
        "sol_promedio_tramites",
        "sol_promedio_entregas",
        "sol_minimo",
        "sol_maximo",
        "sol_terminales",
    ]:
        if col in df.columns:
            df[col] = df[col].fillna("Sin datos")

    return df


def _leer_reporte_cr(path_archivo):
    if not path_archivo or not path_archivo.exists():
        return pd.DataFrame()

    try:
        df = pd.read_csv(path_archivo)
    except Exception:
        return pd.DataFrame()

    df = df.loc[:, ~df.columns.duplicated()]
    df.columns = [str(col).strip().lower() for col in df.columns]

    if df.empty or "funcionario" not in df.columns:
        return pd.DataFrame()

    df = df.copy()

    posibles_cantidad = [
        "cantidad",
        "tramites",
        "total_registros",
        "entregas",
    ]

    posibles_promedio = [
        "promedio_tiempo",
        "promedio_general",
        "promedio_entregas",
    ]

    posibles_minimo = ["tiempo_minimo"]
    posibles_maximo = ["tiempo_maximo"]
    posibles_atipicos = ["tramites_atipicos", "atipicos"]

    columnas_salida = {"funcionario": "funcionario"}

    for col in posibles_cantidad:
        if col in df.columns:
            columnas_salida[col] = "cr_cantidad"
            break

    for col in posibles_promedio:
        if col in df.columns:
            columnas_salida[col] = "cr_promedio"
            break

    for col in posibles_minimo:
        if col in df.columns:
            columnas_salida[col] = "cr_minimo"
            break

    for col in posibles_maximo:
        if col in df.columns:
            columnas_salida[col] = "cr_maximo"
            break

    for col in posibles_atipicos:
        if col in df.columns:
            columnas_salida[col] = "cr_atipicos"
            break

    df = df.rename(columns=columnas_salida)
    df = df[list(columnas_salida.values())]

    if "cr_cantidad" in df.columns:
        df["cr_cantidad"] = pd.to_numeric(df["cr_cantidad"], errors="coerce").fillna(0)
    else:
        df["cr_cantidad"] = 0

    if "cr_atipicos" in df.columns:
        df["cr_atipicos"] = pd.to_numeric(df["cr_atipicos"], errors="coerce").fillna(0)
    else:
        df["cr_atipicos"] = 0

    for col in ["cr_promedio", "cr_minimo", "cr_maximo"]:
        if col not in df.columns:
            df[col] = "Sin datos"
        else:
            df[col] = df[col].fillna("Sin datos")

    return df


def obtener_resumen_dashboard():
    archivo_sol = _buscar_ultimo_archivo([
    "tiempos_sol/*_reporte_funcionarios.csv",
    ])

    archivo_cr = _buscar_ultimo_archivo([
        "tiempos/*CR*_reporte_funcionarios*.csv",
        "tiempos_cr/*_reporte_funcionarios.csv",
        "tiempos_cr/*CR*.csv",
    ])

    df_sol = _leer_reporte_sol(archivo_sol)
    df_cr = _leer_reporte_cr(archivo_cr)

    if df_sol.empty and df_cr.empty:
        return {
            "fuente_sol": "Sin reporte",
            "fuente_cr": "Sin reporte",
            "total_tramites": 0,
            "total_entregas": 0,
            "relacion_global": "0.00",
            "funcionarios_activos": 0,
            "ranking_funcionarios": []
        }

    if df_sol.empty:
        df_sol = pd.DataFrame(columns=[
            "funcionario",
            "sol_tramites",
            "sol_entregas",
            "sol_total",
            "sol_promedio_general",
            "sol_promedio_tramites",
            "sol_promedio_entregas",
            "sol_minimo",
            "sol_maximo",
            "sol_atipicos",
            "sol_porcentaje_atipicos",
            "sol_terminales",
        ])

    if df_cr.empty:
        df_cr = pd.DataFrame(columns=[
            "funcionario",
            "cr_cantidad",
            "cr_promedio",
            "cr_minimo",
            "cr_maximo",
            "cr_atipicos",
        ])

    df = pd.merge(df_sol, df_cr, on="funcionario", how="outer")

    columnas_enteras = [
        "sol_tramites",
        "sol_entregas",
        "sol_total",
        "sol_atipicos",
        "cr_cantidad",
        "cr_atipicos",
    ]

    for col in columnas_enteras:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    columnas_texto = [
        "sol_promedio_general",
        "sol_promedio_tramites",
        "sol_promedio_entregas",
        "sol_minimo",
        "sol_maximo",
        "sol_terminales",
        "cr_promedio",
        "cr_minimo",
        "cr_maximo",
    ]

    for col in columnas_texto:
        if col not in df.columns:
            df[col] = "Sin datos"
        else:
            df[col] = df[col].fillna("Sin datos")

    if "sol_porcentaje_atipicos" not in df.columns:
        df["sol_porcentaje_atipicos"] = 0.0
    else:
        df["sol_porcentaje_atipicos"] = pd.to_numeric(
            df["sol_porcentaje_atipicos"],
            errors="coerce"
        ).fillna(0.0)

    # Para la tabla principal
    df["tramites"] = df["sol_tramites"]
    df["entregas"] = df["cr_cantidad"]
    df["entregas_por_tramite"] = df.apply(
        lambda row: round(row["entregas"] / row["tramites"], 2) if row["tramites"] > 0 else 0,
        axis=1
    )
    df["promedio_tramite"] = df["sol_promedio_tramites"]
    df["promedio_entrega"] = df["cr_promedio"]
    df["atipicos_tramite"] = df["sol_atipicos"]
    df["total_operaciones"] = df["tramites"] + df["entregas"]

    df = df.sort_values(
        by=["total_operaciones", "tramites", "entregas"],
        ascending=False
    )

    total_tramites = int(df["tramites"].sum())
    total_entregas = int(df["entregas"].sum())
    relacion_global = round((total_entregas / total_tramites), 2) if total_tramites > 0 else 0

    ranking = df.to_dict(orient="records")

    return {
        "fuente_sol": archivo_sol.name if archivo_sol else "Sin reporte",
        "fuente_cr": archivo_cr.name if archivo_cr else "Sin reporte",
        "total_tramites": total_tramites,
        "total_entregas": total_entregas,
        "relacion_global": f"{relacion_global:.2f}",
        "funcionarios_activos": int(len(df)),
        "ranking_funcionarios": ranking
    }