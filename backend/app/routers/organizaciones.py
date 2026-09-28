from fastapi import APIRouter, Depends
from sqlalchemy import Connection, text

from app.db import get_connection
from app.schemas import Miembro, Organizacion

router = APIRouter(prefix="/organizaciones", tags=["organizaciones"])


@router.get("", response_model=list[Organizacion])
def listar_organizaciones(conn: Connection = Depends(get_connection)) -> list[Organizacion]:
    rows = conn.execute(text("SELECT OrganizacionId, Nombre FROM Organizaciones")).mappings()
    return [Organizacion(organizacion_id=r["OrganizacionId"], nombre=r["Nombre"]) for r in rows]


@router.get("/{organizacion_id}/miembros", response_model=list[Miembro])
def listar_miembros(
    organizacion_id: int,
    conn: Connection = Depends(get_connection),
) -> list[Miembro]:
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
