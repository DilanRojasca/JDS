from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Connection, text

from app.db import get_connection
from app.schemas import LoginCrear, LoginRespuesta, MiembroSesion
from app.security import create_access_token, get_current_member, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginRespuesta)
def login(datos: LoginCrear, conn: Connection = Depends(get_connection)) -> LoginRespuesta:
    row = conn.execute(
        text(
            """
            SELECT m.MiembroId, m.Nombre, m.PesoVoto, m.OrganizacionId, m.PasswordHash,
                   o.Nombre AS OrganizacionNombre
            FROM Miembros m
            JOIN Organizaciones o ON o.OrganizacionId = m.OrganizacionId
            WHERE m.Identificacion = :identificacion
            """
        ),
        {"identificacion": datos.identificacion.strip()},
    ).mappings().first()

    # Siempre se verifica una clave (aunque el usuario no exista) y el mensaje
    # de error es el mismo en ambos casos: no se filtra que cedulas existen.
    clave_ok = verify_password(datos.password, row["PasswordHash"] if row else None)
    if row is None or not clave_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificación o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LoginRespuesta(
        access_token=create_access_token(row["MiembroId"]),
        miembro=MiembroSesion(
            miembro_id=row["MiembroId"],
            nombre=row["Nombre"],
            peso_voto=row["PesoVoto"],
            organizacion_id=row["OrganizacionId"],
            organizacion_nombre=row["OrganizacionNombre"],
        ),
    )


@router.get("/me", response_model=MiembroSesion)
def me(miembro: MiembroSesion = Depends(get_current_member)) -> MiembroSesion:
    return miembro
