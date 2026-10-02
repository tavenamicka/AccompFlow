import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.core.mail import send_password_reset_email
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.client import Client
from app.models.invitation import Invitation
from app.models.password_reset import PasswordReset
from app.models.user import User
from app.schemas.auth import ForgotPasswordRequest, LoginRequest, RegisterRequest, ResetPasswordRequest, TokenResponse
from app.schemas.user import UserOut
from app.services.organizations import get_default_organization

router = APIRouter(prefix="/api/auth", tags=["auth"])

RESET_TOKEN_TTL = timedelta(hours=1)


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


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


@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Réponse identique que le compte existe ou non (pas d'énumération d'emails).
    generic = {"detail": "Si un compte existe pour cet email, un lien de réinitialisation vient d'être envoyé."}

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None:
        return generic

    # Un seul lien actif par compte : les précédents sont invalidés.
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id, PasswordReset.used.is_(False)).update({"used": True})

    token = secrets.token_urlsafe(32)
    db.add(
        PasswordReset(
            user_id=user.id,
            token_hash=_hash_reset_token(token),
            expires_at=datetime.now(timezone.utc) + RESET_TOKEN_TTL,
        )
    )
    db.commit()

    reset_url = f"{settings.frontend_base_url}/auth/reset-password/{token}"
    try:
        send_password_reset_email(user.email, user.name, reset_url)
    except OSError:
        # Déjà loggé par send_mail ; même réponse qu'un compte inexistant pour
        # ne rien révéler au client.
        pass
    return generic


@router.post("/reset-password")
@limiter.limit("10/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset = db.query(PasswordReset).filter(PasswordReset.token_hash == _hash_reset_token(payload.token)).first()
    if reset is None or reset.used:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien invalide ou déjà utilisé")
    expires_at = reset.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)  # SQLite (tests)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien expiré")
    if len(payload.password) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mot de passe trop court (8 caractères minimum)")

    user = db.get(User, reset.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien invalide ou déjà utilisé")

    user.password_hash = hash_password(payload.password)
    db.query(PasswordReset).filter(PasswordReset.user_id == user.id, PasswordReset.used.is_(False)).update({"used": True})
    db.commit()
    return {"detail": "Mot de passe mis à jour"}


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
