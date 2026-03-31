from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.web.routes.auth import router as auth_router
from app.web.routes.users import router as users_router
from app.web.routes.dashboard import router as dashboard_router
from app.web.routes.upload import router as upload_router
from app.web.routes.funcionarios import router as funcionarios_router

app = FastAPI(title="MAC-METRIC 08")

app.add_middleware(SessionMiddleware, secret_key="macmetric08_clave_temporal")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(dashboard_router)
app.include_router(upload_router)
app.include_router(funcionarios_router)

@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=303)