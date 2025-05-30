import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.api.responses import success_response, error_response, paginated_response
from app.core.errors.exceptions import NotFoundException

client = TestClient(app)


def test_health_check_response_format():
    """
    Test the standardized response format of the health check endpoint
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "message" in data
    assert "data" in data
    assert "meta" in data
    
    # Check data structure
    assert "version" in data["data"]
    assert "environment" in data["data"]
    assert "services" in data["data"]


def test_success_response_format():
    """
    Test the success_response utility function
    """
    response = success_response(
        data={"key": "value"},
        message="Test message",
        meta={"meta_key": "meta_value"}
    )
    
    assert response["status"] == "success"
    assert response["message"] == "Test message"
    assert response["data"] == {"key": "value"}
    assert response["meta"] == {"meta_key": "meta_value"}


def test_error_response_format():
    """
    Test the error_response utility function
    """
    response = error_response(
        message="Error occurred",
        code="TEST_ERROR",
        data={"error_detail": "test"},
        meta={"meta_key": "meta_value"}
    )
    
    assert response["status"] == "error"
    assert response["message"] == "Error occurred"
    assert response["code"] == "TEST_ERROR"
    assert response["data"] == {"error_detail": "test"}
    assert response["meta"] == {"meta_key": "meta_value"}


def test_paginated_response_format():
    """
    Test the paginated_response utility function
    """
    items = [{"id": 1}, {"id": 2}, {"id": 3}]
    total = 10
    page = 1
    page_size = 3
    
    response = paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        message="Items retrieved",
        meta={"extra": "info"}
    )
    
    assert response["status"] == "success"
    assert response["message"] == "Items retrieved"
    assert response["data"] == items
    
    # Check pagination metadata
    assert "pagination" in response["meta"]
    pagination = response["meta"]["pagination"]
    assert pagination["total"] == total
    assert pagination["page"] == page
    assert pagination["page_size"] == page_size
    assert pagination["pages"] == 4  # (10 + 3 - 1) // 3 = 4
    assert pagination["has_next"] is True
    assert pagination["has_prev"] is False
    assert pagination["next_page"] == 2
    assert "prev_page" not in pagination
    
    # Check that additional metadata is preserved
    assert response["meta"]["extra"] == "info"


def test_not_found_exception_response():
    """
    Test that a NotFoundException produces the correct response format
    via the exception handlers
    """
    # Create a test endpoint that raises NotFoundException
    @app.get("/api/v1/test/not-found")
    def test_not_found():
        raise NotFoundException(detail="Test resource not found")
    
    response = client.get("/api/v1/test/not-found")
    assert response.status_code == 404
    
    data = response.json()
    assert data["status"] == "error"
    assert data["code"] == "NOT_FOUND"
    assert data["message"] == "Test resource not found"