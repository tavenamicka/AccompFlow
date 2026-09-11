"""Bootstrap : crée l'organisation par défaut et le compte owner depuis ADMIN_EMAIL/ADMIN_PASSWORD.

Usage (dans le conteneur backend, après `alembic upgrade head`) :
    python -m app.scripts.create_admin
"""

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models.organization import Organization
from app.models.user import User


def _ensure_default_organization(db) -> Organization:
    org = db.query(Organization).order_by(Organization.id).first()
    if org is None:
        org = Organization(name=settings.admin_name, slug="default")
        db.add(org)
        db.flush()
        print(f"Organisation créée : {org.slug}")
    return org


def main() -> None:
    db = SessionLocal()
    try:
        org = _ensure_default_organization(db)

        user = db.query(User).filter(User.email == settings.admin_email.lower()).first()
        if user is None:
            user = User(
                org_id=org.id,
                email=settings.admin_email.lower(),
                name=settings.admin_name,
                password_hash=hash_password(settings.admin_password),
                role="owner",
            )
            db.add(user)
            print(f"Owner créé : {user.email}")
        else:
            user.password_hash = hash_password(settings.admin_password)
            user.role = "owner"
            print(f"Owner mis à jour : {user.email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
