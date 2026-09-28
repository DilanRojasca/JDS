from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Connection, text

from app.db import get_connection
from app.schemas import Miembro, MiembroSesion, Organizacion
from app.security import get_current_member

router = APIRouter(prefix="/organizaciones", tags=["organizaciones"])


@router.get("", response_model=list[Organizacion])
def listar_organizaciones(
    actual: MiembroSesion = Depends(get_current_member),
) -> list[Organizacion]:
    # Un miembro solo ve su propia organizacion (aislamiento multi-tenant).
    return [Organizacion(organizacion_id=actual.organizacion_id, nombre=actual.organizacion_nombre)]


@router.get("/{organizacion_id}/miembros", response_model=list[Miembro])
def listar_miembros(
    organizacion_id: int,
    conn: Connection = Depends(get_connection),
    actual: MiembroSesion = Depends(get_current_member),
) -> list[Miembro]:
    if organizacion_id != actual.organizacion_id:
        raise HTTPException(status_code=403, detail="No perteneces a esta organización")

    rows = conn.execute(
        text(
            "SELECT MiembroId, Nombre, PesoVoto FROM Miembros WHERE OrganizacionId = :org_id ORDER BY Nombre"
        ),
        {"org_id": organizacion_id},
    ).mappings()
    return [
        Miembro(miembro_id=r["MiembroId"], nombre=r["Nombre"], peso_voto=r["PesoVoto"])
        for r in rows
    ]
