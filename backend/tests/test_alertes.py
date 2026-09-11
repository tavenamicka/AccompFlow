from datetime import date

from freezegun import freeze_time


@freeze_time("2026-07-10 10:00:00")
def test_list_alertes_triees_par_pourcentage_desc(client, staff_headers, make_client, db_session):
    from app.models.intervention import Intervention

    client_a = make_client(nom="Client A", date_debut_contrat=date(2026, 7, 10), forfait_n1_h=4)
    client_b = make_client(nom="Client B", date_debut_contrat=date(2026, 7, 10), forfait_n1_h=4)

    db_session.add_all(
        [
            Intervention(client_id=client_a.id, date_intervention=date(2026, 7, 10), niveau="N1", duree_minutes=200, description="x"),
            Intervention(client_id=client_b.id, date_intervention=date(2026, 7, 10), niveau="N1", duree_minutes=230, description="x"),
        ]
    )
    db_session.commit()

    response = client.get("/api/alertes", headers=staff_headers)

    assert response.status_code == 200
    body = response.json()
    assert [a["client_id"] for a in body] == [client_b.id, client_a.id]


def test_list_alertes_vide_sans_depassement(client, staff_headers, make_client):
    make_client(forfait_n1_h=4)

    response = client.get("/api/alertes", headers=staff_headers)

    assert response.status_code == 200
    assert response.json() == []
