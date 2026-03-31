import math


def formatear_minutos_a_hhmmss(minutos):
    if minutos is None or (isinstance(minutos, float) and math.isnan(minutos)):
        return "00:00:00"

    total_segundos = int(round(minutos * 60))
    horas = total_segundos // 3600
    minutos_restantes = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    return f"{horas:02d}:{minutos_restantes:02d}:{segundos:02d}"


def calcular_metricas_cr(df):
    if df is None or df.empty:
        return {
            "total_entregas": 0,
            "promedio_tiempo": "00:00:00",
            "tiempo_minimo": "00:00:00",
            "tiempo_maximo": "00:00:00",
            "atipicos": 0,
            "por_terminal": [],
        }

    total_entregas = len(df)
    promedio = df["minutos_atencion"].mean()
    minimo = df["minutos_atencion"].min()
    maximo = df["minutos_atencion"].max()

    umbral_atipico = promedio * 1.5 if promedio else None
    atipicos = 0
    if umbral_atipico is not None:
        atipicos = int((df["minutos_atencion"] > umbral_atipico).sum())

    por_terminal_df = (
        df.groupby("terminal", dropna=False)
        .agg(
            entregas=("solicitud", "count"),
            promedio_minutos=("minutos_atencion", "mean"),
            minimo_minutos=("minutos_atencion", "min"),
            maximo_minutos=("minutos_atencion", "max"),
        )
        .reset_index()
        .sort_values(by="entregas", ascending=False)
    )

    por_terminal = []
    for _, row in por_terminal_df.iterrows():
        por_terminal.append({
            "terminal": row["terminal"],
            "entregas": int(row["entregas"]),
            "promedio_tiempo": formatear_minutos_a_hhmmss(row["promedio_minutos"]),
            "tiempo_minimo": formatear_minutos_a_hhmmss(row["minimo_minutos"]),
            "tiempo_maximo": formatear_minutos_a_hhmmss(row["maximo_minutos"]),
        })

    return {
        "total_entregas": total_entregas,
        "promedio_tiempo": formatear_minutos_a_hhmmss(promedio),
        "tiempo_minimo": formatear_minutos_a_hhmmss(minimo),
        "tiempo_maximo": formatear_minutos_a_hhmmss(maximo),
        "atipicos": atipicos,
        "por_terminal": por_terminal,
    }