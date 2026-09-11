from datetime import date, datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.client import Client
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User


def _admin_headers(client, db_session, org):
    admin = User(org_id=org.id, email="admin@exemple-test.fr", name="Admin", password_hash=hash_password("adminpass1"), role="owner")
    db_session.add(admin)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "admin@exemple-test.fr", "password": "adminpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}


def _user_headers(client, db_session, org, email="client@exemple-test.fr", name="Client"):
    user = User(org_id=org.id, email=email, name=name, password_hash=hash_password("clientpass1"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    login = client.post("/api/auth/login", json={"email": email, "password": "clientpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}, user


def test_non_admin_cannot_create_invitation(client, db_session, org):
    headers, _ = _user_headers(client, db_session, org)

    response = client.post("/api/admin/invitations", headers=headers, json={"email": "nouveau@exemple-test.fr", "name": "Nouveau"})

    assert response.status_code == 403


def test_admin_can_create_invitation(client, db_session, org, monkeypatch):
    sent = {}
    monkeypatch.setattr(
        "app.api.admin.send_invitation_email",
        lambda to, name, url: sent.update(to=to, name=name, url=url),
    )
    headers = _admin_headers(client, db_session, org)

    response = client.post("/api/admin/invitations", headers=headers, json={"email": "nouveau@exemple-test.fr", "name": "Nouveau Client"})

    assert response.status_code == 201
    assert sent["to"] == "nouveau@exemple-test.fr"
    assert "invitation" in sent["url"]

    listing = client.get("/api/admin/invitations", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1


def test_invitation_generique_cree_la_fiche_client(client, db_session, org, monkeypatch):
    monkeypatch.setattr("app.api.admin.send_invitation_email", lambda to, name, url: None)
    headers = _admin_headers(client, db_session, org)

    response = client.post(
        "/api/admin/invitations",
        headers=headers,
        json={"email": "nouveau.client@exemple-test.fr", "name": "Nouveau Client"},
    )

    assert response.status_code == 201
    invitation = db_session.query(Invitation).filter(Invitation.email == "nouveau.client@exemple-test.fr").first()
    assert invitation.client_id is not None

    created_client = db_session.get(Client, invitation.client_id)
    assert created_client is not None
    assert created_client.org_id == org.id
    assert created_client.nom == "Nouveau Client"
    assert created_client.email == "nouveau.client@exemple-test.fr"
    assert created_client.user_id is None


def test_admin_can_delete_invitation(client, db_session, org, monkeypatch):
    monkeypatch.setattr("app.api.admin.send_invitation_email", lambda to, name, url: None)
    headers = _admin_headers(client, db_session, org)

    created = client.post("/api/admin/invitations", headers=headers, json={"email": "asupprimer@exemple-test.fr", "name": "À supprimer"})
    token = created.json()["token"]

    response = client.delete(f"/api/admin/invitations/{token}", headers=headers)

    assert response.status_code == 204
    listing = client.get("/api/admin/invitations", headers=headers)
    assert listing.json() == []


def test_delete_invitation_inconnue_404(client, db_session, org):
    headers = _admin_headers(client, db_session, org)

    response = client.delete("/api/admin/invitations/token-inconnu", headers=headers)

    assert response.status_code == 404


def test_admin_lists_only_clients(client, db_session, org):
    admin_headers = _admin_headers(client, db_session, org)
    _user_headers(client, db_session, org, email="jean@exemple-test.fr", name="Jean")
    _user_headers(client, db_session, org, email="alice@exemple-test.fr", name="Alice")

    response = client.get("/api/admin/users", headers=admin_headers)

    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert emails == {"jean@exemple-test.fr", "alice@exemple-test.fr"}
    assert "admin@exemple-test.fr" not in emails


def test_non_admin_cannot_list_users(client, db_session, org):
    headers, _ = _user_headers(client, db_session, org)

    response = client.get("/api/admin/users", headers=headers)

    assert response.status_code == 403


def test_admin_uploads_document_to_client_account(client, db_session, org, tmp_path, monkeypatch):
    import io

    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    admin_headers = _admin_headers(client, db_session, org)
    _, client_user = _user_headers(client, db_session, org)

    upload = client.post(
        f"/api/admin/users/{client_user.id}/documents",
        headers=admin_headers,
        files={"file": ("rapport-intervention.pdf", io.BytesIO(b"%PDF-1.4 rapport"), "application/pdf")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    # Le client voit le document sur son propre compte, via ses routes en self-service
    client_headers, _ = _user_headers(client, db_session, org, email="autre@exemple-test.fr", name="Autre")
    own_listing = client.get("/api/documents", headers=client_headers)
    assert own_listing.json() == []  # pas le document d'un autre client

    listing = client.get(f"/api/admin/users/{client_user.id}/documents", headers=admin_headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == doc_id

    delete = client.delete(f"/api/admin/users/{client_user.id}/documents/{doc_id}", headers=admin_headers)
    assert delete.status_code == 200

    listing_after = client.get(f"/api/admin/users/{client_user.id}/documents", headers=admin_headers)
    assert listing_after.json() == []


def test_non_admin_cannot_upload_to_another_account(client, db_session, org, tmp_path, monkeypatch):
    import io

    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    _, target_user = _user_headers(client, db_session, org, email="cible@exemple-test.fr", name="Cible")
    attacker_headers, _ = _user_headers(client, db_session, org, email="attaquant@exemple-test.fr", name="Attaquant")

    response = client.post(
        f"/api/admin/users/{target_user.id}/documents",
        headers=attacker_headers,
        files={"file": ("x.pdf", io.BytesIO(b"contenu"), "application/pdf")},
    )

    assert response.status_code == 403


def test_list_users_signale_la_fiche_client_liee(client, db_session, org, make_client):
    admin_headers = _admin_headers(client, db_session, org)
    _, orphelin = _user_headers(client, db_session, org, email="orphelin@exemple-test.fr", name="Orphelin")
    _, lie = _user_headers(client, db_session, org, email="lie@exemple-test.fr", name="Lié")
    fiche = make_client(nom="Lié", user_id=lie.id)

    response = client.get("/api/admin/users", headers=admin_headers)

    assert response.status_code == 200
    by_email = {u["email"]: u for u in response.json()}
    assert by_email["orphelin@exemple-test.fr"]["client_id"] is None
    assert by_email["lie@exemple-test.fr"]["client_id"] == fiche.id


def test_delete_user_orphelin(client, db_session, org):
    admin_headers = _admin_headers(client, db_session, org)
    _, orphelin = _user_headers(client, db_session, org, email="orphelin2@exemple-test.fr", name="Orphelin2")

    response = client.delete(f"/api/admin/users/{orphelin.id}", headers=admin_headers)

    assert response.status_code == 204
    assert db_session.query(User).filter(User.id == orphelin.id).first() is None


def test_delete_user_refuse_si_fiche_liee(client, db_session, org, make_client):
    admin_headers = _admin_headers(client, db_session, org)
    _, lie = _user_headers(client, db_session, org, email="lie2@exemple-test.fr", name="Lié2")
    make_client(nom="Lié2", user_id=lie.id)

    response = client.delete(f"/api/admin/users/{lie.id}", headers=admin_headers)

    assert response.status_code == 400
    assert db_session.query(User).filter(User.id == lie.id).first() is not None


def _autre_org(db_session, slug="autre-org-admin"):
    autre_org = Organization(name="Autre Org", slug=slug)
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)
    return autre_org


def test_list_users_ne_voit_pas_les_clients_d_une_autre_organisation(client, db_session, org):
    admin_headers = _admin_headers(client, db_session, org)
    autre_org = _autre_org(db_session)
    user_autre_org = User(
        org_id=autre_org.id,
        email="client.autre-org@exemple-test.fr",
        name="Client Autre Org",
        password_hash=hash_password("clientpass1"),
        role="client",
    )
    db_session.add(user_autre_org)
    db_session.commit()
    db_session.refresh(user_autre_org)

    response = client.get("/api/admin/users", headers=admin_headers)

    assert response.status_code == 200
    ids = [u["id"] for u in response.json()]
    assert user_autre_org.id not in ids


def test_delete_user_d_une_autre_organisation_404(client, db_session, org):
    admin_headers = _admin_headers(client, db_session, org)
    autre_org = _autre_org(db_session)
    user_autre_org = User(
        org_id=autre_org.id,
        email="asupprimer.autre-org@exemple-test.fr",
        name="À supprimer",
        password_hash=hash_password("clientpass1"),
        role="client",
    )
    db_session.add(user_autre_org)
    db_session.commit()
    db_session.refresh(user_autre_org)

    response = client.delete(f"/api/admin/users/{user_autre_org.id}", headers=admin_headers)

    assert response.status_code == 404
    assert db_session.query(User).filter(User.id == user_autre_org.id).first() is not None


def test_documents_d_un_client_d_une_autre_organisation_404(client, db_session, org, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    admin_headers = _admin_headers(client, db_session, org)
    autre_org = _autre_org(db_session)
    user_autre_org = User(
        org_id=autre_org.id,
        email="doc.autre-org@exemple-test.fr",
        name="Doc Autre Org",
        password_hash=hash_password("clientpass1"),
        role="client",
    )
    db_session.add(user_autre_org)
    db_session.commit()
    db_session.refresh(user_autre_org)

    assert client.get(f"/api/admin/users/{user_autre_org.id}/documents", headers=admin_headers).status_code == 404

    import io

    upload = client.post(
        f"/api/admin/users/{user_autre_org.id}/documents",
        headers=admin_headers,
        files={"file": ("x.pdf", io.BytesIO(b"contenu"), "application/pdf")},
    )
    assert upload.status_code == 404


def test_list_invitations_ne_voit_pas_celles_d_une_autre_organisation(client, db_session, org, monkeypatch):
    monkeypatch.setattr("app.api.admin.send_invitation_email", lambda to, name, url: None)
    admin_headers = _admin_headers(client, db_session, org)

    autre_org = _autre_org(db_session, slug="autre-org-invitations")
    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1))
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    invitation_autre_org = Invitation(
        token="token-autre-org-0001",
        email="invite.autre-org@exemple-test.fr",
        name="Invité Autre Org",
        client_id=client_autre_org.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(invitation_autre_org)
    db_session.commit()

    response = client.get("/api/admin/invitations", headers=admin_headers)

    assert response.status_code == 200
    tokens = [i["token"] for i in response.json()]
    assert invitation_autre_org.token not in tokens


def test_delete_invitation_d_une_autre_organisation_404(client, db_session, org):
    autre_org = _autre_org(db_session, slug="autre-org-invitations-delete")
    admin_headers = _admin_headers(client, db_session, org)

    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1))
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    invitation_autre_org = Invitation(
        token="token-autre-org-0002",
        email="invite2.autre-org@exemple-test.fr",
        name="Invité Autre Org 2",
        client_id=client_autre_org.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db_session.add(invitation_autre_org)
    db_session.commit()

    response = client.delete(f"/api/admin/invitations/{invitation_autre_org.token}", headers=admin_headers)

    assert response.status_code == 404
    assert db_session.query(Invitation).filter(Invitation.token == invitation_autre_org.token).first() is not None
