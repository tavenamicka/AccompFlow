from datetime import date


def test_create_intervention_simple(client, staff_headers, make_client):
    existing = make_client()

    response = client.post(
        "/api/interventions",
        headers=staff_headers,
        json={
            "client_id": existing.id,
            "date_intervention": "2025-03-20",
            "blocs": [{"niveau": "N1", "duree_minutes": 30, "description": "Dépannage PC"}],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 1
    assert body[0]["groupe_id"] is None


def test_create_intervention_multi_blocs_partage_un_groupe_id(client, staff_headers, make_client):
    existing = make_client()

    response = client.post(
        "/api/interventions",
        headers=staff_headers,
        json={
            "client_id": existing.id,
            "date_intervention": "2025-03-20",
            "blocs": [
                {"niveau": "N1", "duree_minutes": 30, "description": "Assistance"},
                {"niveau": "N2", "duree_minutes": 45, "description": "Optimisation"},
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 2
    assert body[0]["groupe_id"] is not None
    assert body[0]["groupe_id"] == body[1]["groupe_id"]


def test_create_intervention_client_introuvable(client, staff_headers):
    response = client.post(
        "/api/interventions",
        headers=staff_headers,
        json={
            "client_id": 999,
            "date_intervention": "2025-03-20",
            "blocs": [{"niveau": "N1", "duree_minutes": 30, "description": "x"}],
        },
    )

    assert response.status_code == 404


def test_list_interventions_filtre_par_client(client, staff_headers, make_client):
    client_a = make_client(nom="Client A")
    client_b = make_client(nom="Client B")

    for target, niveau in ((client_a, "N1"), (client_b, "N2")):
        client.post(
            "/api/interventions",
            headers=staff_headers,
            json={
                "client_id": target.id,
                "date_intervention": "2025-03-20",
                "blocs": [{"niveau": niveau, "duree_minutes": 30, "description": "x"}],
            },
        )

    response = client.get("/api/interventions", headers=staff_headers, params={"client_id": client_a.id})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == client_a.id


def test_update_and_delete_intervention(client, staff_headers, make_client):
    existing = make_client()
    created = client.post(
        "/api/interventions",
        headers=staff_headers,
        json={
            "client_id": existing.id,
            "date_intervention": "2025-03-20",
            "blocs": [{"niveau": "N1", "duree_minutes": 30, "description": "x"}],
        },
    ).json()[0]

    updated = client.patch(
        f"/api/interventions/{created['id']}",
        headers=staff_headers,
        json={"description": "description corrigée"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "description corrigée"

    deleted = client.delete(f"/api/interventions/{created['id']}", headers=staff_headers)
    assert deleted.status_code == 204

    listing = client.get("/api/interventions", headers=staff_headers, params={"client_id": existing.id})
    assert listing.json() == []


def test_cannot_access_intervention_from_another_organization(client, staff_headers, db_session):
    from app.models.client import Client
    from app.models.intervention import Intervention
    from app.models.organization import Organization

    autre_org = Organization(name="Autre Org", slug="autre-org-2")
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)

    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1))
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    intervention_autre_org = Intervention(
        client_id=client_autre_org.id,
        date_intervention=date(2025, 1, 10),
        niveau="N1",
        duree_minutes=30,
        description="x",
    )
    db_session.add(intervention_autre_org)
    db_session.commit()
    db_session.refresh(intervention_autre_org)

    response = client.get(f"/api/interventions/{intervention_autre_org.id}", headers=staff_headers)

    assert response.status_code == 404


def test_update_intervention_refuse_client_id_d_une_autre_organisation(client, staff_headers, make_client, db_session):
    from app.models.client import Client
    from app.models.organization import Organization

    existing = make_client()
    created = client.post(
        "/api/interventions",
        headers=staff_headers,
        json={
            "client_id": existing.id,
            "date_intervention": "2025-03-20",
            "blocs": [{"niveau": "N1", "duree_minutes": 30, "description": "x"}],
        },
    ).json()[0]

    autre_org = Organization(name="Autre Org", slug="autre-org-3")
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)

    client_autre_org = Client(org_id=autre_org.id, nom="Client Autre Org", date_debut_contrat=date(2025, 1, 1))
    db_session.add(client_autre_org)
    db_session.commit()
    db_session.refresh(client_autre_org)

    response = client.patch(
        f"/api/interventions/{created['id']}",
        headers=staff_headers,
        json={"client_id": client_autre_org.id},
    )

    assert response.status_code == 404
    inchangee = client.get(f"/api/interventions/{created['id']}", headers=staff_headers)
    assert inchangee.json()["client_id"] == existing.id


def test_update_intervention_refuse_client_id_inexistant(client, staff_headers, make_client):
    existing = make_client()
    created = client.post(
        "/api/interventions",
        headers=staff_headers,
        json={
            "client_id": existing.id,
            "date_intervention": "2025-03-20",
            "blocs": [{"niveau": "N1", "duree_minutes": 30, "description": "x"}],
        },
    ).json()[0]

    response = client.patch(
        f"/api/interventions/{created['id']}",
        headers=staff_headers,
        json={"client_id": 999999},
    )

    assert response.status_code == 404
