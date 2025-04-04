"""
Workflow service for n8n integration.

This service provides functionality to:
1. Trigger n8n workflows
2. Track workflow execution status
3. Handle webhook callbacks from n8n
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, HTTPException, status

from app.core.integrations.n8n import (
    N8nAPIClient,
    WorkflowExecutionData,
    WorkflowStatus,
    get_n8n_client,
)

logger = logging.getLogger(__name__)


class WorkflowService:
    """
    Service for managing workflows with n8n.
    """
    
    def __init__(self, n8n_client: N8nAPIClient):
        """
        Initialize the workflow service.
        
        Args:
            n8n_client: The n8n API client
        """
        self.n8n_client = n8n_client
    
    async def trigger_onboarding_workflow(
        self,
        user_id: int,
        email: str,
        name: str,
        verification_url: str,
        token: str,
        team_name: Optional[str] = None,
    ) -> str:
        """
        Trigger the user onboarding workflow.
        
        Args:
            user_id: User ID
            email: User email
            name: User name
            verification_url: Email verification URL
            token: Verification token
            team_name: Optional team name
            
        Returns:
            Execution ID
        """
        # Find the workflow by name
        workflow = await self.n8n_client.get_workflow_by_name("User Onboarding Workflow")
        if not workflow:
            logger.error("Onboarding workflow not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Onboarding workflow not configured"
            )
        
        # Prepare execution data
        execution_data = WorkflowExecutionData(
            workflow_id=workflow["id"],
            data={
                "event": "user_created",
                "user_id": user_id,
                "email": email,
                "name": name,
                "verification_url": verification_url,
                "token": token,
                "team_name": team_name
            }
        )
        
        # Trigger the workflow
        execution_id = await self.n8n_client.trigger_workflow(execution_data)
        logger.info(f"Triggered onboarding workflow for user {user_id}, execution ID: {execution_id}")
        
        return execution_id
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str,
        channel: str = "in-app",
        important: bool = False,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Send a notification through the notification system workflow.
        
        Args:
            user_id: User ID
            title: Notification title
            message: Notification message
            notification_type: Type of notification (e.g., "onboarding", "billing", "activity")
            channel: Notification channel ("email", "in-app", "push", "sms")
            important: Whether the notification is important
            email: User email (required for email channel)
            phone: User phone number (required for SMS channel)
            additional_data: Additional data to pass to the workflow
            
        Returns:
            Execution ID
        """
        # Validate inputs
        if channel == "email" and not email:
            raise ValueError("Email is required for email notifications")
        
        if channel == "sms" and not phone:
            raise ValueError("Phone number is required for SMS notifications")
        
        # Find the workflow by name
        workflow = await self.n8n_client.get_workflow_by_name("Notification System Workflow")
        if not workflow:
            logger.error("Notification workflow not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Notification workflow not configured"
            )
        
        # Prepare execution data
        data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "channel": channel,
            "important": important
        }
        
        if email:
            data["to"] = email
        
        if phone:
            data["to_number"] = phone
        
        if additional_data:
            data.update(additional_data)
        
        execution_data = WorkflowExecutionData(
            workflow_id=workflow["id"],
            data=data
        )
        
        # Trigger the workflow
        execution_id = await self.n8n_client.trigger_workflow(execution_data)
        logger.info(f"Triggered notification workflow for user {user_id}, execution ID: {execution_id}")
        
        return execution_id
    
    async def process_billing_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
    ) -> str:
        """
        Process a billing event through the billing workflow.
        
        Args:
            event_type: Type of billing event (e.g., "invoice.payment_succeeded")
            event_data: Event data from Stripe
            
        Returns:
            Execution ID
        """
        # Find the workflow by name
        workflow = await self.n8n_client.get_workflow_by_name("Billing Workflow")
        if not workflow:
            logger.error("Billing workflow not found")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Billing workflow not configured"
            )
        
        # Prepare execution data
        execution_data = WorkflowExecutionData(
            workflow_id=workflow["id"],
            data={
                "type": event_type,
                "data": {
                    "object": event_data
                },
                "id": event_data.get("id", "unknown")
            }
        )
        
        # Trigger the workflow
        execution_id = await self.n8n_client.trigger_workflow(execution_data)
        logger.info(f"Triggered billing workflow for event {event_type}, execution ID: {execution_id}")
        
        return execution_id
    
    async def check_workflow_status(self, execution_id: str) -> WorkflowStatus:
        """
        Check the status of a workflow execution.
        
        Args:
            execution_id: Workflow execution ID
            
        Returns:
            Workflow status
        """
        return await self.n8n_client.get_workflow_status(execution_id)


# Factory function for dependency injection
def get_workflow_service(
    n8n_client: N8nAPIClient = Depends(get_n8n_client),
) -> WorkflowService:
    """
    Dependency to get the workflow service.
    
    Args:
        n8n_client: The n8n API client
        
    Returns:
        Workflow service
    """
    return WorkflowService(n8n_client=n8n_client)