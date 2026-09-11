from sqlalchemy.orm import Session

from app.models.organization import Organization


def get_default_organization(db: Session) -> Organization:
    """Renvoie l'unique organisation du prototype.

    AccompFlow est mono-tenant pour l'instant (une seule ligne dans
    `organizations`, créée par le script de bootstrap `scripts/create_admin`).
    Ce point d'accès unique est volontairement isolé ici : le jour où il faudra
    résoudre l'organisation par sous-domaine/en-tête (multi-tenant réel), seul
    ce module change — aucun appelant n'a besoin d'être modifié.
    """
    organization = db.query(Organization).order_by(Organization.id).first()
    if organization is None:
        raise RuntimeError(
            "Aucune organisation configurée — lancer `python -m app.scripts.create_admin` avant utilisation."
        )
    return organization
