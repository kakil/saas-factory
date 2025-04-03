import pytest
from unittest.mock import patch, MagicMock
try:
    from unittest.mock import AsyncMock  # Python 3.8+
except ImportError:
    from asyncmock import AsyncMock  # For older Python versions
from fastapi.testclient import TestClient

from app.features.users.models import User
from app.core.security.jwt import create_access_token


@pytest.fixture
def test_user(db):
    """Create a test user in the database"""
    user = User(
        email="testuser@example.com",
        name="Test User",
        is_active=True,
        is_superuser=False,
        supabase_uid="test_supabase_uid"
    )
    user.set_password("password123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_token(test_user):
    """Create a token for the test user"""
    return create_access_token(subject=test_user.email)


@pytest.fixture
def mock_supabase_auth_response():
    """Mock successful Supabase auth response"""
    return {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlckBleGFtcGxlLmNvbSIsImV4cCI6MTcxMjE4MDAwMH0.VZEn4JCRPZmcpVxI2Vy_hQAMJs0ExLUjCxNZnwGtMeY",
        "refresh_token": "test-refresh-token",
        "expires_in": 3600,
        "user": {
            "id": "test_supabase_uid",
            "email": "testuser@example.com",
            "app_metadata": {},
            "user_metadata": {
                "name": "Test User"
            }
        }
    }


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_endpoint(client, test_user, mock_supabase_auth_response):
    """Test login endpoint with mocked Supabase"""
    # Mock Supabase sign_in
    with patch('app.features.auth.api.supabase_auth.sign_in', new_callable=AsyncMock) as mock_sign_in:
        mock_sign_in.return_value = mock_supabase_auth_response
        
        # Test login with valid credentials
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "testuser@example.com", "password": "password123"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["refresh_token"] == "test-refresh-token"
        
        # Verify mock was called
        mock_sign_in.assert_called_once_with(
            email="testuser@example.com", 
            password="password123"
        )


@pytest.mark.asyncio
async def test_refresh_token_endpoint(client, mock_supabase_auth_response):
    """Test refresh token endpoint with mocked Supabase"""
    # Mock Supabase refresh_token
    with patch('app.features.auth.api.supabase_auth.refresh_token', new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = {
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600
        }
        
        # Test refresh with valid token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "test-refresh-token"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-access-token"
        assert data["refresh_token"] == "new-refresh-token"
        assert data["token_type"] == "bearer"
        
        # Verify mock was called
        mock_refresh.assert_called_once_with("test-refresh-token")


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(client, user_token, test_user):
    """Test accessing a protected endpoint with a valid token"""
    # Mock verification
    with patch('app.core.middleware.supabase_auth.verify_token', new_callable=AsyncMock) as mock_verify:
        mock_verify.return_value = {
            "id": test_user.supabase_uid,
            "email": test_user.email
        }
        
        # Access users endpoint
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        # Check response
        assert response.status_code == 200
        assert response.json()["email"] == test_user.email


@pytest.mark.asyncio
async def test_registration_with_organization(client, mock_supabase_auth_response):
    """Test user registration with organization creation"""
    # Mock Supabase sign_up
    with patch('app.features.auth.api.supabase_auth.sign_up', new_callable=AsyncMock) as mock_sign_up:
        mock_sign_up.return_value = mock_supabase_auth_response
        
        # Mock organization creation
        with patch('app.features.teams.service.OrganizationService.create_organization') as mock_create_org:
            org = MagicMock()
            org.id = 1
            org.name = "Test Organization"
            mock_create_org.return_value = org
            
            # Mock user creation
            with patch('app.features.users.service.UserService.create_user_with_organization') as mock_create_user:
                user = MagicMock()
                user.id = 1
                user.email = "newuser@example.com"
                user.name = "New User"
                mock_create_user.return_value = user
                
                # Test registration
                response = client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "newuser@example.com",
                        "password": "password123",
                        "name": "New User",
                        "organization_name": "Test Organization"
                    }
                )
                
                # Check response
                assert response.status_code == 200
                data = response.json()
                assert data["email"] == "newuser@example.com"
                
                # Verify mocks were called
                mock_sign_up.assert_called_once()
                mock_create_org.assert_called_once()
                mock_create_user.assert_called_once()