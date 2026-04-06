from sqlalchemy import text
from app.core.database import engine


def formatear_minutos_a_hhmmss(valor):
    if valor is None:
        return "Sin datos"

    total_segundos = int(round(float(valor) * 60))
    horas = total_segundos // 3600
    minutos = (total_segundos % 3600) // 60
    segundos = total_segundos % 60

    return f"{horas:02}:{minutos:02}:{segundos:02}"


def obtener_archivo_sol(mac=None, fecha_operativa=None):
    condiciones = [
        "tipo = 'TIEMPOS_SOL'",
        "estatus = 'PROCESADO'",
        "activo = TRUE",
    ]
    params = {}

    if mac:
        condiciones.append("mac = :mac")
        params["mac"] = mac

    if fecha_operativa:
        condiciones.append("fecha_operativa = :fecha_operativa")
        params["fecha_operativa"] = fecha_operativa

    where_sql = " AND ".join(condiciones)

    sql = f"""
    SELECT
        id,
        nombre_archivo,
        mac,
        fecha_operativa,
        fecha_carga,
        tipo_periodo
    FROM macmetric.archivos_cargados
    WHERE {where_sql}
    ORDER BY
        CASE
            WHEN tipo_periodo = 'DIARIO' THEN 0
            WHEN tipo_periodo = 'SEMANAL' THEN 1
            ELSE 2
        END,
        fecha_operativa DESC NULLS LAST,
        fecha_carga DESC NULLS LAST,
        id DESC
    LIMIT 1
    """

    with engine.connect() as conn:
        result = conn.execute(text(sql), params).mappings().first()

    return result


def obtener_archivo_cr(mac=None, fecha_operativa=None):
    condiciones = [
        "tipo = 'TIEMPOS_CR'",
        "estatus = 'PROCESADO'",
        "activo = TRUE",
    ]
    params = {}

    if mac:
        condiciones.append("mac = :mac")
        params["mac"] = mac

    if fecha_operativa:
        condiciones.append("fecha_operativa = :fecha_operativa")
        params["fecha_operativa"] = fecha_operativa

    where_sql = " AND ".join(condiciones)

    sql = f"""
    SELECT
        id,
        nombre_archivo,
        mac,
        fecha_operativa,
        fecha_carga,
        tipo_periodo
    FROM macmetric.archivos_cargados
    WHERE {where_sql}
    ORDER BY
        CASE
            WHEN tipo_periodo = 'DIARIO' THEN 0
            WHEN tipo_periodo = 'SEMANAL' THEN 1
            ELSE 2
        END,
        fecha_operativa DESC NULLS LAST,
        fecha_carga DESC NULLS LAST,
        id DESC
    LIMIT 1
    """

    with engine.connect() as conn:
        result = conn.execute(text(sql), params).mappings().first()

    return result


def obtener_resumen_general(archivo_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    COUNT(*) AS total_tramites,
                    ROUND(AVG(ti.minutos_atencion), 2) AS promedio_general,
                    COUNT(DISTINCT t.funcionario_nombre) AS funcionarios_activos
                FROM macmetric.tramites t
                JOIN macmetric.tiempos_atencion ti
                    ON ti.tramite_id = t.id
                WHERE t.archivo_cargado_id = :archivo_id
            """),
            {"archivo_id": archivo_id}
        ).mappings().first()

    if not result:
        return {
            "total_tramites": 0,
            "promedio_mac": "Sin datos",
            "funcionarios_activos": 0,
        }

    return {
        "total_tramites": result["total_tramites"] or 0,
        "promedio_mac": formatear_minutos_a_hhmmss(result["promedio_general"]),
        "funcionarios_activos": result["funcionarios_activos"] or 0,
    }


def obtener_ranking_funcionarios(archivo_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    t.funcionario_nombre AS funcionario,
                    COUNT(*) AS tramites,
                    ROUND(AVG(ti.minutos_atencion), 2) AS promedio_minutos,
                    SUM(CASE WHEN ti.minutos_atencion > 15 THEN 1 ELSE 0 END) AS casos_atipicos,
                    STRING_AGG(
                        DISTINCT COALESCE(t.terminal, 'Sin terminal'),
                        ', ' ORDER BY COALESCE(t.terminal, 'Sin terminal')
                    ) AS terminales
                FROM macmetric.tramites t
                JOIN macmetric.tiempos_atencion ti
                    ON ti.tramite_id = t.id
                WHERE t.archivo_cargado_id = :archivo_id
                GROUP BY t.funcionario_nombre
                ORDER BY tramites DESC, t.funcionario_nombre ASC
            """),
            {"archivo_id": archivo_id}
        ).mappings().all()

    ranking = []
    for row in result:
        promedio_minutos = row["promedio_minutos"] or 0
        casos_atipicos = row["casos_atipicos"] or 0
        tramites = row["tramites"] or 0
        porcentaje_atipicos = (casos_atipicos / tramites) if tramites > 0 else 0

        if tramites < 10:
            desempeno = "Bajo volumen"
        elif promedio_minutos <= 13 and porcentaje_atipicos <= 0.20:
            desempeno = "Alto"
        elif promedio_minutos <= 15 and porcentaje_atipicos <= 0.35:
            desempeno = "Medio"
        else:
            desempeno = "Bajo"

        ranking.append({
            "funcionario": row["funcionario"],
            "tramites": tramites,
            "promedio_tiempo": formatear_minutos_a_hhmmss(promedio_minutos),
            "casos_atipicos": casos_atipicos,
            "terminales": row["terminales"] or "Sin datos",
            "desempeno": desempeno,
        })

    return ranking


