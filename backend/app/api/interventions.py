import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_org, get_current_staff
from app.database import get_db
from app.models.client import Client
from app.models.intervention import Intervention
from app.models.organization import Organization
from app.models.user import User
from app.schemas.intervention import InterventionCreate, InterventionOut, InterventionUpdate

router = APIRouter(
    prefix="/api/interventions",
    tags=["interventions"],
    dependencies=[Depends(get_current_staff)],
)


def _get_intervention_or_404(intervention_id: int, org: Organization, db: Session) -> Intervention:
    intervention = (
        db.query(Intervention)
        .join(Client, Client.id == Intervention.client_id)
        .filter(Intervention.id == intervention_id, Client.org_id == org.id)
        .first()
    )
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention introuvable")
    return intervention


@router.get("", response_model=list[InterventionOut])
def list_interventions(
    client_id: int | None = None,
    date_debut: date | None = None,
    date_fin: date | None = None,
    niveau: str | None = None,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    query = db.query(Intervention).join(Client, Client.id == Intervention.client_id).filter(Client.org_id == org.id)
    if client_id is not None:
        query = query.filter(Intervention.client_id == client_id)
    if date_debut is not None:
        query = query.filter(Intervention.date_intervention >= date_debut)
    if date_fin is not None:
        query = query.filter(Intervention.date_intervention <= date_fin)
    if niveau is not None:
        query = query.filter(Intervention.niveau == niveau)
    return query.order_by(Intervention.date_intervention.desc(), Intervention.id.desc()).all()


@router.post("", response_model=list[InterventionOut], status_code=status.HTTP_201_CREATED)
def create_intervention(
    payload: InterventionCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_staff),
):
    client = db.get(Client, payload.client_id)
    if client is None or client.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    groupe_id = uuid.uuid4() if len(payload.blocs) > 1 else None
    interventions = [
        Intervention(
            client_id=payload.client_id,
            date_intervention=payload.date_intervention,
            user_id=current_user.id,
            groupe_id=groupe_id,
            **bloc.model_dump(),
        )
        for bloc in payload.blocs
    ]
    db.add_all(interventions)
    db.commit()
    for intervention in interventions:
        db.refresh(intervention)
    return interventions


@router.get("/{intervention_id}", response_model=InterventionOut)
def get_intervention(intervention_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    return _get_intervention_or_404(intervention_id, org, db)


@router.patch("/{intervention_id}", response_model=InterventionOut)
def update_intervention(
    intervention_id: int,
    payload: InterventionUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    intervention = _get_intervention_or_404(intervention_id, org, db)

    updates = payload.model_dump(exclude_unset=True)
    if "client_id" in updates:
        nouveau_client = db.get(Client, updates["client_id"])
        if nouveau_client is None or nouveau_client.org_id != org.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")

    for field, value in updates.items():
        setattr(intervention, field, value)
    db.commit()
    db.refresh(intervention)
    return intervention


@router.delete("/{intervention_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_intervention(intervention_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    intervention = _get_intervention_or_404(intervention_id, org, db)
    db.delete(intervention)
    db.commit()
