from sqlalchemy import text

from app.rate_limit import MAX_INTENTOS
from tests.conftest import PASSWORD, login


def test_bloquea_tras_N_intentos_fallidos(client):
    for _ in range(MAX_INTENTOS):
        assert login(client, password="mala").status_code == 401

    r = login(client, password="mala")
    assert r.status_code == 429

    # Ni siquiera con la clave correcta se puede entrar mientras dure el bloqueo.
    assert login(client, password=PASSWORD).status_code == 429


def test_login_correcto_resetea_el_contador(client):
    for _ in range(MAX_INTENTOS - 1):
        assert login(client, password="mala").status_code == 401

    assert login(client, password=PASSWORD).status_code == 200

    # El contador se reinicio: vuelve a tener MAX_INTENTOS disponibles.
    for _ in range(MAX_INTENTOS - 1):
        assert login(client, password="mala").status_code == 401
    assert login(client, password=PASSWORD).status_code == 200


def test_bloqueo_es_por_nombre_no_global(client):
    for _ in range(MAX_INTENTOS):
        login(client, nombre="Ana", password="mala")
    assert login(client, nombre="Ana", password=PASSWORD).status_code == 429
    # Beto no esta bloqueado solo porque Ana lo este.
    assert login(client, nombre="Beto", password=PASSWORD).status_code == 200


# --------------------------------------------------------- olvide-password

def test_olvide_password_resetea_el_hash_y_permite_entrar_con_el_documento(client, engine):
    r = client.post("/auth/olvide-password", json={"nombre": "Ana", "identificacion": "1001"})
    assert r.status_code == 200

    with engine.connect() as c:
        hash_actual = c.execute(text("SELECT PasswordHash FROM Miembros WHERE MiembroId = 1")).scalar()
    assert hash_actual is None

    # La clave vieja ya no sirve; el documento si, con cambio obligatorio.
    assert login(client, nombre="Ana", password=PASSWORD).status_code == 401
    r2 = login(client, nombre="Ana", password="1001")
    assert r2.status_code == 200
    assert r2.json()["miembro"]["debe_cambiar_password"] is True


def test_olvide_password_respuesta_generica_si_los_datos_no_coinciden(client):
    r_malo = client.post("/auth/olvide-password", json={"nombre": "Ana", "identificacion": "0000"})
    r_bueno = client.post("/auth/olvide-password", json={"nombre": "Nadie", "identificacion": "0000"})
    assert r_malo.status_code == r_bueno.status_code == 200
    assert r_malo.json() == r_bueno.json()


def test_olvide_password_exige_que_el_nombre_coincida_con_el_documento(client, engine):
    # Documento de Ana (1001) pero con el nombre de Beto: no debe resetear la clave de Ana.
    client.post("/auth/olvide-password", json={"nombre": "Beto", "identificacion": "1001"})
    with engine.connect() as c:
        hash_actual = c.execute(text("SELECT PasswordHash FROM Miembros WHERE MiembroId = 1")).scalar()
    assert hash_actual is not None
