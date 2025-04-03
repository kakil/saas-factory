import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException

from app.core.security.supabase import SupabaseAuth


class TestSupabaseAuth:
    """Test SupabaseAuth class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.supabase_auth = SupabaseAuth(
            url="https://test.supabase.co",
            key="test_key"
        )
    
    @pytest.mark.asyncio
    async def test_sign_in_success(self):
        """Test successful sign in"""
        # Mock response data
        mock_response_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "user": {
                "id": "user123",
                "email": "test@example.com"
            }
        }
        
        # Mock client and response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.post.return_value = mock_response
        
        # Patch async client
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Test sign in function
            result = await self.supabase_auth.sign_in(
                email="test@example.com",
                password="password123"
            )
            
            # Verify result
            assert result == mock_response_data
            assert result["access_token"] == "test_token"
            assert result["refresh_token"] == "test_refresh"
            
            # Verify client was called with correct arguments
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args[0]
            assert "token?grant_type=password" in call_args[0]
    
    @pytest.mark.asyncio
    async def test_sign_in_failure(self):
        """Test failed sign in"""
        # Mock error response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error_description": "Invalid login credentials"
        }
        mock_client.post.return_value = mock_response
        
        # Patch async client
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Test sign in function should raise exception
            with pytest.raises(HTTPException) as excinfo:
                await self.supabase_auth.sign_in(
                    email="wrong@example.com",
                    password="wrongpassword"
                )
            
            # Verify error details
            assert excinfo.value.status_code == 401
            assert "Invalid login credentials" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_token_success(self):
        """Test successful token verification"""
        # Mock response data
        mock_response_data = {
            "id": "user123",
            "email": "test@example.com",
            "app_metadata": {},
            "user_metadata": {
                "name": "Test User"
            }
        }
        
        # Mock client and response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_client.get.return_value = mock_response
        
        # Patch async client
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Test verify token function
            result = await self.supabase_auth.verify_token("valid_token")
            
            # Verify result
            assert result == mock_response_data
            assert result["id"] == "user123"
            assert result["email"] == "test@example.com"
            
            # Verify client was called with correct arguments
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args[0]
            assert "user" in call_args[0]