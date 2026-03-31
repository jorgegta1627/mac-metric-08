import pandas as pd


def detectar_columna_tipo_tramite(columnas):
    candidatos = [
        "TIPO DE TRAMITE",
        "TIPO DE TRÁMITE",
        "TRAMITE",
        "TRÁMITE",
    ]

    columnas_normalizadas = {str(col).strip().upper(): col for col in columnas}

    for candidato in candidatos:
        if candidato in columnas_normalizadas:
            return columnas_normalizadas[candidato]

    return None


def normalizar_tipo_tramite(valor):
    texto = str(valor).strip().upper()

    if not texto or texto == "NAN":
        return "SIN_CLASIFICAR"

    return texto


def clasificar_categoria_tramite(valor):
    texto = normalizar_tipo_tramite(valor)

    if texto == "SIN_CLASIFICAR":
        return "SIN_CLASIFICAR"

    if "ENTREGA" in texto:
        return "ENTREGA"
    if "INSCRIP" in texto:
        return "INSCRIPCION"
    if "REPOS" in texto:
        return "REPOSICION"
    if "DOMIC" in texto:
        return "CAMBIO_DOMICILIO"
    if "CORREC" in texto:
        return "CORRECCION_DATOS"
    if "REINCORP" in texto:
        return "REINCORPORACION"
    if "REEMPLAZO" in texto:
        return "REEMPLAZO"

    return "TRAMITE"