def obtener_metricas_cr_detalle(archivo_id):
    with engine.connect() as conn:
        resumen = conn.execute(
            text("""
                SELECT
                    COUNT(*) AS total_entregas,
                    AVG(minutos_atencion) AS promedio,
                    MIN(minutos_atencion) AS minimo,
                    MAX(minutos_atencion) AS maximo
                FROM macmetric.entregas_cr
                WHERE archivo_cargado_id = :archivo_id
            """),
            {"archivo_id": archivo_id}
        ).mappings().first()

        por_terminal = conn.execute(
            text("""
                SELECT
                    COALESCE(terminal, 'Sin dato') AS terminal,
                    COUNT(*) AS entregas,
                    AVG(minutos_atencion) AS promedio,
                    MIN(minutos_atencion) AS minimo,
                    MAX(minutos_atencion) AS maximo
                FROM macmetric.entregas_cr
                WHERE archivo_cargado_id = :archivo_id
                GROUP BY COALESCE(terminal, 'Sin dato')
                ORDER BY entregas DESC, terminal
            """),
            {"archivo_id": archivo_id}
        ).mappings().all()

        atipicos = conn.execute(
            text("""
                SELECT COUNT(*) AS total
                FROM macmetric.entregas_cr
                WHERE archivo_cargado_id = :archivo_id
                  AND minutos_atencion > 15
            """),
            {"archivo_id": archivo_id}
        ).scalar() or 0

    if not resumen:
        return {
            "total_entregas": 0,
            "promedio_tiempo": "Sin datos",
            "tiempo_minimo": "Sin datos",
            "tiempo_maximo": "Sin datos",
            "atipicos": 0,
            "por_terminal": [],
        }

    return {
        "total_entregas": resumen["total_entregas"] or 0,
        "promedio_tiempo": formatear_minutos_a_hhmmss(resumen["promedio"]),
        "tiempo_minimo": formatear_minutos_a_hhmmss(resumen["minimo"]),
        "tiempo_maximo": formatear_minutos_a_hhmmss(resumen["maximo"]),
        "atipicos": atipicos,
        "por_terminal": [
            {
                "terminal": fila["terminal"],
                "entregas": fila["entregas"] or 0,
                "promedio": formatear_minutos_a_hhmmss(fila["promedio"]),
                "minimo": formatear_minutos_a_hhmmss(fila["minimo"]),
                "maximo": formatear_minutos_a_hhmmss(fila["maximo"]),
            }
            for fila in por_terminal
        ]
    }


