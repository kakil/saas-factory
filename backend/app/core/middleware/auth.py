from typing import Optional, Dict, Any
import json
import logging

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.security.auth import auth_service
from app.features.users.models import User

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle authentication
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded endpoints
        if self.is_path_excluded(request.url.path):
            return await call_next(request)
            
        # Extract token from headers
        token = self.extract_token(request)
        if not token:
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=json.dumps({"detail": "Not authenticated"}),
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        try:
            # Validate token and get user info
            user_info = await auth_service.get_user_info(token)
            
            # Get database session
            db = next(get_db())
            
            # Get user from database
            user = self.get_user_from_db(db, user_info)
            if not user:
                return Response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=json.dumps({"detail": "User not found"}),
                    media_type="application/json",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Check if user is active
            if not user.is_active:
                return Response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=json.dumps({"detail": "Inactive user"}),
                    media_type="application/json",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Set user in request state
            request.state.user = user
            
            # Continue with the request
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            return Response(
                status_code=e.status_code,
                content=json.dumps({"detail": e.detail}),
                media_type="application/json",
                headers=e.headers or {"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return Response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=json.dumps({"detail": "Authentication error"}),
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
    
    def extract_token(self, request: Request) -> Optional[str]:
        """
        Extract token from request headers
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None
            
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
            
        return parts[1]
    
    def get_user_from_db(self, db: Session, user_info: Dict[str, Any]) -> Optional[User]:
        """
        Get user from database based on user info from token
        """
        # For now, we just look up by email
        email = user_info.get("email")
        if not email:
            return None
            
        return db.query(User).filter(User.email == email).first()