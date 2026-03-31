import pandas as pd


MAPEO_COLUMNAS_CR = {
    "TERMINAL": "terminal",
    "SOLICITUD": "solicitud",
    "FECHA DE ENTREGA": "fecha_entrega",
    "FOLIO NEC": "folio_nec",
    "HORA INICIO ATENCIÓN": "hora_inicio_atencion",
    "CAPTURA TRAMITE_HORA INICIO": "captura_hora_inicio",
    "HORA FIN": "captura_hora_fin",
    "TIEMPO TOTAL DE CAPTURA": "captura_tiempo_total",
    "TIEMPO TOTAL DE ATENCIÓN": "tiempo_total_atencion",
}


def _normalizar_texto(valor):
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    return texto if texto else None


def limpiar_reporte_cr(df):
    df_limpio = df.copy()
    df_limpio.columns = [str(col).strip() for col in df_limpio.columns]

    columnas_presentes = {}
    for original, nuevo in MAPEO_COLUMNAS_CR.items():
        if original in df_limpio.columns:
            columnas_presentes[original] = nuevo

    df_limpio = df_limpio.rename(columns=columnas_presentes)

    columnas_utiles = [
        "terminal",
        "solicitud",
        "fecha_entrega",
        "folio_nec",
        "hora_inicio_atencion",
        "captura_hora_inicio",
        "captura_hora_fin",
        "captura_tiempo_total",
        "tiempo_total_atencion",
    ]

    columnas_disponibles = [c for c in columnas_utiles if c in df_limpio.columns]
    df_limpio = df_limpio[columnas_disponibles].copy()

    columnas_minimas = ["terminal", "solicitud", "tiempo_total_atencion"]
    faltantes = [c for c in columnas_minimas if c not in df_limpio.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas clave en CR: {', '.join(faltantes)}")

    df_limpio["terminal"] = df_limpio["terminal"].apply(_normalizar_texto)
    df_limpio["solicitud"] = df_limpio["solicitud"].apply(_normalizar_texto)

    if "folio_nec" in df_limpio.columns:
        df_limpio["folio_nec"] = df_limpio["folio_nec"].apply(_normalizar_texto)

    df_limpio = df_limpio[df_limpio["terminal"].notna()]
    df_limpio = df_limpio[df_limpio["solicitud"].notna()]
    df_limpio = df_limpio[df_limpio["terminal"].str.upper() != "TERMINAL"]

    if "fecha_entrega" in df_limpio.columns:
        df_limpio["fecha_entrega"] = pd.to_datetime(
            df_limpio["fecha_entrega"],
            errors="coerce",
            dayfirst=True
        ).dt.date

    df_limpio["tiempo_total_atencion_td"] = pd.to_timedelta(
        df_limpio["tiempo_total_atencion"],
        errors="coerce"
    )

    df_limpio = df_limpio[df_limpio["tiempo_total_atencion_td"].notna()]

    df_limpio["minutos_atencion"] = (
        df_limpio["tiempo_total_atencion_td"].dt.total_seconds() / 60
    ).round(2)

    return df_limpio.reset_index(drop=True)