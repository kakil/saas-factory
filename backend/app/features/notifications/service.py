"""
Notification service for managing notifications.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from fastapi import BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.features.notifications.models import Notification, NotificationPreference, NotificationType, NotificationChannel
from app.features.notifications.repository import (
    NotificationRepository, NotificationPreferenceRepository,
    get_notification_repository, get_notification_preference_repository
)
from app.features.notifications.schemas import (
    NotificationCreate, NotificationUpdate, NotificationPreferenceCreate,
    NotificationPreferenceUpdate, BatchNotificationCreate
)
from app.features.workflows.service.workflow_service import WorkflowService, get_workflow_service
from app.core.utilities.email import EmailService, get_email_service

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for notification operations.
    """
    
    def __init__(
        self,
        notification_repository: NotificationRepository,
        preference_repository: NotificationPreferenceRepository,
        workflow_service: WorkflowService,
        email_service: EmailService,
        db: Session,
    ):
        """
        Initialize the notification service.
        
        Args:
            notification_repository: Repository for notification operations
            preference_repository: Repository for notification preference operations
            workflow_service: Service for workflow operations
            email_service: Service for email operations
            db: Database session
        """
        self.notification_repository = notification_repository
        self.preference_repository = preference_repository
        self.workflow_service = workflow_service
        self.email_service = email_service
        self.db = db
    
    async def create_notification(
        self,
        *,
        notification_in: NotificationCreate,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> Notification:
        """
        Create a notification.
        
        Args:
            notification_in: Notification data
            background_tasks: Background tasks for async processing
            
        Returns:
            Created notification
        """
        # Check user notification preferences
        user_preference = self.preference_repository.get_by_type(
            user_id=notification_in.user_id,
            notification_type=notification_in.notification_type,
        )
        
        # If preference exists and notifications are disabled, or channel is not enabled
        if user_preference:
            if not user_preference.enabled:
                logger.info(f"Notifications disabled for user {notification_in.user_id} and type {notification_in.notification_type}")
                return None
                
            if notification_in.channel not in user_preference.channels:
                logger.info(f"Channel {notification_in.channel} disabled for user {notification_in.user_id} and type {notification_in.notification_type}")
                # Fall back to in-app notification if the channel is disabled
                if NotificationChannel.IN_APP in user_preference.channels:
                    notification_in.channel = NotificationChannel.IN_APP
                else:
                    return None
        
        # Create the notification in the database
        notification = self.notification_repository.create(obj_in=notification_in)
        
        # If notification is scheduled for later, just return it
        if notification_in.scheduled_for and notification_in.scheduled_for > datetime.utcnow():
            return notification
        
        # Process the notification based on the channel
        if notification_in.channel == NotificationChannel.EMAIL:
            await self._process_email_notification(notification, background_tasks)
        elif notification_in.channel == NotificationChannel.SMS:
            await self._process_sms_notification(notification)
        elif notification_in.channel == NotificationChannel.PUSH:
            await self._process_push_notification(notification)
        elif notification_in.channel == NotificationChannel.WEBHOOK:
            await self._process_webhook_notification(notification)
        
        # For in-app notifications, just mark them as delivered
        if notification_in.channel == NotificationChannel.IN_APP:
            self.notification_repository.mark_as_delivered(id=notification.id)
        
        return notification
    
    async def create_batch_notification(
        self,
        *,
        batch_in: BatchNotificationCreate,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> List[Notification]:
        """
        Create notifications for multiple users.
        
        Args:
            batch_in: Batch notification data
            background_tasks: Background tasks for async processing
            
        Returns:
            List of created notifications
        """
        created_notifications = []
        
        for user_id in batch_in.user_ids:
            notification_in = NotificationCreate(
                title=batch_in.title,
                message=batch_in.message,
                notification_type=batch_in.notification_type,
                channel=batch_in.channel,
                user_id=user_id,
                organization_id=batch_in.organization_id,
                action_url=batch_in.action_url,
                action_text=batch_in.action_text,
                data=batch_in.data,
                scheduled_for=batch_in.scheduled_for,
            )
            
            notification = await self.create_notification(
                notification_in=notification_in,
                background_tasks=background_tasks,
            )
            
            if notification:
                created_notifications.append(notification)
        
        return created_notifications
    
    async def _process_email_notification(
        self,
        notification: Notification,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> None:
        """
        Process an email notification.
        
        Args:
            notification: The notification to process
            background_tasks: Background tasks for async processing
        """
        # Try to trigger n8n workflow first
        try:
            user = notification.user
            
            if not user or not user.email:
                logger.error(f"User not found or missing email for notification {notification.id}")
                return
            
            # Trigger the workflow using n8n
            execution_id = await self.workflow_service.send_notification(
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                channel="email",
                email=user.email,
                important=(notification.notification_type in [NotificationType.ALERT, NotificationType.SECURITY]),
                additional_data={
                    "action_url": notification.action_url,
                    "action_text": notification.action_text,
                    "data": notification.data,
                }
            )
            
            logger.info(f"Triggered notification workflow for user {user.id}, execution ID: {execution_id}")
            
            # Mark notification as delivered
            self.notification_repository.mark_as_delivered(id=notification.id)
            
        except Exception as e:
            logger.warning(f"Failed to trigger n8n workflow: {str(e)}. Falling back to direct email.")
            
            # Fall back to sending email directly
            if background_tasks:
                user = notification.user
                if user and user.email:
                    # Simple template
                    template = """
                    <html>
                    <body>
                        <h1>{{ title }}</h1>
                        <p>{{ message }}</p>
                        {% if action_url %}
                        <p><a href="{{ action_url }}">{{ action_text or "Click here" }}</a></p>
                        {% endif %}
                        <p>This is an automated message from the SaaS Factory system.</p>
                    </body>
                    </html>
                    """
                    
                    await self.email_service.send_template_email_async(
                        background_tasks=background_tasks,
                        to_email=user.email,
                        subject=notification.title,
                        template_str=template,
                        context={
                            "title": notification.title,
                            "message": notification.message,
                            "action_url": notification.action_url,
                            "action_text": notification.action_text,
                        },
                        is_html=True,
                    )
                    
                    # Mark notification as delivered
                    self.notification_repository.mark_as_delivered(id=notification.id)
    
    async def _process_sms_notification(self, notification: Notification) -> None:
        """
        Process an SMS notification.
        
        Args:
            notification: The notification to process
        """
        # Try to trigger n8n workflow
        try:
            user = notification.user
            
            if not user:
                logger.error(f"User not found for notification {notification.id}")
                return
            
            # Get user's phone number from settings
            phone = None
            if user.settings and "phone" in user.settings:
                phone = user.settings["phone"]
            
            if not phone:
                logger.error(f"User {user.id} does not have a phone number in settings")
                return
            
            # Trigger the workflow using n8n
            execution_id = await self.workflow_service.send_notification(
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                channel="sms",
                phone=phone,
                important=(notification.notification_type in [NotificationType.ALERT, NotificationType.SECURITY]),
            )
            
            logger.info(f"Triggered SMS notification workflow for user {user.id}, execution ID: {execution_id}")
            
            # Mark notification as delivered
            self.notification_repository.mark_as_delivered(id=notification.id)
            
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {str(e)}")
    
    async def _process_push_notification(self, notification: Notification) -> None:
        """
        Process a push notification.
        
        Args:
            notification: The notification to process
        """
        # Try to trigger n8n workflow
        try:
            # Trigger the workflow using n8n
            execution_id = await self.workflow_service.send_notification(
                user_id=notification.user_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                channel="push",
                important=(notification.notification_type in [NotificationType.ALERT, NotificationType.SECURITY]),
                additional_data={
                    "action_url": notification.action_url,
                    "data": notification.data,
                }
            )
            
            logger.info(f"Triggered push notification workflow for user {notification.user_id}, execution ID: {execution_id}")
            
            # Mark notification as delivered
            self.notification_repository.mark_as_delivered(id=notification.id)
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {str(e)}")
    
    async def _process_webhook_notification(self, notification: Notification) -> None:
        """
        Process a webhook notification.
        
        Args:
            notification: The notification to process
        """
        # For webhooks, we currently just mark as delivered
        # In a real implementation, this would call the webhook URL
        self.notification_repository.mark_as_delivered(id=notification.id)
        logger.info(f"Webhook notification {notification.id} marked as delivered")
    
    def get_notification(self, *, id: int) -> Optional[Notification]:
        """
        Get a notification by ID.
        
        Args:
            id: Notification ID
            
        Returns:
            Notification if found
        """
        return self.notification_repository.get(id=id)
    
    def update_notification(
        self,
        *,
        id: int,
        notification_in: NotificationUpdate,
    ) -> Optional[Notification]:
        """
        Update a notification.
        
        Args:
            id: Notification ID
            notification_in: Updated notification data
            
        Returns:
            Updated notification
        """
        notification = self.notification_repository.get(id=id)
        if not notification:
            return None
            
        return self.notification_repository.update(db_obj=notification, obj_in=notification_in)
    
    def delete_notification(self, *, id: int) -> Optional[Notification]:
        """
        Delete a notification.
        
        Args:
            id: Notification ID
            
        Returns:
            Deleted notification
        """
        return self.notification_repository.delete(id=id)
    
    def get_user_notifications(
        self,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
    ) -> List[Notification]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            unread_only: Only return unread notifications
            notification_type: Filter by notification type
            
        Returns:
            List of notifications
        """
        return self.notification_repository.get_by_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            notification_type=notification_type,
        )
    
    def mark_as_read(self, *, id: int) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            id: Notification ID
            
        Returns:
            Updated notification
        """
        return self.notification_repository.mark_as_read(id=id)
    
    def mark_all_as_read(self, *, user_id: int) -> int:
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications updated
        """
        return self.notification_repository.mark_all_as_read(user_id=user_id)
    
    def get_notification_preferences(self, *, user_id: int) -> List[NotificationPreference]:
        """
        Get notification preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of notification preferences
        """
        return self.preference_repository.get_for_user(user_id=user_id)
    
    def update_notification_preference(
        self,
        *,
        user_id: int,
        notification_type: NotificationType,
        preference_in: Union[NotificationPreferenceUpdate, NotificationPreferenceCreate],
    ) -> NotificationPreference:
        """
        Update or create a notification preference.
        
        Args:
            user_id: User ID
            notification_type: Notification type
            preference_in: Updated preference data
            
        Returns:
            Updated or created preference
        """
        # Convert to a dict for easier access
        preference_data = preference_in.dict(exclude_unset=True)
        
        # Get the channels and enabled status
        channels = preference_data.get("channels")
        enabled = preference_data.get("enabled")
        
        # Update or create the preference
        if isinstance(preference_in, NotificationPreferenceCreate):
            # It's a create operation, use all fields
            preference = self.preference_repository.update_or_create(
                user_id=user_id,
                notification_type=notification_type,
                channels=preference_in.channels,
                enabled=preference_in.enabled,
            )
        else:
            # It's an update operation, only use provided fields
            # First get the existing preference
            existing = self.preference_repository.get_by_type(
                user_id=user_id,
                notification_type=notification_type,
            )
            
            if existing:
                # Update with provided fields
                if channels is not None:
                    existing.channels = channels
                if enabled is not None:
                    existing.enabled = enabled
                    
                self.db.commit()
                self.db.refresh(existing)
                preference = existing
            else:
                # Create new with defaults for missing fields
                if channels is None:
                    channels = [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
                if enabled is None:
                    enabled = True
                    
                preference = self.preference_repository.update_or_create(
                    user_id=user_id,
                    notification_type=notification_type,
                    channels=channels,
                    enabled=enabled,
                )
        
        return preference
    
    def update_notification_preferences(
        self,
        *,
        user_id: int,
        preferences: Dict[str, Union[NotificationPreferenceUpdate, NotificationPreferenceCreate]],
    ) -> Dict[str, NotificationPreference]:
        """
        Update multiple notification preferences.
        
        Args:
            user_id: User ID
            preferences: Dictionary of notification types and preferences
            
        Returns:
            Dictionary of updated preferences
        """
        updated_preferences = {}
        
        for type_name, preference_in in preferences.items():
            try:
                notification_type = NotificationType(type_name)
                preference = self.update_notification_preference(
                    user_id=user_id,
                    notification_type=notification_type,
                    preference_in=preference_in,
                )
                updated_preferences[type_name] = preference
            except ValueError:
                logger.warning(f"Invalid notification type: {type_name}")
                continue
        
        return updated_preferences
    
    async def process_scheduled_notifications(
        self,
        background_tasks: BackgroundTasks,
    ) -> int:
        """
        Process notifications that are scheduled for delivery.
        
        Args:
            background_tasks: Background tasks for async processing
            
        Returns:
            Number of notifications processed
        """
        # Get scheduled notifications
        notifications = self.notification_repository.get_scheduled()
        
        processed_count = 0
        for notification in notifications:
            # Process the notification based on the channel
            if notification.channel == NotificationChannel.EMAIL:
                await self._process_email_notification(notification, background_tasks)
            elif notification.channel == NotificationChannel.SMS:
                await self._process_sms_notification(notification)
            elif notification.channel == NotificationChannel.PUSH:
                await self._process_push_notification(notification)
            elif notification.channel == NotificationChannel.WEBHOOK:
                await self._process_webhook_notification(notification)
            else:
                # For in-app notifications, just mark them as delivered
                self.notification_repository.mark_as_delivered(id=notification.id)
                
            processed_count += 1
        
        return processed_count


def get_notification_service(
    notification_repository: NotificationRepository = Depends(get_notification_repository),
    preference_repository: NotificationPreferenceRepository = Depends(get_notification_preference_repository),
    workflow_service: WorkflowService = Depends(get_workflow_service),
    email_service: EmailService = Depends(get_email_service),
    db: Session = Depends(get_db),
) -> NotificationService:
    """
    Dependency to get NotificationService.
    
    Args:
        notification_repository: Repository for notification operations
        preference_repository: Repository for notification preference operations
        workflow_service: Service for workflow operations
        email_service: Service for email operations
        db: Database session
        
    Returns:
        NotificationService instance
    """
    return NotificationService(
        notification_repository=notification_repository,
        preference_repository=preference_repository,
        workflow_service=workflow_service,
        email_service=email_service,
        db=db,
    )