from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_org, get_current_staff
from app.database import get_db
from app.models.client import Client
from app.models.document import Document
from app.models.echeancier import Echeancier
from app.models.intervention import Intervention
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate
from app.schemas.dashboard import ClientDashboardOut
from app.schemas.rapport import PeriodeResumeOut, RapportOut
from app.services.client_dashboard import construire_dashboard
from app.services.clients import get_client_or_404 as _get_client_or_404
from app.services.export import construire_rapport
from app.services.periode import periodes_passees, trouver_periode

router = APIRouter(
    prefix="/api/clients",
    tags=["clients"],
    dependencies=[Depends(get_current_staff)],
)


@router.get("", response_model=list[ClientOut])
def list_clients(actif: bool | None = None, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    query = db.query(Client).filter(Client.org_id == org.id)
    if actif is not None:
        query = query.filter(Client.actif == actif)
    return query.order_by(Client.nom).all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = Client(org_id=org.id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    return _get_client_or_404(client_id, org, db)


@router.get("/{client_id}/dashboard", response_model=ClientDashboardOut)
def get_client_dashboard(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)
    return construire_dashboard(db, client)


@router.get("/{client_id}/periodes", response_model=list[PeriodeResumeOut])
def list_periodes_passees(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)
    resultats = []
    for n, debut, fin in periodes_passees(client.date_debut_contrat):
        data = construire_rapport(db, client, (debut, fin))
        resultats.append(
            PeriodeResumeOut(
                periode_id=f"{debut.year:04d}-{debut.month:02d}",
                periode_debut=debut,
                periode_fin=fin,
                n1=data["n1"],
                n2=data["n2"],
                n3=data["n3"],
                heures_supp_minutes=data["heures_supp_minutes"],
            )
        )
    return resultats


@router.get("/{client_id}/periodes/{yyyy_mm}", response_model=RapportOut)
def get_periode_detail(client_id: int, yyyy_mm: str, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)
    trouvee = trouver_periode(client.date_debut_contrat, yyyy_mm)
    if trouvee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Periode introuvable")
    _, debut, fin = trouvee
    data = construire_rapport(db, client, (debut, fin))
    return RapportOut(
        client_id=client.id,
        client_nom=client.nom,
        periode_debut=debut,
        periode_fin=fin,
        n1=data["n1"],
        n2=data["n2"],
        n3=data["n3"],
        heures_supp_minutes=data["heures_supp_minutes"],
        interventions=data["interventions"],
    )


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    db.commit()
    db.refresh(client)
    return client


@router.post("/{client_id}/archiver", response_model=ClientOut)
def archiver_client(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)
    client.actif = False
    db.commit()
    db.refresh(client)
    return client


@router.post("/{client_id}/reactiver", response_model=ClientOut)
def reactiver_client(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)
    client.actif = True
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, org: Organization = Depends(get_current_org), db: Session = Depends(get_db)):
    client = _get_client_or_404(client_id, org, db)

    a_des_interventions = db.query(Intervention).filter(Intervention.client_id == client_id).first() is not None
    a_des_documents = db.query(Document).filter(Document.client_id == client_id).first() is not None
    a_des_echeanciers = db.query(Echeancier).filter(Echeancier.client_id == client_id).first() is not None
    if a_des_interventions or a_des_documents or a_des_echeanciers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce client a des interventions, documents ou échéanciers enregistrés — archivez-le plutôt que de le supprimer.",
        )

    db.query(Invitation).filter(Invitation.client_id == client_id).delete()
    user_id = client.user_id
    db.delete(client)
    if user_id is not None:
        # Le compte portail est propre à ce client (relation 1:1) : sans fiche,
        # il n'a plus lieu d'exister — on l'emporte avec la suppression.
        user = db.get(User, user_id)
        if user is not None:
            db.delete(user)
    db.commit()
