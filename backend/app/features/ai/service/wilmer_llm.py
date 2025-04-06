import httpx
import json
from typing import Dict, Any, List, Optional
from .base_llm import BaseLLM
from app.core.config.settings import settings


class WilmerLLM(BaseLLM):
    """
    WilmerAI implementation of the BaseLLM interface.
    Communicates with the WilmerAI service for orchestrated AI capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the WilmerAI client.
        
        Args:
            config: Configuration parameters for WilmerAI
        """
        self.api_url = config.get("api_url", settings.WILMER_API_URL)
        self.api_key = config.get("api_key", "")
        self.default_model = config.get("default_model", settings.DEFAULT_AI_MODEL)
        self.timeout = config.get("timeout", 120)  # 2 minute timeout
        
        # Configuration for circuit breaker
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1)
        
        # Headers for API requests
        self.headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the WilmerAI service.
        
        Args:
            prompt: The text prompt to send to WilmerAI
            **kwargs: Additional parameters for the request
                - model: The model to use (defaults to settings.DEFAULT_AI_MODEL)
                - workflow: The workflow to use (defaults to "general")
                - temperature: Sampling temperature (defaults to 0.7)
                - max_tokens: Maximum tokens to generate (defaults to 1000)
                - system_prompt: System prompt to use
                
        Returns:
            str: The generated text response
        """
        model = kwargs.get("model", self.default_model)
        workflow = kwargs.get("workflow", "general")
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1000)
        system_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")
        
        # Format prompt as message if it's not already
        if isinstance(prompt, str):
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            # Assume prompt is already in message format
            messages = prompt
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "workflow": workflow
        }
        
        # Make the API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.api_url}/v1/chat/completions",
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    # Parse the response
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                
                except (httpx.HTTPError, json.JSONDecodeError) as e:
                    if attempt == self.max_retries - 1:
                        raise ValueError(f"Failed to generate text after {self.max_retries} attempts: {str(e)}")
                    
                    # Exponential backoff for retries
                    await httpx.AsyncClient().wait_for_timeout(self.retry_delay * (2 ** attempt))
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings using the WilmerAI service.
        
        Args:
            text: The text to generate embeddings for
            
        Returns:
            List[float]: The embedding vector
        """
        payload = {
            "input": text,
            "model": "text-embedding"  # WilmerAI will route to appropriate embedding model
        }
        
        # Make the API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.api_url}/v1/embeddings",
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    # Parse the response
                    result = response.json()
                    return result["data"][0]["embedding"]
                
                except (httpx.HTTPError, json.JSONDecodeError) as e:
                    if attempt == self.max_retries - 1:
                        raise ValueError(f"Failed to generate embeddings after {self.max_retries} attempts: {str(e)}")
                    
                    # Exponential backoff for retries
                    await httpx.AsyncClient().wait_for_timeout(self.retry_delay * (2 ** attempt))
    
    async def execute_workflow(self, workflow_name: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a specific workflow using the WilmerAI service.
        
        Args:
            workflow_name: The name of the workflow to execute
            prompt: The text prompt to send to the workflow
            **kwargs: Additional parameters for the workflow
            
        Returns:
            Dict[str, Any]: The complete workflow output
        """
        model = kwargs.get("model", self.default_model)
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 1000)
        system_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")
        
        # Format messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Prepare request payload
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "workflow": workflow_name
        }
        
        # Make the API request
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.post(
                        f"{self.api_url}/v1/chat/completions",
                        headers=self.headers,
                        json=payload
                    )
                    response.raise_for_status()
                    
                    # Return the complete response for workflow-specific processing
                    return response.json()
                
                except (httpx.HTTPError, json.JSONDecodeError) as e:
                    if attempt == self.max_retries - 1:
                        raise ValueError(f"Failed to execute workflow after {self.max_retries} attempts: {str(e)}")
                    
                    # Exponential backoff for retries
                    await httpx.AsyncClient().wait_for_timeout(self.retry_delay * (2 ** attempt))