from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_org, get_current_staff
from app.database import get_db
from app.models.organization import Organization
from app.schemas.alerte import AlerteOut
from app.services.consommation import alertes_actives

router = APIRouter(prefix="/api/alertes", tags=["alertes"], dependencies=[Depends(get_current_staff)])


@router.get("", response_model=list[AlerteOut])
def list_alertes(org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    alertes = alertes_actives(db, org.id)
    return sorted(alertes, key=lambda a: a["pourcentage"], reverse=True)
