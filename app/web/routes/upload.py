from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import text

from app.core.database import engine
from backend.services.file_classifier import detectar_mac, detectar_tipo

from app.parsers.siirfe_parser import parse_siirfe_file
from backend.services.time_cleaner import limpiar_reporte_tiempos
from backend.services.time_metrics import calcular_metricas_tiempos
from backend.utils.exporter import exportar_metricas_csv
from backend.services.sol_repository import guardar_sol_en_bd
from app.parsers.siirfe_parser_cr import parse_siirfe_cr_file
from backend.services.cr_cleaner import limpiar_reporte_cr
from backend.services.cr_repository import guardar_cr_en_bd

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[3]
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def validar_sesion(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
    return None


@router.post("/upload")
async def subir_archivo(
    request: Request,
    expected_tipo: str = Form(None),
    archivo: UploadFile = File(...)
):
    sesion = validar_sesion(request)
    if sesion:
        return sesion

    if not archivo.filename:
        return RedirectResponse(
            url="/dashboard?error=No+se+selecciono+ningun+archivo",
            status_code=303
        )

    nombre_original = archivo.filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_guardado = f"{timestamp}_{nombre_original}"
    ruta_destino = UPLOAD_DIR / nombre_guardado

    mac = detectar_mac(nombre_original)
    tipo = detectar_tipo(nombre_original)
    usuario_carga = request.session.get("user")
    role_id = request.session.get("role_id")
    mac_usuario = request.session.get("mac_asignado")

    if expected_tipo and tipo != expected_tipo:
        tipo_legible = "SOL" if tipo == "TIEMPOS_SOL" else "CR" if tipo == "TIEMPOS_CR" else tipo
        expected_legible = "SOL" if expected_tipo == "TIEMPOS_SOL" else "CR" if expected_tipo == "TIEMPOS_CR" else expected_tipo

        return RedirectResponse(
            url=f"/dashboard?error=El+archivo+seleccionado+corresponde+a+{tipo_legible}+y+no+a+{expected_legible}",
            status_code=303
        )

    # Validación por MAC asignado
    if str(role_id) != "1":
        if mac == "DESCONOCIDO":
            return RedirectResponse(
                url="/dashboard?error=No+se+pudo+identificar+el+MAC+del+archivo",
                status_code=303
            )

        if not mac_usuario:
            return RedirectResponse(
                url="/dashboard?error=Tu+usuario+no+tiene+MAC+asignado",
                status_code=303
            )

        if mac != mac_usuario:
            return RedirectResponse(
                url="/dashboard?error=No+puedes+subir+archivos+de+otro+MAC",
                status_code=303
            )

    archivo_id = None

    try:
        contenido = await archivo.read()
        ruta_destino.write_bytes(contenido)

        with engine.begin() as conn:
            resultado = conn.execute(
                text("""
                    INSERT INTO macmetric.archivos_cargados
                    (nombre_archivo, ruta_archivo, mac, tipo, usuario_carga, estatus, activo)
                    VALUES (:nombre_archivo, :ruta_archivo, :mac, :tipo, :usuario_carga, :estatus, :activo)
                    RETURNING id
                """),
                {
                    "nombre_archivo": nombre_original,
                    "ruta_archivo": str(ruta_destino),
                    "mac": mac,
                    "tipo": tipo,
                    "usuario_carga": usuario_carga,
                    "estatus": "PENDIENTE",
                    "activo": True,
                }
            )
            archivo_id = resultado.scalar_one()

        # Procesamiento automático solo para SOL
        if tipo == "TIEMPOS_SOL":
            try:
                resultado_parser = parse_siirfe_file(str(ruta_destino))

                if not resultado_parser["success"]:
                    raise ValueError(resultado_parser["error"])

                df = resultado_parser["data"]

                if df is None or df.empty:
                    raise ValueError("El parser no devolvió datos útiles")

                df = limpiar_reporte_tiempos(df)

                if df.empty:
                    raise ValueError("El archivo quedó sin registros después de la limpieza")

                # Guardar detalle en BD
                resultado_guardado = guardar_sol_en_bd(
                    df=df,
                    archivo_id=archivo_id,
                    nombre_original=nombre_original,
                    mac=mac
                )

                metricas = calcular_metricas_tiempos(df)

                if not metricas:
                    raise ValueError("No se pudieron calcular métricas")

                ranking = metricas.get("por_funcionario", [])
                total_registros = metricas.get("total_registros", 0)

                if total_registros == 0:
                    raise ValueError("El archivo no contiene registros procesables")

                if not ranking:
                    raise ValueError("No se generó ranking por funcionario")

                ruta_reporte = exportar_metricas_csv(
                    metricas=metricas,
                    nombre_archivo_origen=nombre_original,
                    tipo=tipo
                )

                ruta_reporte_path = Path(ruta_reporte)

                if not ruta_reporte_path.exists():
                    raise ValueError("No se generó el archivo de reporte CSV")

                if ruta_reporte_path.stat().st_size == 0:
                    raise ValueError("El reporte CSV se generó vacío")

                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            UPDATE macmetric.archivos_cargados
                            SET estatus = :estatus,
                                mensaje_error = :mensaje_error,
                                fecha_operativa = :fecha_operativa,
                                registros_insertados = :registros_insertados,
                                nombre_reporte_generado = :nombre_reporte_generado
                            WHERE id = :id
                        """),
                        {
                            "id": archivo_id,
                            "estatus": "PROCESADO",
                            "mensaje_error": None,
                            "fecha_operativa": resultado_guardado.get("fecha_operativa"),
                            "registros_insertados": resultado_guardado.get("insertados_tramites", 0),
                            "nombre_reporte_generado": str(ruta_reporte),
                        }
                    )

                mensaje = f"SOL | MAC {mac} | Fecha {resultado_guardado.get('fecha_operativa')} | Registros {resultado_guardado.get('insertados_tramites', 0)}"
                return RedirectResponse(
                    url=f"/dashboard?success={mensaje.replace(' ', '+')}",
                    status_code=303
                )
            except Exception as e:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            UPDATE macmetric.archivos_cargados
                            SET estatus = :estatus,
                                mensaje_error = :mensaje_error
                            WHERE id = :id
                        """),
                        {
                            "id": archivo_id,
                            "estatus": "ERROR",
                            "mensaje_error": str(e),
                        }
                    )

                return RedirectResponse(
                    url="/dashboard?error=El+archivo+SOL+se+subio+pero+fallo+el+procesamiento",
                    status_code=303
                )

        elif tipo == "TIEMPOS_CR":
                    try:
                        resultado_parser = parse_siirfe_cr_file(str(ruta_destino))

                        if not resultado_parser["success"]:
                            raise ValueError(resultado_parser["error"])

                        df = resultado_parser["data"]

                        if df is None or df.empty:
                            raise ValueError("El parser CR no devolvió datos útiles")

                        df = limpiar_reporte_cr(df)

                        if df.empty:
                            raise ValueError("El archivo CR quedó sin registros después de la limpieza")

                        print("COLUMNAS CR:", df.columns.tolist())
                        print("TOTAL REGISTROS CR:", len(df))
                        print(df.head(3))

                        resultado_guardado = guardar_cr_en_bd(
                            df=df,
                            archivo_id=archivo_id,
                            nombre_original=nombre_original,
                            mac=mac
                        )

                        print("RESULTADO GUARDADO CR:", resultado_guardado)

                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    UPDATE macmetric.archivos_cargados
                                    SET estatus = :estatus,
                                        mensaje_error = :mensaje_error,
                                        fecha_operativa = :fecha_operativa,
                                        registros_insertados = :registros_insertados
                                    WHERE id = :id
                                """),
                                {
                                    "id": archivo_id,
                                    "estatus": "PROCESADO",
                                    "mensaje_error": None,
                                    "fecha_operativa": resultado_guardado.get("fecha_operativa"),
                                    "registros_insertados": resultado_guardado.get("insertados_entregas", 0),
                                }
                            )

                        mensaje = f"CR | MAC {mac} | Fecha {resultado_guardado.get('fecha_operativa')} | Registros {resultado_guardado.get('insertados_entregas', 0)}"
                        return RedirectResponse(
                            url=f"/dashboard?success={mensaje.replace(' ', '+')}",
                            status_code=303
                        )

                    except Exception as e:
                        print("ERROR REAL CR:", repr(e))

                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    UPDATE macmetric.archivos_cargados
                                    SET estatus = :estatus,
                                        mensaje_error = :mensaje_error
                                    WHERE id = :id
                                """),
                                {
                                    "id": archivo_id,
                                    "estatus": "ERROR",
                                    "mensaje_error": str(e),
                                }
                            )

                        return RedirectResponse(
                            url=f"/dashboard?error=CR:{str(e)}",
                            status_code=303
                        )

                    except Exception as e:
                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    UPDATE macmetric.archivos_cargados
                                    SET estatus = :estatus,
                                        mensaje_error = :mensaje_error
                                    WHERE id = :id
                                """),
                                {
                                    "id": archivo_id,
                                    "estatus": "ERROR",
                                    "mensaje_error": str(e),
                                }
                            )

                        return RedirectResponse(
                            url="/dashboard?error=El+archivo+CR+se+subio+pero+fallo+el+procesamiento",
                            status_code=303
                        )

        return RedirectResponse(
            url="/dashboard?success=Archivo+cargado+correctamente",
            status_code=303
        )

    except Exception as e:
        if archivo_id is not None:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            UPDATE macmetric.archivos_cargados
                            SET estatus = :estatus,
                                mensaje_error = :mensaje_error
                            WHERE id = :id
                        """),
                        {
                            "id": archivo_id,
                            "estatus": "ERROR",
                            "mensaje_error": str(e),
                        }
                    )
            except Exception:
                pass
        else:
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO macmetric.archivos_cargados
                            (nombre_archivo, ruta_archivo, mac, tipo, usuario_carga, estatus, mensaje_error, activo)
                            VALUES (:nombre_archivo, :ruta_archivo, :mac, :tipo, :usuario_carga, :estatus, :mensaje_error, :activo)
                        """),
                        {
                            "nombre_archivo": nombre_original,
                            "ruta_archivo": "",
                            "mac": mac,
                            "tipo": tipo,
                            "usuario_carga": usuario_carga,
                            "estatus": "ERROR",
                            "mensaje_error": str(e),
                            "activo": True,
                        }
                    )
            except Exception:
                pass

        return RedirectResponse(
            url="/dashboard?error=Error+al+subir+el+archivo",
            status_code=303
        )