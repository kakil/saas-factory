"""
Schemas for workflow-related data.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class WorkflowType(str, Enum):
    """Types of workflows in the system."""
    ONBOARDING = "onboarding"
    NOTIFICATION = "notification"
    BILLING = "billing"
    CUSTOM = "custom"


class WorkflowExecutionStatus(str, Enum):
    """Possible statuses of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    IN_APP = "in-app"
    PUSH = "push"
    SMS = "sms"


class WorkflowExecutionRequest(BaseModel):
    """Base request for executing a workflow."""
    workflow_type: WorkflowType
    workflow_data: Dict[str, Any]


class WorkflowExecutionResponse(BaseModel):
    """Response for a workflow execution request."""
    execution_id: str
    status: WorkflowExecutionStatus
    message: str


class OnboardingWorkflowRequest(BaseModel):
    """Request for the onboarding workflow."""
    user_id: int
    email: str
    name: str
    verification_url: str
    token: str
    team_name: Optional[str] = None


class NotificationRequest(BaseModel):
    """Request for sending a notification."""
    user_id: int
    title: str
    message: str
    notification_type: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    important: bool = False
    email: Optional[str] = None
    phone: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class BillingEventRequest(BaseModel):
    """Request for processing a billing event."""
    event_type: str
    event_data: Dict[str, Any]


class WorkflowStatusRequest(BaseModel):
    """Request for checking a workflow status."""
    execution_id: str


class WorkflowStatusResponse(BaseModel):
    """Response with workflow execution status."""
    execution_id: str
    status: WorkflowExecutionStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    data: Optional[Dict[str, Any]] = None


class WorkflowWebhookRequest(BaseModel):
    """Request body for workflow webhooks."""
    event: str = Field(..., description="Event type that triggered the workflow")
    execution_id: Optional[str] = Field(None, description="n8n execution ID")
    data: Dict[str, Any] = Field({}, description="Webhook payload data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")