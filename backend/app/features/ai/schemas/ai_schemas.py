from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class Message(BaseModel):
    """Schema for a chat message in an AI request."""
    role: Literal["system", "user", "assistant"] = Field(
        description="The role of the message sender"
    )
    content: str = Field(description="The content of the message")


class PromptRequest(BaseModel):
    """Schema for a prompt-based AI request."""
    prompt: str = Field(description="The text prompt to send to the AI")
    model: Optional[str] = Field(
        default=None,
        description="The AI model to use (defaults to configured default)"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Sampling temperature, controls randomness (0.0-1.0)"
    )
    max_tokens: Optional[int] = Field(
        default=1000,
        description="Maximum number of tokens to generate"
    )
    workflow: Optional[str] = Field(
        default="general",
        description="The workflow to use for processing the prompt"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt to provide context to the AI"
    )
    

class ChatRequest(BaseModel):
    """Schema for a chat-based AI request."""
    messages: List[Message] = Field(
        description="The list of messages in the conversation"
    )
    model: Optional[str] = Field(
        default=None,
        description="The AI model to use (defaults to configured default)"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Sampling temperature, controls randomness (0.0-1.0)"
    )
    max_tokens: Optional[int] = Field(
        default=1000,
        description="Maximum number of tokens to generate"
    )
    workflow: Optional[str] = Field(
        default="general",
        description="The workflow to use for processing the conversation"
    )


class CodeGenerationRequest(BaseModel):
    """Schema for a code generation request."""
    prompt: str = Field(
        description="Description of the code to generate"
    )
    language: Optional[str] = Field(
        default=None,
        description="The programming language for the code"
    )
    code_context: Optional[str] = Field(
        default=None,
        description="Additional context or existing code"
    )
    model: Optional[str] = Field(
        default=None,
        description="The AI model to use (defaults to configured default)"
    )
    temperature: Optional[float] = Field(
        default=0.2,
        description="Sampling temperature, lower for more deterministic output"
    )


class ContentGenerationRequest(BaseModel):
    """Schema for a marketing content generation request."""
    topic: str = Field(
        description="The topic to generate content about"
    )
    content_type: Literal["blog", "email", "social", "ad"] = Field(
        description="The type of content to generate"
    )
    tone: Optional[str] = Field(
        default="professional",
        description="The tone of the content (professional, casual, etc.)"
    )
    word_count: Optional[int] = Field(
        default=500,
        description="Target word count for the generated content"
    )
    target_audience: Optional[str] = Field(
        default=None,
        description="Description of the target audience"
    )
    model: Optional[str] = Field(
        default=None,
        description="The AI model to use (defaults to configured default)"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        description="Sampling temperature, controls randomness (0.0-1.0)"
    )


class EmbeddingRequest(BaseModel):
    """Schema for an embedding generation request."""
    text: str = Field(
        description="The text to generate embeddings for"
    )
    model: Optional[str] = Field(
        default=None,
        description="The embedding model to use"
    )


class AIResponse(BaseModel):
    """Schema for an AI response."""
    content: str = Field(
        description="The generated content"
    )
    model_used: str = Field(
        description="The model that generated the response"
    )
    workflow_used: Optional[str] = Field(
        default=None,
        description="The workflow that was used for processing"
    )
    usage: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Usage statistics (tokens, etc.)"
    )


class EmbeddingResponse(BaseModel):
    """Schema for an embedding response."""
    embedding: List[float] = Field(
        description="The embedding vector"
    )
    model_used: str = Field(
        description="The model that generated the embedding"
    )
    dimension: int = Field(
        description="The dimension of the embedding vector"
    )
    usage: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Usage statistics (tokens, etc.)"
    )