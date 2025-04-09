from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request, BackgroundTasks
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
from app.features.ai.dependencies import check_ai_rate_limit, get_usage_tracker, get_async_ai_processor
from app.features.ai.service.usage_tracker import AIUsageTracker
from app.features.ai.service.async_processor import AsyncAIProcessor
from app.core.security import get_current_active_user
from app.features.users.models import User

router = APIRouter()


@router.post("/generate", response_model=AIResponse, dependencies=[Depends(check_ai_rate_limit)])
async def generate_from_prompt(
    request: PromptRequest,
    req: Request,
    ai_service: AIService = Depends(),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
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
        
        # Track usage
        token_estimate = len(request.prompt.split()) + len(content.split())
        await usage_tracker.track_request(
            user_id=current_user.id,
            tenant_id=getattr(req.state, "tenant_id", None),
            request_type="generate",
            model=params.get("model", "default"),
            tokens=token_estimate
        )
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used=request.workflow,
            usage={
                "estimated_tokens": token_estimate,
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(content.split())
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=AIResponse, dependencies=[Depends(check_ai_rate_limit)])
async def generate_from_chat(
    request: ChatRequest,
    req: Request,
    ai_service: AIService = Depends(),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
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
        
        # Track usage - estimate tokens from all messages
        input_tokens = sum(len(msg.content.split()) for msg in request.messages)
        output_tokens = len(content.split())
        total_tokens = input_tokens + output_tokens
        
        await usage_tracker.track_request(
            user_id=current_user.id,
            tenant_id=getattr(req.state, "tenant_id", None),
            request_type="chat",
            model=params.get("model", "default"),
            tokens=total_tokens
        )
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used=request.workflow,
            usage={
                "estimated_tokens": total_tokens,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code", response_model=AIResponse, dependencies=[Depends(check_ai_rate_limit)])
async def generate_code(
    request: CodeGenerationRequest,
    req: Request,
    ai_service: AIService = Depends(),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
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
        
        # Track usage
        input_tokens = len(prompt.split())
        output_tokens = len(content.split())
        total_tokens = input_tokens + output_tokens
        
        await usage_tracker.track_request(
            user_id=current_user.id,
            tenant_id=getattr(req.state, "tenant_id", None),
            request_type="code",
            model=params.get("model", "default"),
            tokens=total_tokens
        )
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used="code_generation",
            usage={
                "estimated_tokens": total_tokens,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content", response_model=AIResponse, dependencies=[Depends(check_ai_rate_limit)])
async def generate_marketing_content(
    request: ContentGenerationRequest,
    req: Request,
    ai_service: AIService = Depends(),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
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
        
        # Track usage
        input_tokens = len(prompt.split())
        output_tokens = len(content.split())
        total_tokens = input_tokens + output_tokens
        
        await usage_tracker.track_request(
            user_id=current_user.id,
            tenant_id=getattr(req.state, "tenant_id", None),
            request_type="content",
            model=params.get("model", "default"),
            tokens=total_tokens
        )
        
        # Return formatted response
        return AIResponse(
            content=content,
            model_used=request.model or "default",
            workflow_used="content_generation",
            usage={
                "estimated_tokens": total_tokens,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/embeddings", response_model=EmbeddingResponse, dependencies=[Depends(check_ai_rate_limit)])
async def generate_embeddings(
    request: EmbeddingRequest,
    req: Request,
    ai_service: AIService = Depends(),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate embeddings for the given text.
    """
    try:
        # Generate embeddings
        embedding = await ai_service.get_embeddings(request.text)
        
        # Track usage (embeddings typically use input tokens only)
        token_estimate = len(request.text.split())
        
        await usage_tracker.track_request(
            user_id=current_user.id,
            tenant_id=getattr(req.state, "tenant_id", None),
            request_type="embeddings",
            model=request.model or "default-embedding",
            tokens=token_estimate
        )
        
        # Return formatted response
        return EmbeddingResponse(
            embedding=embedding,
            model_used=request.model or "default-embedding",
            dimension=len(embedding),
            usage={
                "estimated_tokens": token_estimate,
                "input_tokens": token_estimate
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows", response_model=List[str], dependencies=[Depends(check_ai_rate_limit)])
async def list_available_workflows(
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available WilmerAI workflows.
    """
    # For now, return the hardcoded workflows we've defined
    return ["general", "code_generation", "content_generation"]


@router.get("/usage", response_model=Dict[str, Any], dependencies=[Depends(check_ai_rate_limit)])
async def get_usage_statistics(
    req: Request,
    timeframe: str = Query("day", description="Timeframe for usage statistics (day, week, month)"),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get AI usage statistics for the current user or tenant.
    """
    tenant_id = getattr(req.state, "tenant_id", None)
    
    # Get usage statistics
    stats = await usage_tracker.get_usage_stats(
        user_id=current_user.id,
        tenant_id=tenant_id,
        timeframe=timeframe
    )
    
    return stats


@router.post("/admin/limits/user/{user_id}", response_model=Dict[str, Any])
async def set_user_limits(
    user_id: int,
    limits: Dict[str, int] = Body(..., description="Rate limits to set for the user"),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Set custom rate limits for a user.
    Requires admin privileges.
    """
    # TODO: Check if current user is admin
    
    # Set limits
    await usage_tracker.set_user_limits(user_id, limits)
    
    return {
        "success": True,
        "message": f"Rate limits set for user {user_id}",
        "limits": limits
    }


@router.post("/admin/limits/tenant/{tenant_id}", response_model=Dict[str, Any])
async def set_tenant_limits(
    tenant_id: int,
    limits: Dict[str, int] = Body(..., description="Rate limits to set for the tenant"),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Set custom rate limits for a tenant.
    Requires admin privileges.
    """
    # TODO: Check if current user is admin
    
    # Set limits
    await usage_tracker.set_tenant_limits(tenant_id, limits)
    
    return {
        "success": True,
        "message": f"Rate limits set for tenant {tenant_id}",
        "limits": limits
    }


# Async processing endpoints

@router.post("/async/generate", response_model=Dict[str, Any], dependencies=[Depends(check_ai_rate_limit)])
async def async_generate(
    request: PromptRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    callback_url: Optional[str] = Query(None, description="URL to call when processing completes"),
    async_processor: AsyncAIProcessor = Depends(get_async_ai_processor),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit an asynchronous text generation task.
    Results will be available via the task status endpoint or delivered via webhook.
    """
    # Prepare parameters
    payload = request.dict()
    
    # Submit task
    result = await async_processor.submit_task(
        task_type="generate",
        payload=payload,
        callback_url=callback_url,
        user_id=current_user.id,
        tenant_id=getattr(req.state, "tenant_id", None),
        background_tasks=background_tasks
    )
    
    # Track task submission in usage stats
    await usage_tracker.track_request(
        user_id=current_user.id,
        tenant_id=getattr(req.state, "tenant_id", None),
        request_type="async_generate",
        model=request.model or "default",
        tokens=0  # We don't know token count yet
    )
    
    return result


@router.post("/async/chat", response_model=Dict[str, Any], dependencies=[Depends(check_ai_rate_limit)])
async def async_chat(
    request: ChatRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    callback_url: Optional[str] = Query(None, description="URL to call when processing completes"),
    async_processor: AsyncAIProcessor = Depends(get_async_ai_processor),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit an asynchronous chat task.
    Results will be available via the task status endpoint or delivered via webhook.
    """
    # Prepare parameters
    payload = request.dict()
    
    # Submit task
    result = await async_processor.submit_task(
        task_type="chat",
        payload=payload,
        callback_url=callback_url,
        user_id=current_user.id,
        tenant_id=getattr(req.state, "tenant_id", None),
        background_tasks=background_tasks
    )
    
    # Track task submission in usage stats
    await usage_tracker.track_request(
        user_id=current_user.id,
        tenant_id=getattr(req.state, "tenant_id", None),
        request_type="async_chat",
        model=request.model or "default",
        tokens=0  # We don't know token count yet
    )
    
    return result


@router.post("/async/code", response_model=Dict[str, Any], dependencies=[Depends(check_ai_rate_limit)])
async def async_code_generation(
    request: CodeGenerationRequest,
    req: Request,
    background_tasks: BackgroundTasks,
    callback_url: Optional[str] = Query(None, description="URL to call when processing completes"),
    async_processor: AsyncAIProcessor = Depends(get_async_ai_processor),
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker),
    current_user: User = Depends(get_current_active_user)
):
    """
    Submit an asynchronous code generation task.
    Results will be available via the task status endpoint or delivered via webhook.
    """
    # Prepare parameters
    payload = request.dict()
    
    # Submit task
    result = await async_processor.submit_task(
        task_type="code",
        payload=payload,
        callback_url=callback_url,
        user_id=current_user.id,
        tenant_id=getattr(req.state, "tenant_id", None),
        background_tasks=background_tasks
    )
    
    # Track task submission in usage stats
    await usage_tracker.track_request(
        user_id=current_user.id,
        tenant_id=getattr(req.state, "tenant_id", None),
        request_type="async_code",
        model=request.model or "default",
        tokens=0  # We don't know token count yet
    )
    
    return result


@router.get("/async/tasks/{task_id}", response_model=Dict[str, Any])
async def get_async_task_status(
    task_id: str,
    async_processor: AsyncAIProcessor = Depends(get_async_ai_processor),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the status of an asynchronous task.
    """
    return await async_processor.get_task_status(task_id)


@router.get("/async/tasks/{task_id}/result", response_model=Dict[str, Any])
async def get_async_task_result(
    task_id: str,
    async_processor: AsyncAIProcessor = Depends(get_async_ai_processor),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the result of a completed asynchronous task.
    """
    result = await async_processor.get_task_result(task_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task result not found or not completed"
        )
    
    return result


@router.get("/async/tasks", response_model=List[Dict[str, Any]])
async def list_async_tasks(
    limit: int = Query(100, description="Maximum number of tasks to return"),
    async_processor: AsyncAIProcessor = Depends(get_async_ai_processor),
    current_user: User = Depends(get_current_active_user)
):
    """
    List pending asynchronous tasks for the current user.
    """
    return await async_processor.list_pending_tasks(user_id=current_user.id, limit=limit)