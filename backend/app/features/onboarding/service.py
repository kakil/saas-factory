"""
Onboarding service for user registration and welcome flow.
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config.settings import settings
from app.core.db.session import get_db
from app.core.utilities.email import EmailService, get_email_service
from app.features.users.models import User
from app.features.users.repository import UserRepository, get_user_repository
from app.features.users.service import UserService, get_user_service
from app.features.teams.service import TeamService, get_team_service
from app.features.workflows.service.workflow_service import WorkflowService, get_workflow_service

logger = logging.getLogger(__name__)


class OnboardingService:
    """
    Service for handling user onboarding processes.
    """
    
    def __init__(
        self,
        email_service: EmailService,
        user_service: UserService,
        team_service: TeamService,
        user_repository: UserRepository,
        workflow_service: WorkflowService,
        db: Session,
    ):
        """
        Initialize the onboarding service.
        
        Args:
            email_service: Email service for sending emails
            user_service: User service for user management
            team_service: Team service for team management
            user_repository: User repository for data access
            workflow_service: n8n workflow service
            db: Database session
        """
        self.email_service = email_service
        self.user_service = user_service
        self.team_service = team_service
        self.user_repository = user_repository
        self.workflow_service = workflow_service
        self.db = db
    
    async def start_onboarding_flow(
        self,
        user_id: int,
        background_tasks: BackgroundTasks,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start the onboarding flow for a user.
        
        Args:
            user_id: User ID
            background_tasks: FastAPI background tasks
            base_url: Base URL for links
            
        Returns:
            A dictionary with the result
        """
        # Get the user
        user = self.user_repository.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate verification token
        token = user.generate_verification_token()
        self.db.commit()
        
        # Create verification URL
        if not base_url:
            base_url = f"{settings.SERVER_HOST}:{settings.SERVER_PORT}"
        
        verification_url = urljoin(
            base_url,
            f"/api/v1/onboarding/verify?token={token}&email={user.email}"
        )
        
        # Try to trigger n8n workflow first
        try:
            # Trigger the workflow using n8n
            execution_id = await self.workflow_service.trigger_onboarding_workflow(
                user_id=user.id,
                email=user.email,
                name=user.name or "",
                verification_url=verification_url,
                token=token,
                team_name=user.organization.name if user.organization else None,
            )
            
            logger.info(f"Triggered onboarding workflow for user {user.id}, execution ID: {execution_id}")
            return {
                "success": True,
                "message": "Onboarding flow started",
                "execution_id": execution_id,
                "verification_url": verification_url,
            }
            
        except Exception as e:
            logger.warning(f"Failed to trigger n8n workflow: {str(e)}. Falling back to direct email.")
            # Fall back to sending email directly
            return await self._send_verification_email_fallback(
                user=user,
                verification_url=verification_url,
                background_tasks=background_tasks,
            )
    
    async def _send_verification_email_fallback(
        self,
        user: User,
        verification_url: str,
        background_tasks: BackgroundTasks,
    ) -> Dict[str, Any]:
        """
        Fallback method to send verification email directly.
        
        Args:
            user: User to send email to
            verification_url: Verification URL
            background_tasks: FastAPI background tasks
            
        Returns:
            A dictionary with the result
        """
        # Email template
        template = """
        <html>
        <body>
            <h1>Welcome to SaaS Factory!</h1>
            <p>Hi {{ name }},</p>
            <p>Thanks for signing up. Please verify your email address by clicking the link below:</p>
            <p><a href="{{ verification_url }}">Verify my email</a></p>
            <p>This link is valid for 24 hours.</p>
            <p>If you didn't sign up for an account, please ignore this email.</p>
            <p>Best regards,<br>The SaaS Factory Team</p>
        </body>
        </html>
        """
        
        await self.email_service.send_template_email_async(
            background_tasks=background_tasks,
            to_email=user.email,
            subject="Welcome to SaaS Factory - Verify Your Email",
            template_str=template,
            context={
                "name": user.name or "there",
                "verification_url": verification_url,
            },
            is_html=True,
        )
        
        logger.info(f"Sent verification email directly to user {user.id}")
        
        return {
            "success": True,
            "message": "Verification email sent",
            "verification_url": verification_url,
        }
    
    def verify_email(self, token: str, email: str) -> Dict[str, Any]:
        """
        Verify a user's email.
        
        Args:
            token: Verification token
            email: User's email
            
        Returns:
            A dictionary with the result
        """
        # Get the user
        user = self.user_repository.get_by_email(email=email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify the token
        if not user.verify_email(token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Save the changes
        self.db.commit()
        
        return {
            "success": True,
            "message": "Email verified successfully"
        }
    
    async def create_default_team(
        self,
        user_id: int,
        team_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a default team for a user.
        
        Args:
            user_id: User ID
            team_name: Optional team name
            
        Returns:
            A dictionary with the result
        """
        # Get the user
        user = self.user_repository.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Default team name
        if not team_name:
            team_name = f"{user.name or 'User'}'s Team"
        
        # Create the team
        team = self.team_service.create_team(
            name=team_name,
            description="Default team created during onboarding",
            organization_id=user.organization_id,
        )
        
        # Add the user to the team
        self.team_service.add_user_to_team(team_id=team.id, user_id=user.id)
        
        return {
            "success": True,
            "message": "Default team created",
            "team": {
                "id": team.id,
                "name": team.name,
            }
        }


def get_onboarding_service(
    email_service: EmailService = Depends(get_email_service),
    user_service: UserService = Depends(get_user_service),
    team_service: TeamService = Depends(get_team_service),
    user_repository: UserRepository = Depends(get_user_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    db: Session = Depends(get_db),
) -> OnboardingService:
    """
    Get an OnboardingService instance.
    
    Args:
        email_service: Email service
        user_service: User service
        team_service: Team service
        user_repository: User repository
        workflow_service: Workflow service
        db: Database session
        
    Returns:
        An OnboardingService instance
    """
    return OnboardingService(
        email_service=email_service,
        user_service=user_service,
        team_service=team_service,
        user_repository=user_repository,
        workflow_service=workflow_service,
        db=db,
    )