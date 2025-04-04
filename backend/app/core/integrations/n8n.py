"""
n8n API client for the SaaS Factory Blueprint.

This module provides a client for interacting with the n8n API to:
1. Trigger workflows
2. Check workflow execution status
3. Manage workflows programmatically
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

import httpx
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


class WorkflowExecutionData(BaseModel):
    """Data required to execute a workflow."""
    workflow_id: str
    node_name: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowStatus(BaseModel):
    """Status of a workflow execution."""
    execution_id: str
    status: str
    data: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


class N8nAPIClient:
    """
    Client for interacting with the n8n API.
    """
    
    def __init__(self):
        """Initialize the n8n API client."""
        self.api_url = settings.N8N_API_URL
        self.api_key = settings.N8N_API_KEY
        self.headers = {
            "X-N8N-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to the n8n API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data
        """
        url = f"{self.api_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=self.headers,
                    timeout=30.0  # 30 second timeout
                )
                
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error with n8n API: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Error communicating with n8n: {str(e)}"
            )
        except httpx.RequestError as e:
            logger.error(f"Request error with n8n API: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"n8n service unavailable: {str(e)}"
            )
    
    async def trigger_workflow(self, execution_data: WorkflowExecutionData) -> str:
        """
        Trigger a workflow execution.
        
        Args:
            execution_data: Workflow execution data
            
        Returns:
            Execution ID
        """
        endpoint = f"workflows/{execution_data.workflow_id}/execute"
        payload = {}
        
        if execution_data.data:
            payload["data"] = execution_data.data
        
        if execution_data.node_name:
            payload["startNode"] = execution_data.node_name
        
        response = await self._make_request("POST", endpoint, data=payload)
        return response.get("executionId", "")
    
    async def get_workflow_status(self, execution_id: str) -> WorkflowStatus:
        """
        Get the status of a workflow execution.
        
        Args:
            execution_id: Workflow execution ID
            
        Returns:
            Workflow status
        """
        endpoint = f"executions/{execution_id}"
        response = await self._make_request("GET", endpoint)
        
        return WorkflowStatus(
            execution_id=execution_id,
            status=response.get("status", "unknown"),
            data=response.get("data", {}),
            started_at=response.get("startedAt"),
            finished_at=response.get("finishedAt")
        )
    
    async def get_workflow_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all workflows.
        
        Returns:
            List of workflows
        """
        endpoint = "workflows"
        response = await self._make_request("GET", endpoint)
        return response.get("data", [])
    
    async def get_workflow_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a workflow by name.
        
        Args:
            name: Workflow name
            
        Returns:
            Workflow data if found, None otherwise
        """
        workflows = await self.get_workflow_list()
        for workflow in workflows:
            if workflow.get("name") == name:
                return workflow
        return None


# Create a singleton instance
n8n_client = N8nAPIClient()


# Dependency for FastAPI
async def get_n8n_client() -> N8nAPIClient:
    """
    Dependency to get the n8n API client.
    
    Returns:
        n8n API client
    """
    return n8n_client