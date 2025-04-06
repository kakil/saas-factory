from typing import Dict, Any, List, Optional
from fastapi import Depends
from redis import Redis

from app.core.config.settings import settings
from app.core.db.redis import get_redis_connection
from .base_llm import BaseLLM
from .wilmer_llm import WilmerLLM


class AIService:
    """
    Service for handling AI-related operations and coordinating with LLM providers.
    """
    
    def __init__(
        self,
        llm: Optional[BaseLLM] = None,
        redis: Optional[Redis] = Depends(get_redis_connection),
    ):
        """
        Initialize the AI service.
        
        Args:
            llm: The LLM implementation to use
            redis: Redis connection for caching responses
        """
        if llm is None:
            # Create default WilmerAI instance
            config = {
                "api_url": settings.WILMER_API_URL,
                "default_model": settings.DEFAULT_AI_MODEL,
            }
            self.llm = WilmerLLM(config)
        else:
            self.llm = llm
            
        self.redis = redis
        self.cache_ttl = 3600  # 1 hour default cache expiration
    
    async def generate_content(self, prompt: str, **kwargs) -> str:
        """
        Generate content using the configured LLM with caching.
        
        Args:
            prompt: The text prompt to send to the LLM
            **kwargs: Additional parameters for the LLM
            
        Returns:
            str: The generated content
        """
        # Check if caching is disabled
        skip_cache = kwargs.pop("skip_cache", False)
        
        if not skip_cache and self.redis:
            # Generate cache key based on prompt and key parameters
            cache_key = f"ai:content:{self._generate_cache_key(prompt, kwargs)}"
            
            # Check cache first
            cached = await self.redis.get(cache_key)
            if cached:
                return cached.decode("utf-8")
        
        # Generate content from LLM
        content = await self.llm.generate_text(prompt, **kwargs)
        
        # Cache the result if caching is enabled
        if not skip_cache and self.redis:
            ttl = kwargs.get("cache_ttl", self.cache_ttl)
            await self.redis.setex(cache_key, ttl, content)
        
        return content
    
    async def generate_code(self, prompt: str, **kwargs) -> str:
        """
        Generate code using the specialized code workflow.
        
        Args:
            prompt: The code generation prompt
            **kwargs: Additional parameters for the LLM
            
        Returns:
            str: The generated code
        """
        # Set code generation specific parameters
        kwargs["workflow"] = "code_generation"
        kwargs["temperature"] = kwargs.get("temperature", 0.2)  # Lower temperature for code
        
        # Generate code with specialized workflow
        result = await self.llm.execute_workflow(
            workflow_name="code_generation",
            prompt=prompt,
            **kwargs
        )
        
        # Extract just the code part from the structured response
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        
        return "Error: Failed to generate code"
    
    async def generate_marketing_content(self, topic: str, **kwargs) -> str:
        """
        Generate marketing content using the content generation workflow.
        
        Args:
            topic: The topic to generate content about
            **kwargs: Additional parameters for the workflow
            
        Returns:
            str: The generated marketing content
        """
        # Set content generation specific parameters
        kwargs["workflow"] = "content_generation"
        
        # Generate content with specialized workflow
        result = await self.llm.execute_workflow(
            workflow_name="content_generation",
            prompt=f"Generate compelling marketing content about: {topic}",
            **kwargs
        )
        
        # Extract content from the response
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        
        return "Error: Failed to generate marketing content"
    
    async def analyze_data(self, data: str, **kwargs) -> Dict[str, Any]:
        """
        Analyze data using specialized analysis capabilities.
        
        Args:
            data: The data to analyze
            **kwargs: Additional parameters for analysis
            
        Returns:
            Dict[str, Any]: The analysis results
        """
        # Future implementation for data analysis workflow
        pass
    
    async def get_embeddings(self, text: str) -> List[float]:
        """
        Get embeddings for the provided text.
        
        Args:
            text: The text to generate embeddings for
            
        Returns:
            List[float]: The embedding vector
        """
        return await self.llm.generate_embeddings(text)
    
    def _generate_cache_key(self, prompt: str, params: Dict[str, Any]) -> str:
        """
        Generate a deterministic cache key from the prompt and parameters.
        
        Args:
            prompt: The text prompt
            params: The parameters affecting the output
            
        Returns:
            str: A hash-based cache key
        """
        # Only include parameters that affect the output
        relevant_params = {
            k: v for k, v in params.items() 
            if k in ["model", "workflow", "temperature", "max_tokens", "system_prompt"]
        }
        
        # Create a string representation and hash it
        key_parts = [prompt] + [f"{k}={v}" for k, v in sorted(relevant_params.items())]
        key_str = "|".join(key_parts)
        
        import hashlib
        return hashlib.md5(key_str.encode()).hexdigest()