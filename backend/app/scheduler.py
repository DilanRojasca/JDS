"""Cierre automático de votaciones por ventana de tiempo.

Regla de negocio #5 del README ("ventana de tiempo estricta"): una votacion
debe pasar de 'Pendiente' a 'Abierta' al llegar su FechaApertura, y de
'Pendiente'/'Abierta' a 'Cerrada' al llegar su FechaCierre, sin esperar a
que un administrador la cierre a mano. sp_RegistrarVoto ya rechaza votos
fuera de esa ventana aunque el Estado no se haya actualizado todavia, asi
que este job no protege la integridad del voto (eso ya esta cubierto) --
solo mantiene el campo Estado honesto para que el frontend y los reportes
no muestren como 'Abierta' una votacion cuyo plazo ya vencio.
"""
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from app.db import engine
from app.mongo import log_evento

logger = logging.getLogger("uvicorn.error")

_scheduler: BackgroundScheduler | None = None


def _transicionar_estados() -> None:
    try:
        with engine.begin() as conn:
            abiertas = (
                conn.execute(
                    text(
                        """
                        UPDATE Votaciones SET Estado = 'Abierta'
                        OUTPUT INSERTED.VotacionId, INSERTED.OrganizacionId
                        WHERE Estado = 'Pendiente' AND FechaApertura <= GETDATE() AND FechaCierre > GETDATE()
                        """
                    )
                )
                .mappings()
                .all()
            )
            cerradas = (
                conn.execute(
                    text(
                        """
                        UPDATE Votaciones SET Estado = 'Cerrada'
                        OUTPUT INSERTED.VotacionId, INSERTED.OrganizacionId
                        WHERE Estado IN ('Pendiente', 'Abierta') AND FechaCierre <= GETDATE()
                        """
                    )
                )
                .mappings()
                .all()
            )
    except Exception:
        # No debe tumbar el proceso de la API: se reintenta en el siguiente
        # tick del scheduler.
        logger.exception("Fallo al transicionar el estado de votaciones por ventana de tiempo")
        return

    for fila in abiertas:
        log_evento(
            organizacion_id=fila["OrganizacionId"],
            miembro_id=None,
            accion="apertura_automatica",
            detalle={"votacion_id": fila["VotacionId"]},
        )
    for fila in cerradas:
        log_evento(
            organizacion_id=fila["OrganizacionId"],
            miembro_id=None,
            accion="cierre_automatico",
            detalle={"votacion_id": fila["VotacionId"]},
        )


def iniciar_scheduler() -> BackgroundScheduler:
    global _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_transicionar_estados, "interval", seconds=30, id="transicionar_votaciones")
    _scheduler.start()
    return _scheduler


def detener_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
