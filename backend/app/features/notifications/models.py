"""
Notification data models.
"""

from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.db.base import Base


class NotificationType(str, PyEnum):
    """Types of notifications."""
    SYSTEM = "system"           # System notifications
    ACTIVITY = "activity"       # User activity notifications
    ALERT = "alert"             # Important alerts
    BILLING = "billing"         # Billing-related notifications
    TEAM = "team"               # Team-related notifications
    WELCOME = "welcome"         # Onboarding/welcome notifications
    SECURITY = "security"       # Security-related notifications


class NotificationChannel(str, PyEnum):
    """Delivery channels for notifications."""
    IN_APP = "in_app"           # In-app notifications
    EMAIL = "email"             # Email notifications
    SMS = "sms"                 # SMS notifications
    PUSH = "push"               # Push notifications
    WEBHOOK = "webhook"         # Webhook notifications


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    notification_type = Column(String, primary_key=True)
    channels = Column(JSON, nullable=False, default=lambda: ["in_app", "email"])
    enabled = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")


class Notification(Base):
    """
    Notification model representing a system notification.
    """
    __tablename__ = "notifications"

    # Basic notification details
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(
        Enum(NotificationType), 
        nullable=False, 
        default=NotificationType.SYSTEM,
        index=True
    )
    
    # Recipients
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Delivery details
    channel = Column(
        Enum(NotificationChannel),
        nullable=False,
        default=NotificationChannel.IN_APP,
        index=True
    )
    is_read = Column(Boolean, default=False, nullable=False)
    is_delivered = Column(Boolean, default=False, nullable=False)
    
    # Link/action details
    action_url = Column(String, nullable=True)
    action_text = Column(String, nullable=True)
    
    # Extra data
    data = Column(JSON, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    organization = relationship("Organization", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, title='{self.title}', type='{self.notification_type}')>"
    
    def mark_as_read(self):
        """Mark the notification as read."""
        self.is_read = True
        self.read_at = datetime.utcnow()
        
    def mark_as_delivered(self):
        """Mark the notification as delivered."""
        self.is_delivered = True
        self.sent_at = datetime.utcnow()