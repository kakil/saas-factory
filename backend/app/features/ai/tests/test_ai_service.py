import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.features.ai.service.ai_service import AIService
from app.features.ai.service.base_llm import BaseLLM


class TestAIService:
    """
    Unit tests for the AIService class.
    """

    def test_init_with_default_llm(self):
        """Test that AIService creates a default LLM when none is provided."""
        with patch("app.features.ai.service.ai_service.WilmerLLM") as mock_llm_class:
            mock_llm_instance = MagicMock()
            mock_llm_class.return_value = mock_llm_instance
            
            service = AIService()
            
            # Assert WilmerLLM was created with expected config
            mock_llm_class.assert_called_once()
            assert service.llm == mock_llm_instance

    def test_init_with_custom_llm(self):
        """Test that AIService uses the provided LLM."""
        mock_llm = MagicMock(spec=BaseLLM)
        service = AIService(llm=mock_llm)
        
        assert service.llm == mock_llm

    @pytest.mark.asyncio
    async def test_generate_content_no_cache(self):
        """Test generate_content method with caching disabled."""
        # Setup
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.generate_text = AsyncMock(return_value="Generated content")
        
        service = AIService(llm=mock_llm)
        
        # Execute
        result = await service.generate_content(
            "Test prompt", 
            skip_cache=True,
            model="test-model"
        )
        
        # Assert
        assert result == "Generated content"
        mock_llm.generate_text.assert_called_once_with(
            "Test prompt", 
            model="test-model"
        )

    @pytest.mark.asyncio
    async def test_generate_content_with_cache_miss(self):
        """Test generate_content with cache miss."""
        # Setup
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.generate_text = AsyncMock(return_value="Generated content")
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        
        service = AIService(llm=mock_llm, redis=mock_redis)
        
        # Execute
        result = await service.generate_content("Test prompt", model="test-model")
        
        # Assert
        assert result == "Generated content"
        mock_llm.generate_text.assert_called_once()
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_content_with_cache_hit(self):
        """Test generate_content with cache hit."""
        # Setup
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.generate_text = AsyncMock(return_value="Generated content")
        
        mock_redis = MagicMock()
        mock_redis.get = AsyncMock(return_value="Cached content")
        
        service = AIService(llm=mock_llm, redis=mock_redis)
        
        # Execute
        result = await service.generate_content("Test prompt", model="test-model")
        
        # Assert
        assert result == "Cached content"
        mock_llm.generate_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_code(self):
        """Test the generate_code method."""
        # Setup
        mock_result = {
            "choices": [
                {"message": {"content": "def test(): pass"}}
            ]
        }
        
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.execute_workflow = AsyncMock(return_value=mock_result)
        
        service = AIService(llm=mock_llm)
        
        # Execute
        result = await service.generate_code(
            "Write a test function", 
            language="python"
        )
        
        # Assert
        assert result == "def test(): pass"
        mock_llm.execute_workflow.assert_called_once_with(
            workflow_name="code_generation",
            prompt="Write a test function",
            workflow="code_generation",
            temperature=0.2,
            language="python"
        )

    @pytest.mark.asyncio
    async def test_generate_marketing_content(self):
        """Test the generate_marketing_content method."""
        # Setup
        mock_result = {
            "choices": [
                {"message": {"content": "Marketing content about AI"}}
            ]
        }
        
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.execute_workflow = AsyncMock(return_value=mock_result)
        
        service = AIService(llm=mock_llm)
        
        # Execute
        result = await service.generate_marketing_content(
            "Generate compelling marketing content about: AI",
            tone="professional"
        )
        
        # Assert
        assert result == "Marketing content about AI"
        mock_llm.execute_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_embeddings(self):
        """Test the get_embeddings method."""
        # Setup
        mock_embeddings = [0.1, 0.2, 0.3]
        mock_llm = MagicMock(spec=BaseLLM)
        mock_llm.generate_embeddings = AsyncMock(return_value=mock_embeddings)
        
        service = AIService(llm=mock_llm)
        
        # Execute
        result = await service.get_embeddings("Test text")
        
        # Assert
        assert result == mock_embeddings
        mock_llm.generate_embeddings.assert_called_once_with("Test text")

    def test_generate_cache_key(self):
        """Test the _generate_cache_key method."""
        # Setup
        service = AIService()
        
        # Execute
        key = service._generate_cache_key(
            "Test prompt", 
            {
                "model": "test-model",
                "temperature": 0.7,
                "irrelevant_param": "should be ignored"
            }
        )
        
        # Assert
        assert isinstance(key, str)
        assert len(key) > 0