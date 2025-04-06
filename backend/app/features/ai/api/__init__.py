from fastapi import APIRouter
from .endpoints import router as ai_router

router = APIRouter()
router.include_router(ai_router, prefix="", tags=["AI"])

__all__ = ["router"]