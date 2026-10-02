from datetime import date, timedelta

from app.core.security import hash_password
from app.models.organization import Organization
from app.models.user import User


def _activer(client, headers, client_id):
    r = client.patch(f"/api/clients/{client_id}", headers=headers, json={"echeanciers_actif": True})
    assert r.status_code == 200
    assert r.json()["echeanciers_actif"] is True


def _portail_headers(client, db_session, org, fiche, email="portail@exemple-test.fr"):
    user = User(org_id=org.id, email=email, name="Portail", password_hash=hash_password("clientpass1"), role="client")
    db_session.add(user)
    db_session.commit()
    fiche.user_id = user.id
    db_session.commit()
    login = client.post("/api/auth/login", json={"email": email, "password": "clientpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_creation_refusee_si_option_desactivee(client, staff_headers, make_client):
    fiche = make_client()
    r = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "Pack", "type_echeance": "pack"})
    assert r.status_code == 400


def test_cycle_complet_plusieurs_echeanciers(client, staff_headers, make_client):
    fiche = make_client()
    _activer(client, staff_headers, fiche.id)

    pack = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "Pack 10h", "type_echeance": "pack"})
    formation = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "Formation Excel", "type_echeance": "formation"})
    assert pack.status_code == 201 and formation.status_code == 201

    listing = client.get(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers).json()
    assert [e["titre"] for e in listing] == ["Pack 10h", "Formation Excel"]

    ech = client.post(
        f"/api/echeanciers/{pack.json()['id']}/echeances",
        headers=staff_headers,
        json={"date_facturation": "2026-01-01", "date_echeance": "2026-01-17", "montant": 150.5, "numero_facture": "F-1"},
    )
    assert ech.status_code == 201
    assert ech.json()["montant"] == 150.5
    assert ech.json()["statut"] == "attente"
    assert ech.json()["date_paiement"] is None

    paye = client.patch(f"/api/echeances/{ech.json()['id']}", headers=staff_headers, json={"statut": "paye"})
    assert paye.json()["statut"] == "paye"
    assert paye.json()["date_paiement"] == date.today().isoformat()
    assert paye.json()["en_retard"] is False

    repasse = client.patch(f"/api/echeances/{ech.json()['id']}", headers=staff_headers, json={"statut": "attente"})
    assert repasse.json()["date_paiement"] is None

    supprime = client.delete(f"/api/echeances/{ech.json()['id']}", headers=staff_headers)
    assert supprime.status_code == 204

    assert client.delete(f"/api/echeanciers/{formation.json()['id']}", headers=staff_headers).status_code == 204
    restants = client.get(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers).json()
    assert len(restants) == 1


def test_en_retard_calcule(client, staff_headers, make_client):
    fiche = make_client()
    _activer(client, staff_headers, fiche.id)
    e = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "X"}).json()
    passe = (date.today() - timedelta(days=3)).isoformat()
    futur = (date.today() + timedelta(days=3)).isoformat()
    en_retard = client.post(f"/api/echeanciers/{e['id']}/echeances", headers=staff_headers, json={"date_echeance": passe}).json()
    a_venir = client.post(f"/api/echeanciers/{e['id']}/echeances", headers=staff_headers, json={"date_echeance": futur}).json()
    assert en_retard["en_retard"] is True
    assert a_venir["en_retard"] is False


def test_type_invalide_et_montant_negatif_refuses(client, staff_headers, make_client):
    fiche = make_client()
    _activer(client, staff_headers, fiche.id)
    assert client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "X", "type_echeance": "nimporte"}).status_code == 422
    e = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "X"}).json()
    assert client.post(f"/api/echeanciers/{e['id']}/echeances", headers=staff_headers, json={"montant": -5}).status_code == 422


def test_isolation_par_organisation(client, staff_headers, make_client, db_session):
    autre_org = Organization(name="Autre", slug="autre")
    db_session.add(autre_org)
    db_session.commit()
    etranger = make_client(nom="Etranger", org_id=autre_org.id, echeanciers_actif=True)

    assert client.get(f"/api/clients/{etranger.id}/echeanciers", headers=staff_headers).status_code == 404
    assert client.post(f"/api/clients/{etranger.id}/echeanciers", headers=staff_headers, json={"titre": "X"}).status_code == 404


