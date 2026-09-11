from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

PARIS_TZ = ZoneInfo("Europe/Paris")


def aujourdhui_paris() -> date:
    return datetime.now(PARIS_TZ).date()


def _index_periode(date_debut_contrat: date, reference: date) -> int:
    """Index (n) de la période anniversaire contenant `reference`.

    Le jour anniversaire de la période n est toujours recalculé depuis
    `date_debut_contrat` via relativedelta (jamais chaîné depuis la période
    précédente) pour éviter la dérive du jour du mois (ex: contrat au 31,
    mois à 30 jours).
    """
    delta = relativedelta(reference, date_debut_contrat)
    n = delta.years * 12 + delta.months

    while date_debut_contrat + relativedelta(months=n) > reference:
        n -= 1
    while date_debut_contrat + relativedelta(months=n + 1) <= reference:
        n += 1

    return n


def periode_par_index(date_debut_contrat: date, n: int) -> tuple[date, date]:
    date_debut_periode = date_debut_contrat + relativedelta(months=n)
    date_fin_periode = date_debut_contrat + relativedelta(months=n + 1) - timedelta(days=1)
    return date_debut_periode, date_fin_periode


def periode_courante(date_debut_contrat: date, reference: date | None = None) -> tuple[date, date]:
    """Calcule la période anniversaire courante d'un client (du dernier jour
    anniversaire inclus au jour précédant le prochain jour anniversaire inclus)."""
    reference = reference or aujourdhui_paris()
    n = _index_periode(date_debut_contrat, reference)
    return periode_par_index(date_debut_contrat, n)


def index_periode_courante(date_debut_contrat: date, reference: date | None = None) -> int:
    reference = reference or aujourdhui_paris()
    return _index_periode(date_debut_contrat, reference)


def periodes_passees(date_debut_contrat: date, reference: date | None = None) -> list[tuple[int, date, date]]:
    """Liste des périodes strictement antérieures à la période courante,
    de la plus récente à la plus ancienne."""
    n_courant = index_periode_courante(date_debut_contrat, reference)
    return [(n,) + periode_par_index(date_debut_contrat, n) for n in range(n_courant - 1, -1, -1)]


def trouver_periode(date_debut_contrat: date, yyyy_mm: str) -> tuple[int, date, date] | None:
    """Retrouve la période dont le jour anniversaire de début tombe dans le
    mois `yyyy_mm` (ex: "2025-03"). Retourne None si le format est invalide
    ou qu'aucune période ne démarre dans ce mois."""
    try:
        annee, mois = (int(x) for x in yyyy_mm.split("-"))
        reference_approx = date(annee, mois, 1)
    except (ValueError, TypeError):
        return None

    n_estimate = _index_periode(date_debut_contrat, reference_approx)
    for n in (n_estimate - 1, n_estimate, n_estimate + 1):
        if n < 0:
            continue
        debut, fin = periode_par_index(date_debut_contrat, n)
        if (debut.year, debut.month) == (annee, mois):
            return n, debut, fin
    return None
