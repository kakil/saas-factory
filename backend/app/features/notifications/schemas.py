"""
Notification schemas.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum

from pydantic import BaseModel, Field

from app.features.notifications.models import NotificationType, NotificationChannel


# Base notification schema
class NotificationBase(BaseModel):
    """Base notification schema."""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM
    channel: NotificationChannel = NotificationChannel.IN_APP
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[datetime] = None


# Schema for creating a notification
class NotificationCreate(NotificationBase):
    """Schema for creating a notification."""
    user_id: int
    organization_id: Optional[int] = None


# Schema for updating a notification
class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""
    title: Optional[str] = None
    message: Optional[str] = None
    is_read: Optional[bool] = None
    is_delivered: Optional[bool] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Schema for response
class Notification(NotificationBase):
    """Schema for notification response."""
    id: int
    user_id: int
    organization_id: Optional[int] = None
    is_read: bool
    is_delivered: bool
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Schema for batch notification creation
class BatchNotificationCreate(BaseModel):
    """Schema for creating multiple notifications."""
    title: str
    message: str
    notification_type: NotificationType = NotificationType.SYSTEM
    channel: NotificationChannel = NotificationChannel.IN_APP
    user_ids: List[int]
    organization_id: Optional[int] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    scheduled_for: Optional[datetime] = None


# Notification preference schemas
class NotificationPreferenceBase(BaseModel):
    """Base notification preference schema."""
    notification_type: NotificationType
    channels: List[NotificationChannel] = [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    enabled: bool = True


# Schema for creating notification preference
class NotificationPreferenceCreate(NotificationPreferenceBase):
    """Schema for creating a notification preference."""
    user_id: int


# Schema for updating notification preference
class NotificationPreferenceUpdate(BaseModel):
    """Schema for updating a notification preference."""
    channels: Optional[List[NotificationChannel]] = None
    enabled: Optional[bool] = None


# Schema for response
class NotificationPreference(NotificationPreferenceBase):
    """Schema for notification preference response."""
    user_id: int
    
    class Config:
        """Pydantic config."""
        from_attributes = True


# Schema for updating all preferences
class NotificationPreferencesUpdate(BaseModel):
    """Schema for updating all notification preferences."""
    preferences: Dict[str, Union[NotificationPreferenceUpdate, NotificationPreferenceCreate]]