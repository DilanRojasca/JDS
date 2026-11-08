from sqlalchemy import text

from tests.conftest import login


def admin_auth(client):
    token = login(client, "Ana").json()["access_token"]  # Ana = Administrador de Org A
    return {"Authorization": f"Bearer {token}"}


def miembro_auth(client):
    token = login(client, "Beto").json()["access_token"]  # Beto = Miembro de Org A
    return {"Authorization": f"Bearer {token}"}


def auditor_auth(client):
    token = login(client, "Vero").json()["access_token"]  # Vero = Auditor de Org A
    return {"Authorization": f"Bearer {token}"}


# --------------------------------------------------------- crear votacion

def test_admin_crea_votacion(client):
    headers = admin_auth(client)
    body = {
        "titulo": "Nueva votacion",
        "descripcion": "desc",
        "quorum_requerido": 3.0,
        "fecha_apertura": "2026-01-01T00:00:00",
        "fecha_cierre": "2030-01-01T00:00:00",
        "opciones": ["Si", "No"],
    }
    r = client.post("/votaciones", json=body, headers=headers)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["titulo"] == "Nueva votacion"
    assert data["estado"] == "Pendiente"
    assert [o["texto_opcion"] for o in data["opciones"]] == ["Si", "No"]


def test_miembro_no_puede_crear_votacion(client):
    headers = miembro_auth(client)
    body = {
        "titulo": "No deberia poder",
        "quorum_requerido": 3.0,
        "fecha_apertura": "2026-01-01T00:00:00",
        "fecha_cierre": "2030-01-01T00:00:00",
        "opciones": ["Si", "No"],
    }
    assert client.post("/votaciones", json=body, headers=headers).status_code == 403


def test_crear_votacion_exige_minimo_dos_opciones_y_ventana_valida(client):
    headers = admin_auth(client)
    base = {
        "titulo": "X",
        "quorum_requerido": 1.0,
        "fecha_apertura": "2026-01-01T00:00:00",
        "fecha_cierre": "2030-01-01T00:00:00",
    }
    assert client.post("/votaciones", json={**base, "opciones": ["Solo una"]}, headers=headers).status_code == 422

    invertida = {**base, "opciones": ["Si", "No"], "fecha_apertura": "2030-01-01T00:00:00", "fecha_cierre": "2026-01-01T00:00:00"}
    assert client.post("/votaciones", json=invertida, headers=headers).status_code == 422


# --------------------------------------------------------------- cerrar

def test_admin_cierra_votacion(client, engine):
    headers = admin_auth(client)
    r = client.post("/votaciones/1/cerrar", headers=headers)
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "Cerrada"
    with engine.connect() as c:
        estado = c.execute(text("SELECT Estado FROM Votaciones WHERE VotacionId = 1")).scalar()
    assert estado == "Cerrada"


def test_no_se_puede_cerrar_dos_veces(client):
    headers = admin_auth(client)
    assert client.post("/votaciones/1/cerrar", headers=headers).status_code == 200
    assert client.post("/votaciones/1/cerrar", headers=headers).status_code == 409


def test_miembro_no_puede_cerrar_votacion(client):
    headers = miembro_auth(client)
    assert client.post("/votaciones/1/votos", json={"opcion_id": 1}, headers=headers).status_code == 201
    assert client.post("/votaciones/1/cerrar", headers=headers).status_code == 403


def test_admin_no_puede_cerrar_votacion_de_otra_organizacion(client):
    headers = admin_auth(client)
    assert client.post("/votaciones/2/cerrar", headers=headers).status_code == 404


# ----------------------------------------------------------- crear miembro

def test_admin_crea_miembro(client, engine):
    headers = admin_auth(client)
    body = {"identificacion": "9999", "nombre": "Nuevo Miembro", "peso_voto": 1.5}
    r = client.post("/organizaciones/1/miembros", json=body, headers=headers)
    assert r.status_code == 201, r.text
    assert r.json()["rol"] == "Miembro"
    with engine.connect() as c:
        fila = c.execute(text("SELECT PasswordHash, Rol FROM Miembros WHERE Identificacion = '9999'")).mappings().first()
    assert fila["PasswordHash"] is None  # entra con el documento como clave temporal
    assert fila["Rol"] == "Miembro"


def test_no_se_puede_duplicar_identificacion(client):
    headers = admin_auth(client)
    body = {"identificacion": "1002", "nombre": "Repetido", "peso_voto": 1.0}  # 1002 = Beto
    assert client.post("/organizaciones/1/miembros", json=body, headers=headers).status_code == 409


def test_miembro_no_puede_crear_miembros(client):
    headers = miembro_auth(client)
    body = {"identificacion": "9998", "nombre": "X", "peso_voto": 1.0}
    assert client.post("/organizaciones/1/miembros", json=body, headers=headers).status_code == 403


def test_admin_no_puede_crear_miembro_en_otra_organizacion(client):
    headers = admin_auth(client)  # Ana es admin de Org A
    body = {"identificacion": "9997", "nombre": "X", "peso_voto": 1.0}
    assert client.post("/organizaciones/2/miembros", json=body, headers=headers).status_code == 403


# ------------------------------------------------------------- auditoria

def test_auditor_puede_leer_auditoria_pero_no_administrar(client):
    headers = auditor_auth(client)
    assert client.get("/auditoria", headers=headers).status_code == 200
    assert client.post("/votaciones/1/cerrar", headers=headers).status_code == 403


def test_miembro_no_puede_leer_auditoria(client):
    headers = miembro_auth(client)
    assert client.get("/auditoria", headers=headers).status_code == 403


def test_auditoria_vacia_sin_mongo_configurado(client):
    # En pruebas no hay MONGODB_URI: listar_eventos() es no-op (ver app/mongo.py).
    headers = admin_auth(client)
    client.post("/votaciones/1/votos", json={"opcion_id": 1}, headers=headers)
    r = client.get("/auditoria", headers=headers)
    assert r.status_code == 200
    assert r.json() == []