def test_isolation_echeancier_autre_organisation(client, staff_headers, make_client, db_session):
    from app.models.echeancier import Echeance, Echeancier

    autre_org = Organization(name="Autre", slug="autre")
    db_session.add(autre_org)
    db_session.commit()
    etranger = make_client(nom="Etranger", org_id=autre_org.id, echeanciers_actif=True)
    ech = Echeancier(client_id=etranger.id, titre="Secret", type_echeance="pack")
    db_session.add(ech)
    db_session.commit()
    ligne = Echeance(echeancier_id=ech.id, statut="attente")
    db_session.add(ligne)
    db_session.commit()

    assert client.patch(f"/api/echeanciers/{ech.id}", headers=staff_headers, json={"titre": "Piraté"}).status_code == 404
    assert client.delete(f"/api/echeanciers/{ech.id}", headers=staff_headers).status_code == 404
    assert client.patch(f"/api/echeances/{ligne.id}", headers=staff_headers, json={"statut": "paye"}).status_code == 404
    assert client.delete(f"/api/echeances/{ligne.id}", headers=staff_headers).status_code == 404


def test_portail_lecture_seule_et_option(client, staff_headers, make_client, db_session, org):
    fiche = make_client()
    headers = _portail_headers(client, db_session, org, fiche)

    assert client.get("/api/me/echeanciers", headers=headers).json() == []

    _activer(client, staff_headers, fiche.id)
    e = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "Pack", "type_echeance": "pack"}).json()
    client.post(f"/api/echeanciers/{e['id']}/echeances", headers=staff_headers, json={"montant": 90})

    vu = client.get("/api/me/echeanciers", headers=headers).json()
    assert len(vu) == 1 and vu[0]["titre"] == "Pack" and vu[0]["echeances"][0]["montant"] == 90

    assert client.post(f"/api/clients/{fiche.id}/echeanciers", headers=headers, json={"titre": "X"}).status_code == 403
    assert client.patch(f"/api/echeances/{vu[0]['echeances'][0]['id']}", headers=headers, json={"statut": "paye"}).status_code == 403

    client.patch(f"/api/clients/{fiche.id}", headers=staff_headers, json={"echeanciers_actif": False})
    assert client.get("/api/me/echeanciers", headers=headers).json() == []


def test_portail_ne_voit_que_ses_echeanciers(client, staff_headers, make_client, db_session, org):
    a = make_client(nom="A", echeanciers_actif=True)
    b = make_client(nom="B", echeanciers_actif=True)
    headers_a = _portail_headers(client, db_session, org, a, email="a@exemple-test.fr")
    client.post(f"/api/clients/{b.id}/echeanciers", headers=staff_headers, json={"titre": "Pour B"})

    assert client.get("/api/me/echeanciers", headers=headers_a).json() == []


def test_suppression_client_bloquee_par_echeanciers(client, staff_headers, make_client):
    fiche = make_client()
    _activer(client, staff_headers, fiche.id)
    client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "X"})

    assert client.delete(f"/api/clients/{fiche.id}", headers=staff_headers).status_code == 400


def test_echeances_dans_l_ordre_de_creation(client, staff_headers, make_client):
    fiche = make_client()
    _activer(client, staff_headers, fiche.id)
    e = client.post(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers, json={"titre": "X"}).json()
    for jour in ("2026-12-01", "2026-03-01", "2026-06-01"):
        client.post(f"/api/echeanciers/{e['id']}/echeances", headers=staff_headers, json={"date_echeance": jour})

    lignes = client.get(f"/api/clients/{fiche.id}/echeanciers", headers=staff_headers).json()[0]["echeances"]
    assert [l["date_echeance"] for l in lignes] == ["2026-12-01", "2026-03-01", "2026-06-01"]
