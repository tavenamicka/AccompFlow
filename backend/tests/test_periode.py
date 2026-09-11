from datetime import date

import pytest

from app.services.periode import periode_courante, periodes_passees, trouver_periode


def test_exemple_context_md():
    # Contrat démarré le 15 mars 2025 → 15 nov → 14 déc pour une référence fin novembre.
    debut, fin = periode_courante(date(2025, 3, 15), reference=date(2025, 11, 20))
    assert (debut, fin) == (date(2025, 11, 15), date(2025, 12, 14))


def test_reference_egale_au_jour_anniversaire():
    debut, fin = periode_courante(date(2025, 3, 15), reference=date(2025, 3, 15))
    assert (debut, fin) == (date(2025, 3, 15), date(2025, 4, 14))


def test_veille_du_prochain_anniversaire_reste_dans_la_periode_courante():
    debut, fin = periode_courante(date(2025, 3, 15), reference=date(2025, 4, 14))
    assert (debut, fin) == (date(2025, 3, 15), date(2025, 4, 14))


def test_jour_anniversaire_suivant_demarre_une_nouvelle_periode():
    debut, fin = periode_courante(date(2025, 3, 15), reference=date(2025, 4, 15))
    assert (debut, fin) == (date(2025, 4, 15), date(2025, 5, 14))


@pytest.mark.parametrize(
    "reference,attendu",
    [
        # Contrat démarré le 31 janvier 2025 (année non bissextile).
        (date(2025, 2, 15), (date(2025, 1, 31), date(2025, 2, 27))),  # février n'a que 28 jours
        (date(2025, 2, 28), (date(2025, 2, 28), date(2025, 3, 30))),  # nouvelle période dès le 28
        (date(2025, 3, 31), (date(2025, 3, 31), date(2025, 4, 29))),  # mars a bien 31 jours
        (date(2025, 4, 30), (date(2025, 4, 30), date(2025, 5, 30))),  # avril clampé à 30
    ],
)
def test_cas_31_janvier(reference, attendu):
    assert periode_courante(date(2025, 1, 31), reference=reference) == attendu


def test_cas_31_janvier_annee_bissextile():
    # 2024 est bissextile : la période autour du 29 février doit démarrer le 29, pas le 28.
    debut, fin = periode_courante(date(2024, 1, 31), reference=date(2024, 2, 29))
    assert (debut, fin) == (date(2024, 2, 29), date(2024, 3, 30))


def test_periodes_passees_exclut_la_periode_courante_et_est_triee_recent_dabord():
    debut_contrat = date(2025, 3, 15)
    reference = date(2025, 6, 1)  # période courante = 15 mai -> 14 juin

    periodes = periodes_passees(debut_contrat, reference=reference)

    assert [(d, f) for _, d, f in periodes] == [
        (date(2025, 4, 15), date(2025, 5, 14)),
        (date(2025, 3, 15), date(2025, 4, 14)),
    ]


def test_periodes_passees_vide_si_contrat_recent():
    debut_contrat = date(2025, 3, 15)
    assert periodes_passees(debut_contrat, reference=date(2025, 3, 20)) == []


def test_trouver_periode_par_yyyy_mm():
    debut_contrat = date(2025, 3, 15)
    assert trouver_periode(debut_contrat, "2025-04") == (1, date(2025, 4, 15), date(2025, 5, 14))
    assert trouver_periode(debut_contrat, "2025-03") == (0, date(2025, 3, 15), date(2025, 4, 14))


def test_trouver_periode_cas_31_janvier():
    # Contrat au 31 janvier : la période qui démarre en avril (clampée au 30)
    # doit bien être retrouvée via "2025-04".
    debut_contrat = date(2025, 1, 31)
    assert trouver_periode(debut_contrat, "2025-04") == (3, date(2025, 4, 30), date(2025, 5, 30))


def test_trouver_periode_mois_sans_periode_retourne_none():
    debut_contrat = date(2025, 3, 15)
    assert trouver_periode(debut_contrat, "2024-01") is None


def test_trouver_periode_format_invalide_retourne_none():
    assert trouver_periode(date(2025, 3, 15), "n_importe_quoi") is None
