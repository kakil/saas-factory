"""
Workflow API router.
"""

from fastapi import APIRouter

from app.features.workflows.api.endpoints import router as endpoints_router

router = APIRouter()

router.include_router(endpoints_router, prefix="/workflows", tags=["workflows"])

__all__ = ["router"]