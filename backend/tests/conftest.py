import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database, drop_database
from fastapi.testclient import TestClient

from app.core.db.base import Base
from app.main import app
from app.core.db.session import get_db
from tests.test_settings import test_settings

# Test database URL - using the test settings
TEST_DATABASE_URL = f"postgresql://{test_settings.POSTGRES_USER}:{test_settings.POSTGRES_PASSWORD}@{test_settings.POSTGRES_SERVER}/{test_settings.POSTGRES_DB}"

# Create test database engine
test_engine = create_engine(TEST_DATABASE_URL)

# Create test database session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def setup_test_db():
    """Set up test database"""
    # Create test database if it doesn't exist
    if not database_exists(test_engine.url):
        create_database(test_engine.url)

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    yield

    # Drop test database after tests
    drop_database(test_engine.url)


@pytest.fixture
def db(setup_test_db):
    """Get test database session"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """Get test client with dependency override"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Reset dependency override
    app.dependency_overrides = {}