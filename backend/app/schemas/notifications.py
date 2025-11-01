"""
Notification System Schemas (Story 3.3.1 & 3.3.2)

Pydantic models for email notifications and in-app notifications.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class NotificationPriority(str, Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class NotificationStatus(str, Enum):
    """Notification delivery status."""

    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class NotificationType(str, Enum):
    """Notification type."""

    EMAIL = "email"
    IN_APP = "in_app"
    BOTH = "both"


class EmailRecipient(BaseModel):
    """Email recipient information."""

    email: EmailStr = Field(..., description="Recipient email address")
    name: str = Field(..., description="Recipient name")

    class Config:
        json_schema_extra = {
            "example": {"email": "student@mnps.edu", "name": "John Doe"}
        }


class EmailNotificationRequest(BaseModel):
    """Request to send email notification."""

    type: NotificationType = Field(
        default=NotificationType.EMAIL, description="Notification type"
    )
    recipient: EmailRecipient = Field(..., description="Email recipient")
    template: str = Field(..., description="Email template name")
    data: Dict[str, Any] = Field(default={}, description="Template data")
    priority: NotificationPriority = Field(
        default=NotificationPriority.NORMAL, description="Send priority"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "type": "email",
                "recipient": {"email": "student@mnps.edu", "name": "John Doe"},
                "template": "content_ready",
                "data": {
                    "topic_name": "Newton's Third Law",
                    "interest": "basketball",
                    "video_url": "https://vividly.edu/content/abc123",
                    "thumbnail_url": "https://cdn.vividly.edu/thumbnails/abc123.jpg",
                },
                "priority": "normal",
            }
        }


class EmailNotificationResponse(BaseModel):
    """Response after queuing email notification."""

    notification_id: str = Field(..., description="Unique notification ID")
    status: NotificationStatus = Field(..., description="Current status")
    estimated_send_time: Optional[str] = Field(
        None, description="Estimated send time (ISO format)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "notification_id": "notif_001",
                "status": "queued",
                "estimated_send_time": "2025-11-18T10:00:30Z",
            }
        }


class NotificationStatusResponse(BaseModel):
    """Notification delivery status."""

    notification_id: str = Field(..., description="Notification ID")
    status: NotificationStatus = Field(..., description="Delivery status")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    delivered_at: Optional[datetime] = Field(
        None, description="When notification was delivered"
    )
    opened_at: Optional[datetime] = Field(None, description="When email was opened")
    clicked_at: Optional[datetime] = Field(None, description="When link was clicked")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_id": "notif_001",
                "status": "delivered",
                "sent_at": "2025-11-18T10:00:32Z",
                "delivered_at": "2025-11-18T10:00:34Z",
                "opened_at": "2025-11-18T10:05:12Z",
                "clicked_at": "2025-11-18T10:05:45Z",
                "error_message": None,
            }
        }


class BatchNotificationItem(BaseModel):
    """Single notification in batch request."""

    recipient: EmailRecipient = Field(..., description="Email recipient")
    template: str = Field(..., description="Email template name")
    data: Dict[str, Any] = Field(default={}, description="Template data")


class BatchNotificationRequest(BaseModel):
    """Request to send batch notifications."""

    notifications: List[BatchNotificationItem] = Field(
        ..., description="List of notifications", max_length=100
    )

    class Config:
        json_schema_extra = {
            "example": {
                "notifications": [
                    {
                        "recipient": {"email": "user1@mnps.edu", "name": "User 1"},
                        "template": "welcome_student",
                        "data": {
                            "activation_link": "https://vividly.edu/activate/abc123"
                        },
                    },
                    {
                        "recipient": {"email": "user2@mnps.edu", "name": "User 2"},
                        "template": "welcome_student",
                        "data": {
                            "activation_link": "https://vividly.edu/activate/def456"
                        },
                    },
                ]
            }
        }


class BatchNotificationResponse(BaseModel):
    """Response for batch notification request."""

    batch_id: str = Field(..., description="Batch ID")
    queued_count: int = Field(..., description="Number of notifications queued")
    failed_count: int = Field(..., description="Number that failed to queue")
    notification_ids: List[str] = Field(..., description="List of notification IDs")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_001",
                "queued_count": 95,
                "failed_count": 5,
                "notification_ids": ["notif_001", "notif_002", "..."],
            }
        }


# In-App Notification Schemas (Story 3.3.2)


class InAppNotification(BaseModel):
    """In-app notification."""

    notification_id: str = Field(..., description="Notification ID")
    user_id: str = Field(..., description="User ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: str = Field(
        ..., description="Notification type (info, success, warning, error)"
    )
    link: Optional[str] = Field(None, description="Optional link")
    read: bool = Field(default=False, description="Whether notification has been read")
    created_at: datetime = Field(..., description="Creation timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "notification_id": "notif_inapp_001",
                "user_id": "user_student_001",
                "title": "New Content Available",
                "message": "Your personalized video for Newton's Third Law is ready!",
                "type": "success",
                "link": "/content/abc123",
                "read": False,
                "created_at": "2025-11-18T10:00:00Z",
            }
        }


class InAppNotificationList(BaseModel):
    """List of in-app notifications."""

    notifications: List[InAppNotification] = Field(
        ..., description="List of notifications"
    )
    unread_count: int = Field(..., description="Number of unread notifications")
    total_count: int = Field(..., description="Total notification count")

    class Config:
        json_schema_extra = {
            "example": {"notifications": [], "unread_count": 3, "total_count": 15}
        }


class MarkReadRequest(BaseModel):
    """Request to mark notifications as read."""

    notification_ids: List[str] = Field(
        ..., description="List of notification IDs to mark as read"
    )

    class Config:
        json_schema_extra = {
            "example": {"notification_ids": ["notif_001", "notif_002", "notif_003"]}
        }
