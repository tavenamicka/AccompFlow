import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest-only-not-used-in-prod")
os.environ.setdefault("ADMIN_EMAIL", "admin@test.local")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-password")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.limiter import limiter
from app.database import Base, get_db
from app.main import app
from app.models.organization import Organization

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=engine)
    limiter.reset()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    return TestingSessionLocal()


@pytest.fixture
def org(db_session):
    organization = Organization(name="Organisation Test", slug="test")
    db_session.add(organization)
    db_session.commit()
    db_session.refresh(organization)
    return organization


@pytest.fixture
def make_client(db_session, org):
    from datetime import date

    from app.models.client import Client

    def _make_client(**kwargs):
        defaults = {"nom": "Client Test", "date_debut_contrat": date(2025, 3, 15), "org_id": org.id}
        defaults.update(kwargs)
        client = Client(**defaults)
        db_session.add(client)
        db_session.commit()
        db_session.refresh(client)
        return client

    return _make_client


@pytest.fixture
def staff_headers(client, db_session, org):
    from app.core.security import hash_password
    from app.models.user import User

    staff = User(org_id=org.id, email="staff@exemple-test.fr", name="Staff Test", password_hash=hash_password("staffpass1"), role="staff")
    db_session.add(staff)
    db_session.commit()

    login = client.post("/api/auth/login", json={"email": "staff@exemple-test.fr", "password": "staffpass1"})
    return {"Authorization": f"Bearer {login.json()['token']}"}
