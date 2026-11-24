import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

from models.db_models import User
from utils.security import hash_password, create_access_token

# Import models so SQLAlchemy registers all tables in Base.metadata.
from models import db_models  # noqa: F401

# Read the test database URL from .env.
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is missing from your .env file.")

# Safety check: never allow tests to run against the development database.
database_name = make_url(TEST_DATABASE_URL).database

if database_name != "insurance_claims_test":
    raise RuntimeError(
        "Tests must run only against the insurance_claims_test database."
    )

test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test tables once and remove them after the test session."""
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def db_session(setup_test_database):
    """Give each test its own transaction, rolled back after the test."""
    connection = test_engine.connect()
    transaction = connection.begin()

    db = TestingSessionLocal(bind=connection)

    try:
        yield db
    finally:
        db.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """Provide a TestClient that uses the isolated test database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def authenticated_client(client, db_session, monkeypatch):
    """Provide a client authenticated as a claimant."""

    # Mock Redis blocklist check.
    monkeypatch.setattr(
        "utils.dependencies.is_token_blocklisted",
        lambda jti: False,
    )

    # Create a test user.
    test_user = User(
        name="Test Claimant",
        email="claimant@test.com",
        phone_number="9876543210",
        role="claimant",
        password_hash=hash_password("TestPassword123"),
    )

    db_session.add(test_user)
    db_session.flush()

    # Generate a genuine JWT access token.
    access_token = create_access_token({"sub": str(test_user.user_id)})

    # Attach token to all requests from this client.
    client.headers.update({"Authorization": f"Bearer {access_token}"})

    return client


@pytest.fixture
def admin_client(client, db_session, monkeypatch):
    """Provide a client authenticated as an admin."""

    monkeypatch.setattr(
        "utils.dependencies.is_token_blocklisted",
        lambda jti: False,
    )

    admin_user = User(
        name="Test Admin",
        email="admin@test.com",
        phone_number="9876543211",
        role="admin",
        password_hash=hash_password("AdminPassword123"),
    )

    db_session.add(admin_user)
    db_session.flush()

    access_token = create_access_token({"sub": str(admin_user.user_id)})

    client.headers.update({"Authorization": f"Bearer {access_token}"})

    return client
