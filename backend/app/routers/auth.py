from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Connection, text

from app.db import get_connection
from app.schemas import (
    CambiarPasswordCrear,
    LoginCrear,
    LoginRespuesta,
    MensajeRespuesta,
    MiembroSesion,
)
from app.security import (
    create_access_token,
    get_current_member,
    hash_password,
    verify_documento_temporal,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginRespuesta)
def login(datos: LoginCrear, conn: Connection = Depends(get_connection)) -> LoginRespuesta:
    # El nombre no es unico: se traen todos los homonimos y la cuenta real
    # es la del unico (si lo hay) cuya contraseña sea correcta.
    candidatos = conn.execute(
        text(
            """
            SELECT m.MiembroId, m.Nombre, m.PesoVoto, m.OrganizacionId, m.PasswordHash,
                   m.Identificacion, o.Nombre AS OrganizacionNombre
            FROM Miembros m
            JOIN Organizaciones o ON o.OrganizacionId = m.OrganizacionId
            WHERE LOWER(LTRIM(RTRIM(m.Nombre))) = LOWER(LTRIM(RTRIM(:nombre)))
            """
        ),
        {"nombre": datos.nombre},
    ).mappings().all()

    autenticado = None
    for candidato in candidatos:
        if candidato["PasswordHash"] is not None:
            clave_ok = verify_password(datos.password, candidato["PasswordHash"])
        else:
            clave_ok = verify_documento_temporal(datos.password, candidato["Identificacion"])
        if clave_ok:
            autenticado = candidato
            break

    if not candidatos:
        # Ningun nombre coincide: se verifica una clave igual para que la
        # respuesta tarde lo mismo y no se filtre que nombres existen.
        verify_password(datos.password, None)

    if autenticado is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LoginRespuesta(
        access_token=create_access_token(autenticado["MiembroId"]),
        miembro=MiembroSesion(
            miembro_id=autenticado["MiembroId"],
            nombre=autenticado["Nombre"],
            peso_voto=autenticado["PesoVoto"],
            organizacion_id=autenticado["OrganizacionId"],
            organizacion_nombre=autenticado["OrganizacionNombre"],
            debe_cambiar_password=autenticado["PasswordHash"] is None,
        ),
    )


@router.get("/me", response_model=MiembroSesion)
def me(miembro: MiembroSesion = Depends(get_current_member)) -> MiembroSesion:
    return miembro


@router.post("/set-password", response_model=MensajeRespuesta)
def set_password(
    datos: CambiarPasswordCrear,
    miembro: MiembroSesion = Depends(get_current_member),
    conn: Connection = Depends(get_connection),
) -> MensajeRespuesta:
    """Define la clave propia del miembro autenticado.

    Disponible aunque `debe_cambiar_password` sea True (es justamente la
    salida de ese estado): a diferencia del resto de la API, este endpoint
    usa get_current_member y no get_current_member_activo.
    """
    with conn.begin():
        conn.execute(
            text("UPDATE Miembros SET PasswordHash = :hash WHERE MiembroId = :miembro_id"),
            {"hash": hash_password(datos.nueva_password), "miembro_id": miembro.miembro_id},
        )
    return MensajeRespuesta(mensaje="Contraseña actualizada correctamente")
