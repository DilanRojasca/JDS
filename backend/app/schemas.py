from datetime import datetime

from pydantic import BaseModel


class Organizacion(BaseModel):
    organizacion_id: int
    nombre: str


class Miembro(BaseModel):
    miembro_id: int
    nombre: str
    peso_voto: float


class OpcionVoto(BaseModel):
    opcion_id: int
    texto_opcion: str


class VotacionResumen(BaseModel):
    votacion_id: int
    titulo: str
    estado: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    quorum_requerido: float


class VotacionDetalle(VotacionResumen):
    descripcion: str | None
    opciones: list[OpcionVoto]


class OpcionResultado(BaseModel):
    opcion_id: int
    texto_opcion: str
    peso: float
    votos: int


class ResultadoVotacion(BaseModel):
    votacion_id: int
    titulo: str
    quorum_requerido: float
    peso_total_votado: float
    quorum_alcanzado: bool
    estado: str
    fecha_apertura: datetime
    fecha_cierre: datetime
    peso_total_padron: float
    miembros_total: int
    miembros_votantes: int
    opciones: list[OpcionResultado]


class VotoCrear(BaseModel):
    miembro_id: int
    opcion_id: int


class VotoConfirmacion(BaseModel):
    mensaje: str
