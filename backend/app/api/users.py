from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.user import ChangePasswordRequest, UserOut, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.name is not None:
        current_user.name = payload.name
    if payload.phone is not None:
        current_user.phone = payload.phone
    if payload.email is not None:
        nouvel_email = payload.email.lower()
        if nouvel_email != current_user.email.lower():
            deja_pris = db.query(User).filter(func.lower(User.email) == nouvel_email, User.id != current_user.id).first()
            if deja_pris is not None:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette adresse email est déjà utilisée")
            current_user.email = nouvel_email
            # Garde la fiche client liée synchronisée avec l'email de connexion.
            fiche = db.query(Client).filter(Client.user_id == current_user.id).first()
            if fiche is not None:
                fiche.email = nouvel_email
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe actuel incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe trop court (8 caractères minimum)")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"status": "password_changed"}
