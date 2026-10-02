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


def _request_reset(client, monkeypatch, email):
    sent = []
    monkeypatch.setattr("app.api.auth.send_password_reset_email", lambda to, name, url: sent.append((to, url)))
    response = client.post("/api/auth/forgot-password", json={"email": email})
    return response, sent


def _token_of(sent):
    return sent[-1][1].rsplit("/", 1)[1]


def test_forgot_password_unknown_email_is_generic(client, monkeypatch):
    response, sent = _request_reset(client, monkeypatch, "inconnu@exemple-test.fr")

    assert response.status_code == 200
    assert sent == []


def test_password_reset_full_flow(client, db_session, org, monkeypatch):
    _make_user(db_session, org, email="jean@exemple-test.fr", password="ancienmdp1")

    response, sent = _request_reset(client, monkeypatch, "jean@exemple-test.fr")
    assert response.status_code == 200
    token = _token_of(sent)

    reset = client.post("/api/auth/reset-password", json={"token": token, "password": "nouveaumdp1"})
    assert reset.status_code == 200

    assert client.post("/api/auth/login", json={"email": "jean@exemple-test.fr", "password": "ancienmdp1"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "jean@exemple-test.fr", "password": "nouveaumdp1"}).status_code == 200

    # Lien à usage unique
    again = client.post("/api/auth/reset-password", json={"token": token, "password": "autremdp123"})
    assert again.status_code == 400


def test_reset_password_invalid_token(client):
    response = client.post("/api/auth/reset-password", json={"token": "nimportequoi", "password": "nouveaumdp1"})
    assert response.status_code == 400


def test_reset_password_expired_token(client, db_session, org, monkeypatch):
    from app.models.password_reset import PasswordReset

    _make_user(db_session, org, email="jean@exemple-test.fr")
    _, sent = _request_reset(client, monkeypatch, "jean@exemple-test.fr")
    reset = db_session.query(PasswordReset).first()
    reset.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    response = client.post("/api/auth/reset-password", json={"token": _token_of(sent), "password": "nouveaumdp1"})
    assert response.status_code == 400


def test_reset_password_too_short(client, db_session, org, monkeypatch):
    _make_user(db_session, org, email="jean@exemple-test.fr")
    _, sent = _request_reset(client, monkeypatch, "jean@exemple-test.fr")

    response = client.post("/api/auth/reset-password", json={"token": _token_of(sent), "password": "court"})
    assert response.status_code == 400


def test_new_request_invalidates_previous_link(client, db_session, org, monkeypatch):
    _make_user(db_session, org, email="jean@exemple-test.fr")
    _, sent1 = _request_reset(client, monkeypatch, "jean@exemple-test.fr")
    old_token = _token_of(sent1)
    _, sent2 = _request_reset(client, monkeypatch, "jean@exemple-test.fr")

    old = client.post("/api/auth/reset-password", json={"token": old_token, "password": "nouveaumdp1"})
    new = client.post("/api/auth/reset-password", json={"token": _token_of(sent2), "password": "nouveaumdp1"})
    assert old.status_code == 400
    assert new.status_code == 200
