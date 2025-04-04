#!/usr/bin/env python
"""
Standalone test runner for API response utilities
"""
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.api.responses import success_response, error_response, paginated_response
from app.core.errors.exceptions import NotFoundException
from app.core.errors.handlers import add_exception_handlers


class TestApiResponses(unittest.TestCase):
    def setUp(self):
        # Create test app
        self.app = FastAPI()
        
        # Add exception handlers
        add_exception_handlers(self.app)
        
        # Add test endpoints
        @self.app.get("/api/v1/health")
        def health_check():
            return success_response(
                message="API is healthy",
                data={
                    "version": "v1",
                    "environment": "test",
                    "services": {"api": "healthy", "database": "healthy"}
                },
                meta={"uptime": "unknown"}
            )
        
        @self.app.get("/api/v1/test/not-found")
        def test_not_found():
            raise NotFoundException(detail="Test resource not found")
        
        # Create test client
        self.client = TestClient(self.app)
    
    def test_health_check_response_format(self):
        """
        Test the standardized response format of the health check endpoint
        """
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        self.assertIn("data", data)
        self.assertIn("meta", data)
        
        # Check data structure
        self.assertIn("version", data["data"])
        self.assertIn("environment", data["data"])
        self.assertIn("services", data["data"])
    
    def test_not_found_exception_response(self):
        """
        Test that a NotFoundException produces the correct response format
        via the exception handlers
        """
        response = self.client.get("/api/v1/test/not-found")
        self.assertEqual(response.status_code, 404)
        
        data = response.json()
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["code"], "NOT_FOUND")
        self.assertEqual(data["message"], "Test resource not found")
    
    def test_success_response_format(self):
        """
        Test the success_response utility function
        """
        response = success_response(
            data={"key": "value"},
            message="Test message",
            meta={"meta_key": "meta_value"}
        )
        
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["message"], "Test message")
        self.assertEqual(response["data"], {"key": "value"})
        self.assertEqual(response["meta"], {"meta_key": "meta_value"})
    
    def test_error_response_format(self):
        """
        Test the error_response utility function
        """
        response = error_response(
            message="Error occurred",
            code="TEST_ERROR",
            data={"error_detail": "test"},
            meta={"meta_key": "meta_value"}
        )
        
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["message"], "Error occurred")
        self.assertEqual(response["code"], "TEST_ERROR")
        self.assertEqual(response["data"], {"error_detail": "test"})
        self.assertEqual(response["meta"], {"meta_key": "meta_value"})
    
    def test_paginated_response_format(self):
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
        
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["message"], "Items retrieved")
        self.assertEqual(response["data"], items)
        
        # Check pagination metadata
        self.assertIn("pagination", response["meta"])
        pagination = response["meta"]["pagination"]
        self.assertEqual(pagination["total"], total)
        self.assertEqual(pagination["page"], page)
        self.assertEqual(pagination["page_size"], page_size)
        self.assertEqual(pagination["pages"], 4)  # (10 + 3 - 1) // 3 = 4
        self.assertTrue(pagination["has_next"])
        self.assertFalse(pagination["has_prev"])
        self.assertEqual(pagination["next_page"], 2)
        self.assertNotIn("prev_page", pagination)
        
        # Check that additional metadata is preserved
        self.assertEqual(response["meta"]["extra"], "info")


if __name__ == "__main__":
    unittest.main()