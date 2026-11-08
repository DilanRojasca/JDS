from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

from app.db import get_connection
from app.mongo import log_evento
from app.schemas import Miembro, MiembroCrear, MiembroSesion, Organizacion
from app.security import get_current_member_activo, require_admin

router = APIRouter(prefix="/organizaciones", tags=["organizaciones"])


@router.get("", response_model=list[Organizacion])
def listar_organizaciones(
    actual: MiembroSesion = Depends(get_current_member_activo),
) -> list[Organizacion]:
    # Un miembro solo ve su propia organizacion (aislamiento multi-tenant).
    return [Organizacion(organizacion_id=actual.organizacion_id, nombre=actual.organizacion_nombre)]


@router.get("/{organizacion_id}/miembros", response_model=list[Miembro])
def listar_miembros(
    organizacion_id: int,
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(get_current_member_activo),
) -> list[Miembro]:
    if organizacion_id != actual.organizacion_id:
        raise HTTPException(status_code=403, detail="No perteneces a esta organización")

    rows = conn.execute(
        text(
            "SELECT MiembroId, Nombre, PesoVoto, Rol FROM Miembros WHERE OrganizacionId = :org_id ORDER BY Nombre"
        ),
        {"org_id": organizacion_id},
    ).mappings()
    return [
        Miembro(miembro_id=r["MiembroId"], nombre=r["Nombre"], peso_voto=r["PesoVoto"], rol=r["Rol"])
        for r in rows
    ]


@router.post("/{organizacion_id}/miembros", response_model=Miembro, status_code=201)
def crear_miembro(
    organizacion_id: int,
    datos: MiembroCrear,
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(require_admin),
) -> Miembro:
    if organizacion_id != actual.organizacion_id:
        raise HTTPException(status_code=403, detail="No perteneces a esta organización")

    try:
        with conn.begin():
            result = conn.execute(
                text(
                    """
                    INSERT INTO Miembros (OrganizacionId, Identificacion, Nombre, PesoVoto, PasswordHash, Rol)
                    OUTPUT INSERTED.MiembroId
                    VALUES (:org_id, :identificacion, :nombre, :peso_voto, NULL, :rol)
                    """
                ),
                {
                    "org_id": organizacion_id,
                    "identificacion": datos.identificacion,
                    "nombre": datos.nombre,
                    "peso_voto": datos.peso_voto,
                    "rol": datos.rol.value,
                },
            )
            miembro_id = result.scalar_one()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409, detail="Ya existe un miembro con esa identificación"
        ) from exc

    log_evento(
        organizacion_id=organizacion_id,
        miembro_id=actual.miembro_id,
        accion="crear_miembro",
        detalle={"miembro_creado_id": miembro_id, "nombre": datos.nombre, "rol": datos.rol.value},
    )

    return Miembro(miembro_id=miembro_id, nombre=datos.nombre, peso_voto=datos.peso_voto, rol=datos.rol)
