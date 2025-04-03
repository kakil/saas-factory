import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.security.supabase import SupabaseAuth
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_sign_in_success():
    """Test successful sign in"""
    # Create Supabase Auth client
    auth_client = SupabaseAuth(
        url="https://test.supabase.co",
        key="test_key"
    )
    
    # Mock response data
    mock_response_data = {
        "access_token": "test_token",
        "refresh_token": "test_refresh",
        "user": {
            "id": "user123",
            "email": "test@example.com"
        }
    }
    
    # Create mock async client and response
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    
    # Patch httpx.AsyncClient with our mock
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call sign_in
        result = await auth_client.sign_in(
            email="test@example.com",
            password="password123"
        )
        
        # Verify result
        assert result == mock_response_data
        assert result["access_token"] == "test_token"
        assert result["refresh_token"] == "test_refresh"
        
        # Verify correct endpoint was called
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args[0]
        assert "token?grant_type=password" in call_args[0]


@pytest.mark.asyncio
async def test_sign_in_failure():
    """Test failed sign in"""
    # Create Supabase Auth client
    auth_client = SupabaseAuth(
        url="https://test.supabase.co",
        key="test_key"
    )
    
    # Create mock async client and error response
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "error_description": "Invalid login credentials"
    }
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value = mock_response
    
    # Patch httpx.AsyncClient with our mock
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call sign_in should raise exception
        with pytest.raises(HTTPException) as excinfo:
            await auth_client.sign_in(
                email="wrong@example.com",
                password="wrongpassword"
            )
        
        # Verify exception details
        assert excinfo.value.status_code == 401
        assert "Invalid login credentials" in excinfo.value.detail


@pytest.mark.asyncio
async def test_verify_token_success():
    """Test successful token verification"""
    # Create Supabase Auth client
    auth_client = SupabaseAuth(
        url="https://test.supabase.co",
        key="test_key"
    )
    
    # Mock response data
    mock_response_data = {
        "id": "user123",
        "email": "test@example.com",
        "app_metadata": {},
        "user_metadata": {
            "name": "Test User"
        }
    }
    
    # Create mock async client and response
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_client.__aenter__.return_value = mock_client
    mock_client.get.return_value = mock_response
    
    # Patch httpx.AsyncClient with our mock
    with patch('httpx.AsyncClient', return_value=mock_client):
        # Call verify_token
        result = await auth_client.verify_token("valid_token")
        
        # Verify result
        assert result == mock_response_data
        assert result["id"] == "user123"
        assert result["email"] == "test@example.com"
        
        # Verify correct endpoint was called with auth header
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args[0]
        assert "user" in call_args[0]
        assert "Authorization" in mock_client.get.call_args[1]["headers"]
        assert "Bearer valid_token" in mock_client.get.call_args[1]["headers"]["Authorization"]