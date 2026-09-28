from sqlalchemy import text

from tests.conftest import login


def _votos(engine):
    with engine.connect() as c:
        return c.execute(text("SELECT VotacionId, MiembroId, OpcionId FROM Votos ORDER BY VotoId")).all()


# ------------------------------------------------- aislamiento por organizacion

def test_listar_solo_muestra_votaciones_de_mi_organizacion(client, auth):
    r = client.get("/votaciones", headers=auth)
    assert r.status_code == 200
    assert [v["titulo"] for v in r.json()] == ["Votacion de A"]


def test_no_se_puede_ver_votacion_ni_resultado_de_otra_organizacion(client, auth):
    assert client.get("/votaciones/2", headers=auth).status_code == 404
    assert client.get("/votaciones/2/resultado", headers=auth).status_code == 404
    assert client.get("/votaciones/999", headers=auth).status_code == 404  # igual que una ajena


def test_no_se_puede_votar_en_otra_organizacion(client, engine, auth):
    r = client.post("/votaciones/2/votos", json={"opcion_id": 3}, headers=auth)
    assert r.status_code == 404
    assert _votos(engine) == []


def test_organizaciones_y_miembros_limitados_a_la_propia(client, auth):
    orgs = client.get("/organizaciones", headers=auth).json()
    assert [o["nombre"] for o in orgs] == ["Org A"]
    assert client.get("/organizaciones/1/miembros", headers=auth).status_code == 200
    assert client.get("/organizaciones/2/miembros", headers=auth).status_code == 403


# ------------------------------------------------------------------- votar

def test_el_voto_se_registra_a_nombre_del_dueño_del_token(client, engine, auth):
    r = client.post("/votaciones/1/votos", json={"opcion_id": 1}, headers=auth)
    assert r.status_code == 201, r.text
    assert _votos(engine) == [(1, 1, 1)]  # miembro 1 = Ana


def test_no_se_puede_suplantar_a_otro_miembro_desde_el_body(client, engine, auth):
    # Un cliente malicioso intenta votar "como Beto" (id 2) con el token de Ana.
    r = client.post("/votaciones/1/votos", json={"opcion_id": 1, "miembro_id": 2}, headers=auth)
    assert r.status_code == 201
    assert _votos(engine) == [(1, 1, 1)]  # quedo a nombre de Ana; el miembro_id del body se ignora


def test_no_hay_doble_voto(client, engine, auth):
    assert client.post("/votaciones/1/votos", json={"opcion_id": 1}, headers=auth).status_code == 201
    r = client.post("/votaciones/1/votos", json={"opcion_id": 2}, headers=auth)
    assert r.status_code != 201
    assert len(_votos(engine)) == 1


def test_resultado_pondera_por_el_peso_de_cada_miembro(client, auth):
    beto = {"Authorization": f"Bearer {login(client, '1002').json()['access_token']}"}
    client.post("/votaciones/1/votos", json={"opcion_id": 1}, headers=auth)   # Ana  2.0 -> A favor
    client.post("/votaciones/1/votos", json={"opcion_id": 2}, headers=beto)   # Beto 3.0 -> En contra
    r = client.get("/votaciones/1/resultado", headers=auth).json()
    assert r["peso_total_votado"] == 5.0
    assert r["quorum_alcanzado"] is True
    assert {o["texto_opcion"]: o["peso"] for o in r["opciones"]} == {"A favor": 2.0, "En contra": 3.0}
    assert r["miembros_votantes"] == 2
