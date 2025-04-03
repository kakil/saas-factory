from typing import Optional, Dict, Any
import json

from fastapi import HTTPException, status
import httpx

from app.core.config.settings import settings


class SupabaseAuth:
    """
    Supabase Auth client implementation
    """
    
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.auth_url = f"{url}/auth/v1"
        self.headers = {
            "apiKey": key,
            "Content-Type": "application/json"
        }
    
    async def sign_up(self, email: str, password: str, user_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth
        """
        payload = {
            "email": email,
            "password": password,
        }
        
        if user_metadata:
            payload["user_metadata"] = user_metadata
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/signup",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error_description", "Registration failed")
                except Exception:
                    error_msg = "Registration failed"
                    
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
                
            return response.json()
    
    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user with Supabase Auth
        """
        payload = {
            "email": email,
            "password": password,
        }
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/token?grant_type=password",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error_description", "Authentication failed")
                except Exception:
                    error_msg = "Authentication failed"
                    
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_msg,
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return response.json()
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a user's token with Supabase Auth
        """
        headers = self.headers.copy()
        headers["Authorization"] = f"Bearer {token}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.auth_url}/user",
                headers=headers
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return response.json()

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh an access token using the refresh token
        """
        payload = {
            "refresh_token": refresh_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.auth_url}/token?grant_type=refresh_token",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not refresh token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
                
            return response.json()


# Create a Supabase Auth instance
supabase_auth = SupabaseAuth(settings.SUPABASE_URL, settings.SUPABASE_KEY)