"""Asigna o cambia la contraseña de un miembro.

Uso (desde la carpeta backend/, con el venv activo):

    python -m scripts.set_password 52104887

La contraseña se pide por consola (no queda en el historial del shell).
"""
import sys
from getpass import getpass

from sqlalchemy import text

from app.db import engine
from app.security import hash_password

MIN_LENGTH = 8


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python -m scripts.set_password <identificacion>")
        return 2

    identificacion = sys.argv[1].strip()
    password = getpass("Nueva contraseña: ")
    if len(password) < MIN_LENGTH:
        print(f"La contraseña debe tener al menos {MIN_LENGTH} caracteres.")
        return 1
    if password != getpass("Repite la contraseña: "):
        print("Las contraseñas no coinciden.")
        return 1

    with engine.begin() as conn:
        result = conn.execute(
            text("UPDATE Miembros SET PasswordHash = :h WHERE Identificacion = :i"),
            {"h": hash_password(password), "i": identificacion},
        )

    if result.rowcount == 0:
        print(f"No existe ningún miembro con identificación {identificacion}.")
        return 1

    print("Contraseña actualizada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
