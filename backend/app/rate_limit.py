"""Límite de intentos de login.

En memoria del proceso, no en Mongo ni en SQL Server: es un contador
efímero de protección (no un dato de negocio ni de auditoría), por eso no
necesita persistir entre reinicios ni una tabla propia. Si la API corre en
varias instancias detrás de un balanceador, cada una lleva su propio
contador -- suficiente para este alcance; una limitación real
multi-instancia necesitaría un almacen compartido (p. ej. Redis), fuera de
alcance por ahora.

Se limita por nombre normalizado (no por miembro_id): el login resuelve
homónimos probando la contraseña contra cada candidato, así que a esta
altura ni siquiera se sabe todavía qué miembro es. Limitar por nombre basta
para frenar fuerza bruta contra una cuenta conocida.
"""
import threading
import time

MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 15 * 60  # 15 minutos

_lock = threading.Lock()
# nombre_normalizado -> (intentos_fallidos, marca_de_tiempo_del_primero)
_intentos: dict[str, tuple[int, float]] = {}


def _normalizar(nombre: str) -> str:
    return nombre.strip().lower()


def segundos_bloqueado_restantes(nombre: str) -> int:
    """>0 si el nombre está bloqueado por demasiados intentos fallidos."""
    clave = _normalizar(nombre)
    with _lock:
        registro = _intentos.get(clave)
        if registro is None:
            return 0
        intentos, inicio = registro
        transcurrido = time.monotonic() - inicio
        if transcurrido >= VENTANA_SEGUNDOS:
            del _intentos[clave]
            return 0
        if intentos < MAX_INTENTOS:
            return 0
        return int(VENTANA_SEGUNDOS - transcurrido)


def registrar_intento_fallido(nombre: str) -> None:
    clave = _normalizar(nombre)
    ahora = time.monotonic()
    with _lock:
        intentos, inicio = _intentos.get(clave, (0, ahora))
        if ahora - inicio >= VENTANA_SEGUNDOS:
            intentos, inicio = 0, ahora
        _intentos[clave] = (intentos + 1, inicio)


def limpiar_intentos(nombre: str) -> None:
    """Se llama tras un login exitoso: un acierto resetea el contador."""
    with _lock:
        _intentos.pop(_normalizar(nombre), None)
