"""
Simplified conftest for running API response utility tests without loading the entire app
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Create a clean test FastAPI app
@pytest.fixture
def app():
    app = FastAPI()
    
    # Add health endpoint with our standardized response
    @app.get("/api/v1/health")
    def health_check():
        from app.core.api.responses import success_response
        return success_response(
            message="API is healthy",
            data={
                "version": "v1",
                "environment": "test",
                "services": {"api": "healthy", "database": "healthy"}
            },
            meta={"uptime": "unknown"}
        )
    
    # Add error test endpoint
    @app.get("/api/v1/test/not-found")
    def test_not_found():
        from app.core.errors.exceptions import NotFoundException
        raise NotFoundException(detail="Test resource not found")
    
    return app


@pytest.fixture
def client(app):
    """
    Get test client without requiring database or dependencies
    """
    # Add exception handlers to the app
    from app.core.errors.handlers import add_exception_handlers
    add_exception_handlers(app)
    
    with TestClient(app) as test_client:
        yield test_client