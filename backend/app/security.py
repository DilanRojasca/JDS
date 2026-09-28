from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Connection, text

from app.config import settings
from app.db import get_connection
from app.schemas import MiembroSesion

_bearer = HTTPBearer(auto_error=False)

# bcrypt solo considera los primeros 72 bytes; en vez de fallar con claves
# largas (bcrypt >= 5 lanza ValueError) se recortan de forma explicita.
_BCRYPT_MAX_BYTES = 72


def _pw_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode("ascii")


# Hash de relleno: cuando la identificacion no existe (o el miembro no tiene
# clave asignada) se verifica contra este igual, para que la respuesta tarde
# lo mismo y no se pueda descubrir que identificaciones estan registradas.
_DUMMY_HASH = hash_password("no-es-una-clave-real")


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        bcrypt.checkpw(_pw_bytes(password), _DUMMY_HASH.encode("ascii"))
        return False
    try:
        return bcrypt.checkpw(_pw_bytes(password), password_hash.encode("ascii"))
    except ValueError:  # hash malformado en la BD
        return False


def create_access_token(miembro_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(miembro_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _no_autenticado(detalle: str = "No autenticado") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_member(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    conn: Connection = Depends(get_connection),
) -> MiembroSesion:
    """Devuelve el miembro dueño del token o responde 401.

    Se consulta la BD en cada peticion (en vez de confiar solo en el token)
    para que un miembro eliminado deje de tener acceso de inmediato.
    """
    if credentials is None:
        raise _no_autenticado()

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
        miembro_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        raise _no_autenticado("Sesión inválida o expirada") from None

    # Transaccion explicita y corta: deja la conexion limpia para que los
    # endpoints (p. ej. registrar_voto) puedan abrir la suya con conn.begin().
    with conn.begin():
        row = conn.execute(
            text(
                """
                SELECT m.MiembroId, m.Nombre, m.PesoVoto, m.OrganizacionId,
                       o.Nombre AS OrganizacionNombre
                FROM Miembros m
                JOIN Organizaciones o ON o.OrganizacionId = m.OrganizacionId
                WHERE m.MiembroId = :miembro_id
                """
            ),
            {"miembro_id": miembro_id},
        ).mappings().first()

    if row is None:
        raise _no_autenticado("Sesión inválida o expirada")

    return MiembroSesion(
        miembro_id=row["MiembroId"],
        nombre=row["Nombre"],
        peso_voto=row["PesoVoto"],
        organizacion_id=row["OrganizacionId"],
        organizacion_nombre=row["OrganizacionNombre"],
    )
