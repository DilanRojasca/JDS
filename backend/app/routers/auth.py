from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Connection, text

from app.db import get_connection
from app.mongo import log_evento
from app.rate_limit import (
    limpiar_intentos,
    registrar_intento_fallido,
    segundos_bloqueado_restantes,
)
from app.schemas import (
    CambiarPasswordCrear,
    LoginCrear,
    LoginRespuesta,
    MensajeRespuesta,
    MiembroSesion,
    OlvidePasswordCrear,
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
    restante = segundos_bloqueado_restantes(datos.nombre)
    if restante > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos fallidos. Intenta de nuevo en {restante // 60 + 1} minuto(s).",
        )

    # El nombre no es unico: se traen todos los homonimos y la cuenta real
    # es la del unico (si lo hay) cuya contraseña sea correcta.
    candidatos = conn.execute(
        text(
            """
            SELECT m.MiembroId, m.Nombre, m.PesoVoto, m.OrganizacionId, m.PasswordHash, m.Rol,
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
        registrar_intento_fallido(datos.nombre)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    limpiar_intentos(datos.nombre)

    log_evento(
        organizacion_id=autenticado["OrganizacionId"],
        miembro_id=autenticado["MiembroId"],
        accion="login",
        detalle={"nombre": autenticado["Nombre"]},
    )

    return LoginRespuesta(
        access_token=create_access_token(autenticado["MiembroId"]),
        miembro=MiembroSesion(
            miembro_id=autenticado["MiembroId"],
            nombre=autenticado["Nombre"],
            peso_voto=autenticado["PesoVoto"],
            rol=autenticado["Rol"],
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
    log_evento(
        organizacion_id=miembro.organizacion_id,
        miembro_id=miembro.miembro_id,
        accion="set_password",
        detalle={},
    )
    return MensajeRespuesta(mensaje="Contraseña actualizada correctamente")


_MENSAJE_OLVIDE_PASSWORD = (
    "Si los datos coinciden con un miembro registrado, ya puedes volver a iniciar sesión "
    "usando tu número de documento como contraseña temporal; se te pedirá definir una nueva."
)


@router.post("/olvide-password", response_model=MensajeRespuesta)
def olvide_password(
    datos: OlvidePasswordCrear, conn: Connection = Depends(get_connection)
) -> MensajeRespuesta:
    """Recuperación de clave olvidada: vuelve al flujo de "primer ingreso"
    (documento como contraseña temporal, ver verify_documento_temporal) en
    vez de inventar un flujo de recuperación nuevo. Se identifica al
    miembro por Identificacion (unica en toda la plataforma) y se exige
    además que el nombre coincida, para no resetear la clave de alguien
    solo porque un atacante conoce (o adivina) su documento.

    Responde siempre el mismo mensaje, exista o no ese miembro, para no
    filtrar qué identificaciones están registradas.
    """
    with conn.begin():
        fila = conn.execute(
            text(
                """
                SELECT MiembroId, OrganizacionId FROM Miembros
                WHERE Identificacion = :identificacion
                  AND LOWER(LTRIM(RTRIM(Nombre))) = LOWER(LTRIM(RTRIM(:nombre)))
                """
            ),
            {"identificacion": datos.identificacion, "nombre": datos.nombre},
        ).mappings().first()

        if fila is not None:
            conn.execute(
                text("UPDATE Miembros SET PasswordHash = NULL WHERE MiembroId = :miembro_id"),
                {"miembro_id": fila["MiembroId"]},
            )

    if fila is not None:
        log_evento(
            organizacion_id=fila["OrganizacionId"],
            miembro_id=fila["MiembroId"],
            accion="password_olvidada",
            detalle={},
        )

    return MensajeRespuesta(mensaje=_MENSAJE_OLVIDE_PASSWORD)
