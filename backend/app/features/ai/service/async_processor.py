import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Callable, Awaitable, List

import httpx
from redis.asyncio import Redis
from fastapi import BackgroundTasks

from app.features.ai.service.base_llm import BaseLLM
from app.core.config.settings import settings


class AsyncAIProcessor:
    """
    Handle asynchronous AI processing with webhooks.
    
    This class allows for long-running AI tasks to be processed asynchronously,
    with results delivered via webhook when complete.
    """
    
    def __init__(self, redis_client: Redis, llm: BaseLLM):
        """
        Initialize the async processor.
        
        Args:
            redis_client: Redis client for job tracking
            llm: The LLM implementation to use
        """
        self.redis = redis_client
        self.llm = llm
        self.task_prefix = "ai:async_task:"
        self.result_prefix = "ai:async_result:"
        # How long to keep results in Redis
        self.result_ttl = 3600  # 1 hour
    
    async def submit_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        callback_url: Optional[str] = None,
        user_id: Optional[int] = None,
        tenant_id: Optional[int] = None,
        background_tasks: BackgroundTasks = None
    ) -> Dict[str, Any]:
        """
        Submit an async AI task.
        
        Args:
            task_type: Type of AI task (generate, chat, code, etc.)
            payload: Task parameters
            callback_url: URL to call when task completes
            user_id: ID of the user submitting the task
            tenant_id: ID of the tenant
            background_tasks: FastAPI BackgroundTasks for immediate return
            
        Returns:
            Dict with task ID and status
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Create task data
        task_data = {
            "id": task_id,
            "type": task_type,
            "payload": payload,
            "callback_url": callback_url,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "status": "pending",
            "created_at": asyncio.get_event_loop().time(),
        }
        
        # Store task in Redis
        task_key = f"{self.task_prefix}{task_id}"
        await self.redis.set(task_key, json.dumps(task_data))
        await self.redis.expire(task_key, 86400)  # 24 hour expiry
        
        # Add to processing queue
        await self.redis.lpush("ai:task_queue", task_id)
        
        # Start processing in background if background_tasks provided
        if background_tasks:
            background_tasks.add_task(self._process_task, task_id)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "message": "Task submitted for asynchronous processing"
        }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of an async task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Dict with task status and details
        """
        # Check if task exists
        task_key = f"{self.task_prefix}{task_id}"
        task_data = await self.redis.get(task_key)
        
        if not task_data:
            return {
                "task_id": task_id,
                "status": "not_found",
                "message": "Task not found"
            }
        
        # Parse task data
        task = json.loads(task_data)
        
        # Check if result exists
        result_key = f"{self.result_prefix}{task_id}"
        result_data = await self.redis.get(result_key)
        
        if result_data:
            result = json.loads(result_data)
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "created_at": task.get("created_at"),
                "completed_at": result.get("timestamp")
            }
        
        return {
            "task_id": task_id,
            "status": task.get("status", "unknown"),
            "message": f"Task is {task.get('status', 'unknown')}",
            "created_at": task.get("created_at")
        }
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a completed task.
        
        Args:
            task_id: The task ID
            
        Returns:
            Dict with task result or None if not completed
        """
        result_key = f"{self.result_prefix}{task_id}"
        result_data = await self.redis.get(result_key)
        
        if result_data:
            return json.loads(result_data)
        
        return None
    
    async def list_pending_tasks(
        self, 
        user_id: Optional[int] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List pending tasks for a user.
        
        Args:
            user_id: The user ID (optional)
            limit: Maximum number of tasks to return
            
        Returns:
            List of pending tasks
        """
        # Get task IDs from queue
        task_ids = await self.redis.lrange("ai:task_queue", 0, limit - 1)
        
        tasks = []
        for task_id in task_ids:
            task_key = f"{self.task_prefix}{task_id.decode('utf-8')}"
            task_data = await self.redis.get(task_key)
            
            if task_data:
                task = json.loads(task_data)
                
                # Filter by user if specified
                if user_id is None or task.get("user_id") == user_id:
                    tasks.append(task)
                    
                    # Stop if we've reached the limit
                    if len(tasks) >= limit:
                        break
        
        return tasks
    
    async def _process_task(self, task_id: str) -> None:
        """
        Process an async task.
        
        Args:
            task_id: The task ID
        """
        # Get task data
        task_key = f"{self.task_prefix}{task_id}"
        task_data = await self.redis.get(task_key)
        
        if not task_data:
            return
        
        task = json.loads(task_data)
        
        # Update status to processing
        task["status"] = "processing"
        await self.redis.set(task_key, json.dumps(task))
        
        # Get task details
        task_type = task["type"]
        payload = task["payload"]
        callback_url = task.get("callback_url")
        
        try:
            # Process based on task type
            result = await self._execute_ai_task(task_type, payload)
            
            # Store result
            result_data = {
                "task_id": task_id,
                "result": result,
                "success": True,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            result_key = f"{self.result_prefix}{task_id}"
            await self.redis.set(result_key, json.dumps(result_data))
            await self.redis.expire(result_key, self.result_ttl)
            
            # Update task status
            task["status"] = "completed"
            await self.redis.set(task_key, json.dumps(task))
            
            # Call webhook if specified
            if callback_url:
                await self._send_webhook(callback_url, result_data)
                
        except Exception as e:
            # Handle error
            error_data = {
                "task_id": task_id,
                "error": str(e),
                "success": False,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            # Store error
            result_key = f"{self.result_prefix}{task_id}"
            await self.redis.set(result_key, json.dumps(error_data))
            await self.redis.expire(result_key, self.result_ttl)
            
            # Update task status
            task["status"] = "failed"
            task["error"] = str(e)
            await self.redis.set(task_key, json.dumps(task))
            
            # Call webhook with error if specified
            if callback_url:
                await self._send_webhook(callback_url, error_data)
    
    async def _execute_ai_task(self, task_type: str, payload: Dict[str, Any]) -> Any:
        """
        Execute an AI task based on type.
        
        Args:
            task_type: Type of AI task
            payload: Task parameters
            
        Returns:
            Result of the AI task
        """
        if task_type == "generate":
            prompt = payload.get("prompt", "")
            return await self.llm.generate_text(prompt, **payload)
            
        elif task_type == "chat":
            messages = payload.get("messages", [])
            return await self.llm.generate_text(messages, **payload)
            
        elif task_type == "code":
            prompt = payload.get("prompt", "")
            language = payload.get("language")
            
            # Build full prompt
            full_prompt = f"Generate {language or ''} code for: {prompt}"
            
            if "code_context" in payload:
                full_prompt += f"\n\nContext or existing code:\n```\n{payload['code_context']}\n```"
                
            # Set code generation workflow
            params = {**payload, "workflow": "code_generation"}
            
            return await self.llm.generate_text(full_prompt, **params)
            
        elif task_type == "embeddings":
            text = payload.get("text", "")
            return await self.llm.generate_embeddings(text)
            
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _send_webhook(self, url: str, data: Dict[str, Any]) -> None:
        """
        Send a webhook with task results.
        
        Args:
            url: The webhook URL
            data: The data to send
        """
        try:
            # Sign webhook payload if secret is configured
            headers = {
                "Content-Type": "application/json",
                "User-Agent": f"SaasFactory-AI-Webhooks/{settings.PROJECT_NAME}",
                "X-SaasFactory-Event": "ai.task.completed"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(url, json=data, headers=headers)
                
        except Exception as e:
            # Log webhook failure but don't fail the task
            print(f"Webhook delivery failed: {str(e)}")


async def get_async_processor(
    redis_client: Redis,
    llm: BaseLLM
) -> AsyncAIProcessor:
    """
    Get an AsyncAIProcessor instance.
    
    Args:
        redis_client: Redis client
        llm: LLM implementation
        
    Returns:
        AsyncAIProcessor instance
    """
    return AsyncAIProcessor(redis_client=redis_client, llm=llm)