from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import text

from app.config import settings
from app.security import hash_password, verify_password
from tests.conftest import PASSWORD, PASSWORD_ANA_B, login


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
    assert body["miembro"]["debe_cambiar_password"] is False
    cuerpo_sin_nombres_de_campo = str(body).lower().replace("access_token", "").replace("debe_cambiar_password", "")
    assert "password" not in cuerpo_sin_nombres_de_campo
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
    fantasma = login(client, nombre="Nadie")
    assert fantasma.status_code == malo.status_code == 401
    assert fantasma.json() == malo.json()  # no se filtra que nombres existen


# ------------------------------------------ clave temporal (documento) y homonimos

def test_login_con_documento_como_clave_temporal_funciona_y_marca_cambio_obligatorio(client):
    r = login(client, nombre="SinClave", password="1003")
    assert r.status_code == 200
    assert r.json()["miembro"]["debe_cambiar_password"] is True


def test_login_temporal_rechaza_cualquier_cosa_que_no_sea_el_documento_exacto(client):
    assert login(client, nombre="SinClave", password="1003 ").status_code == 401
    assert login(client, nombre="SinClave", password="cualquiera").status_code == 401


def test_debe_cambiar_password_bloquea_rutas_de_negocio_pero_no_me_ni_set_password(client):
    token = login(client, nombre="SinClave", password="1003").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/auth/me", headers=headers).status_code == 200
    assert client.get("/votaciones", headers=headers).status_code == 403
    assert client.get("/organizaciones", headers=headers).status_code == 403
    assert client.post("/votaciones/1/votos", json={"opcion_id": 1}, headers=headers).status_code == 403

    r = client.post("/auth/set-password", json={"nueva_password": "clave-nueva-123"}, headers=headers)
    assert r.status_code == 200

    # Con la clave ya definida, las rutas de negocio quedan disponibles...
    assert client.get("/votaciones", headers=headers).status_code == 200
    # ...y el documento deja de servir como clave: hay que usar la nueva.
    assert login(client, nombre="SinClave", password="1003").status_code == 401
    r2 = login(client, nombre="SinClave", password="clave-nueva-123")
    assert r2.status_code == 200
    assert r2.json()["miembro"]["debe_cambiar_password"] is False


def test_set_password_exige_longitud_minima(client):
    token = login(client, nombre="SinClave", password="1003").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/auth/set-password", json={"nueva_password": "corta"}, headers=headers)
    assert r.status_code == 422


def test_login_con_nombre_duplicado_se_resuelve_por_la_clave_correcta(client):
    # Hay dos miembros llamados "Ana" (orgs distintas, claves distintas): el
    # nombre no alcanza para identificar la cuenta, la clave si.
    r1 = login(client, nombre="Ana", password=PASSWORD)
    r2 = login(client, nombre="Ana", password=PASSWORD_ANA_B)
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["miembro"]["organizacion_nombre"] == "Org A"
    assert r2.json()["miembro"]["organizacion_nombre"] == "Org B"
    assert r1.json()["miembro"]["miembro_id"] != r2.json()["miembro"]["miembro_id"]

    # Ninguna de las dos claves de "Ana" sirve para otra cuenta.
    assert login(client, nombre="Ana", password="clave-que-no-es-de-ninguna").status_code == 401


def test_login_nombre_no_distingue_mayusculas_ni_espacios(client):
    assert login(client, nombre="  ANA  ", password=PASSWORD).status_code == 200


def test_login_valida_el_cuerpo(client):
    assert client.post("/auth/login", json={}).status_code == 422
    assert client.post("/auth/login", json={"nombre": "Ana"}).status_code == 422


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
