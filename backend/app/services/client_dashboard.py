from sqlalchemy.orm import Session

from app.models.client import Client
from app.schemas.dashboard import ClientDashboardOut, NiveauConso
from app.services.consommation import SEUIL_ALERTE_PCT, calculer_pourcentage, consommations_par_niveau
from app.services.periode import periode_courante


def construire_dashboard(db: Session, client: Client) -> ClientDashboardOut:
    """Partagé entre la vue admin (n'importe quel client) et la vue self-service
    du client connecté (voir api/clients.py et api/me.py)."""
    periode_debut, periode_fin = periode_courante(client.date_debut_contrat)
    periode = (periode_debut, periode_fin)

    totaux = consommations_par_niveau(db, client.id, periode)

    pct_n1 = calculer_pourcentage(totaux["N1"], client.forfait_n1_h)
    pct_n2 = calculer_pourcentage(totaux["N2"], client.forfait_n2_h)

    return ClientDashboardOut(
        client_id=client.id,
        client_nom=client.nom,
        periode_debut=periode_debut,
        periode_fin=periode_fin,
        n1=NiveauConso(forfait_h=client.forfait_n1_h, consomme_minutes=totaux["N1"], pourcentage=round(pct_n1, 1)),
        n2=NiveauConso(forfait_h=client.forfait_n2_h, consomme_minutes=totaux["N2"], pourcentage=round(pct_n2, 1)),
        n3=NiveauConso(forfait_h=None, consomme_minutes=totaux["N3"], pourcentage=None),
        alerte=pct_n1 >= SEUIL_ALERTE_PCT or pct_n2 >= SEUIL_ALERTE_PCT,
    )
