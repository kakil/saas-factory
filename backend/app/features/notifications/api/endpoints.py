"""
API endpoints for notifications.
"""

from typing import List, Dict, Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.core.api.responses import success_response, error_response
from app.core.api.pagination import PaginationParams
from app.core.dependencies import get_current_user
from app.features.users.models import User
from app.features.notifications.models import NotificationType, NotificationChannel
from app.features.notifications.service import NotificationService, get_notification_service
from app.features.notifications.schemas import (
    Notification, NotificationCreate, NotificationUpdate,
    NotificationPreference, NotificationPreferenceCreate, NotificationPreferenceUpdate,
    BatchNotificationCreate, NotificationPreferencesUpdate,
)

router = APIRouter()


@router.get("", response_model=List[Notification])
async def get_notifications(
    pagination: PaginationParams = Depends(),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get notifications for the current user.
    
    This endpoint returns notifications for the authenticated user.
    Notifications can be filtered by status (read/unread) and type.
    """
    notifications = notification_service.get_user_notifications(
        user_id=current_user.id,
        skip=pagination.skip,
        limit=pagination.limit,
        unread_only=unread_only,
        notification_type=notification_type,
    )
    
    return success_response(
        data=notifications,
        message="Notifications retrieved successfully",
        meta={"unread_filter": unread_only}
    )


@router.post("", response_model=Notification)
async def create_notification(
    notification_in: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Create a new notification.
    
    This endpoint is typically used by system components rather than directly by users.
    """
    # Only allow creating notifications for self or if admin
    if notification_in.user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to create notifications for other users",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    notification = await notification_service.create_notification(
        notification_in=notification_in,
        background_tasks=background_tasks,
    )
    
    if not notification:
        return error_response(
            message="Notification was not created (possibly due to user preferences)",
            code="NOTIFICATION_SKIPPED",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    
    return success_response(
        data=notification,
        message="Notification created successfully"
    )


@router.post("/batch", response_model=List[Notification])
async def create_batch_notification(
    batch_in: BatchNotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Create notifications for multiple users.
    
    This endpoint is typically used by system components or admin users.
    """
    # Only allow admin users to create batch notifications
    if not current_user.is_superuser:
        return error_response(
            message="Only admin users can create batch notifications",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    notifications = await notification_service.create_batch_notification(
        batch_in=batch_in,
        background_tasks=background_tasks,
    )
    
    return success_response(
        data=notifications,
        message=f"Created {len(notifications)} notifications"
    )


@router.get("/{notification_id}", response_model=Notification)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get a specific notification by ID.
    """
    notification = notification_service.get_notification(id=notification_id)
    
    if not notification:
        return error_response(
            message="Notification not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    # Check permission - users can only view their own notifications
    if notification.user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to view this notification",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    return success_response(
        data=notification,
        message="Notification retrieved successfully"
    )


@router.patch("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: int,
    notification_in: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Update a notification.
    """
    # Get the notification first to check permissions
    notification = notification_service.get_notification(id=notification_id)
    
    if not notification:
        return error_response(
            message="Notification not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    # Check permission - users can only update their own notifications
    if notification.user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to update this notification",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    updated_notification = notification_service.update_notification(
        id=notification_id,
        notification_in=notification_in,
    )
    
    return success_response(
        data=updated_notification,
        message="Notification updated successfully"
    )


@router.delete("/{notification_id}", response_model=Notification)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Delete a notification.
    """
    # Get the notification first to check permissions
    notification = notification_service.get_notification(id=notification_id)
    
    if not notification:
        return error_response(
            message="Notification not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    # Check permission - users can only delete their own notifications
    if notification.user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to delete this notification",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    deleted_notification = notification_service.delete_notification(id=notification_id)
    
    return success_response(
        data=deleted_notification,
        message="Notification deleted successfully"
    )


@router.post("/{notification_id}/read", response_model=Notification)
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Mark a notification as read.
    """
    # Get the notification first to check permissions
    notification = notification_service.get_notification(id=notification_id)
    
    if not notification:
        return error_response(
            message="Notification not found",
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    # Check permission - users can only mark their own notifications as read
    if notification.user_id != current_user.id and not current_user.is_superuser:
        return error_response(
            message="You don't have permission to mark this notification as read",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    updated_notification = notification_service.mark_as_read(id=notification_id)
    
    return success_response(
        data=updated_notification,
        message="Notification marked as read"
    )


@router.post("/read-all", response_model=Dict[str, Any])
async def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Mark all notifications for the current user as read.
    """
    count = notification_service.mark_all_as_read(user_id=current_user.id)
    
    return success_response(
        data={"count": count},
        message=f"Marked {count} notifications as read"
    )


@router.get("/preferences", response_model=List[NotificationPreference])
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get notification preferences for the current user.
    """
    preferences = notification_service.get_notification_preferences(user_id=current_user.id)
    
    return success_response(
        data=preferences,
        message="Notification preferences retrieved successfully"
    )


@router.put("/preferences/{notification_type}", response_model=NotificationPreference)
async def update_notification_preference(
    notification_type: NotificationType,
    preference_in: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Update notification preference for a specific notification type.
    """
    preference = notification_service.update_notification_preference(
        user_id=current_user.id,
        notification_type=notification_type,
        preference_in=preference_in,
    )
    
    return success_response(
        data=preference,
        message="Notification preference updated successfully"
    )


@router.put("/preferences", response_model=Dict[str, NotificationPreference])
async def update_all_notification_preferences(
    preferences_in: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Update multiple notification preferences at once.
    """
    preferences = notification_service.update_notification_preferences(
        user_id=current_user.id,
        preferences=preferences_in.preferences,
    )
    
    return success_response(
        data=preferences,
        message="Notification preferences updated successfully"
    )


@router.post("/process-scheduled", response_model=Dict[str, Any])
async def process_scheduled_notifications(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Process notifications that are scheduled for delivery.
    
    This endpoint is typically called by a scheduled job or cron task.
    It can also be called manually by admin users.
    """
    # Only allow admin users to trigger scheduled notification processing
    if not current_user.is_superuser:
        return error_response(
            message="Only admin users can process scheduled notifications",
            code="PERMISSION_DENIED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
    
    count = await notification_service.process_scheduled_notifications(
        background_tasks=background_tasks,
    )
    
    return success_response(
        data={"count": count},
        message=f"Processed {count} scheduled notifications"
    )