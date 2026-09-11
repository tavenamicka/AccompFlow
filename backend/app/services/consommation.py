from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.intervention import Intervention
from app.services.periode import periode_courante

SEUIL_ALERTE_PCT = 80


def consommation(db: Session, client_id: int, niveau: str, periode: tuple[date, date]) -> int:
    """Total des minutes consommées par un client sur un niveau, pour une période donnée."""
    date_debut, date_fin = periode
    total = (
        db.query(func.sum(Intervention.duree_minutes))
        .filter(
            Intervention.client_id == client_id,
            Intervention.niveau == niveau,
            Intervention.date_intervention >= date_debut,
            Intervention.date_intervention <= date_fin,
        )
        .scalar()
    )
    return total or 0


def consommations_par_niveau(db: Session, client_id: int, periode: tuple[date, date]) -> dict[str, int]:
    """Total des minutes consommées par niveau (N1/N2/N3) pour un client sur une
    période, en une seule requête groupée — évite d'enchaîner un `consommation()`
    par niveau (3 allers-retours en base) là où un seul suffit."""
    date_debut, date_fin = periode
    lignes = (
        db.query(Intervention.niveau, func.sum(Intervention.duree_minutes))
        .filter(
            Intervention.client_id == client_id,
            Intervention.date_intervention >= date_debut,
            Intervention.date_intervention <= date_fin,
        )
        .group_by(Intervention.niveau)
        .all()
    )
    totaux = {"N1": 0, "N2": 0, "N3": 0}
    totaux.update({niveau: int(total) for niveau, total in lignes})
    return totaux


def calculer_pourcentage(minutes_consommees: int, forfait_heures: int) -> float:
    if forfait_heures <= 0:
        return 0.0
    return (minutes_consommees / (forfait_heures * 60)) * 100


def alertes_actives(db: Session, org_id: int) -> list[dict]:
    """Liste des couples (client, niveau N1/N2) ayant atteint le seuil d'alerte (>= 80%),
    pour les clients actifs de l'organisation donnée."""
    alertes = []
    clients = db.query(Client).filter(Client.org_id == org_id, Client.actif == True).all()  # noqa: E712
    for client in clients:
        periode = periode_courante(client.date_debut_contrat)
        totaux = consommations_par_niveau(db, client.id, periode)
        for niveau, forfait_h in (("N1", client.forfait_n1_h), ("N2", client.forfait_n2_h)):
            pct = calculer_pourcentage(totaux[niveau], forfait_h)
            if pct >= SEUIL_ALERTE_PCT:
                alertes.append(
                    {
                        "client_id": client.id,
                        "client_nom": client.nom,
                        "niveau": niveau,
                        "pourcentage": round(pct, 1),
                    }
                )
    return alertes
