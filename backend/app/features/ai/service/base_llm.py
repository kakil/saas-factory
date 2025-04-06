from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class BaseLLM(ABC):
    """
    Abstract base class for different LLM providers.
    Provides a common interface for all LLM implementations.
    """
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on a prompt.
        
        Args:
            prompt: The text prompt to send to the LLM
            **kwargs: Additional parameters for the LLM (temperature, max_tokens, etc.)
            
        Returns:
            str: The generated text response
        """
        pass
    
    @abstractmethod
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        
        Args:
            text: The text to generate embeddings for
            
        Returns:
            List[float]: The embedding vector
        """
        pass
    
    @staticmethod
    def from_config(provider: str, config: Dict[str, Any]) -> 'BaseLLM':
        """
        Factory method to create an LLM instance based on provider name.
        
        Args:
            provider: The name of the LLM provider
            config: Configuration for the LLM provider
            
        Returns:
            BaseLLM: An instance of a concrete LLM implementation
        """
        # Import implementations dynamically to avoid circular imports
        from .wilmer_llm import WilmerLLM
        
        if provider.lower() == "wilmerai":
            return WilmerLLM(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")