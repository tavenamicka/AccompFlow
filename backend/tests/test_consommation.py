import uuid
from datetime import date

from freezegun import freeze_time

from app.models.intervention import Intervention
from app.services.consommation import alertes_actives, calculer_pourcentage, consommation


def _ajouter_intervention(db_session, client, niveau, duree_minutes, date_intervention, groupe_id=None):
    intervention = Intervention(
        client_id=client.id,
        date_intervention=date_intervention,
        niveau=niveau,
        duree_minutes=duree_minutes,
        description="intervention de test",
        groupe_id=groupe_id,
    )
    db_session.add(intervention)
    db_session.commit()
    return intervention


def test_calculer_pourcentage():
    assert calculer_pourcentage(0, 4) == 0
    assert calculer_pourcentage(120, 4) == 50
    assert calculer_pourcentage(192, 4) == 80
    assert calculer_pourcentage(300, 4) == 125


def test_calculer_pourcentage_forfait_nul_ne_divise_pas_par_zero():
    assert calculer_pourcentage(60, 0) == 0.0


def test_consommation_agrege_par_niveau(db_session, make_client):
    client = make_client()
    periode = (date(2026, 1, 1), date(2026, 1, 31))
    _ajouter_intervention(db_session, client, "N1", 30, date(2026, 1, 10))
    _ajouter_intervention(db_session, client, "N1", 45, date(2026, 1, 20))
    _ajouter_intervention(db_session, client, "N2", 60, date(2026, 1, 15))

    assert consommation(db_session, client.id, "N1", periode) == 75
    assert consommation(db_session, client.id, "N2", periode) == 60
    assert consommation(db_session, client.id, "N3", periode) == 0


def test_consommation_ignore_hors_periode_et_autres_clients(db_session, make_client):
    client_a = make_client(nom="Client Test A")
    client_b = make_client(nom="Client Test B")
    periode = (date(2026, 1, 1), date(2026, 1, 31))

    _ajouter_intervention(db_session, client_a, "N1", 30, date(2026, 1, 10))
    _ajouter_intervention(db_session, client_a, "N1", 999, date(2025, 12, 31))  # hors période
    _ajouter_intervention(db_session, client_b, "N1", 999, date(2026, 1, 10))  # autre client

    assert consommation(db_session, client_a.id, "N1", periode) == 30


def test_split_compte_chaque_bloc_sur_son_propre_niveau(db_session, make_client):
    client = make_client()
    periode = (date(2026, 1, 1), date(2026, 1, 31))
    groupe_id = uuid.uuid4()

    _ajouter_intervention(db_session, client, "N1", 30, date(2026, 1, 10), groupe_id=groupe_id)
    _ajouter_intervention(db_session, client, "N2", 45, date(2026, 1, 10), groupe_id=groupe_id)

    assert consommation(db_session, client.id, "N1", periode) == 30
    assert consommation(db_session, client.id, "N2", periode) == 45


@freeze_time("2026-07-10 10:00:00")
def test_alertes_actives_seuil_80_pourcent(db_session, make_client, org):
    client = make_client(
        date_debut_contrat=date(2026, 7, 10),
        forfait_n1_h=4,  # 240 minutes
        forfait_n2_h=3,  # 180 minutes
    )
    # 200 / 240 = 83.3% => doit déclencher l'alerte N1
    _ajouter_intervention(db_session, client, "N1", 200, date(2026, 7, 10))
    # 50 / 180 = 27.8% => ne doit pas déclencher l'alerte N2
    _ajouter_intervention(db_session, client, "N2", 50, date(2026, 7, 10))

    alertes = alertes_actives(db_session, org.id)
    alertes_client = [a for a in alertes if a["client_id"] == client.id]

    assert len(alertes_client) == 1
    assert alertes_client[0]["niveau"] == "N1"
    assert alertes_client[0]["pourcentage"] > 80


@freeze_time("2026-07-10 10:00:00")
def test_alertes_actives_isole_par_organisation(db_session, make_client, org):
    from app.models.organization import Organization

    autre_org = Organization(name="Autre Org", slug="autre")
    db_session.add(autre_org)
    db_session.commit()
    db_session.refresh(autre_org)

    client_autre_org = make_client(org_id=autre_org.id, date_debut_contrat=date(2026, 7, 10), forfait_n1_h=4)
    _ajouter_intervention(db_session, client_autre_org, "N1", 300, date(2026, 7, 10))

    alertes = alertes_actives(db_session, org.id)

    assert alertes == []
