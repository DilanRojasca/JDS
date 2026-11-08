"""Historial de auditoria en MongoDB Atlas.

Esta es la segunda base de datos del proyecto: SQL Server sigue siendo la
unica fuente de verdad para organizaciones, miembros, votaciones y votos
(todo lo transaccional). Mongo guarda solo un log de eventos -- append-only,
de esquema variable segun el tipo de evento -- que no participa en ninguna
regla de negocio. Por eso el logging es "best effort": si Mongo esta
inalcanzable o MONGODB_URI no esta configurado, la API sigue funcionando
con normalidad y el evento simplemente no queda registrado (se avisa por
log, nunca se propaga como error HTTP).
"""
import logging
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.config import settings

logger = logging.getLogger("uvicorn.error")

_client: MongoClient | None = None
_inicializado = False


def _coleccion_auditoria() -> Collection | None:
    global _client, _inicializado

    if not settings.mongodb_uri:
        return None

    if not _inicializado:
        _inicializado = True
        try:
            _client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
            _client.admin.command("ping")
        except PyMongoError:
            logger.warning("No se pudo conectar a MongoDB Atlas; la auditoría queda deshabilitada.")
            _client = None

    if _client is None:
        return None
    return _client[settings.mongodb_db]["auditoria"]


def log_evento(
    *,
    organizacion_id: int | None,
    miembro_id: int | None,
    accion: str,
    detalle: dict[str, Any] | None = None,
) -> None:
    """Registra un evento de auditoria. Nunca lanza: un fallo de Mongo no
    debe tumbar la peticion HTTP que lo origino."""
    coleccion = _coleccion_auditoria()
    if coleccion is None:
        return

    try:
        coleccion.insert_one(
            {
                "organizacion_id": organizacion_id,
                "miembro_id": miembro_id,
                "accion": accion,
                "detalle": detalle or {},
                "fecha": datetime.now(timezone.utc),
            }
        )
    except PyMongoError:
        logger.warning("No se pudo registrar el evento de auditoría '%s' en MongoDB.", accion)


def listar_eventos(
    *, organizacion_id: int, limite: int = 100
) -> list[dict[str, Any]]:
    """Devuelve los eventos de auditoria de una organizacion, mas recientes
    primero. Lista vacia si Mongo no esta configurado o no responde."""
    coleccion = _coleccion_auditoria()
    if coleccion is None:
        return []

    try:
        cursor = (
            coleccion.find({"organizacion_id": organizacion_id})
            .sort("fecha", -1)
            .limit(limite)
        )
        return list(cursor)
    except PyMongoError:
        logger.warning("No se pudo leer el historial de auditoría desde MongoDB.")
        return []
