import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestAIEndpoints:
    """
    Tests for AI API endpoints.
    """
    
    @patch("app.features.ai.api.endpoints.get_current_active_user")
    @patch("app.features.ai.api.endpoints.AIService")
    async def test_generate_from_prompt(self, mock_ai_service, mock_get_user, client):
        """Test the /generate endpoint."""
        # Setup
        mock_get_user.return_value = {"id": 1, "email": "test@example.com"}
        
        mock_ai_service_instance = mock_ai_service.return_value
        mock_ai_service_instance.generate_content = AsyncMock(return_value="Generated text")
        
        # Execute
        response = client.post(
            "/api/v1/ai/generate",
            json={
                "prompt": "Test prompt",
                "model": "test-model",
                "temperature": 0.7,
                "max_tokens": 100,
                "workflow": "general"
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "content" in response.json()
        assert response.json()["content"] == "Generated text"
        assert response.json()["model_used"] == "test-model"
        assert response.json()["workflow_used"] == "general"
    
    @patch("app.features.ai.api.endpoints.get_current_active_user")
    @patch("app.features.ai.api.endpoints.AIService")
    async def test_chat_endpoint(self, mock_ai_service, mock_get_user, client):
        """Test the /chat endpoint."""
        # Setup
        mock_get_user.return_value = {"id": 1, "email": "test@example.com"}
        
        mock_ai_service_instance = mock_ai_service.return_value
        mock_ai_service_instance.llm.generate_text = AsyncMock(return_value="Chat response")
        
        # Execute
        response = client.post(
            "/api/v1/ai/chat",
            json={
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, how are you?"}
                ],
                "model": "test-model",
                "temperature": 0.7
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["content"] == "Chat response"
    
    @patch("app.features.ai.api.endpoints.get_current_active_user")
    @patch("app.features.ai.api.endpoints.AIService")
    async def test_code_generation(self, mock_ai_service, mock_get_user, client):
        """Test the /code endpoint."""
        # Setup
        mock_get_user.return_value = {"id": 1, "email": "test@example.com"}
        
        mock_ai_service_instance = mock_ai_service.return_value
        mock_ai_service_instance.generate_code = AsyncMock(return_value="def test(): pass")
        
        # Execute
        response = client.post(
            "/api/v1/ai/code",
            json={
                "prompt": "Write a test function",
                "language": "python",
                "temperature": 0.2
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["content"] == "def test(): pass"
        assert response.json()["workflow_used"] == "code_generation"
    
    @patch("app.features.ai.api.endpoints.get_current_active_user")
    @patch("app.features.ai.api.endpoints.AIService")
    async def test_content_generation(self, mock_ai_service, mock_get_user, client):
        """Test the /content endpoint."""
        # Setup
        mock_get_user.return_value = {"id": 1, "email": "test@example.com"}
        
        mock_ai_service_instance = mock_ai_service.return_value
        mock_ai_service_instance.generate_marketing_content = AsyncMock(return_value="Marketing content")
        
        # Execute
        response = client.post(
            "/api/v1/ai/content",
            json={
                "topic": "AI",
                "content_type": "blog",
                "tone": "professional",
                "word_count": 500
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["content"] == "Marketing content"
        assert response.json()["workflow_used"] == "content_generation"
    
    @patch("app.features.ai.api.endpoints.get_current_active_user")
    @patch("app.features.ai.api.endpoints.AIService")
    async def test_embeddings(self, mock_ai_service, mock_get_user, client):
        """Test the /embeddings endpoint."""
        # Setup
        mock_get_user.return_value = {"id": 1, "email": "test@example.com"}
        
        mock_ai_service_instance = mock_ai_service.return_value
        mock_ai_service_instance.get_embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Execute
        response = client.post(
            "/api/v1/ai/embeddings",
            json={
                "text": "Test text",
                "model": "embedding-model"
            }
        )
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "embedding" in response.json()
        assert response.json()["embedding"] == [0.1, 0.2, 0.3]
        assert response.json()["dimension"] == 3
    
    @patch("app.features.ai.api.endpoints.get_current_active_user")
    async def test_list_workflows(self, mock_get_user, client):
        """Test the /workflows endpoint."""
        # Setup
        mock_get_user.return_value = {"id": 1, "email": "test@example.com"}
        
        # Execute
        response = client.get("/api/v1/ai/workflows")
        
        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)
        assert "general" in response.json()
        assert "code_generation" in response.json()
        assert "content_generation" in response.json()