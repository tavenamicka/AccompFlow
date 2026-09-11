from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.models.invitation import Invitation
from app.models.user import User


def _make_invitation(db_session, token="abc123", email="client@exemple-test.fr", name="Client Test", expired=False):
    invitation = Invitation(
        token=token,
        email=email,
        name=name,
        expires_at=datetime.now(timezone.utc) + (timedelta(days=-1) if expired else timedelta(days=7)),
    )
    db_session.add(invitation)
    db_session.commit()
    return invitation


def _make_user(db_session, org, email="user@exemple-test.fr", password="password123"):
    user = User(org_id=org.id, email=email, name="Utilisateur Test", password_hash=hash_password(password))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_success(client, db_session, org):
    _make_user(db_session, org, email="jean@exemple-test.fr", password="secret1234")

    response = client.post("/api/auth/login", json={"email": "jean@exemple-test.fr", "password": "secret1234"})

    assert response.status_code == 200
    body = response.json()
    assert body["user"]["email"] == "jean@exemple-test.fr"
    assert "token" in body


def test_login_wrong_password(client, db_session, org):
    _make_user(db_session, org, email="jean@exemple-test.fr", password="secret1234")

    response = client.post("/api/auth/login", json={"email": "jean@exemple-test.fr", "password": "wrong"})

    assert response.status_code == 401


def test_register_with_valid_invitation(client, db_session, org):
    _make_invitation(db_session, token="tok1", email="nouveau@exemple-test.fr")

    response = client.post("/api/auth/register", json={"token": "tok1", "password": "unmotdepasse"})

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "nouveau@exemple-test.fr"

    invitation = db_session.query(Invitation).filter(Invitation.token == "tok1").first()
    assert invitation.used is True


def test_register_with_expired_invitation(client, db_session):
    _make_invitation(db_session, token="tok2", email="expire@exemple-test.fr", expired=True)

    response = client.post("/api/auth/register", json={"token": "tok2", "password": "unmotdepasse"})

    assert response.status_code == 400


def test_register_with_used_invitation_rejected(client, db_session):
    invitation = _make_invitation(db_session, token="tok3", email="deja@exemple-test.fr")
    invitation.used = True
    db_session.commit()

    response = client.post("/api/auth/register", json={"token": "tok3", "password": "unmotdepasse"})

    assert response.status_code == 400


def test_me_requires_auth(client):
    response = client.get("/api/auth/me")
    assert response.status_code in (401, 403)


def test_me_with_valid_token(client, db_session, org):
    _make_user(db_session, org, email="jean@exemple-test.fr", password="secret1234")
    login = client.post("/api/auth/login", json={"email": "jean@exemple-test.fr", "password": "secret1234"})
    token = login.json()["token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "jean@exemple-test.fr"
