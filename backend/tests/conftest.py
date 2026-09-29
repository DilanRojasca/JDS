"""Fixtures de prueba.

Las pruebas NO necesitan SQL Server ni el driver ODBC: usan SQLite en memoria
con el mismo esquema. Diferencias respecto a produccion, resueltas aqui:
  - ISNULL() es palabra reservada en SQLite -> se traduce a IFNULL().
  - `EXEC sp_RegistrarVoto` no existe en SQLite -> se traduce a un INSERT en
    Votos (respeta el UNIQUE). Las reglas propias del SP (ventana de tiempo,
    opcion valida) NO se prueban aqui; viven en schema.sql.
"""
import os
import re
import sys
import types

os.environ["JWT_SECRET"] = "clave-solo-para-pruebas-" + "x" * 16

# pyodbc necesita el driver ODBC del sistema; para importar app.db (que crea
# el engine, sin conectar) basta un modulo falso.
if "pyodbc" not in sys.modules:
    try:
        import pyodbc  # noqa: F401
    except ImportError:
        fake = types.ModuleType("pyodbc")
        fake.version = "5.2.0"
        fake.paramstyle = "qmark"
        fake.pooling = False
        fake.Cursor = type("Cursor", (), {"nextset": lambda self: None})
        sys.modules["pyodbc"] = fake

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from app.db import get_connection
from app.main import app
from app.security import hash_password

SCHEMA = """
CREATE TABLE Organizaciones (OrganizacionId INTEGER PRIMARY KEY AUTOINCREMENT, Nombre TEXT NOT NULL);
CREATE TABLE Miembros (
    MiembroId INTEGER PRIMARY KEY AUTOINCREMENT, OrganizacionId INT NOT NULL,
    Identificacion TEXT NOT NULL UNIQUE, Nombre TEXT NOT NULL, PesoVoto REAL NOT NULL,
    PasswordHash TEXT NULL);
CREATE TABLE Votaciones (
    VotacionId INTEGER PRIMARY KEY AUTOINCREMENT, OrganizacionId INT NOT NULL, Titulo TEXT NOT NULL,
    Descripcion TEXT, QuorumRequerido REAL NOT NULL, FechaApertura TEXT NOT NULL,
    FechaCierre TEXT NOT NULL, Estado TEXT NOT NULL);
CREATE TABLE OpcionesVoto (OpcionId INTEGER PRIMARY KEY AUTOINCREMENT, VotacionId INT NOT NULL, TextoOpcion TEXT NOT NULL);
CREATE TABLE Votos (
    VotoId INTEGER PRIMARY KEY AUTOINCREMENT, VotacionId INT NOT NULL, MiembroId INT NOT NULL,
    OpcionId INT NOT NULL, FechaHora TEXT DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT UQ_Voto_Miembro_Votacion UNIQUE (VotacionId, MiembroId));
CREATE VIEW vw_ResultadosYQuorum AS
SELECT V.VotacionId, V.Titulo, V.QuorumRequerido,
       ISNULL(SUM(M.PesoVoto), 0) AS PesoTotalVotado,
       CASE WHEN ISNULL(SUM(M.PesoVoto), 0) >= V.QuorumRequerido THEN 1 ELSE 0 END AS QuorumAlcanzado,
       V.Estado, V.FechaApertura, V.FechaCierre
FROM Votaciones V
LEFT JOIN Votos Vo ON V.VotacionId = Vo.VotacionId
LEFT JOIN Miembros M ON Vo.MiembroId = M.MiembroId
GROUP BY V.VotacionId, V.Titulo, V.QuorumRequerido, V.Estado, V.FechaApertura, V.FechaCierre;
"""

PASSWORD = "clave-correcta-123"
PASSWORD_ANA_B = "otra-clave-valida-456"  # de la segunda "Ana" (homonima, Org B)


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )

    @event.listens_for(eng, "before_cursor_execute", retval=True)
    def _traducir(conn, cursor, statement, parameters, context, executemany):
        statement = re.sub(r"\bISNULL\(", "IFNULL(", statement)
        if statement.startswith("EXEC sp_RegistrarVoto"):
            statement = (
                "INSERT INTO Votos (VotacionId, MiembroId, OpcionId) VALUES (?, ?, ?) "
                "RETURNING 'Voto registrado exitosamente' AS Mensaje"
            )
        return statement, parameters

    h = hash_password(PASSWORD)
    h_ana_b = hash_password(PASSWORD_ANA_B)
    with eng.begin() as c:
        for stmt in SCHEMA.split(";\n"):
            if stmt.strip():
                c.execute(text(stmt))
        c.execute(text("INSERT INTO Organizaciones (Nombre) VALUES ('Org A'), ('Org B')"))
        c.execute(
            text(
                "INSERT INTO Miembros (OrganizacionId, Identificacion, Nombre, PesoVoto, PasswordHash) VALUES "
                "(1, '1001', 'Ana',   2.0, :h),"
                "(1, '1002', 'Beto',  3.0, :h),"
                "(2, '2001', 'Carla', 5.0, :h),"
                "(1, '1003', 'SinClave', 1.0, NULL),"
                "(2, '2002', 'Ana',   4.0, :h_ana_b)"  # homonima de (1) en otra org, con otra clave
            ),
            {"h": h, "h_ana_b": h_ana_b},
        )
        c.execute(
            text(
                "INSERT INTO Votaciones (OrganizacionId, Titulo, QuorumRequerido, FechaApertura, FechaCierre, Estado) VALUES "
                "(1, 'Votacion de A', 4.0, '2026-01-01T00:00:00', '2030-01-01T00:00:00', 'Abierta'),"
                "(2, 'Votacion de B', 4.0, '2026-01-01T00:00:00', '2030-01-01T00:00:00', 'Abierta')"
            )
        )
        c.execute(
            text(
                "INSERT INTO OpcionesVoto (VotacionId, TextoOpcion) VALUES "
                "(1, 'A favor'), (1, 'En contra'), (2, 'A favor'), (2, 'En contra')"
            )
        )
    return eng


@pytest.fixture()
def client(engine):
    def _get_connection():
        with engine.connect() as conn:
            yield conn

    app.dependency_overrides[get_connection] = _get_connection
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, nombre="Ana", password=PASSWORD):
    return client.post("/auth/login", json={"nombre": nombre, "password": password})


@pytest.fixture()
def auth(client):
    """Headers de un miembro autenticado (Ana, Org A)."""
    token = login(client).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
