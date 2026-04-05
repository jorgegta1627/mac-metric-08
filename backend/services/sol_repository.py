from datetime import datetime
import pandas as pd
from sqlalchemy import text

from app.core.database import engine
from backend.services.time_metrics import (
    detectar_columna_tipo_tramite,
    clasificar_categoria_tramite,
)


def _valor_limpio(valor, default=None):
    if pd.isna(valor):
        return default
    texto = str(valor).strip()
    if texto.lower() == "nan":
        return default
    return texto if texto != "" else default


def _parse_fecha(valor):
    if pd.isna(valor):
        return None

    fecha = pd.to_datetime(valor, errors="coerce", dayfirst=True)
    if pd.isna(fecha):
        return None

    return fecha.date()


def _parse_timestamp(fecha_base, valor_hora):
    if fecha_base is None or pd.isna(valor_hora):
        return None

    texto = str(valor_hora).strip()
    if not texto or texto.lower() == "nan":
        return None

    try:
        hora = pd.to_timedelta(texto)
        dt = datetime.combine(fecha_base, datetime.min.time()) + hora
        return dt
    except Exception:
        pass

    try:
        dt = pd.to_datetime(f"{fecha_base} {texto}", errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime()
    except Exception:
        return None


def _parse_minutos(valor_tiempo_total):
    if pd.isna(valor_tiempo_total):
        return None

    try:
        td = pd.to_timedelta(valor_tiempo_total, errors="coerce")
        if pd.isna(td):
            return None
        return round(td.total_seconds() / 60, 2)
    except Exception:
        return None


def guardar_sol_en_bd(df, archivo_id, nombre_original, mac):
    if df is None or df.empty:
        return {
            "insertados_tramites": 0,
            "insertados_tiempos": 0,
            "fecha_operativa": None,
        }

    df_trabajo = df.copy()
    df_trabajo.columns = [str(col).strip() for col in df_trabajo.columns]

    columna_tipo = detectar_columna_tipo_tramite(df_trabajo.columns)

    if columna_tipo and "TIPO_TRAMITE_CATEGORIA" not in df_trabajo.columns:
        df_trabajo["TIPO_TRAMITE_CATEGORIA"] = df_trabajo[columna_tipo].apply(clasificar_categoria_tramite)
    elif "TIPO_TRAMITE_CATEGORIA" not in df_trabajo.columns:
        df_trabajo["TIPO_TRAMITE_CATEGORIA"] = "SIN_CLASIFICAR"

    insertados_tramites = 0
    insertados_tiempos = 0
    fecha_operativa_global = None

    with engine.begin() as conn:
        for _, row in df_trabajo.iterrows():
            fecha_tramite = _parse_fecha(row.get("FECHA DE TRAMITE"))
            if fecha_tramite is not None:
                if fecha_operativa_global is None or fecha_tramite > fecha_operativa_global:
                    fecha_operativa_global = fecha_tramite

            folio = _valor_limpio(row.get("SOLICITUD"))
            tipo_tramite = _valor_limpio(row.get(columna_tipo)) if columna_tipo else None
            tipo_categoria = _valor_limpio(row.get("TIPO_TRAMITE_CATEGORIA"), "SIN_CLASIFICAR")
            funcionario = _valor_limpio(row.get("NOMBRE FUNCIONARIO"))
            terminal = _valor_limpio(row.get("TERMINAL"))
            domicilio_visible = _valor_limpio(row.get("DOMICILIO VISIBLE"))

            # Evitar duplicados básicos del mismo archivo
            existe = conn.execute(
                text("""
                    SELECT id
                    FROM macmetric.tramites
                    WHERE archivo_cargado_id = :archivo_id
                      AND COALESCE(folio_tramite, '') = COALESCE(:folio, '')
                      AND COALESCE(funcionario_nombre, '') = COALESCE(:funcionario, '')
                      AND COALESCE(terminal, '') = COALESCE(:terminal, '')
                    LIMIT 1
                """),
                {
                    "archivo_id": archivo_id,
                    "folio": folio,
                    "funcionario": funcionario,
                    "terminal": terminal,
                }
            ).scalar()

            if existe:
                continue

            tramite_id = conn.execute(
                text("""
                    INSERT INTO macmetric.tramites (
                        carga_archivo_id,
                        archivo_cargado_id,
                        mac_modulo,
                        fecha_tramite,
                        folio_tramite,
                        tipo_tramite,
                        tipo_tramite_categoria,
                        funcionario_nombre,
                        terminal,
                        domicilio_visible,
                        origen_archivo
                    )
                    VALUES (
                        NULL,
                        :archivo_cargado_id,
                        :mac_modulo,
                        :fecha_tramite,
                        :folio_tramite,
                        :tipo_tramite,
                        :tipo_tramite_categoria,
                        :funcionario_nombre,
                        :terminal,
                        :domicilio_visible,
                        :origen_archivo
                    )
                    RETURNING id
                """),
                {
                    "archivo_cargado_id": archivo_id,
                    "mac_modulo": mac,
                    "fecha_tramite": fecha_tramite,
                    "folio_tramite": folio,
                    "tipo_tramite": tipo_tramite,
                    "tipo_tramite_categoria": tipo_categoria,
                    "funcionario_nombre": funcionario,
                    "terminal": terminal,
                    "domicilio_visible": domicilio_visible,
                    "origen_archivo": nombre_original,
                }
            ).scalar_one()

            insertados_tramites += 1

            hora_inicio = _parse_timestamp(fecha_tramite, row.get("HORA INICIO ATENCIÓN"))
            hora_fin = _parse_timestamp(fecha_tramite, row.get("HORA FIN ATENCIÓN"))
            minutos = _parse_minutos(row.get("TIEMPO TOTAL DE ATENCIÓN"))

            dentro_norma = None
            if minutos is not None:
                dentro_norma = minutos <= 15

            conn.execute(
                text("""
                    INSERT INTO macmetric.tiempos_atencion (
                        carga_archivo_id,
                        archivo_cargado_id,
                        tramite_id,
                        mac_modulo,
                        fecha_atencion,
                        hora_inicio,
                        hora_fin,
                        minutos_atencion,
                        dentro_norma,
                        observaciones,
                        origen_archivo
                    )
                    VALUES (
                        NULL,
                        :archivo_cargado_id,
                        :tramite_id,
                        :mac_modulo,
                        :fecha_atencion,
                        :hora_inicio,
                        :hora_fin,
                        :minutos_atencion,
                        :dentro_norma,
                        :observaciones,
                        :origen_archivo
                    )
                """),
                {
                    "archivo_cargado_id": archivo_id,
                    "tramite_id": tramite_id,
                    "mac_modulo": mac,
                    "fecha_atencion": fecha_tramite,
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                    "minutos_atencion": minutos,
                    "dentro_norma": dentro_norma,
                    "observaciones": None,
                    "origen_archivo": nombre_original,
                }
            )

            insertados_tiempos += 1

    return {
        "insertados_tramites": insertados_tramites,
        "insertados_tiempos": insertados_tiempos,
        "fecha_operativa": fecha_operativa_global,
    }