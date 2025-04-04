"""
API endpoints for workflow automation with n8n.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import APIKeyHeader

from app.core.dependencies import get_current_user
from app.core.api.responses import success_response, error_response
from app.core.errors.exceptions import ValidationException, PermissionDeniedException
from app.features.users.models import User
from app.features.workflows.service.workflow_service import WorkflowService, get_workflow_service
from app.features.workflows.schemas.workflow import (
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    OnboardingWorkflowRequest,
    NotificationRequest,
    BillingEventRequest,
    WorkflowStatusRequest,
    WorkflowStatusResponse,
    WorkflowWebhookRequest,
    WorkflowExecutionStatus,
)
from app.core.config.settings import settings

router = APIRouter()

# API key for webhooks
X_API_KEY = APIKeyHeader(name="X-API-Key")


def verify_webhook_api_key(api_key: str = Depends(X_API_KEY)):
    """
    Verify the API key for webhook endpoints.
    
    Args:
        api_key: API key from the request header
        
    Returns:
        The API key if valid
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if api_key != settings.N8N_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


@router.post("/onboarding", response_model=WorkflowExecutionResponse)
async def trigger_onboarding_workflow(
    request: OnboardingWorkflowRequest,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Trigger the user onboarding workflow.
    
    This workflow handles:
    - Welcome email
    - Email verification
    - Default team creation
    - Welcome notification
    """
    # Only admins can trigger onboarding for other users
    if request.user_id != current_user.id and not current_user.is_superuser:
        raise PermissionDeniedException(detail="Not authorized to trigger onboarding for other users")
    
    try:
        execution_id = await workflow_service.trigger_onboarding_workflow(
            user_id=request.user_id,
            email=request.email,
            name=request.name,
            verification_url=request.verification_url,
            token=request.token,
            team_name=request.team_name,
        )
        
        return success_response(
            data=WorkflowExecutionResponse(
                execution_id=execution_id,
                status=WorkflowExecutionStatus.PENDING,
                message="Onboarding workflow triggered successfully"
            ).dict(),
            message="Onboarding workflow started"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to trigger onboarding workflow: {str(e)}",
            code="WORKFLOW_ERROR"
        )


@router.post("/notifications", response_model=WorkflowExecutionResponse)
async def send_notification(
    request: NotificationRequest,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Send a notification through the notification system workflow.
    
    This can use multiple channels:
    - Email
    - In-app notifications
    - Push notifications
    - SMS
    """
    # Users can only send notifications to themselves unless they're admins
    if request.user_id != current_user.id and not current_user.is_superuser:
        raise PermissionDeniedException(detail="Not authorized to send notifications to other users")
    
    try:
        execution_id = await workflow_service.send_notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            channel=request.channel.value,
            important=request.important,
            email=request.email,
            phone=request.phone,
            additional_data=request.additional_data,
        )
        
        return success_response(
            data=WorkflowExecutionResponse(
                execution_id=execution_id,
                status=WorkflowExecutionStatus.PENDING,
                message="Notification workflow triggered successfully"
            ).dict(),
            message="Notification sent"
        )
    except ValueError as e:
        raise ValidationException(detail=str(e))
    except Exception as e:
        return error_response(
            message=f"Failed to send notification: {str(e)}",
            code="WORKFLOW_ERROR"
        )


@router.post("/billing/events", response_model=WorkflowExecutionResponse)
async def process_billing_event(
    request: BillingEventRequest,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Process a billing event through the billing workflow.
    
    This handles various billing events like:
    - Payment succeeded
    - Payment failed
    - Subscription created/updated/cancelled
    """
    # Only admins can process billing events
    if not current_user.is_superuser:
        raise PermissionDeniedException(detail="Not authorized to process billing events")
    
    try:
        execution_id = await workflow_service.process_billing_event(
            event_type=request.event_type,
            event_data=request.event_data,
        )
        
        return success_response(
            data=WorkflowExecutionResponse(
                execution_id=execution_id,
                status=WorkflowExecutionStatus.PENDING,
                message="Billing workflow triggered successfully"
            ).dict(),
            message="Billing event processing started"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to process billing event: {str(e)}",
            code="WORKFLOW_ERROR"
        )


@router.get("/status/{execution_id}", response_model=WorkflowStatusResponse)
async def check_workflow_status(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Check the status of a workflow execution.
    """
    try:
        status = await workflow_service.check_workflow_status(execution_id)
        
        return success_response(
            data=WorkflowStatusResponse(
                execution_id=status.execution_id,
                status=WorkflowExecutionStatus(status.status),
                started_at=status.started_at,
                finished_at=status.finished_at,
                data=status.data
            ).dict(),
            message="Workflow status retrieved"
        )
    except Exception as e:
        return error_response(
            message=f"Failed to check workflow status: {str(e)}",
            code="WORKFLOW_ERROR"
        )


@router.post("/webhooks/n8n", status_code=status.HTTP_200_OK)
async def n8n_webhook(
    request: Request,
    webhook_data: dict = Body(...),
    api_key: str = Depends(verify_webhook_api_key),
    workflow_service: WorkflowService = Depends(get_workflow_service),
):
    """
    Webhook endpoint for n8n callbacks.
    
    This endpoint is called by n8n to report workflow execution status and results.
    It's secured with an API key to prevent unauthorized access.
    """
    try:
        # Log webhook data for debugging
        webhook_request = WorkflowWebhookRequest(
            event=webhook_data.get("event", "unknown"),
            execution_id=webhook_data.get("executionId"),
            data=webhook_data.get("data", {}),
            timestamp=webhook_data.get("timestamp")
        )
        
        # Here you would typically process the webhook data and update your system accordingly
        # For example, update a database record with the workflow result
        
        return success_response(
            message="Webhook received successfully",
            data={"event": webhook_request.event, "execution_id": webhook_request.execution_id}
        )
    except Exception as e:
        return error_response(
            message=f"Failed to process webhook: {str(e)}",
            code="WEBHOOK_ERROR"
        )