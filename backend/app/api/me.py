from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.client import Client
from app.models.echeancier import Echeancier
from app.models.user import User
from app.schemas.dashboard import ClientDashboardOut
from app.schemas.echeancier import EcheancierOut
from app.services.client_dashboard import construire_dashboard

router = APIRouter(prefix="/api/me", tags=["me"], dependencies=[Depends(get_current_user)])


@router.get("/dashboard", response_model=ClientDashboardOut)
def get_my_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Consommation du client connecté — jamais un client_id en paramètre :
    la fiche est résolue uniquement via le compte connecté (`user_id`), donc
    aucun risque de fuite vers la fiche d'un autre client."""
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune fiche client liée à ce compte")
    return construire_dashboard(db, client)


@router.get("/echeanciers", response_model=list[EcheancierOut])
def get_my_echeanciers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Échéanciers du client connecté, en lecture seule. Liste vide si
    l'admin n'a pas activé l'option pour ce client."""
    client = db.query(Client).filter(Client.user_id == current_user.id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune fiche client liée à ce compte")
    if not client.echeanciers_actif:
        return []
    return db.query(Echeancier).filter(Echeancier.client_id == client.id).order_by(Echeancier.created_at, Echeancier.id).all()
