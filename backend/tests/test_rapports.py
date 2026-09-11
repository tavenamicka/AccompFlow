from datetime import date

from freezegun import freeze_time

from app.core.security import hash_password
from app.models.document import Document
from app.models.intervention import Intervention
from app.models.user import User


@freeze_time("2025-03-20 10:00:00")
def test_get_rapport_pdf_sans_compte_client_ne_depose_rien(client, staff_headers, make_client, db_session, tmp_path, monkeypatch):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))
    existing = make_client(date_debut_contrat=date(2025, 3, 15), forfait_n1_h=4)
    db_session.add(
        Intervention(client_id=existing.id, date_intervention=date(2025, 3, 20), niveau="N1", duree_minutes=200, description="x")
    )
    db_session.commit()

    response = client.get(f"/api/rapports/{existing.id}/pdf", headers=staff_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert db_session.query(Document).count() == 0


@freeze_time("2025-03-20 10:00:00")
def test_get_rapport_pdf_avec_compte_client_depose_le_document(
    client, staff_headers, make_client, db_session, org, tmp_path, monkeypatch
):
    monkeypatch.setattr("app.config.settings.upload_dir", str(tmp_path))

    portail_user = User(org_id=org.id, email="client-portail@exemple-test.fr", name="Client Portail", password_hash=hash_password("clientpass1"), role="client")
    db_session.add(portail_user)
    db_session.commit()
    db_session.refresh(portail_user)

    existing = make_client(date_debut_contrat=date(2025, 3, 15), forfait_n1_h=4, user_id=portail_user.id)
    db_session.add(
        Intervention(client_id=existing.id, date_intervention=date(2025, 3, 20), niveau="N1", duree_minutes=200, description="x")
    )
    db_session.commit()

    response = client.get(f"/api/rapports/{existing.id}/pdf", headers=staff_headers)

    assert response.status_code == 200

    document = db_session.query(Document).filter(Document.user_id == portail_user.id).one()
    assert document.client_id == existing.id
    assert document.document_type == "rapport_intervention"
    assert document.period_label == "2025-03"
    assert document.mime_type == "application/pdf"

    # Le client voit le rapport apparaître dans ses propres documents (self-service)
    login = client.post("/api/auth/login", json={"email": "client-portail@exemple-test.fr", "password": "clientpass1"})
    token = login.json()["token"]
    own_documents = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert len(own_documents.json()) == 1
    assert own_documents.json()[0]["document_type"] == "rapport_intervention"


@freeze_time("2025-03-20 10:00:00")
def test_get_rapport_xlsx(client, staff_headers, make_client):
    existing = make_client(date_debut_contrat=date(2025, 3, 15))

    response = client.get(f"/api/rapports/{existing.id}/xlsx", headers=staff_headers)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_rapport_client_introuvable(client, staff_headers):
    response = client.get("/api/rapports/999/pdf", headers=staff_headers)
    assert response.status_code == 404


def test_rapport_cannot_access_client_from_another_organization(client, staff_headers, db_session):
    from app.models.client import Client
    from app.models.organization import Organization

    autre_org = Organization(name="Autre Org", slug="autre-org-rapports")
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)

    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1))
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    response = client.get(f"/api/rapports/{client_autre_org.id}/pdf", headers=staff_headers)

    assert response.status_code == 404