def obtener_resumen_dashboard_db(mac=None, fecha_operativa=None):
    archivo_sol = obtener_archivo_sol(mac=mac, fecha_operativa=fecha_operativa)
    archivo_cr = obtener_archivo_cr(mac=mac, fecha_operativa=fecha_operativa)

    if not archivo_sol and not archivo_cr:
        return None

    resumen_general = {
        "total_tramites": 0,
        "promedio_mac": "Sin datos",
        "funcionarios_activos": 0,
    }
    ranking = []

    if archivo_sol:
        resumen_general = obtener_resumen_general(archivo_sol["id"])
        ranking = obtener_ranking_funcionarios(archivo_sol["id"])

    resumen_cr = {
        "total_entregas": 0,
        "promedio_entrega": "Sin datos",
        "tiempo_minimo": "Sin datos",
        "tiempo_maximo": "Sin datos",
        "atipicos": 0,
        "por_terminal": [],
    }

    if archivo_cr:
        detalle_cr = obtener_metricas_cr_detalle(archivo_cr["id"])
        resumen_cr = {
            "total_entregas": detalle_cr["total_entregas"],
            "promedio_entrega": detalle_cr["promedio_tiempo"],
            "tiempo_minimo": detalle_cr["tiempo_minimo"],
            "tiempo_maximo": detalle_cr["tiempo_maximo"],
            "atipicos": detalle_cr["atipicos"],
            "por_terminal": detalle_cr["por_terminal"],
        }

    total_tramites = resumen_general["total_tramites"]
    total_entregas = resumen_cr["total_entregas"]

    relacion_global = "0.00"
    if total_tramites > 0:
        relacion_global = f"{(total_entregas / total_tramites):.2f}"

    return {
        "archivo_id": archivo_sol["id"] if archivo_sol else None,
        "fuente_sol": archivo_sol["nombre_archivo"] if archivo_sol else "Sin reporte",
        "fuente_cr": archivo_cr["nombre_archivo"] if archivo_cr else "Sin reporte",
        "mac": (archivo_sol["mac"] if archivo_sol else archivo_cr["mac"]) if (archivo_sol or archivo_cr) else "Sin datos",
        "fecha_operativa": (
            archivo_sol["fecha_operativa"] if archivo_sol else archivo_cr["fecha_operativa"]
        ) if (archivo_sol or archivo_cr) else "Sin datos",
        "total_tramites": total_tramites,
        "total_entregas": total_entregas,
        "relacion_global": relacion_global,
        "promedio_mac": resumen_general["promedio_mac"],
        "funcionarios_activos": resumen_general["funcionarios_activos"],
        "ranking_funcionarios": ranking,
        "promedio_entrega": resumen_cr["promedio_entrega"],
        "tiempo_minimo": resumen_cr["tiempo_minimo"],
        "tiempo_maximo": resumen_cr["tiempo_maximo"],
        "atipicos_cr": resumen_cr["atipicos"],
        "distribucion_terminal_cr": resumen_cr["por_terminal"],
    }


