import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import jwt
from datetime import datetime, timedelta

from fastapi import HTTPException

from app.core.security.auth import BaseAuthProvider, JWTAuthProvider, AuthService
from app.core.config.settings import settings


class TestJWTAuthProvider:
    """Test JWTAuthProvider class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.provider = JWTAuthProvider()
        self.test_secret = "test_secret_key"
        
        # Create a valid token for testing
        payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow(),
            "metadata": {"role": "user"}
        }
        self.valid_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        # Create an expired token
        expired_payload = {
            "sub": "test@example.com",
            "exp": datetime.utcnow() - timedelta(minutes=30),
            "iat": datetime.utcnow() - timedelta(hours=1)
        }
        self.expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
    
    @pytest.mark.asyncio
    async def test_provider_name(self):
        """Test provider name"""
        assert self.provider.provider_name == "jwt"
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self):
        """Test successful token validation"""
        result = await self.provider.validate_token(self.valid_token)
        assert result["sub"] == "test@example.com"
        assert "exp" in result
        assert "metadata" in result
        assert result["metadata"]["role"] == "user"
    
    @pytest.mark.asyncio
    async def test_validate_token_expired(self):
        """Test expired token validation"""
        with pytest.raises(HTTPException) as excinfo:
            await self.provider.validate_token(self.expired_token)
        assert excinfo.value.status_code == 401
        assert "Token expired" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self):
        """Test invalid token validation"""
        with pytest.raises(HTTPException) as excinfo:
            await self.provider.validate_token("invalid_token")
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_info_success(self):
        """Test getting user info from token"""
        user_info = await self.provider.get_user_info(self.valid_token)
        assert user_info["email"] == "test@example.com"
        assert user_info["provider"] == "jwt"
        assert "metadata" in user_info
    
    @pytest.mark.asyncio
    async def test_get_user_info_no_subject(self):
        """Test getting user info from token without subject"""
        # Create a token without subject
        payload = {
            "exp": datetime.utcnow() + timedelta(minutes=30),
            "iat": datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        
        with pytest.raises(HTTPException) as excinfo:
            await self.provider.get_user_info(token)
        assert excinfo.value.status_code == 401
        assert "Invalid token content" in excinfo.value.detail


class TestAuthService:
    """Test AuthService class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mock providers
        self.jwt_provider = AsyncMock(spec=BaseAuthProvider)
        self.jwt_provider.provider_name = "jwt"
        self.jwt_provider.validate_token.return_value = {"sub": "jwt_user@example.com"}
        self.jwt_provider.get_user_info.return_value = {
            "email": "jwt_user@example.com",
            "provider": "jwt"
        }
        
        self.other_provider = AsyncMock(spec=BaseAuthProvider)
        self.other_provider.provider_name = "other"
        self.other_provider.validate_token.return_value = {"sub": "other_user@example.com"}
        self.other_provider.get_user_info.return_value = {
            "email": "other_user@example.com",
            "provider": "other"
        }
        
        # Create auth service with mock providers
        self.auth_service = AuthService()
        self.auth_service.providers = {}  # Clear existing providers
        self.auth_service.register_provider(self.jwt_provider)
        self.auth_service.register_provider(self.other_provider)
    
    @pytest.mark.asyncio
    async def test_validate_token_with_hint(self):
        """Test validating token with provider hint"""
        result = await self.auth_service.validate_token("token", provider_hint="jwt")
        assert result["sub"] == "jwt_user@example.com"
        self.jwt_provider.validate_token.assert_called_once_with("token")
        self.other_provider.validate_token.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_validate_token_try_all(self):
        """Test validating token trying all providers"""
        # Make JWT provider fail
        self.jwt_provider.validate_token.side_effect = HTTPException(status_code=401, detail="JWT failed")
        
        # The other provider should succeed
        result = await self.auth_service.validate_token("token")
        assert result["sub"] == "other_user@example.com"
        self.jwt_provider.validate_token.assert_called_once_with("token")
        self.other_provider.validate_token.assert_called_once_with("token")
    
    @pytest.mark.asyncio
    async def test_validate_token_all_fail(self):
        """Test validating token when all providers fail"""
        # Make all providers fail
        self.jwt_provider.validate_token.side_effect = HTTPException(status_code=401, detail="JWT failed")
        self.other_provider.validate_token.side_effect = HTTPException(status_code=401, detail="Other failed")
        
        with pytest.raises(HTTPException) as excinfo:
            await self.auth_service.validate_token("token")
        assert excinfo.value.status_code == 401
        assert "Invalid authentication token" in excinfo.value.detail
    
    @pytest.mark.asyncio
    async def test_get_user_info_with_hint(self):
        """Test getting user info with provider hint"""
        result = await self.auth_service.get_user_info("token", provider_hint="other")
        assert result["email"] == "other_user@example.com"
        assert result["provider"] == "other"
        self.other_provider.get_user_info.assert_called_once_with("token")
        self.jwt_provider.get_user_info.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_info_try_all(self):
        """Test getting user info trying all providers"""
        # Make JWT provider fail
        self.jwt_provider.get_user_info.side_effect = HTTPException(status_code=401, detail="JWT failed")
        
        # The other provider should succeed
        result = await self.auth_service.get_user_info("token")
        assert result["email"] == "other_user@example.com"
        self.jwt_provider.get_user_info.assert_called_once_with("token")
        self.other_provider.get_user_info.assert_called_once_with("token")