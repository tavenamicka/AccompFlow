from app.core.security import hash_password
from app.models.client import Client
from app.models.user import User


def _staff_headers(client, db_session, org):
    staff = User(org_id=org.id, email="staff2@exemple-test.fr", name="Staff", password_hash=hash_password("staffpass1"), role="staff")
    db_session.add(staff)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "staff2@exemple-test.fr", "password": "staffpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def test_inviter_un_client_puis_inscription_lie_le_compte(client, db_session, org, make_client, monkeypatch):
    monkeypatch.setattr("app.api.admin.send_invitation_email", lambda to, name, url: None)
    headers = _staff_headers(client, db_session, org)
    existing = make_client(nom="Jean Test", email="jean.invite@exemple-test.fr")

    invite = client.post(
        "/api/admin/invitations",
        headers=headers,
        json={"email": existing.email, "name": existing.nom, "client_id": existing.id},
    )
    assert invite.status_code == 201
    token = invite.json()["token"]

    register = client.post("/api/auth/register", json={"token": token, "password": "unmotdepasse"})
    assert register.status_code == 201
    user_id = register.json()["user"]["id"]

    db_session.refresh(existing)
    assert existing.user_id == user_id


def test_invitation_refuse_si_client_deja_lie(client, db_session, org, make_client):
    headers = _staff_headers(client, db_session, org)
    autre_user = User(org_id=org.id, email="deja-lie@exemple-test.fr", name="Déjà lié", password_hash=hash_password("x"), role="client")
    db_session.add(autre_user)
    db_session.commit()
    db_session.refresh(autre_user)
    existing = make_client(email="deja-lie@exemple-test.fr", user_id=autre_user.id)

    response = client.post(
        "/api/admin/invitations",
        headers=headers,
        json={"email": existing.email, "name": existing.nom, "client_id": existing.id},
    )

    assert response.status_code == 400


def test_invitation_refuse_client_dune_autre_organisation(client, db_session, org, make_client):
    from datetime import date

    from app.models.organization import Organization

    headers = _staff_headers(client, db_session, org)
    autre_org = Organization(name="Autre Org", slug="autre-org-invit")
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)

    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1), email="x@exemple-test.fr")
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    response = client.post(
        "/api/admin/invitations",
        headers=headers,
        json={"email": "x@exemple-test.fr", "name": "Client Autre Org", "client_id": client_autre_org.id},
    )

    assert response.status_code == 404
