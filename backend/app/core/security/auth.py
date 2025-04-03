from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List
import logging
from abc import ABC, abstractmethod

from fastapi import HTTPException, status
from jose import jwt, JWTError
from pydantic import ValidationError

from app.core.config.settings import settings
from app.core.security.jwt import create_access_token, ALGORITHM

logger = logging.getLogger(__name__)


class BaseAuthProvider(ABC):
    """
    Abstract base class for authentication providers
    """
    
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a token and return the payload if valid
        """
        pass
    
    @abstractmethod
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from token
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the name of the auth provider
        """
        pass


class JWTAuthProvider(BaseAuthProvider):
    """
    JWT authentication provider using application's own JWT
    """
    
    @property
    def provider_name(self) -> str:
        return "jwt"
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate a JWT token and return the payload if valid
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[ALGORITHM]
            )
            
            # Check for expiration
            expiration = payload.get("exp")
            if expiration and datetime.fromtimestamp(expiration) < datetime.utcnow():
                logger.warning("JWT token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except ValidationError as e:
            logger.warning(f"JWT payload validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        Get user information from JWT token
        """
        payload = await self.validate_token(token)
        
        # Extract user identifier
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token content",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Return user info from token
        return {
            "id": None,  # No ID in JWT, will need to be looked up
            "email": user_id,  # We use email as subject in our JWT
            "provider_id": None,  # No provider-specific ID for our own JWT
            "metadata": payload.get("metadata", {}),
            "provider": self.provider_name
        }


class AuthService:
    """
    Authentication service that manages multiple auth providers
    """
    
    def __init__(self):
        self.providers: Dict[str, BaseAuthProvider] = {}
        self.register_provider(JWTAuthProvider())
    
    def register_provider(self, provider: BaseAuthProvider) -> None:
        """
        Register an authentication provider
        """
        self.providers[provider.provider_name] = provider
        logger.info(f"Registered auth provider: {provider.provider_name}")
    
    async def validate_token(self, token: str, provider_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a token using the appropriate provider
        """
        # If provider hint is given, try that provider first
        if provider_hint and provider_hint in self.providers:
            try:
                return await self.providers[provider_hint].validate_token(token)
            except HTTPException:
                # If hint provider fails, continue to try others
                if len(self.providers) == 1:
                    # If only one provider is registered, re-raise the exception
                    raise
                
        # Try all registered providers
        errors: List[str] = []
        for provider_name, provider in self.providers.items():
            if provider_hint and provider_name == provider_hint:
                # Skip if we already tried this one
                continue
                
            try:
                return await provider.validate_token(token)
            except HTTPException as e:
                errors.append(f"{provider_name}: {e.detail}")
        
        # If all providers failed, raise an exception
        logger.warning(f"Token validation failed for all providers: {errors}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    async def get_user_info(self, token: str, provider_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information from a token
        """
        # If provider hint is given, try that provider first
        if provider_hint and provider_hint in self.providers:
            try:
                return await self.providers[provider_hint].get_user_info(token)
            except HTTPException:
                # If hint provider fails, continue to try others
                if len(self.providers) == 1:
                    # If only one provider is registered, re-raise the exception
                    raise
                
        # Try all registered providers
        errors: List[str] = []
        for provider_name, provider in self.providers.items():
            if provider_hint and provider_name == provider_hint:
                # Skip if we already tried this one
                continue
                
            try:
                return await provider.get_user_info(token)
            except HTTPException as e:
                errors.append(f"{provider_name}: {e.detail}")
        
        # If all providers failed, raise an exception
        logger.warning(f"User info retrieval failed for all providers: {errors}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not retrieve user information",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Create global auth service instance
auth_service = AuthService()