from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.client import Client
from app.models.invitation import Invitation
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.organizations import get_default_organization

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    token = create_access_token(subject=str(user.id), email=user.email)
    return TokenResponse(token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    invitation = db.query(Invitation).filter(Invitation.token == payload.token).first()
    if invitation is None or invitation.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation invalide ou déjà utilisée")
    expires_at = invitation.expires_at
    if expires_at.tzinfo is None:
        # SQLite (tests) ne conserve pas le fuseau horaire, contrairement à
        # Postgres (timestamptz) — on le suppose UTC dans ce cas.
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expirée")
    if len(payload.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe trop court (8 caractères minimum)")

    existing = db.query(User).filter(User.email == invitation.email.lower()).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Un compte existe déjà pour cet email")

    user = User(
        org_id=get_default_organization(db).id,
        email=invitation.email.lower(),
        name=invitation.name,
        password_hash=hash_password(payload.password),
        role="client",
    )
    db.add(user)

    invitation.used = True
    invitation.used_at = datetime.now(timezone.utc)
    db.flush()  # attribue user.id avant de l'utiliser ci-dessous

    if invitation.client_id is not None:
        client = db.get(Client, invitation.client_id)
        # Défensif : ne lie que si la fiche n'a pas déjà un compte (ne devrait
        # pas arriver, create_invitation le vérifie déjà à la création).
        if client is not None and client.user_id is None:
            client.user_id = user.id

    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id), email=user.email)
    return TokenResponse(token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
