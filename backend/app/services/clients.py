from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.organization import Organization


def get_client_or_404(client_id: int, org: Organization, db: Session) -> Client:
    """Résout un client scopé à l'organisation courante, ou lève 404.

    Partagé entre les routers clients et rapports pour éviter de dupliquer
    cette vérification d'isolation multi-tenant à chaque point d'accès.
    """
    client = db.get(Client, client_id)
    if client is None or client.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return client
