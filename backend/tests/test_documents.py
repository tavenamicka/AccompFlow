import io

from app.core.security import hash_password
from app.models.user import User


def _auth_headers(client, db_session, org, email="jean@exemple-test.fr", password="secret1234"):
    user = User(org_id=org.id, email=email, name="Jean Test", password_hash=hash_password(password))
    db_session.add(user)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": email, "password": password})
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_upload_list_download_delete(client, db_session, org, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    headers = _auth_headers(client, db_session, org)

    upload = client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("facture.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")},
    )
    assert upload.status_code == 201
    doc_id = upload.json()["id"]

    listing = client.get("/api/documents", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    download = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert download.status_code == 200
    assert download.content == b"%PDF-1.4 fake content"

    delete = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert delete.status_code == 200

    listing_after = client.get("/api/documents", headers=headers)
    assert listing_after.json() == []


def test_reject_disallowed_mime_type(client, db_session, org, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    headers = _auth_headers(client, db_session, org)

    response = client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("script.exe", io.BytesIO(b"MZ"), "application/x-msdownload")},
    )

    assert response.status_code == 400


def test_reject_content_type_falsifie(client, db_session, org, tmp_path, monkeypatch):
    """Le Content-Type déclaré prétend être un PDF, mais le contenu réel est
    un exécutable Windows (signature "MZ") — la signature réelle doit
    primer sur la déclaration du client."""
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    headers = _auth_headers(client, db_session, org)

    response = client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("faux-rapport.pdf", io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00"), "application/pdf")},
    )

    assert response.status_code == 400
    assert client.get("/api/documents", headers=headers).json() == []


def test_filter_by_document_type(client, db_session, org, tmp_path, monkeypatch):
    from app.models.document import Document

    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    headers = _auth_headers(client, db_session, org)

    client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("facture.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")},
    )
    upload_rapport = client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("rapport.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")},
    )
    rapport_id = upload_rapport.json()["id"]
    db_session.query(Document).filter(Document.id == rapport_id).update({"document_type": "rapport_intervention"})
    db_session.commit()

    response = client.get("/api/documents", headers=headers, params={"document_type": "rapport_intervention"})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == rapport_id


def test_cannot_access_other_users_document(client, db_session, org, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    headers_a = _auth_headers(client, db_session, org, email="a@exemple-test.fr")
    headers_b = _auth_headers(client, db_session, org, email="b@exemple-test.fr")

    upload = client.post(
        "/api/documents",
        headers=headers_a,
        files={"file": ("facture.pdf", io.BytesIO(b"%PDF-1.4 fake content"), "application/pdf")},
    )
    doc_id = upload.json()["id"]

    response = client.get(f"/api/documents/{doc_id}", headers=headers_b)
    assert response.status_code == 404
