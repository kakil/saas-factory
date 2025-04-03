import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config.settings import settings
from app.core.db.base import Base
from app.core.db.session import get_db
from app.features.users.models import User
from app.features.teams.models import Organization, Team, user_team
from app.main import app

# Set up test database
TEST_SQLALCHEMY_DATABASE_URI = settings.SQLALCHEMY_DATABASE_URI + "_test"
engine = create_engine(str(TEST_SQLALCHEMY_DATABASE_URI))
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    # Create test database tables
    Base.metadata.create_all(bind=engine)

    # Create test session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

    # Drop test database tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    # Dependency override
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    # Create test organization
    organization = Organization(name="Test Organization", plan_id="free")
    db_session.add(organization)
    db_session.commit()

    # Create test user
    user = User(
        email="test@example.com",
        name="Test User",
        is_active=True,
        is_superuser=False,
        organization_id=organization.id,
    )
    user.set_password("password")
    db_session.add(user)
    db_session.commit()

    return user


@pytest.fixture(scope="function")
def test_admin(db_session):
    # Create admin user
    admin = User(
        email="admin@example.com",
        name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    admin.set_password("admin")
    db_session.add(admin)
    db_session.commit()

    return admin


@pytest.fixture(scope="function")
def admin_token(client, test_admin):
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": test_admin.email, "password": "admin"},
    )
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def user_token(client, test_user):
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": test_user.email, "password": "password"},
    )
    return response.json()["access_token"]


def test_create_user(client, admin_token):
    response = client.post(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "new@example.com",
            "password": "newpassword",
            "name": "New User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["name"] == "New User"
    assert "id" in data


def test_read_users(client, admin_token, test_user):
    response = client.get(
        f"{settings.API_V1_STR}/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(user["email"] == test_user.email for user in data)


def test_read_user(client, user_token, test_user):
    response = client.get(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


def test_update_user(client, admin_token, test_user):
    response = client.put(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_delete_user(client, admin_token, test_user):
    response = client.delete(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200

    # Verify user is deleted
    response = client.get(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


def test_read_current_user(client, user_token, test_user):
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["name"] == test_user.name


def test_update_current_user(client, user_token, test_user):
    response = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "My New Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "My New Name"


def test_update_user_settings(client, user_token, test_user):
    settings_data = {
        "theme": "dark",
        "notifications": {
            "email": True,
            "push": False
        }
    }
    response = client.patch(
        f"{settings.API_V1_STR}/users/me/settings",
        headers={"Authorization": f"Bearer {user_token}"},
        json=settings_data,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["settings"]["theme"] == "dark"
    assert data["settings"]["notifications"]["email"] is True
    assert data["settings"]["notifications"]["push"] is False