def obtener_detalle_funcionario(nombre_funcionario, mac=None, fecha_operativa=None, tipo_tramite=None):
    condiciones_base = ["t.funcionario_nombre = :nombre_funcionario"]
    params_base = {"nombre_funcionario": nombre_funcionario}

    if mac:
        condiciones_base.append("t.mac_modulo = :mac")
        params_base["mac"] = mac

    if fecha_operativa:
        condiciones_base.append("t.fecha_tramite = :fecha_operativa")
        params_base["fecha_operativa"] = fecha_operativa

    where_sql_base = " AND ".join(condiciones_base)

    with engine.connect() as conn:
        resumen = conn.execute(
            text(f"""
                SELECT
                    t.funcionario_nombre,
                    t.mac_modulo,
                    t.fecha_tramite,
                    COUNT(*) AS total_tramites,
                    ROUND(AVG(ti.minutos_atencion), 2) AS promedio_minutos,
                    MIN(ti.minutos_atencion) AS minimo_minutos,
                    MAX(ti.minutos_atencion) AS maximo_minutos,
                    SUM(CASE WHEN ti.minutos_atencion > 15 THEN 1 ELSE 0 END) AS mayores_15,
                    STRING_AGG(
                        DISTINCT COALESCE(t.terminal, 'Sin terminal'),
                        ', ' ORDER BY COALESCE(t.terminal, 'Sin terminal')
                    ) AS terminales
                FROM macmetric.tramites t
                JOIN macmetric.tiempos_atencion ti
                    ON ti.tramite_id = t.id
                WHERE {where_sql_base}
                GROUP BY t.funcionario_nombre, t.mac_modulo, t.fecha_tramite
                ORDER BY t.fecha_tramite DESC
                LIMIT 1
            """),
            params_base
        ).mappings().first()

        if not resumen:
            return None

        condiciones_detalle = [where_sql_base]
        params_detalle = {
            **params_base,
            "mac_resumen": resumen["mac_modulo"],
            "fecha_resumen": resumen["fecha_tramite"],
        }

        if tipo_tramite:
            condiciones_detalle.append("COALESCE(t.tipo_tramite_categoria, 'Sin dato') = :tipo_tramite")
            params_detalle["tipo_tramite"] = tipo_tramite

        where_sql_detalle = " AND ".join(condiciones_detalle)

        detalle_tramites = conn.execute(
            text(f"""
                SELECT
                    t.folio_tramite,
                    t.tipo_tramite,
                    t.tipo_tramite_categoria,
                    ti.hora_inicio,
                    ti.hora_fin,
                    ti.minutos_atencion,
                    t.terminal,
                    t.domicilio_visible,
                    t.estatus_tramite
                FROM macmetric.tramites t
                JOIN macmetric.tiempos_atencion ti
                    ON ti.tramite_id = t.id
                WHERE {where_sql_detalle}
                  AND t.mac_modulo = :mac_resumen
                  AND t.fecha_tramite = :fecha_resumen
                ORDER BY ti.hora_inicio ASC NULLS LAST
            """),
            params_detalle
        ).mappings().all()

        resumen_por_tipo = conn.execute(
            text(f"""
                SELECT
                    COALESCE(t.tipo_tramite_categoria, 'Sin dato') AS tipo_tramite_categoria,
                    COUNT(*) AS total,
                    ROUND(AVG(ti.minutos_atencion), 2) AS promedio_minutos,
                    MIN(ti.minutos_atencion) AS minimo_minutos,
                    MAX(ti.minutos_atencion) AS maximo_minutos,
                    SUM(CASE WHEN ti.minutos_atencion > 15 THEN 1 ELSE 0 END) AS mayores_15
                FROM macmetric.tramites t
                JOIN macmetric.tiempos_atencion ti
                    ON ti.tramite_id = t.id
                WHERE {where_sql_base}
                  AND t.mac_modulo = :mac_resumen
                  AND t.fecha_tramite = :fecha_resumen
                GROUP BY COALESCE(t.tipo_tramite_categoria, 'Sin dato')
                ORDER BY total DESC, tipo_tramite_categoria
            """),
            {
                **params_base,
                "mac_resumen": resumen["mac_modulo"],
                "fecha_resumen": resumen["fecha_tramite"],
            }
        ).mappings().all()

    return {
        "funcionario": resumen["funcionario_nombre"],
        "mac": resumen["mac_modulo"],
        "fecha_operativa": resumen["fecha_tramite"],
        "total_tramites": resumen["total_tramites"] or 0,
        "promedio_tiempo": formatear_minutos_a_hhmmss(resumen["promedio_minutos"]),
        "tiempo_minimo": formatear_minutos_a_hhmmss(resumen["minimo_minutos"]),
        "tiempo_maximo": formatear_minutos_a_hhmmss(resumen["maximo_minutos"]),
        "mayores_15": resumen["mayores_15"] or 0,
        "terminales": resumen["terminales"] or "Sin datos",
        "tipo_seleccionado": tipo_tramite or "",
        "tramites": [
            {
                "folio_tramite": row["folio_tramite"] or "Sin dato",
                "tipo_tramite": row["tipo_tramite"] or "Sin dato",
                "tipo_tramite_categoria": row["tipo_tramite_categoria"] or "Sin dato",
                "hora_inicio": row["hora_inicio"].strftime("%H:%M:%S") if row["hora_inicio"] else "Sin dato",
                "hora_fin": row["hora_fin"].strftime("%H:%M:%S") if row["hora_fin"] else "Sin dato",
                "tiempo_atencion": formatear_minutos_a_hhmmss(row["minutos_atencion"]),
                "terminal": row["terminal"] or "Sin dato",
                "domicilio_visible": row["domicilio_visible"] or "Sin dato",
                "estatus_tramite": row["estatus_tramite"] or "Sin dato",
            }
            for row in detalle_tramites
        ],
        "resumen_por_tipo": [
            {
                "tipo_tramite_categoria": row["tipo_tramite_categoria"],
                "total": row["total"] or 0,
                "promedio_tiempo": formatear_minutos_a_hhmmss(row["promedio_minutos"]),
                "tiempo_minimo": formatear_minutos_a_hhmmss(row["minimo_minutos"]),
                "tiempo_maximo": formatear_minutos_a_hhmmss(row["maximo_minutos"]),
                "mayores_15": row["mayores_15"] or 0,
            }
            for row in resumen_por_tipo
        ],
    }