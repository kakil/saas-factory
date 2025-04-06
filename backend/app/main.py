from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config.settings import settings
from app.core.middleware import AuthMiddleware, TenantMiddleware
from app.core.errors.handlers import add_exception_handlers
from app.core.api.responses import success_response
from app.features.auth.api import router as auth_router
from app.features.users.api import router as users_router
from app.features.teams.api import router as teams_router
from app.features.workflows.api.router import router as workflows_router
from app.features.onboarding.api import router as onboarding_router
from app.features.notifications.api.router import router as notifications_router
from app.features.billing.api import router as billing_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Python-based API for the SaaS Factory",
    version="0.1.0",
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

# Add Auth middleware
app.add_middleware(AuthMiddleware)

# Add Tenant middleware
app.add_middleware(TenantMiddleware)

# Add exception handlers
add_exception_handlers(app)

# Include API routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(teams_router, prefix=f"{settings.API_V1_STR}", tags=["teams"])
app.include_router(workflows_router, prefix=f"{settings.API_V1_STR}", tags=["workflows"])
app.include_router(onboarding_router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["onboarding"])
app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(billing_router, prefix=f"{settings.API_V1_STR}/billing", tags=["billing"])


@app.get("/")
def read_root():
    """
    Root endpoint for health check
    """
    return success_response(
        message="SaaS Factory API is running",
        data={"version": settings.API_V1_STR, "environment": settings.ENVIRONMENT}
    )


@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    """
    Health check endpoint
    """
    return success_response(
        message="SaaS Factory API is running",
        data={
            "version": settings.API_V1_STR,
            "environment": settings.ENVIRONMENT,
            "services": {
                "api": "healthy",
                "database": "healthy"
            }
        },
        meta={
            "uptime": "unknown",  # In a real implementation, this would be actual uptime
            "server_time": "unknown"  # In a real implementation, this would be actual time
        }
    )


# Test endpoint for exception handling test
@app.get("/api/v1/test/not-found")
def test_not_found():
    """
    Test endpoint that raises a NotFoundException
    Only used for testing the exception handler
    """
    from app.core.errors.exceptions import NotFoundException
    raise NotFoundException(detail="Test resource not found")


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.SERVER_PORT, reload=True)