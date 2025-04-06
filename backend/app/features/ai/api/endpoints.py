from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Dict, Any, Optional

from app.features.ai.schemas import (
    PromptRequest,
    ChatRequest,
    CodeGenerationRequest,
    ContentGenerationRequest,
    EmbeddingRequest,
    AIResponse,
    EmbeddingResponse,
    Message
)
from app.features.ai.service import AIService
from app.core.security import get_current_active_user
from app.features.users.models import User

router = APIRouter()


@router.post("/generate", response_model=AIResponse)
async def generate_from_prompt(
    request: PromptRequest,
    ai_service: AIService = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate AI content from a text prompt.
    """
    try:
        # Prepare parameters from request
        params = {
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "workflow": request.workflow,
            "system_prompt": request.system_prompt
        }
        
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Generate content
        content = await ai_service.generate_content(request.prompt, **params)
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used=request.workflow,
            usage=None  # Usage tracking to be implemented
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=AIResponse)
async def generate_from_chat(
    request: ChatRequest,
    ai_service: AIService = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate AI content from a chat conversation.
    """
    try:
        # Prepare parameters from request
        params = {
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "workflow": request.workflow
        }
        
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Generate content using the LLM
        # Pass messages directly to generate_text
        content = await ai_service.llm.generate_text(request.messages, **params)
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used=request.workflow,
            usage=None  # Usage tracking to be implemented
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code", response_model=AIResponse)
async def generate_code(
    request: CodeGenerationRequest,
    ai_service: AIService = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate code based on a description.
    """
    try:
        # Build the prompt
        prompt = f"Generate {request.language or ''} code for: {request.prompt}"
        
        if request.code_context:
            prompt += f"\n\nContext or existing code:\n```\n{request.code_context}\n```"
        
        # Prepare parameters
        params = {
            "model": request.model,
            "temperature": request.temperature,
            "workflow": "code_generation"
        }
        
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Generate code
        content = await ai_service.generate_code(prompt, **params)
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used="code_generation",
            usage=None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content", response_model=AIResponse)
async def generate_marketing_content(
    request: ContentGenerationRequest,
    ai_service: AIService = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate marketing content based on topic and parameters.
    """
    try:
        # Build detailed prompt
        prompt = f"Create a {request.content_type} about: {request.topic}"
        
        if request.tone:
            prompt += f"\nTone: {request.tone}"
        
        if request.word_count:
            prompt += f"\nTarget word count: {request.word_count}"
        
        if request.target_audience:
            prompt += f"\nTarget audience: {request.target_audience}"
        
        # Prepare parameters
        params = {
            "model": request.model,
            "temperature": request.temperature,
            "workflow": "content_generation"
        }
        
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Generate marketing content
        content = await ai_service.generate_marketing_content(prompt, **params)
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used="content_generation",
            usage=None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    ai_service: AIService = Depends(),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate embeddings for the given text.
    """
    try:
        # Generate embeddings
        embedding = await ai_service.get_embeddings(request.text)
        
        # Return formatted response
        return EmbeddingResponse(
            embedding=embedding,
            model_used=request.model or "default-embedding",
            dimension=len(embedding),
            usage=None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows", response_model=List[str])
async def list_available_workflows(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available WilmerAI workflows.
    """
    # For now, return the hardcoded workflows we've defined
    return ["general", "code_generation", "content_generation"]