import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

import redis.asyncio as redis
from fastapi import HTTPException, status


class AIUsageTracker:
    """
    Track and manage AI usage metrics and rate limits.
    
    This class handles:
    - Request rate limiting
    - Token usage tracking
    - Usage statistics for billing and monitoring
    - Per-tenant and per-user usage metrics
    """
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize the usage tracker.
        
        Args:
            redis_client: Redis client for storing usage data
        """
        self.redis = redis_client
        
        # Default rate limits (can be overridden per tenant/plan)
        self.default_limits = {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "requests_per_day": 1000,
            "tokens_per_day": 100000,
        }
        
        # Key prefixes for Redis
        self.REQUEST_COUNT_PREFIX = "ai:usage:requests:"
        self.TOKEN_COUNT_PREFIX = "ai:usage:tokens:"
        self.RATE_LIMIT_PREFIX = "ai:rate_limit:"
        self.USER_LIMITS_PREFIX = "ai:user_limits:"
        self.TENANT_LIMITS_PREFIX = "ai:tenant_limits:"
    
    async def track_request(
        self, 
        user_id: int, 
        tenant_id: Optional[int], 
        request_type: str, 
        model: str, 
        tokens: Optional[int] = None
    ) -> None:
        """
        Track an AI request in usage metrics.
        
        Args:
            user_id: The ID of the user making the request
            tenant_id: The tenant ID (organization) if applicable
            request_type: Type of request (chat, completion, embedding, etc.)
            model: The AI model used for the request
            tokens: Number of tokens used (if known)
        """
        timestamp = datetime.utcnow()
        minute_key = timestamp.strftime("%Y-%m-%d:%H:%M")
        hour_key = timestamp.strftime("%Y-%m-%d:%H")
        day_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")
        
        # Prepare request data
        request_data = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "request_type": request_type,
            "model": model,
            "tokens": tokens
        }
        
        # Update request counts (for rate limiting)
        pipeline = self.redis.pipeline()
        
        # Per-user request counts
        user_minute_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:minute:{minute_key}"
        user_hour_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:hour:{hour_key}"
        user_day_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:day:{day_key}"
        
        pipeline.incr(user_minute_key)
        pipeline.expire(user_minute_key, 120)  # Keep for 2 minutes
        
        pipeline.incr(user_hour_key)
        pipeline.expire(user_hour_key, 3600 + 60)  # Keep for 1 hour + 1 minute
        
        pipeline.incr(user_day_key)
        pipeline.expire(user_day_key, 86400 + 60)  # Keep for 1 day + 1 minute
        
        # If tenant_id is provided, track tenant usage as well
        if tenant_id:
            tenant_minute_key = f"{self.REQUEST_COUNT_PREFIX}tenant:{tenant_id}:minute:{minute_key}"
            tenant_hour_key = f"{self.REQUEST_COUNT_PREFIX}tenant:{tenant_id}:hour:{hour_key}"
            tenant_day_key = f"{self.REQUEST_COUNT_PREFIX}tenant:{tenant_id}:day:{day_key}"
            
            pipeline.incr(tenant_minute_key)
            pipeline.expire(tenant_minute_key, 120)
            
            pipeline.incr(tenant_hour_key)
            pipeline.expire(tenant_hour_key, 3600 + 60)
            
            pipeline.incr(tenant_day_key)
            pipeline.expire(tenant_day_key, 86400 + 60)
        
        # Track token usage if provided
        if tokens:
            user_tokens_day_key = f"{self.TOKEN_COUNT_PREFIX}user:{user_id}:day:{day_key}"
            user_tokens_month_key = f"{self.TOKEN_COUNT_PREFIX}user:{user_id}:month:{month_key}"
            
            pipeline.incrby(user_tokens_day_key, tokens)
            pipeline.expire(user_tokens_day_key, 86400 + 60)
            
            pipeline.incrby(user_tokens_month_key, tokens)
            pipeline.expire(user_tokens_month_key, 30 * 86400 + 60)  # 30 days + 1 minute
            
            if tenant_id:
                tenant_tokens_day_key = f"{self.TOKEN_COUNT_PREFIX}tenant:{tenant_id}:day:{day_key}"
                tenant_tokens_month_key = f"{self.TOKEN_COUNT_PREFIX}tenant:{tenant_id}:month:{month_key}"
                
                pipeline.incrby(tenant_tokens_day_key, tokens)
                pipeline.expire(tenant_tokens_day_key, 86400 + 60)
                
                pipeline.incrby(tenant_tokens_month_key, tokens)
                pipeline.expire(tenant_tokens_month_key, 30 * 86400 + 60)
        
        # Store detailed request logs (most recent 1000 per user)
        user_log_key = f"ai:logs:user:{user_id}"
        log_entry = json.dumps(request_data)
        
        pipeline.lpush(user_log_key, log_entry)
        pipeline.ltrim(user_log_key, 0, 999)  # Keep only most recent 1000
        pipeline.expire(user_log_key, 30 * 86400)  # 30 days
        
        # Execute all Redis commands
        await pipeline.execute()
    
    async def check_rate_limit(
        self, 
        user_id: int, 
        tenant_id: Optional[int] = None, 
        request_type: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if a user has exceeded their rate limits.
        
        Args:
            user_id: The ID of the user making the request
            tenant_id: The tenant ID (organization) if applicable
            request_type: Type of request (optional, for request-specific limits)
            
        Returns:
            Tuple containing:
            - Boolean indicating if limit is exceeded (True = allowed, False = exceeded)
            - Dict with limit details (current usage, limits, etc.)
        """
        now = datetime.utcnow()
        minute_key = now.strftime("%Y-%m-%d:%H:%M")
        hour_key = now.strftime("%Y-%m-%d:%H")
        day_key = now.strftime("%Y-%m-%d")
        
        # Get custom limits if any
        user_limits = await self._get_user_limits(user_id)
        if tenant_id:
            tenant_limits = await self._get_tenant_limits(tenant_id)
            # Merge, favoring the more permissive limits
            limits = {
                k: max(user_limits.get(k, 0), tenant_limits.get(k, 0)) 
                for k in set(user_limits) | set(tenant_limits)
            }
            # If a limit isn't in either, use default
            for k, v in self.default_limits.items():
                if k not in limits or limits[k] == 0:
                    limits[k] = v
        else:
            # Use user limits with fallback to defaults
            limits = {**self.default_limits, **user_limits}
        
        # Check current usage
        pipeline = self.redis.pipeline()
        
        # Request count keys
        user_minute_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:minute:{minute_key}"
        user_hour_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:hour:{hour_key}"
        user_day_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:day:{day_key}"
        
        # Token count key
        user_tokens_day_key = f"{self.TOKEN_COUNT_PREFIX}user:{user_id}:day:{day_key}"
        
        # Get current usage
        pipeline.get(user_minute_key)
        pipeline.get(user_hour_key)
        pipeline.get(user_day_key)
        pipeline.get(user_tokens_day_key)
        
        # Execute and process results
        results = await pipeline.execute()
        minute_count = int(results[0] or 0)
        hour_count = int(results[1] or 0)
        day_count = int(results[2] or 0)
        tokens_day = int(results[3] or 0)
        
        # Check against limits
        usage = {
            "requests_per_minute": minute_count,
            "requests_per_hour": hour_count,
            "requests_per_day": day_count,
            "tokens_per_day": tokens_day,
        }
        
        limit_exceeded = False
        limit_info = {}
        
        for limit_name, limit_value in limits.items():
            if limit_name in usage and usage[limit_name] >= limit_value:
                limit_exceeded = True
                limit_info[limit_name] = {
                    "current": usage[limit_name],
                    "limit": limit_value,
                    "exceeded": True
                }
            else:
                limit_info[limit_name] = {
                    "current": usage.get(limit_name, 0),
                    "limit": limit_value,
                    "exceeded": False
                }
        
        return (not limit_exceeded, {
            "allowed": not limit_exceeded,
            "limits": limit_info,
            "user_id": user_id,
            "tenant_id": tenant_id
        })
    
    async def get_usage_stats(
        self, 
        user_id: Optional[int] = None, 
        tenant_id: Optional[int] = None,
        timeframe: str = "day"
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a user or tenant.
        
        Args:
            user_id: The ID of the user to get stats for (optional)
            tenant_id: The tenant ID to get stats for (optional)
            timeframe: The timeframe to get stats for ('day', 'week', 'month')
            
        Returns:
            Dict with usage statistics
        """
        now = datetime.utcnow()
        
        # Calculate date ranges
        if timeframe == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            date_keys = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
                          for i in range(1)]
            
        elif timeframe == "week":
            start_date = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0)
            date_keys = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
                          for i in range(7)]
            
        elif timeframe == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            days_in_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            days_in_month = days_in_month.day
            date_keys = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") 
                          for i in range(days_in_month)]
        else:
            date_keys = [now.strftime("%Y-%m-%d")]
        
        # Prepare Redis keys
        pipeline = self.redis.pipeline()
        
        # For request count stats
        if user_id:
            for date_key in date_keys:
                user_day_key = f"{self.REQUEST_COUNT_PREFIX}user:{user_id}:day:{date_key}"
                user_tokens_day_key = f"{self.TOKEN_COUNT_PREFIX}user:{user_id}:day:{date_key}"
                pipeline.get(user_day_key)
                pipeline.get(user_tokens_day_key)
        
        if tenant_id:
            for date_key in date_keys:
                tenant_day_key = f"{self.REQUEST_COUNT_PREFIX}tenant:{tenant_id}:day:{date_key}"
                tenant_tokens_day_key = f"{self.TOKEN_COUNT_PREFIX}tenant:{tenant_id}:day:{date_key}"
                pipeline.get(tenant_day_key)
                pipeline.get(tenant_tokens_day_key)
        
        # Execute and collect results
        results = await pipeline.execute()
        
        # Process results
        stats = {
            "timeframe": timeframe,
            "period_start": start_date.isoformat(),
            "period_end": now.isoformat(),
        }
        
        if user_id:
            user_stats = {
                "total_requests": 0,
                "total_tokens": 0,
                "daily_breakdown": {}
            }
            
            for i, date_key in enumerate(date_keys):
                req_count = int(results[i*2] or 0)
                token_count = int(results[i*2+1] or 0)
                
                user_stats["total_requests"] += req_count
                user_stats["total_tokens"] += token_count
                user_stats["daily_breakdown"][date_key] = {
                    "requests": req_count,
                    "tokens": token_count
                }
            
            stats["user"] = {
                "id": user_id,
                "stats": user_stats
            }
        
        if tenant_id:
            offset = len(date_keys) * 2 if user_id else 0
            tenant_stats = {
                "total_requests": 0,
                "total_tokens": 0,
                "daily_breakdown": {}
            }
            
            for i, date_key in enumerate(date_keys):
                req_count = int(results[offset + i*2] or 0)
                token_count = int(results[offset + i*2+1] or 0)
                
                tenant_stats["total_requests"] += req_count
                tenant_stats["total_tokens"] += token_count
                tenant_stats["daily_breakdown"][date_key] = {
                    "requests": req_count,
                    "tokens": token_count
                }
            
            stats["tenant"] = {
                "id": tenant_id,
                "stats": tenant_stats
            }
        
        return stats
    
    async def _get_user_limits(self, user_id: int) -> Dict[str, int]:
        """
        Get custom limits for a user (if any).
        
        Args:
            user_id: The user ID
            
        Returns:
            Dict with custom limits (empty if none)
        """
        user_limits_key = f"{self.USER_LIMITS_PREFIX}{user_id}"
        limits_json = await self.redis.get(user_limits_key)
        
        if limits_json:
            try:
                return json.loads(limits_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    async def _get_tenant_limits(self, tenant_id: int) -> Dict[str, int]:
        """
        Get custom limits for a tenant (if any).
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            Dict with custom limits (empty if none)
        """
        tenant_limits_key = f"{self.TENANT_LIMITS_PREFIX}{tenant_id}"
        limits_json = await self.redis.get(tenant_limits_key)
        
        if limits_json:
            try:
                return json.loads(limits_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    async def set_user_limits(self, user_id: int, limits: Dict[str, int]) -> None:
        """
        Set custom limits for a user.
        
        Args:
            user_id: The user ID
            limits: Dict with custom limits
        """
        user_limits_key = f"{self.USER_LIMITS_PREFIX}{user_id}"
        await self.redis.set(user_limits_key, json.dumps(limits))
    
    async def set_tenant_limits(self, tenant_id: int, limits: Dict[str, int]) -> None:
        """
        Set custom limits for a tenant.
        
        Args:
            tenant_id: The tenant ID
            limits: Dict with custom limits
        """
        tenant_limits_key = f"{self.TENANT_LIMITS_PREFIX}{tenant_id}"
        await self.redis.set(tenant_limits_key, json.dumps(limits))