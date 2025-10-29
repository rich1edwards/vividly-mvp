"""
Notification API Endpoints (Story 3.3.1 & 3.3.2)

Internal endpoints for email notifications and user-facing endpoints for in-app notifications.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.schemas.notifications import (
    EmailNotificationRequest,
    EmailNotificationResponse,
    NotificationStatusResponse,
    BatchNotificationRequest,
    BatchNotificationResponse,
    InAppNotificationList,
    MarkReadRequest,
    NotificationStatus,
)
from app.services.email_service import EmailService
from app.utils.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter()


def get_email_service() -> EmailService:
    """
    Dependency to get email service instance.

    For production: Inject SendGrid client
    For testing: Can inject mocks
    """
    # TODO: In production, initialize with actual SendGrid client
    # from sendgrid import SendGridAPIClient
    # import os
    # sendgrid_client = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    return EmailService(sendgrid_client=None)


# ============================================================================
# Story 3.3.1: Email Notification Endpoints (Internal API)
# ============================================================================

@router.post(
    "/send",
    response_model=EmailNotificationResponse,
    summary="Send email notification",
    description="""
    Queue email notification for sending.

    This is an internal endpoint used by backend services to send transactional emails.
    In production, this should require service-to-service authentication.

    **Templates:**
    - welcome_student: New student welcome email
    - welcome_teacher: New teacher welcome email
    - welcome_admin: New admin welcome email
    - password_reset: Password reset link
    - content_ready: Content generation complete
    - account_request_approved: Account approved notification
    - account_request_denied: Account request update
    """,
    status_code=status.HTTP_202_ACCEPTED
)
async def send_notification(
    request: EmailNotificationRequest,
    email_service: EmailService = Depends(get_email_service),
    # service_token: str = Depends(require_service_token)  # TODO: Service auth
):
    """
    Send email notification.

    Args:
        request: Email notification request
        email_service: Email service dependency

    Returns:
        EmailNotificationResponse with notification ID and status
    """
    try:
        notification_id, status_str = email_service.queue_email(
            recipient_email=request.recipient.email,
            recipient_name=request.recipient.name,
            template=request.template,
            data=request.data,
            priority=request.priority.value
        )

        # Calculate estimated send time (in production, based on queue depth)
        from datetime import datetime, timedelta
        estimated_time = datetime.utcnow() + timedelta(seconds=30)

        return EmailNotificationResponse(
            notification_id=notification_id,
            status=NotificationStatus.QUEUED if status_str == "queued" else NotificationStatus.FAILED,
            estimated_send_time=estimated_time.isoformat() + "Z" if status_str == "queued" else None
        )

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue notification"
        )


@router.get(
    "/{notification_id}/status",
    response_model=NotificationStatusResponse,
    summary="Get notification status",
    description="""
    Get delivery status for a notification.

    Returns current status and delivery timestamps.
    """
)
async def get_notification_status(
    notification_id: str,
    email_service: EmailService = Depends(get_email_service),
    # service_token: str = Depends(require_service_token)  # TODO: Service auth
):
    """
    Get notification delivery status.

    Args:
        notification_id: Notification ID
        email_service: Email service dependency

    Returns:
        NotificationStatusResponse with delivery status
    """
    try:
        status_info = email_service.get_status(notification_id)

        return NotificationStatusResponse(
            notification_id=status_info["notification_id"],
            status=NotificationStatus(status_info["status"]),
            sent_at=status_info.get("sent_at"),
            delivered_at=status_info.get("delivered_at"),
            opened_at=status_info.get("opened_at"),
            clicked_at=status_info.get("clicked_at"),
            error_message=status_info.get("error_message")
        )

    except Exception as e:
        logger.error(f"Failed to get notification status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )


@router.post(
    "/send/batch",
    response_model=BatchNotificationResponse,
    summary="Send batch notifications",
    description="""
    Send multiple email notifications in batch.

    Useful for bulk operations like sending welcome emails to multiple users.
    Maximum 100 notifications per batch.
    """,
    status_code=status.HTTP_202_ACCEPTED
)
async def send_batch_notifications(
    request: BatchNotificationRequest,
    email_service: EmailService = Depends(get_email_service),
    # service_token: str = Depends(require_service_token)  # TODO: Service auth
):
    """
    Send batch email notifications.

    Args:
        request: Batch notification request
        email_service: Email service dependency

    Returns:
        BatchNotificationResponse with batch results
    """
    try:
        # Convert Pydantic models to dicts
        notifications = [
            {
                "recipient": {
                    "email": notif.recipient.email,
                    "name": notif.recipient.name
                },
                "template": notif.template,
                "data": notif.data
            }
            for notif in request.notifications
        ]

        batch_id, queued_count, failed_count, notification_ids = email_service.send_batch(
            notifications=notifications
        )

        return BatchNotificationResponse(
            batch_id=batch_id,
            queued_count=queued_count,
            failed_count=failed_count,
            notification_ids=notification_ids
        )

    except Exception as e:
        logger.error(f"Failed to send batch notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue batch notifications"
        )


# ============================================================================
# Story 3.3.2: In-App Notification Endpoints (User-Facing API)
# ============================================================================

@router.get(
    "/inbox",
    response_model=InAppNotificationList,
    summary="Get user notifications",
    description="""
    Get in-app notifications for authenticated user.

    Returns list of recent notifications and unread count.
    Supports filtering by read/unread status.
    """,
    tags=["notifications-user"]
)
async def get_user_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user in-app notifications.

    Args:
        unread_only: Only return unread notifications
        limit: Maximum number of notifications to return
        current_user: Authenticated user
        db: Database session

    Returns:
        InAppNotificationList with notifications
    """
    try:
        # TODO: Query from Notification model
        # For now, return empty list
        return InAppNotificationList(
            notifications=[],
            unread_count=0,
            total_count=0
        )

    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.post(
    "/mark-read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark notifications as read",
    description="""
    Mark one or more notifications as read.

    Updates read status for specified notification IDs.
    """,
    tags=["notifications-user"]
)
async def mark_notifications_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notifications as read.

    Args:
        request: List of notification IDs to mark as read
        current_user: Authenticated user
        db: Database session

    Returns:
        204 No Content on success
    """
    try:
        # TODO: Update Notification records
        # For now, just return success
        logger.info(f"Marked {len(request.notification_ids)} notifications as read for user {current_user.user_id}")
        return None

    except Exception as e:
        logger.error(f"Failed to mark notifications read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications"
        )


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification",
    description="""
    Delete a notification from user's inbox.
    """,
    tags=["notifications-user"]
)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user notification.

    Args:
        notification_id: Notification ID to delete
        current_user: Authenticated user
        db: Database session

    Returns:
        204 No Content on success
    """
    try:
        # TODO: Delete Notification record
        # Verify ownership before deleting
        logger.info(f"Deleted notification {notification_id} for user {current_user.user_id}")
        return None

    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
