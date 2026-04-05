from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.dashboard_db_reader import obtener_detalle_funcionario

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def validar_sesion(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)
    return None


@router.get("/funcionario/{nombre_funcionario}")
def detalle_funcionario(
    request: Request,
    nombre_funcionario: str,
    mac: str = None,
    fecha: str = None,
    tipo: str = None
):

    detalle = obtener_detalle_funcionario(
    nombre_funcionario=nombre_funcionario,
    mac=mac,
    fecha_operativa=fecha,
    tipo_tramite=tipo
)

    if not detalle:
        return templates.TemplateResponse(
        request=request,
        name="funcionario_detalle.html",
        context={
            "detalle": None,
            "nombre_funcionario": nombre_funcionario,
            "mac_seleccionado": mac,
            "fecha_seleccionada": fecha,
            "error": "No se encontraron datos para el funcionario seleccionado.",
            "tipo_seleccionado": tipo,
        },
        )

    return templates.TemplateResponse(
    request=request,
    name="funcionario_detalle.html",
    context={
        "detalle": detalle,
        "nombre_funcionario": nombre_funcionario,
        "mac_seleccionado": mac,
        "fecha_seleccionada": fecha,
        "error": None,
    },
    )