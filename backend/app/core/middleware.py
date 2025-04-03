from typing import Optional, Dict, Any
import json

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
import jwt

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.features.users.models import User


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle JWT authentication
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        if self.is_path_excluded(request.url.path):
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=json.dumps({"detail": "Not authenticated"}),
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        try:
            token_type, token = auth_header.split()
            if token_type.lower() != "bearer":
                raise ValueError("Invalid token type")
                
            # Get the user from token
            user = await self.get_user_from_token(token, request)
            if not user:
                raise ValueError("Invalid token")
                
            # Set user in request state
            request.state.user = user
            
            # Continue with the request
            response = await call_next(request)
            return response
            
        except (ValueError, jwt.PyJWTError) as e:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=json.dumps({"detail": f"Authentication error: {str(e)}"}),
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def is_path_excluded(self, path: str) -> bool:
        """
        Check if a path should be excluded from authentication
        """
        excluded_paths = [
            "/",
            f"{settings.API_V1_STR}/docs",
            f"{settings.API_V1_STR}/redoc",
            f"{settings.API_V1_STR}/openapi.json",
            f"{settings.API_V1_STR}/health",
            f"{settings.API_V1_STR}/auth/login",
            f"{settings.API_V1_STR}/auth/token",
            f"{settings.API_V1_STR}/auth/register",
            f"{settings.API_V1_STR}/auth/refresh",
        ]
        
        return any(path.startswith(excluded) for excluded in excluded_paths)
    
    async def get_user_from_token(self, token: str, request: Request) -> Optional[User]:
        """
        Get user from token
        """
        # Get DB session
        db = next(get_db())
        
        try:
            from app.core.security.supabase import supabase_auth
            
            # Verify with Supabase (async)
            user_data = await supabase_auth.verify_token(token)
            
            # Get or create user in our database
            supabase_uid = user_data.get("id")
            email = user_data.get("email")
            
            if not email or not supabase_uid:
                return None
                
            # Query user by Supabase UID
            user = db.query(User).filter(User.supabase_uid == supabase_uid).first()
            
            # If not found, try by email
            if not user:
                user = db.query(User).filter(User.email == email).first()
                
                # If user exists but doesn't have Supabase UID, update it
                if user:
                    user.supabase_uid = supabase_uid
                    db.commit()
                    
            return user
            
        except Exception:
            # Fallback to local JWT validation
            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=["HS256"]
                )
                email = payload.get("sub")
                
                if not email:
                    return None
                    
                # Get user from database by email
                user = db.query(User).filter(User.email == email).first()
                return user
                
            except Exception:
                return None