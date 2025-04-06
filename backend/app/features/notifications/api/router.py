"""
Notifications API router.
"""

from fastapi import APIRouter

from app.features.notifications.api import endpoints

router = APIRouter()

router.include_router(endpoints.router, tags=["notifications"])

__all__ = ["router"]