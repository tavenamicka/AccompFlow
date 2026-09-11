from datetime import date

from freezegun import freeze_time

from app.core.security import hash_password
from app.models.intervention import Intervention
from app.models.user import User


def _client_headers(client, db_session, org, email="client-portail@exemple-test.fr"):
    user = User(org_id=org.id, email=email, name="Client Portail", password_hash=hash_password("clientpass1"), role="client")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    login = client.post("/api/auth/login", json={"email": email, "password": "clientpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}, user


def test_me_dashboard_sans_fiche_client_liee(client, db_session, org):
    headers, _ = _client_headers(client, db_session, org)

    response = client.get("/api/me/dashboard", headers=headers)

    assert response.status_code == 404


@freeze_time("2025-03-20 10:00:00")
def test_me_dashboard_reflete_la_consommation_du_client_connecte(client, db_session, org, make_client):
    headers, portail_user = _client_headers(client, db_session, org)
    existing = make_client(date_debut_contrat=date(2025, 3, 15), forfait_n1_h=4, user_id=portail_user.id)
    db_session.add(
        Intervention(client_id=existing.id, date_intervention=date(2025, 3, 20), niveau="N1", duree_minutes=200, description="x")
    )
    db_session.commit()

    response = client.get("/api/me/dashboard", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["client_id"] == existing.id
    assert body["n1"]["consomme_minutes"] == 200
    assert body["alerte"] is True


def test_me_dashboard_ne_montre_pas_la_fiche_dun_autre_client(client, db_session, org, make_client):
    headers, _ = _client_headers(client, db_session, org)
    autre_user = User(org_id=org.id, email="autre-client@exemple-test.fr", name="Autre", password_hash=hash_password("x"), role="client")
    db_session.add(autre_user)
    db_session.commit()
    db_session.refresh(autre_user)
    make_client(user_id=autre_user.id)

    response = client.get("/api/me/dashboard", headers=headers)

    assert response.status_code == 404
