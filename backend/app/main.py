import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.routers import auth, organizaciones, votaciones

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="VotaCoop API", version="0.1.0")


# Debe registrarse ANTES que CORS (queda por dentro de el). Asi, un error
# inesperado se convierte en una respuesta 500 normal que SI recibe las
# cabeceras CORS; sin esto el navegador oculta el fallo real tras un
# confuso "blocked by CORS policy".
@app.middleware("http")
async def errores_como_json(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        if isinstance(exc, SQLAlchemyError):
            detalle = (
                "Error de base de datos. Revisa la terminal de la API; lo mas comun es "
                "no haber ejecutado schema.sql o migracion_login.sql, o que SQL Server no este accesible."
            )
        else:
            detalle = "Error interno del servidor. Revisa la terminal de la API."
        return JSONResponse(status_code=500, content={"detail": detalle})


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organizaciones.router)
app.include_router(votaciones.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
