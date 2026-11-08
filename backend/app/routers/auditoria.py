from fastapi import APIRouter, Depends

from app.mongo import listar_eventos
from app.schemas import EventoAuditoria, MiembroSesion
from app.security import require_admin_o_auditor

router = APIRouter(prefix="/auditoria", tags=["auditoria"])


@router.get("", response_model=list[EventoAuditoria])
def listar_auditoria(
    actual: MiembroSesion = Depends(require_admin_o_auditor),
) -> list[EventoAuditoria]:
    """Historial de eventos de la organización del miembro autenticado,
    más recientes primero. Vive en MongoDB (ver app/mongo.py); lista vacía
    si Mongo no está configurado o no responde."""
    eventos = listar_eventos(organizacion_id=actual.organizacion_id)
    return [
        EventoAuditoria(
            accion=e["accion"],
            miembro_id=e.get("miembro_id"),
            detalle=e.get("detalle", {}),
            fecha=e["fecha"],
        )
        for e in eventos
    ]
