from fastapi import Depends, HTTPException, status, Request
from redis.asyncio import Redis

from app.core.db.redis import get_redis_connection
from app.features.ai.service.usage_tracker import AIUsageTracker
from app.features.ai.service.async_processor import AsyncAIProcessor, get_async_processor
from app.features.ai.service import AIService


async def get_usage_tracker(redis: Redis = Depends(get_redis_connection)) -> AIUsageTracker:
    """
    Dependency to provide an AIUsageTracker instance.
    
    Args:
        redis: Redis connection
        
    Returns:
        AIUsageTracker instance
    """
    return AIUsageTracker(redis_client=redis)


async def get_async_ai_processor(
    redis: Redis = Depends(get_redis_connection),
    ai_service: AIService = Depends()
) -> AsyncAIProcessor:
    """
    Dependency to provide an AsyncAIProcessor instance.
    
    Args:
        redis: Redis connection
        ai_service: AI service with LLM
        
    Returns:
        AsyncAIProcessor instance
    """
    return AsyncAIProcessor(redis_client=redis, llm=ai_service.llm)


async def check_ai_rate_limit(
    request: Request,
    usage_tracker: AIUsageTracker = Depends(get_usage_tracker)
) -> None:
    """
    Middleware-like dependency to check rate limits before handling AI requests.
    
    Args:
        request: The request object
        usage_tracker: The usage tracker
        
    Raises:
        HTTPException: If rate limits are exceeded
    """
    # Get user ID and tenant ID from request state
    user_id = getattr(request.state, "user_id", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    
    if not user_id:
        # Not a logged-in user, skip rate limiting
        return
    
    # Check rate limits
    allowed, limit_info = await usage_tracker.check_rate_limit(
        user_id=user_id,
        tenant_id=tenant_id
    )
    
    if not allowed:
        # Store rate limit info in request state for logging
        request.state.rate_limit_info = limit_info
        
        # Get the most restrictive limit that was exceeded
        limits = limit_info.get("limits", {})
        exceeded_limits = [
            f"{limit_name} (limit: {info['limit']}, current: {info['current']})"
            for limit_name, info in limits.items()
            if info.get("exceeded", False)
        ]
        
        detail = "Rate limit exceeded"
        if exceeded_limits:
            detail = f"Rate limit exceeded: {', '.join(exceeded_limits)}"
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": "60"}
        )