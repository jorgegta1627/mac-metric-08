from datetime import datetime, timedelta
from urllib.parse import quote_plus
import traceback

from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from sqlalchemy import text

from app.core.database import engine

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def validar_sesion(request: Request):
    if "user" not in request.session:
        return RedirectResponse(url="/login", status_code=303)

    last_activity = request.session.get("last_activity")

    if not last_activity:
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    last_activity_dt = datetime.fromisoformat(last_activity)

    if datetime.now() - last_activity_dt > timedelta(minutes=15):
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    request.session["last_activity"] = datetime.now().isoformat()
    return None


def validar_admin(request: Request):
    sesion = validar_sesion(request)
    if sesion:
        return sesion

    role_id = request.session.get("role_id")

    if role_id != 1:
     return RedirectResponse(url="/dashboard", status_code=303)

    return None


@router.get("/admin/usuarios")
def usuarios_page(request: Request, edit_id: int | None = None):
    permiso = validar_admin(request)
    if permiso:
        return permiso

    with engine.connect() as conn:
        roles = conn.execute(
            text("SELECT id, nombre FROM macmetric.roles ORDER BY id")
        ).mappings().all()

        usuarios = conn.execute(
            text("""
                SELECT u.id, u.username, u.nombre_completo, u.role_id, r.nombre AS rol, u.activo
                FROM macmetric.usuarios u
                JOIN macmetric.roles r ON r.id = u.role_id
                ORDER BY u.id
            """)
        ).mappings().all()

        usuario_edicion = None
        if edit_id:
            usuario_edicion = conn.execute(
                text("""
                    SELECT id, username, nombre_completo, role_id, activo
                    FROM macmetric.usuarios
                    WHERE id = :id
                """),
                {"id": edit_id}
            ).mappings().first()

    return templates.TemplateResponse(
    request=request,
    name="users.html",
    context={
        "roles": roles,
        "usuarios": usuarios,
        "usuario_edicion": usuario_edicion,
        "success": request.query_params.get("success"),
        "error": request.query_params.get("error"),
        "current_user": request.session.get("user"),
        "role_id": request.session.get("role_id"),
    },
    )


@router.post("/admin/usuarios")
def crear_usuario(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    nombre: str = Form(...),
    rol_id: int = Form(...),
):
    permiso = validar_admin(request)
    if permiso:
        return permiso

    try:
        password_hash = pwd_context.hash(password)

        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO macmetric.usuarios
                    (username, nombre_completo, password_hash, role_id, activo)
                    VALUES (:username, :nombre, :password_hash, :rol_id, true)
                """),
                {
                    "username": username.strip(),
                    "nombre": nombre.strip(),
                    "password_hash": password_hash,
                    "rol_id": rol_id,
                }
            )

        msg = quote_plus("Usuario creado correctamente")
        return RedirectResponse(url=f"/admin/usuarios?success={msg}", status_code=303)

    except Exception as e:
        print("ERROR AL CREAR USUARIO:")
        traceback.print_exc()

        msg = "Error al crear usuario"
        if "duplicate key" in str(e).lower():
            msg = "El usuario ya existe"

        msg = quote_plus(msg)
        return RedirectResponse(url=f"/admin/usuarios?error={msg}", status_code=303)


@router.post("/admin/usuarios/{user_id}/editar")
def editar_usuario(
    request: Request,
    user_id: int,
    username: str = Form(...),
    nombre: str = Form(...),
    rol_id: int = Form(...),
    activo: str = Form(...),
    password: str = Form(""),
):
    permiso = validar_admin(request)
    if permiso:
        return permiso

    try:
        activo_bool = activo == "true"

        with engine.begin() as conn:
            if password.strip():
                password_hash = pwd_context.hash(password)
                conn.execute(
                    text("""
                        UPDATE macmetric.usuarios
                        SET username = :username,
                            nombre_completo = :nombre,
                            role_id = :rol_id,
                            activo = :activo,
                            password_hash = :password_hash
                        WHERE id = :id
                    """),
                    {
                        "id": user_id,
                        "username": username.strip(),
                        "nombre": nombre.strip(),
                        "rol_id": rol_id,
                        "activo": activo_bool,
                        "password_hash": password_hash,
                    }
                )
            else:
                conn.execute(
                    text("""
                        UPDATE macmetric.usuarios
                        SET username = :username,
                            nombre_completo = :nombre,
                            role_id = :rol_id,
                            activo = :activo
                        WHERE id = :id
                    """),
                    {
                        "id": user_id,
                        "username": username.strip(),
                        "nombre": nombre.strip(),
                        "rol_id": rol_id,
                        "activo": activo_bool,
                    }
                )

        msg = quote_plus("Usuario actualizado correctamente")
        return RedirectResponse(url=f"/admin/usuarios?success={msg}", status_code=303)

    except Exception as e:
        print("ERROR AL EDITAR USUARIO:")
        traceback.print_exc()

        msg = "Error al editar usuario"
        if "duplicate key" in str(e).lower():
            msg = "El usuario ya existe"

        msg = quote_plus(msg)
        return RedirectResponse(url=f"/admin/usuarios?error={msg}", status_code=303)


@router.post("/admin/usuarios/{user_id}/eliminar")
def eliminar_usuario(request: Request, user_id: int):
    permiso = validar_admin(request)
    if permiso:
        return permiso

    try:
        with engine.begin() as conn:
            usuario = conn.execute(
                text("SELECT username FROM macmetric.usuarios WHERE id = :id"),
                {"id": user_id}
            ).mappings().first()

            if not usuario:
                msg = quote_plus("El usuario no existe")
                return RedirectResponse(url=f"/admin/usuarios?error={msg}", status_code=303)

            if usuario["username"] == request.session.get("user"):
                msg = quote_plus("No puedes eliminar el usuario con sesión activa")
                return RedirectResponse(url=f"/admin/usuarios?error={msg}", status_code=303)

            conn.execute(
                text("DELETE FROM macmetric.usuarios WHERE id = :id"),
                {"id": user_id}
            )

        msg = quote_plus("Usuario eliminado correctamente")
        return RedirectResponse(url=f"/admin/usuarios?success={msg}", status_code=303)

    except Exception:
        print("ERROR AL ELIMINAR USUARIO:")
        traceback.print_exc()

        msg = quote_plus("Error al eliminar usuario")
        return RedirectResponse(url=f"/admin/usuarios?error={msg}", status_code=303)