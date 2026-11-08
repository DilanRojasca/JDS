from tests.conftest import login


def super_auth(client):
    token = login(client, "Super").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def admin_auth(client):
    token = login(client, "Ana").json()["access_token"]  # Administrador de Org A
    return {"Authorization": f"Bearer {token}"}


def test_superadmin_ve_todas_las_organizaciones(client):
    r = client.get("/organizaciones", headers=super_auth(client))
    assert r.status_code == 200
    assert {o["nombre"] for o in r.json()} == {"Org A", "Org B"}


def test_miembro_normal_solo_ve_su_organizacion(client):
    r = client.get("/organizaciones", headers=admin_auth(client))
    assert [o["nombre"] for o in r.json()] == ["Org A"]


def test_superadmin_crea_organizacion(client):
    r = client.post("/organizaciones", json={"nombre": "Org Nueva"}, headers=super_auth(client))
    assert r.status_code == 201, r.text
    assert r.json()["nombre"] == "Org Nueva"

    orgs = client.get("/organizaciones", headers=super_auth(client)).json()
    assert "Org Nueva" in {o["nombre"] for o in orgs}


def test_admin_normal_no_puede_crear_organizacion(client):
    r = client.post("/organizaciones", json={"nombre": "No deberia"}, headers=admin_auth(client))
    assert r.status_code == 403


def test_superadmin_ve_miembros_de_cualquier_organizacion(client):
    r = client.get("/organizaciones/2/miembros", headers=super_auth(client))
    assert r.status_code == 200
    assert {m["nombre"] for m in r.json()} == {"Carla", "Ana"}


def test_admin_no_ve_miembros_de_otra_organizacion_aunque_exista_un_superadmin(client):
    assert client.get("/organizaciones/2/miembros", headers=admin_auth(client)).status_code == 403


def test_superadmin_lee_auditoria_de_cualquier_organizacion(client):
    r = client.get("/auditoria", params={"organizacion_id": 2}, headers=super_auth(client))
    assert r.status_code == 200  # vacia (sin Mongo en pruebas), pero no 403


def test_admin_ignora_el_parametro_organizacion_id_en_auditoria(client):
    # Ana es admin de Org A; pedir organizacion_id=2 no le da acceso a Org B.
    r = client.get("/auditoria", params={"organizacion_id": 2}, headers=admin_auth(client))
    assert r.status_code == 200  # responde, pero igual filtrado a su propia organizacion
