import sys
import os
import asyncio
import unittest
from unittest.mock import patch, AsyncMock

# Add the main application directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.security.supabase import SupabaseAuth
from fastapi import HTTPException


class TestSupabaseAuth(unittest.TestCase):
    def setUp(self):
        self.auth_client = SupabaseAuth(
            url="https://test.supabase.co",
            key="test_key"
        )
        
        # Setup mock response data
        self.success_response_data = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "user": {
                "id": "user123",
                "email": "test@example.com"
            }
        }

    async def test_sign_in_success(self):
        # Create mock async client and response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.success_response_data
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        
        # Patch httpx.AsyncClient with our mock
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Call sign_in
            result = await self.auth_client.sign_in(
                email="test@example.com",
                password="password123"
            )
            
            # Verify result
            self.assertEqual(result, self.success_response_data)
            self.assertEqual(result["access_token"], "test_token")
            self.assertEqual(result["refresh_token"], "test_refresh")
            
            # Verify correct endpoint was called
            mock_client.post.assert_called_once()
            args = mock_client.post.call_args[0]
            self.assertIn("token?grant_type=password", args[0])

    async def test_sign_in_failure(self):
        # Create mock async client and error response
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error_description": "Invalid login credentials"
        }
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        
        # Patch httpx.AsyncClient with our mock
        with patch('httpx.AsyncClient', return_value=mock_client):
            # Call sign_in should raise exception
            with self.assertRaises(HTTPException) as context:
                await self.auth_client.sign_in(
                    email="wrong@example.com",
                    password="wrongpassword"
                )
            
            # Verify exception details
            self.assertEqual(context.exception.status_code, 401)
            self.assertIn("Invalid login credentials", context.exception.detail)

    def run_async_test(self, coroutine):
        return asyncio.run(coroutine)
    
    def test_sign_in_success_runner(self):
        self.run_async_test(self.test_sign_in_success())
        
    def test_sign_in_failure_runner(self):
        self.run_async_test(self.test_sign_in_failure())


if __name__ == "__main__":
    unittest.main()