from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from passlib.context import CryptContext

from app.core.database import engine, test_db_connection

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


@router.get("/login", response_class=HTMLResponse)
def login_view(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "db_status": "Conectada" if test_db_connection() else "Sin conexión",
            "message": None,
            "message_type": None,
        },
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    message = None
    message_type = None

    try:
        with engine.connect() as conn:
            user = conn.execute(
                text("""
                    SELECT 
                        u.id,
                        u.username,
                        u.nombre_completo,
                        u.password_hash,
                        u.role_id,
                        r.nombre AS role_name,
                        u.activo
                    FROM macmetric.usuarios u
                    JOIN macmetric.roles r ON r.id = u.role_id
                    WHERE u.username = :username
                """),
                {"username": username}
            ).mappings().first()
        if not user:
            message = "Usuario o contraseña incorrectos."
            message_type = "error"
        elif not user["activo"]:
            message = "El usuario se encuentra inactivo."
            message_type = "error"
        elif not pwd_context.verify(password, user["password_hash"]):
            message = "Usuario o contraseña incorrectos."
            message_type = "error"
        else:
            request.session["user"] = user["username"]
            request.session["role_id"] = user["role_id"]
            request.session["role_name"] = user["role_name"]
            request.session["last_activity"] = datetime.now().isoformat()
            return RedirectResponse(url="/dashboard", status_code=303)

    except Exception as e:
        message = f"Error en login: {str(e)}"
        message_type = "error"

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "db_status": "Conectada" if test_db_connection() else "Sin conexión",
            "message": message,
            "message_type": message_type,
        },
    )


@router.get("/health/db")
def health_db():
    return {"database": "ok" if test_db_connection() else "error"}


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)