def calcular_metricas_tiempos(df, factor_atipico=1.5):
    resultado = {}

    df_trabajo = df.copy()
    df_trabajo.columns = [str(col).strip() for col in df_trabajo.columns]

    resultado["total_registros"] = len(df_trabajo)

    # =========================
    # TIEMPO TOTAL
    # =========================
    if "TIEMPO TOTAL DE ATENCIÓN" in df_trabajo.columns:
        df_trabajo["TIEMPO_TOTAL"] = pd.to_timedelta(
            df_trabajo["TIEMPO TOTAL DE ATENCIÓN"],
            errors="coerce"
        )
    else:
        df_trabajo["TIEMPO_TOTAL"] = pd.NaT

    tiempos_validos_global = df_trabajo["TIEMPO_TOTAL"].dropna()

    if not tiempos_validos_global.empty:
        promedio_global = tiempos_validos_global.mean()
        umbral_atipico = promedio_global * factor_atipico

        resultado["promedio_tiempo_atencion"] = str(promedio_global)
        resultado["umbral_atipico"] = str(umbral_atipico)
        resultado["criterio_atipico"] = f"Tiempo mayor a {factor_atipico} veces el promedio general"
    else:
        promedio_global = pd.NaT
        umbral_atipico = pd.NaT
        resultado["promedio_tiempo_atencion"] = "Sin datos válidos"
        resultado["umbral_atipico"] = "Sin datos válidos"
        resultado["criterio_atipico"] = "Sin datos válidos"

    # =========================
    # RESUMEN POR TERMINAL
    # =========================
    if "TERMINAL" in df_trabajo.columns:
        conteo_terminal = df_trabajo["TERMINAL"].value_counts(dropna=False)
        resultado["por_terminal"] = conteo_terminal.to_dict()
        resultado["porcentaje_terminal"] = (
            (conteo_terminal / len(df_trabajo)) * 100
        ).round(2).to_dict()
    else:
        resultado["por_terminal"] = {}
        resultado["porcentaje_terminal"] = {}

    # =========================
    # TIPO DE TRÁMITE
    # =========================
    columna_tipo = detectar_columna_tipo_tramite(df_trabajo.columns)
    resultado["columna_tipo_detectada"] = columna_tipo if columna_tipo else "NO_ENCONTRADA"

    if columna_tipo:
        df_trabajo["TIPO_TRAMITE_NORMALIZADO"] = df_trabajo[columna_tipo].apply(normalizar_tipo_tramite)
        df_trabajo["CATEGORIA_TRAMITE"] = df_trabajo[columna_tipo].apply(clasificar_categoria_tramite)
    else:
        df_trabajo["TIPO_TRAMITE_NORMALIZADO"] = "SIN_CLASIFICAR"
        df_trabajo["CATEGORIA_TRAMITE"] = "SIN_CLASIFICAR"

    # =========================
    # RESUMEN GENERAL POR CATEGORÍA
    # =========================
    resultado["por_categoria"] = (
        df_trabajo["CATEGORIA_TRAMITE"]
        .value_counts(dropna=False)
        .to_dict()
    )

    # Compatibilidad opcional con estructuras viejas
    resumen_por_tipo = (
        df_trabajo["CATEGORIA_TRAMITE"]
        .value_counts(dropna=False)
        .reset_index()
    )
    resumen_por_tipo.columns = ["tipo_tramite", "cantidad"]
    resultado["resumen_por_tipo"] = resumen_por_tipo.to_dict(orient="records")

    # =========================
    # RESUMEN POR FUNCIONARIO
    # =========================
    resultado["por_funcionario"] = []
    resultado["detalle_funcionario_categoria"] = []

    if "NOMBRE FUNCIONARIO" in df_trabajo.columns:
        df_trabajo["NOMBRE FUNCIONARIO"] = (
            df_trabajo["NOMBRE FUNCIONARIO"]
            .astype(str)
            .str.strip()
        )

        df_func = df_trabajo[
            df_trabajo["NOMBRE FUNCIONARIO"].notna()
            & (df_trabajo["NOMBRE FUNCIONARIO"] != "")
            & (df_trabajo["NOMBRE FUNCIONARIO"].str.upper() != "NOMBRE FUNCIONARIO")
            & (df_trabajo["NOMBRE FUNCIONARIO"].str.lower() != "nan")
        ].copy()

        if not df_func.empty:
            agrupado = df_func.groupby("NOMBRE FUNCIONARIO")
            resumen_funcionarios = []
            detalle_categoria = []

            for nombre, grupo in agrupado:
                tiempos_validos = grupo["TIEMPO_TOTAL"].dropna()

                promedio_general = tiempos_validos.mean() if not tiempos_validos.empty else pd.NaT
                minimo = tiempos_validos.min() if not tiempos_validos.empty else pd.NaT
                maximo = tiempos_validos.max() if not tiempos_validos.empty else pd.NaT

                if not tiempos_validos.empty and pd.notna(umbral_atipico):
                    atipicos = int((tiempos_validos > umbral_atipico).sum())
                else:
                    atipicos = 0

                terminales = []
                if "TERMINAL" in grupo.columns:
                    terminales = (
                        grupo["TERMINAL"]
                        .dropna()
                        .astype(str)
                        .str.strip()
                        .unique()
                        .tolist()
                    )

                total_registros = int(len(grupo))

                entregas = int((grupo["CATEGORIA_TRAMITE"] == "ENTREGA").sum())
                tramites_reales = int(total_registros - entregas)

                grupo_entregas = grupo[grupo["CATEGORIA_TRAMITE"] == "ENTREGA"]
                grupo_tramites = grupo[grupo["CATEGORIA_TRAMITE"] != "ENTREGA"]

                tiempos_entregas = grupo_entregas["TIEMPO_TOTAL"].dropna()
                tiempos_tramites = grupo_tramites["TIEMPO_TOTAL"].dropna()

                promedio_entregas = (
                    str(tiempos_entregas.mean()) if not tiempos_entregas.empty else "Sin datos"
                )
                promedio_tramites = (
                    str(tiempos_tramites.mean()) if not tiempos_tramites.empty else "Sin datos"
                )

                porcentaje_atipicos = round((atipicos / total_registros) * 100, 2) if total_registros else 0

                resumen_funcionarios.append({
                    "funcionario": nombre,
                    "total_registros": total_registros,
                    "entregas": entregas,
                    "tramites_reales": tramites_reales,
                    "promedio_general": str(promedio_general) if pd.notna(promedio_general) else "Sin datos",
                    "promedio_entregas": promedio_entregas,
                    "promedio_tramites": promedio_tramites,
                    "tiempo_minimo": str(minimo) if pd.notna(minimo) else "Sin datos",
                    "tiempo_maximo": str(maximo) if pd.notna(maximo) else "Sin datos",
                    "tramites_atipicos": atipicos,
                    "porcentaje_atipicos": porcentaje_atipicos,
                    "terminales": ", ".join(terminales) if terminales else "Sin dato"
                })

                agrupado_categoria = grupo.groupby("CATEGORIA_TRAMITE")

                for categoria, grupo_cat in agrupado_categoria:
                    tiempos_cat = grupo_cat["TIEMPO_TOTAL"].dropna()

                    promedio_cat = tiempos_cat.mean() if not tiempos_cat.empty else pd.NaT
                    minimo_cat = tiempos_cat.min() if not tiempos_cat.empty else pd.NaT
                    maximo_cat = tiempos_cat.max() if not tiempos_cat.empty else pd.NaT

                    if not tiempos_cat.empty and pd.notna(umbral_atipico):
                        atipicos_cat = int((tiempos_cat > umbral_atipico).sum())
                    else:
                        atipicos_cat = 0

                    detalle_categoria.append({
                        "funcionario": nombre,
                        "tipo_tramite": categoria,
                        "cantidad": int(len(grupo_cat)),
                        "promedio_tiempo": str(promedio_cat) if pd.notna(promedio_cat) else "Sin datos",
                        "tiempo_minimo": str(minimo_cat) if pd.notna(minimo_cat) else "Sin datos",
                        "tiempo_maximo": str(maximo_cat) if pd.notna(maximo_cat) else "Sin datos",
                        "tramites_atipicos": atipicos_cat,
                    })

            resumen_funcionarios = sorted(
                resumen_funcionarios,
                key=lambda x: x["total_registros"],
                reverse=True
            )

            detalle_categoria = sorted(
                detalle_categoria,
                key=lambda x: (x["funcionario"], -x["cantidad"])
            )

            resultado["por_funcionario"] = resumen_funcionarios
            resultado["detalle_funcionario_categoria"] = detalle_categoria

    return resultado