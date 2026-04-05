from datetime import datetime
import pandas as pd
from sqlalchemy import text

from app.core.database import engine


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


def guardar_cr_en_bd(df, archivo_id, nombre_original, mac):
    if df is None or df.empty:
        return {
            "insertados_entregas": 0,
            "fecha_operativa": None,
        }

    df_trabajo = df.copy()
    insertados_entregas = 0
    fecha_operativa_global = None

    with engine.begin() as conn:
        for _, row in df_trabajo.iterrows():
            fecha_entrega = _parse_fecha(row.get("fecha_entrega"))
            if fecha_entrega is not None:
                if fecha_operativa_global is None or fecha_entrega > fecha_operativa_global:
                    fecha_operativa_global = fecha_entrega

            solicitud = _valor_limpio(row.get("solicitud"))
            folio_nec = _valor_limpio(row.get("folio_nec"))
            terminal = _valor_limpio(row.get("terminal"))

            if fecha_entrega is None or solicitud is None or terminal is None:
                continue

            existe = conn.execute(
                text("""
                    SELECT id
                    FROM macmetric.entregas_cr
                    WHERE archivo_cargado_id = :archivo_id
                      AND COALESCE(solicitud, '') = COALESCE(:solicitud, '')
                      AND COALESCE(terminal, '') = COALESCE(:terminal, '')
                      AND fecha_entrega = :fecha_entrega
                    LIMIT 1
                """),
                {
                    "archivo_id": archivo_id,
                    "solicitud": solicitud,
                    "terminal": terminal,
                    "fecha_entrega": fecha_entrega,
                }
            ).scalar()

            if existe:
                continue

            hora_inicio = _parse_timestamp(fecha_entrega, row.get("hora_inicio_atencion"))
            hora_fin = _parse_timestamp(fecha_entrega, row.get("captura_hora_fin"))
            minutos = row.get("minutos_atencion")

            if pd.isna(minutos):
                minutos = None
            else:
                minutos = round(float(minutos), 2)

            dentro_norma = None
            if minutos is not None:
                dentro_norma = minutos <= 15

            conn.execute(
                text("""
                    INSERT INTO macmetric.entregas_cr (
                        archivo_cargado_id,
                        mac_modulo,
                        fecha_entrega,
                        solicitud,
                        folio_nec,
                        terminal,
                        hora_inicio,
                        hora_fin,
                        minutos_atencion,
                        dentro_norma,
                        origen_archivo
                    )
                    VALUES (
                        :archivo_cargado_id,
                        :mac_modulo,
                        :fecha_entrega,
                        :solicitud,
                        :folio_nec,
                        :terminal,
                        :hora_inicio,
                        :hora_fin,
                        :minutos_atencion,
                        :dentro_norma,
                        :origen_archivo
                    )
                """),
                {
                    "archivo_cargado_id": archivo_id,
                    "mac_modulo": mac,
                    "fecha_entrega": fecha_entrega,
                    "solicitud": solicitud,
                    "folio_nec": folio_nec,
                    "terminal": terminal,
                    "hora_inicio": hora_inicio,
                    "hora_fin": hora_fin,
                    "minutos_atencion": minutos,
                    "dentro_norma": dentro_norma,
                    "origen_archivo": nombre_original,
                }
            )

            insertados_entregas += 1

    return {
        "insertados_entregas": insertados_entregas,
        "fecha_operativa": fecha_operativa_global,
    }