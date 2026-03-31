from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request):
    resumen = {
        "total_tramites": 1099,
        "promedio_mac": "00:12:23",
        "ranking_funcionarios": [
            {
                "funcionario": "MONROY SORIANO GIOVANNI YAEL",
                "tramites": 183,
                "promedio_tiempo": "00:20:21",
                "casos_atipicos": 73,
            },
            {
                "funcionario": "LOPEZ IBARRA JUAN ARMANDO",
                "tramites": 136,
                "promedio_tiempo": "00:07:38",
                "casos_atipicos": 0,
            },
            {
                "funcionario": "RODRIGUEZ CORONILLA LUCERO",
                "tramites": 128,
                "promedio_tiempo": "00:06:12",
                "casos_atipicos": 0,
            },
            {
                "funcionario": "DIAZ ROJAS JENNIFER",
                "tramites": 120,
                "promedio_tiempo": "00:06:56",
                "casos_atipicos": 0,
            },
        ],
    }

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "resumen": resumen,
        },
    )