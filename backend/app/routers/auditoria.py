from fastapi import APIRouter, Depends, Query

from app.mongo import listar_eventos
from app.schemas import EventoAuditoria, MiembroSesion, Rol
from app.security import require_admin_o_auditor

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=list[EventoAuditoria])
def listar_auditoria(
    organizacion_id: int | None = Query(
        None, description="Solo Superadministrador: auditoría de otra organización."
    ),
    actual: MiembroSesion = Depends(require_admin_o_auditor),
) -> list[EventoAuditoria]:
    """Historial de eventos de una organización, más recientes primero. Vive
    en MongoDB (ver app/mongo.py); lista vacía si Mongo no está configurado
    o no responde.

    Por defecto es la organización del miembro autenticado; el
    Superadministrador puede pasar `organizacion_id` para ver la de
    cualquier otra (para el resto de roles ese parámetro se ignora)."""
    org_id = (
        organizacion_id
        if organizacion_id is not None and actual.rol == Rol.SUPERADMINISTRADOR
        else actual.organizacion_id
    )
    eventos = listar_eventos(organizacion_id=org_id)
    return [
        EventoAuditoria(
            accion=e["accion"],
            miembro_id=e.get("miembro_id"),
            detalle=e.get("detalle", {}),
            fecha=e["fecha"],
        )
        for e in eventos
    ]
