"""
Repository for notification operations.
"""

from typing import List, Optional, Dict, Any, Type, TypeVar
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.db.repository import BaseRepository
from app.core.db.session import get_db
from app.features.notifications.models import Notification, NotificationPreference, NotificationType, NotificationChannel

# Define types for type hints
NotificationCreate = TypeVar("NotificationCreate")
NotificationUpdate = TypeVar("NotificationUpdate")
NotificationPreferenceCreate = TypeVar("NotificationPreferenceCreate")
NotificationPreferenceUpdate = TypeVar("NotificationPreferenceUpdate")


class NotificationRepository(BaseRepository[Notification, NotificationCreate, NotificationUpdate]):
    """
    Repository for notification operations.
    """
    
    def get_by_user(
        self, 
        *, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
    ) -> List[Notification]:
        """
        Get notifications for a specific user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            unread_only: Only return unread notifications
            notification_type: Filter by notification type
            
        Returns:
            List of notifications
        """
        query = self.db.query(self.model).filter(self.model.user_id == user_id)
        
        if unread_only:
            query = query.filter(self.model.is_read == False)
            
        if notification_type:
            query = query.filter(self.model.notification_type == notification_type)
            
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_by_organization(
        self, 
        *, 
        organization_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        notification_type: Optional[NotificationType] = None,
    ) -> List[Notification]:
        """
        Get notifications for a specific organization.
        
        Args:
            organization_id: Organization ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            notification_type: Filter by notification type
            
        Returns:
            List of notifications
        """
        query = self.db.query(self.model).filter(self.model.organization_id == organization_id)
            
        if notification_type:
            query = query.filter(self.model.notification_type == notification_type)
            
        return query.order_by(self.model.created_at.desc()).offset(skip).limit(limit).all()
    
    def mark_as_read(self, *, id: int) -> Optional[Notification]:
        """
        Mark a notification as read.
        
        Args:
            id: Notification ID
            
        Returns:
            Updated notification
        """
        notification = self.get(id=id)
        if notification:
            notification.mark_as_read()
            self.db.commit()
            self.db.refresh(notification)
        return notification
    
    def mark_all_as_read(self, *, user_id: int) -> int:
        """
        Mark all notifications for a user as read.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications updated
        """
        now = datetime.utcnow()
        result = self.db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.is_read == False
        ).update(
            {"is_read": True, "read_at": now},
            synchronize_session=False
        )
        self.db.commit()
        return result
    
    def mark_as_delivered(self, *, id: int) -> Optional[Notification]:
        """
        Mark a notification as delivered.
        
        Args:
            id: Notification ID
            
        Returns:
            Updated notification
        """
        notification = self.get(id=id)
        if notification:
            notification.mark_as_delivered()
            self.db.commit()
            self.db.refresh(notification)
        return notification
    
    def get_scheduled(self, *, limit: int = 100) -> List[Notification]:
        """
        Get notifications scheduled for delivery.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of scheduled notifications
        """
        now = datetime.utcnow()
        return self.db.query(self.model).filter(
            self.model.scheduled_for <= now,
            self.model.is_delivered == False,
        ).limit(limit).all()


class NotificationPreferenceRepository(BaseRepository[NotificationPreference, NotificationPreferenceCreate, NotificationPreferenceUpdate]):
    """
    Repository for notification preference operations.
    """
    
    def get_for_user(self, *, user_id: int) -> List[NotificationPreference]:
        """
        Get notification preferences for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of notification preferences
        """
        return self.db.query(self.model).filter(self.model.user_id == user_id).all()
    
    def get_by_type(self, *, user_id: int, notification_type: NotificationType) -> Optional[NotificationPreference]:
        """
        Get notification preference for a specific type.
        
        Args:
            user_id: User ID
            notification_type: Notification type
            
        Returns:
            Notification preference if found
        """
        return self.db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.notification_type == notification_type,
        ).first()
    
    def update_or_create(
        self, 
        *, 
        user_id: int, 
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        enabled: bool = True,
    ) -> NotificationPreference:
        """
        Update or create notification preference.
        
        Args:
            user_id: User ID
            notification_type: Notification type
            channels: Notification channels
            enabled: Whether notifications are enabled
            
        Returns:
            Updated or created notification preference
        """
        preference = self.get_by_type(user_id=user_id, notification_type=notification_type)
        
        if preference:
            preference.channels = channels
            preference.enabled = enabled
            self.db.commit()
            self.db.refresh(preference)
            return preference
        else:
            # Create new preference
            new_preference = NotificationPreference(
                user_id=user_id,
                notification_type=notification_type,
                channels=channels,
                enabled=enabled,
            )
            self.db.add(new_preference)
            self.db.commit()
            self.db.refresh(new_preference)
            return new_preference


def get_notification_repository(db: Session = Depends(get_db)) -> NotificationRepository:
    """
    Dependency to get NotificationRepository.
    
    Args:
        db: Database session
        
    Returns:
        NotificationRepository instance
    """
    return NotificationRepository(Notification, db)


def get_notification_preference_repository(db: Session = Depends(get_db)) -> NotificationPreferenceRepository:
    """
    Dependency to get NotificationPreferenceRepository.
    
    Args:
        db: Database session
        
    Returns:
        NotificationPreferenceRepository instance
    """
    return NotificationPreferenceRepository(NotificationPreference, db)