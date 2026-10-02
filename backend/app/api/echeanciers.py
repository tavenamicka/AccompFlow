from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_org, get_current_staff
from app.database import get_db
from app.models.echeancier import Echeance, Echeancier
from app.models.organization import Organization
from app.schemas.echeancier import (
    EcheanceCreate,
    EcheanceOut,
    EcheanceUpdate,
    EcheancierCreate,
    EcheancierOut,
    EcheancierUpdate,
)
from app.services.clients import get_client_or_404

router = APIRouter(prefix="/api", tags=["echeanciers"], dependencies=[Depends(get_current_staff)])


def _get_echeancier_or_404(echeancier_id: int, org: Organization, db: Session) -> Echeancier:
    echeancier = db.get(Echeancier, echeancier_id)
    if echeancier is None or echeancier.client.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Échéancier introuvable")
    return echeancier


def _get_echeance_or_404(echeance_id: int, org: Organization, db: Session) -> Echeance:
    echeance = db.get(Echeance, echeance_id)
    if echeance is None or echeance.echeancier.client.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Échéance introuvable")
    return echeance


def _coherer_paiement(echeance: Echeance) -> None:
    """Une échéance payée a toujours une date de paiement (aujourd'hui par
    défaut), une échéance en attente n'en a jamais."""
    if echeance.statut == "paye":
        if echeance.date_paiement is None:
            echeance.date_paiement = date.today()
    else:
        echeance.date_paiement = None


@router.get("/clients/{client_id}/echeanciers", response_model=list[EcheancierOut])
def list_echeanciers(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = get_client_or_404(client_id, org, db)
    return db.query(Echeancier).filter(Echeancier.client_id == client.id).order_by(Echeancier.created_at, Echeancier.id).all()


@router.post("/clients/{client_id}/echeanciers", response_model=EcheancierOut, status_code=status.HTTP_201_CREATED)
def create_echeancier(
    client_id: int,
    payload: EcheancierCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    client = get_client_or_404(client_id, org, db)
    if not client.echeanciers_actif:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="L'option échéanciers n'est pas activée pour ce client.",
        )
    echeancier = Echeancier(client_id=client.id, **payload.model_dump())
    db.add(echeancier)
    db.commit()
    db.refresh(echeancier)
    return echeancier


@router.patch("/echeanciers/{echeancier_id}", response_model=EcheancierOut)
def update_echeancier(
    echeancier_id: int,
    payload: EcheancierUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    echeancier = _get_echeancier_or_404(echeancier_id, org, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field in ("titre", "type_echeance") and value is None:
            continue
        setattr(echeancier, field, value)
    db.commit()
    db.refresh(echeancier)
    return echeancier


@router.delete("/echeanciers/{echeancier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_echeancier(echeancier_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    echeancier = _get_echeancier_or_404(echeancier_id, org, db)
    db.delete(echeancier)
    db.commit()


@router.post("/echeanciers/{echeancier_id}/echeances", response_model=EcheanceOut, status_code=status.HTTP_201_CREATED)
def create_echeance(
    echeancier_id: int,
    payload: EcheanceCreate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    echeancier = _get_echeancier_or_404(echeancier_id, org, db)
    echeance = Echeance(echeancier_id=echeancier.id, **payload.model_dump())
    _coherer_paiement(echeance)
    db.add(echeance)
    db.commit()
    db.refresh(echeance)
    return echeance


@router.patch("/echeances/{echeance_id}", response_model=EcheanceOut)
def update_echeance(
    echeance_id: int,
    payload: EcheanceUpdate,
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    echeance = _get_echeance_or_404(echeance_id, org, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "statut" and value is None:
            continue
        setattr(echeance, field, value)
    _coherer_paiement(echeance)
    db.commit()
    db.refresh(echeance)
    return echeance


@router.delete("/echeances/{echeance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_echeance(echeance_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    echeance = _get_echeance_or_404(echeance_id, org, db)
    db.delete(echeance)
    db.commit()
