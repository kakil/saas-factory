from datetime import datetime, timedelta
from typing import Any, Optional, Dict

from jose import jwt
from passlib.context import CryptContext
import httpx

from app.core.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None, extra_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a JWT access token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Basic payload with expiration and subject
    to_encode = {"exp": expire, "sub": str(subject)}
    
    # Add any extra data to the payload
    if extra_data:
        to_encode.update(extra_data)
        
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password
    """
    return pwd_context.hash(password)


async def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify a token with Supabase Auth
    
    Returns the payload if valid, raises an exception if not
    """
    async with httpx.AsyncClient() as client:
        headers = {
            "apiKey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {token}"
        }
        response = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers=headers
        )
        
        if response.status_code != 200:
            raise ValueError("Invalid token")
            
        return response.json()