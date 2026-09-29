from datetime import datetime

from pydantic import BaseModel, Field


class Organizacion(BaseModel):
    organizacion_id: int
    nombre: str


class Miembro(BaseModel):
    miembro_id: int
    nombre: str
    peso_voto: float


class MiembroSesion(Miembro):
    organizacion_id: int
    organizacion_nombre: str
    # True mientras el miembro no haya definido una clave propia: entro con
    # su documento como clave temporal y el resto de la API le queda
    # bloqueada hasta llamar a POST /auth/set-password.
    debe_cambiar_password: bool = False


class LoginCrear(BaseModel):
    # El usuario de login es el nombre del miembro (no es unico: la cuenta
    # real se resuelve validando la contraseña contra cada homonimo). La
    # contraseña es la que el miembro definio, o su numero de documento si
    # todavia no ha definido una (ver verify_documento_temporal).
    nombre: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)


class LoginRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"
    miembro: MiembroSesion


class CambiarPasswordCrear(BaseModel):
    nueva_password: str = Field(min_length=8, max_length=128)


class MensajeRespuesta(BaseModel):
    mensaje: str


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
    # El miembro NO viene en el body: se toma del token de sesion.
    opcion_id: int


class VotoConfirmacion(BaseModel):
    mensaje: str
