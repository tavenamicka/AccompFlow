from freezegun import freeze_time

from app.core.security import hash_password
from app.models.user import User


def _client_role_headers(client, db_session, org, email="client@exemple-test.fr"):
    user = User(org_id=org.id, email=email, name="Client Role", password_hash=hash_password("clientpass1"), role="client")
    db_session.add(user)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": email, "password": "clientpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_client_role_cannot_list_clients(client, db_session, org):
    headers = _client_role_headers(client, db_session, org)

    response = client.get("/api/clients", headers=headers)

    assert response.status_code == 403


def test_staff_creates_and_lists_client(client, staff_headers):
    payload = {
        "nom": "Jean Dupont",
        "email": "jean.dupont@exemple-test.fr",
        "date_debut_contrat": "2025-03-15",
        "forfait_n1_h": 4,
        "forfait_n2_h": 3,
    }
    created = client.post("/api/clients", headers=staff_headers, json=payload)
    assert created.status_code == 201
    assert created.json()["nom"] == "Jean Dupont"

    listing = client.get("/api/clients", headers=staff_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_update_and_archive_client(client, staff_headers, make_client):
    existing = make_client(nom="À modifier")

    updated = client.patch(f"/api/clients/{existing.id}", headers=staff_headers, json={"notes": "suivi renforcé"})
    assert updated.status_code == 200
    assert updated.json()["notes"] == "suivi renforcé"

    archived = client.post(f"/api/clients/{existing.id}/archiver", headers=staff_headers)
    assert archived.status_code == 200
    assert archived.json()["actif"] is False

    listing_actifs = client.get("/api/clients", headers=staff_headers, params={"actif": True})
    assert listing_actifs.json() == []

    reactivated = client.post(f"/api/clients/{existing.id}/reactiver", headers=staff_headers)
    assert reactivated.status_code == 200
    assert reactivated.json()["actif"] is True

    listing_actifs_apres = client.get("/api/clients", headers=staff_headers, params={"actif": True})
    assert len(listing_actifs_apres.json()) == 1


@freeze_time("2025-03-20 10:00:00")
def test_client_dashboard_reflects_consumption(client, staff_headers, make_client, db_session):
    from datetime import date

    from app.models.intervention import Intervention

    existing = make_client(date_debut_contrat=date(2025, 3, 15), forfait_n1_h=4)
    intervention = Intervention(
        client_id=existing.id,
        date_intervention=date(2025, 3, 20),
        niveau="N1",
        duree_minutes=200,
        description="assistance",
    )
    db_session.add(intervention)
    db_session.commit()

    response = client.get(f"/api/clients/{existing.id}/dashboard", headers=staff_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["n1"]["consomme_minutes"] == 200
    assert body["alerte"] is True


def test_delete_client_sans_donnees(client, staff_headers, make_client, db_session, org):
    from app.models.user import User

    portail = User(org_id=org.id, email="portail@exemple-test.fr", name="Portail", password_hash=hash_password("x"), role="client")
    db_session.add(portail)
    db_session.commit()
    db_session.refresh(portail)
    portail_id = portail.id
    existing = make_client(nom="À supprimer", user_id=portail_id)

    response = client.delete(f"/api/clients/{existing.id}", headers=staff_headers)

    assert response.status_code == 204
    assert client.get(f"/api/clients/{existing.id}", headers=staff_headers).status_code == 404
    assert db_session.query(User).filter(User.id == portail_id).first() is None


def test_delete_client_refuse_si_interventions(client, staff_headers, make_client, db_session):
    from datetime import date

    from app.models.intervention import Intervention

    existing = make_client(nom="Avec historique")
    intervention = Intervention(
        client_id=existing.id,
        date_intervention=date(2025, 3, 20),
        niveau="N1",
        duree_minutes=30,
        description="assistance",
    )
    db_session.add(intervention)
    db_session.commit()

    response = client.delete(f"/api/clients/{existing.id}", headers=staff_headers)

    assert response.status_code == 400
    assert client.get(f"/api/clients/{existing.id}", headers=staff_headers).status_code == 200


def test_cannot_access_client_from_another_organization(client, staff_headers, db_session):
    from datetime import date

    from app.models.client import Client
    from app.models.organization import Organization

    autre_org = Organization(name="Autre Org", slug="autre-org")
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)

    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1))
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    response = client.get(f"/api/clients/{client_autre_org.id}", headers=staff_headers)

    assert response.status_code == 404
