"""
API endpoints for user onboarding.
"""

from typing import Dict, Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status, Request, Query

from app.core.api.responses import success_response, error_response
from app.features.users.models import User
from app.features.users.service import UserService, get_user_service
from app.features.onboarding.service import OnboardingService, get_onboarding_service
from app.core.dependencies import get_current_user

router = APIRouter()


@router.post("/start")
async def start_onboarding(
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: Optional[int] = None,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
    current_user: User = Depends(get_current_user),
):
    """
    Start the onboarding process for a user.
    
    This will generate a verification token and trigger the onboarding workflow.
    """
    # Use the current user if no user_id is provided
    if user_id is None:
        user_id = current_user.id
    elif user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to start onboarding for other users",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    # Get base URL from request
    base_url = str(request.base_url)
    
    # Start the onboarding flow
    result = await onboarding_service.start_onboarding_flow(
        user_id=user_id,
        background_tasks=background_tasks,
        base_url=base_url,
    )
    
    return success_response(
        data=result,
        message="Onboarding process started"
    )


@router.get("/verify")
async def verify_email(
    token: str = Query(...),
    email: str = Query(...),
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
):
    """
    Verify a user's email address with the provided token.
    """
    try:
        result = onboarding_service.verify_email(token=token, email=email)
        return success_response(
            data=result,
            message="Email verified successfully"
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            code="VERIFICATION_ERROR",
            status_code=e.status_code,
        )


@router.post("/create-team")
async def create_default_team(
    team_name: Optional[str] = None,
    user_id: Optional[int] = None,
    onboarding_service: OnboardingService = Depends(get_onboarding_service),
    current_user: User = Depends(get_current_user),
):
    """
    Create a default team for a user.
    
    This is typically part of the onboarding process but can be called separately.
    """
    # Use the current user if no user_id is provided
    if user_id is None:
        user_id = current_user.id
    elif user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to create teams for other users",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    # Create the team
    result = await onboarding_service.create_default_team(
        user_id=user_id,
        team_name=team_name,
    )
    
    return success_response(
        data=result,
        message="Default team created"
    )