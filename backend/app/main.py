from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.features.auth.api import router as auth_router
from app.features.users.api import router as users_router
from app.features.teams.api import router as teams_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Middleware to set tenant context
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # Skip for auth and root endpoints
    if request.url.path.startswith(f"{settings.API_V1_STR}/auth") or request.url.path == "/":
        return await call_next(request)

    # For other endpoints, attempt to get tenant context from request
    # This will be implemented in Phase 2

    return await call_next(request)


# Include API routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(teams_router, prefix=f"{settings.API_V1_STR}", tags=["teams"])


@app.get("/")
def read_root():
    """
    Root endpoint for health check
    """
    return {"status": "healthy", "message": "SaaS Factory API is running"}


@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "SaaS Factory API is running"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=True)