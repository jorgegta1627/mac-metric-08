from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.dashboard_db_reader import obtener_resumen_dashboard_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def validar_sesion(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
    return None


@router.get("/dashboard")
def dashboard_view(request: Request, mac: str = None, fecha: str = None):
    sesion = validar_sesion(request)
    if sesion:
        return sesion

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    mac_seleccionado = mac or ""
    fecha_seleccionada = fecha or ""

    resumen = obtener_resumen_dashboard_db(
        mac=mac_seleccionado if mac_seleccionado else None,
        fecha_operativa=fecha_seleccionada if fecha_seleccionada else None
    )

    if not resumen:
        resumen = {
            "archivo_id": None,
            "fuente_sol": "Sin reporte",
            "fuente_cr": "Sin reporte",
            "mac": "Sin datos",
            "fecha_operativa": "Sin datos",
            "total_tramites": 0,
            "total_entregas": 0,
            "relacion_global": "0.00",
            "promedio_mac": "Sin datos",
            "funcionarios_activos": 0,
            "ranking_funcionarios": [],
            "promedio_entrega": "Sin datos",
            "tiempo_minimo": "Sin datos",
            "tiempo_maximo": "Sin datos",
            "atipicos_cr": 0,
            "distribucion_terminal_cr": [],
        }

    cr_resultado = {
        "success": True,
        "error": None,
        "metricas": {
            "total_entregas": resumen.get("total_entregas", 0),
            "promedio_tiempo": resumen.get("promedio_entrega", "Sin datos"),
            "tiempo_minimo": resumen.get("tiempo_minimo", "Sin datos"),
            "tiempo_maximo": resumen.get("tiempo_maximo", "Sin datos"),
            "atipicos": resumen.get("atipicos_cr", 0),
            "por_terminal": resumen.get("distribucion_terminal_cr", []),
        },
        "archivo": resumen.get("fuente_cr", "Sin reporte"),
    }

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "success": success,
            "error": error,
            "resumen": resumen,
            "cr_resultado": cr_resultado,
            "mac_seleccionado": mac_seleccionado,
            "fecha_seleccionada": fecha_seleccionada,
            "usuario": request.session.get("user"),
        }
    )