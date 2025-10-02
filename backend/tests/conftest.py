"""Pytest configuration and shared fixtures."""
import os
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add backend to path to allow 'from src import X' style imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Test database URL - using in-memory SQLite for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine and session
# Use StaticPool to share the in-memory database across connections
from sqlalchemy.pool import StaticPool

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Essential for in-memory SQLite to share the same database
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Import using src.* notation to match how routers import
from src.database import Base, get_db
from src.models import DBUser, DBDeck, DBFlashcard # Import all models to register them
from src.utils import hash_password
from src.main import app


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables - models must be imported first so they register with Base
    Base.metadata.create_all(bind=test_engine)

    # Start a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session bound to the transaction
    db = TestingSessionLocal(bind=connection)

    try:
        yield db
    finally:
        db.close()
        # Rollback the transaction to clean up test data
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency.

    Note: This fixture depends on db_session to ensure tables are created
    before any tests run.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = DBUser(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """Get authentication headers for a test user."""
    response = client.post(
        "/login",
        data={"username": "testuser", "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_deck(db_session, test_user):
    """Create a test deck."""
    deck = DBDeck(
        name="Test Deck",
        description="A test deck",
        user_id=test_user.id,
        created_at=datetime.now()
    )
    db_session.add(deck)
    db_session.commit()
    db_session.refresh(deck)
    return deck


@pytest.fixture
def test_flashcard(db_session, test_user, test_deck):
    """Create a test flashcard."""
    flashcard = DBFlashcard(
        front="What is 2+2?",
        back="4",
        user_id=test_user.id,
        deck_id=test_deck.id,
        created_at=datetime.now(),
        next_review_at=datetime.now()
    )
    db_session.add(flashcard)
    db_session.commit()
    db_session.refresh(flashcard)
    return flashcard
