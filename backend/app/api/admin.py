import logging
import secrets
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.documents import save_uploaded_document
from app.config import settings
from app.core.deps import get_current_org, get_current_staff
from app.core.mail import send_invitation_email
from app.database import get_db
from app.models.client import Client
from app.models.document import Document
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User
from app.schemas.document import DocumentOut
from app.schemas.invitation import InvitationCreate, InvitationCreateOut, InvitationOut
from app.schemas.user import UserOut, UserWithClientOut

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger("app.admin")


@router.get("/users", response_model=list[UserWithClientOut])
def list_users(
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    users = db.query(User).filter(User.role == "client", User.org_id == org.id).order_by(User.name).all()
    client_ids = dict(
        db.query(Client.user_id, Client.id)
        .filter(Client.org_id == org.id, Client.user_id.isnot(None))
        .all()
    )
    return [
        UserWithClientOut(**UserOut.model_validate(user).model_dump(), client_id=client_ids.get(user.id))
        for user in users
    ]


def _get_client(user_id: int, org: Organization, db: Session) -> User:
    user = db.get(User, user_id)
    if user is None or user.role != "client" or user.org_id != org.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    user = _get_client(user_id, org, db)
    fiche_liee = db.query(Client).filter(Client.user_id == user_id).first()
    if fiche_liee is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce compte est lié à une fiche client — supprimez la fiche plutôt que le compte.",
        )
    db.delete(user)
    db.commit()


@router.get("/users/{user_id}/documents", response_model=list[DocumentOut])
def list_client_documents(
    user_id: int,
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    _get_client(user_id, org, db)
    return (
        db.query(Document)
        .filter(Document.user_id == user_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )


@router.post("/users/{user_id}/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_client_document(
    user_id: int,
    file: UploadFile,
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    _get_client(user_id, org, db)
    return await save_uploaded_document(file, user_id, db)


@router.delete("/users/{user_id}/documents/{document_id}")
def delete_client_document(
    user_id: int,
    document_id: int,
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    _get_client(user_id, org, db)
    document = db.get(Document, document_id)
    if document is None or document.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
    Path(document.file_path).unlink(missing_ok=True)
    db.delete(document)
    db.commit()
    return {"status": "deleted", "id": document_id}


@router.post("/invitations", response_model=InvitationCreateOut, status_code=201)
def create_invitation(
    payload: InvitationCreate,
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    client_id = payload.client_id
    if client_id is not None:
        client = db.get(Client, client_id)
        if client is None or client.org_id != org.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
        if client.user_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ce client a déjà un compte portail")
    else:
        # Invitation générique (pas envoyée depuis une fiche client existante) :
        # on crée la fiche en même temps que l'invitation, pour que l'accès
        # portail et la fiche client apparaissent ensemble dans la page Clients.
        client = Client(
            org_id=org.id,
            nom=payload.name,
            email=payload.email.lower(),
            date_debut_contrat=date.today(),
        )
        db.add(client)
        db.flush()  # attribue client.id avant de l'utiliser ci-dessous
        client_id = client.id

    token = secrets.token_hex(16)
    invitation = Invitation(
        token=token,
        email=payload.email.lower(),
        name=payload.name,
        client_id=client_id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    db.commit()

    invitation_url = f"{settings.frontend_base_url}/auth/invitation/{token}"
    try:
        send_invitation_email(payload.email, payload.name, invitation_url)
    except OSError:
        # L'invitation est déjà en base — un accroc du relais mail ne doit
        # pas faire échouer la création. L'admin peut toujours copier/coller
        # invitation_url manuellement au client.
        logger.warning("Invitation créée mais email non envoyé à %s", payload.email)

    return InvitationCreateOut(token=token, invitation_url=invitation_url)


@router.get("/invitations", response_model=list[InvitationOut])
def list_invitations(
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    # Invitation ne porte pas d'org_id propre : elle est toujours créée avec un
    # client_id renseigné (voir create_invitation ci-dessus), donc la jointure
    # vers Client est le seul moyen fiable de la scoper par organisation.
    return (
        db.query(Invitation)
        .join(Client, Client.id == Invitation.client_id)
        .filter(Client.org_id == org.id)
        .order_by(Invitation.created_at.desc())
        .all()
    )


@router.delete("/invitations/{token}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invitation(
    token: str,
    _: User = Depends(get_current_staff),
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    invitation = (
        db.query(Invitation)
        .join(Client, Client.id == Invitation.client_id)
        .filter(Invitation.token == token, Client.org_id == org.id)
        .first()
    )
    if invitation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation introuvable")
    db.delete(invitation)
    db.commit()
