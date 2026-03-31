import pandas as pd


def limpiar_reporte_tiempos(df):
    df_limpio = df.copy()

    if "TERMINAL" in df_limpio.columns:
        df_limpio = df_limpio[df_limpio["TERMINAL"].notna()]
        df_limpio = df_limpio[
            df_limpio["TERMINAL"].astype(str).str.strip().str.upper() != "TERMINAL"
        ]

    df_limpio = df_limpio.dropna(how="all")
    df_limpio = df_limpio.reset_index(drop=True)

    return df_limpio