from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import text

from app.config import settings
from app.security import hash_password, verify_password
from tests.conftest import PASSWORD, login


def _token(sub, secret=None, exp_delta=timedelta(hours=1), alg="HS256"):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(sub), "iat": now, "exp": now + exp_delta},
        secret or settings.jwt_secret,
        algorithm=alg,
    )


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------- login

def test_login_correcto_devuelve_token_y_miembro(client):
    r = login(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["miembro"]["nombre"] == "Ana"
    assert body["miembro"]["organizacion_nombre"] == "Org A"
    assert "password" not in str(body).lower().replace("access_token", "")
    assert "hash" not in str(body).lower()


def test_me_con_el_token_del_login(client, auth):
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["miembro_id"] == 1


def test_login_clave_incorrecta(client):
    r = login(client, password="otra-clave")
    assert r.status_code == 401


def test_login_usuario_inexistente_da_el_mismo_error_que_clave_mala(client):
    malo = login(client, password="otra-clave")
    fantasma = login(client, identificacion="9999")
    assert fantasma.status_code == malo.status_code == 401
    assert fantasma.json() == malo.json()  # no se filtra que cedulas existen


def test_miembro_sin_clave_asignada_no_puede_entrar(client):
    assert login(client, identificacion="1003", password="").status_code == 422
    assert login(client, identificacion="1003", password="cualquiera").status_code == 401


def test_login_valida_el_cuerpo(client):
    assert client.post("/auth/login", json={}).status_code == 422
    assert client.post("/auth/login", json={"identificacion": "1001"}).status_code == 422


def test_clave_larga_no_revienta():
    larga = "ñ" * 200
    assert verify_password(larga, hash_password(larga)) is True


def test_hash_no_es_la_clave_y_es_salado():
    assert hash_password(PASSWORD) != PASSWORD
    assert hash_password(PASSWORD) != hash_password(PASSWORD)


# --------------------------------------------------------------- tokens

RUTAS_PROTEGIDAS = [
    ("get", "/auth/me"),
    ("get", "/organizaciones"),
    ("get", "/organizaciones/1/miembros"),
    ("get", "/votaciones"),
    ("get", "/votaciones/1"),
    ("get", "/votaciones/1/resultado"),
    ("post", "/votaciones/1/votos"),
]


def test_health_es_publico(client):
    assert client.get("/health").status_code == 200


def test_todas_las_rutas_exigen_token(client):
    for metodo, ruta in RUTAS_PROTEGIDAS:
        kwargs = {"json": {"opcion_id": 1}} if metodo == "post" else {}
        r = getattr(client, metodo)(ruta, **kwargs)
        assert r.status_code == 401, f"{metodo.upper()} {ruta} deberia dar 401, dio {r.status_code}"


def test_tokens_invalidos_son_rechazados(client):
    casos = {
        "basura": "esto-no-es-un-jwt",
        "firmado con otro secreto": _token(1, secret="otro-secreto-" + "y" * 32),
        "expirado": _token(1, exp_delta=timedelta(seconds=-5)),
        "sub no numerico": _token("abc"),
    }
    for nombre, tok in casos.items():
        assert client.get("/auth/me", headers=bearer(tok)).status_code == 401, nombre

    # alg=none (ataque clasico): sin firma
    sin_firma = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                           key=None, algorithm="none")
    assert client.get("/auth/me", headers=bearer(sin_firma)).status_code == 401


def test_token_sin_exp_es_rechazado(client):
    tok = jwt.encode({"sub": "1"}, settings.jwt_secret, algorithm="HS256")
    assert client.get("/auth/me", headers=bearer(tok)).status_code == 401


def test_token_de_miembro_eliminado_deja_de_servir(client, engine, auth):
    assert client.get("/auth/me", headers=auth).status_code == 200
    with engine.begin() as c:
        c.execute(text("DELETE FROM Miembros WHERE MiembroId = 1"))
    assert client.get("/auth/me", headers=auth).status_code == 401
