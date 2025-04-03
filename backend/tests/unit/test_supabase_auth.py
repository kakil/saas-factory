import pytest
from unittest.mock import patch, MagicMock
try:
    from unittest.mock import AsyncMock  # Python 3.8+
except ImportError:
    from asyncmock import AsyncMock  # For older Python versions
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.core.security.supabase import SupabaseAuth
from app.core.security.supabase import supabase_auth
from app.features.users.schemas import Login, UserRegistration
from app.features.users.models import User
from app.features.users.repository import UserRepository


@pytest.fixture
def mock_supabase_response():
    """Mock successful Supabase auth response"""
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "bearer",
        "user": {
            "id": "test_supabase_uid",
            "email": "test@example.com"
        }
    }


@pytest.fixture
def mock_user():
    """Create a mock user"""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.supabase_uid = "test_supabase_uid"
    user.is_active = True
    user.is_superuser = False
    user.organization_id = 1
    return user


@pytest.mark.asyncio
async def test_supabase_sign_in_success(mock_supabase_response):
    """Test successful Supabase sign in"""
    # Mock the httpx.AsyncClient to return successful response
    with patch('httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_async_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_supabase_response
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.post.return_value = mock_response
        mock_client.return_value = mock_async_client
        
        # Call sign_in
        result = await supabase_auth.sign_in("test@example.com", "password123")
        
        # Assert results
        assert result == mock_supabase_response
        assert result["access_token"] == "test_access_token"
        mock_async_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_supabase_sign_in_failure():
    """Test failed Supabase sign in"""
    # Mock the httpx.AsyncClient to return error response
    with patch('httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_async_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error_description": "Invalid credentials"}
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.post.return_value = mock_response
        mock_client.return_value = mock_async_client
        
        # Call sign_in and check for exception
        with pytest.raises(HTTPException) as exc_info:
            await supabase_auth.sign_in("test@example.com", "wrong_password")
        
        # Check exception details
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_supabase_verify_token_success(mock_supabase_response):
    """Test successful token verification"""
    # Mock the httpx.AsyncClient to return successful response
    with patch('httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_async_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_supabase_response["user"]
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.get.return_value = mock_response
        mock_client.return_value = mock_async_client
        
        # Call verify_token
        result = await supabase_auth.verify_token("test_token")
        
        # Assert results
        assert result == mock_supabase_response["user"]
        assert result["id"] == "test_supabase_uid"
        mock_async_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_supabase_verify_token_failure():
    """Test failed token verification"""
    # Mock the httpx.AsyncClient to return error response
    with patch('httpx.AsyncClient') as mock_client:
        # Setup mock response
        mock_async_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.get.return_value = mock_response
        mock_client.return_value = mock_async_client
        
        # Call verify_token and check for exception
        with pytest.raises(HTTPException) as exc_info:
            await supabase_auth.verify_token("invalid_token")
        
        # Check exception details
        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_login_endpoint(client, mock_supabase_response, mock_user):
    """Test login endpoint with mocked Supabase and user repository"""
    # Mock dependencies
    with patch('app.features.auth.api.supabase_auth.sign_in', new_callable=AsyncMock) as mock_sign_in:
        mock_sign_in.return_value = mock_supabase_response
        
        with patch('app.features.users.service.UserService.get_by_email') as mock_get_user:
            mock_get_user.return_value = mock_user
            
            # Make login request
            response = client.post(
                "/api/v1/auth/login", 
                json={"email": "test@example.com", "password": "password123"}
            )
            
            # Check response
            assert response.status_code == 200
            assert response.json()["access_token"] == "test_access_token"
            assert response.json()["refresh_token"] == "test_refresh_token"
            assert response.json()["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_auth_login_user_not_found(client, mock_supabase_response):
    """Test login when user is authenticated by Supabase but not in our database"""
    # Mock dependencies
    with patch('app.features.auth.api.supabase_auth.sign_in', new_callable=AsyncMock) as mock_sign_in:
        mock_sign_in.return_value = mock_supabase_response
        
        with patch('app.features.users.service.UserService.get_by_email') as mock_get_user:
            mock_get_user.return_value = None
            
            # Make login request
            response = client.post(
                "/api/v1/auth/login", 
                json={"email": "test@example.com", "password": "password123"}
            )
            
            # Check response
            assert response.status_code == 401
            assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_auth_register_endpoint(client, mock_supabase_response, mock_user):
    """Test register endpoint with mocked Supabase"""
    # Mock dependencies
    with patch('app.features.auth.api.supabase_auth.sign_up', new_callable=AsyncMock) as mock_sign_up:
        mock_sign_up.return_value = mock_supabase_response
        
        with patch('app.features.teams.service.OrganizationService.create_organization') as mock_create_org:
            mock_org = MagicMock()
            mock_org.id = 1
            mock_create_org.return_value = mock_org
            
            with patch('app.features.users.service.UserService.create_user_with_organization') as mock_create_user:
                mock_create_user.return_value = mock_user
                
                # Make register request with organization
                response = client.post(
                    "/api/v1/auth/register", 
                    json={
                        "email": "test@example.com", 
                        "password": "password123",
                        "name": "Test User",
                        "organization_name": "Test Org"
                    }
                )
                
                # Check response
                assert response.status_code == 200
                assert response.json()["email"] == mock_user.email
                mock_sign_up.assert_called_once()
                mock_create_org.assert_called_once()
                mock_create_user.assert_called_once()