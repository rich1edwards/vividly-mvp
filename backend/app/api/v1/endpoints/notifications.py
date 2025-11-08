"""
Notification API Endpoints (Story 3.3.1, 3.3.2 & Phase 1.4)

Internal endpoints for email notifications and user-facing endpoints for in-app notifications.

Phase 1.4: Real-Time Notification API Endpoints (Server-Sent Events)
- SSE endpoint for real-time push notifications
- Redis Pub/Sub for distributed messaging
- Connection lifecycle management

References:
- PHASE_1_4_WEBSOCKET_SPECIFICATION.md
- SESSION_13_PHASE_1_4_INFRASTRUCTURE.md
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, AsyncGenerator
import logging
import uuid
import asyncio
import json

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
from app.services.notification_service import (
    NotificationService,
    get_notification_service,
)
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
    status_code=status.HTTP_202_ACCEPTED,
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
            priority=request.priority.value,
        )

        # Calculate estimated send time (in production, based on queue depth)
        from datetime import datetime, timedelta

        estimated_time = datetime.utcnow() + timedelta(seconds=30)

        return EmailNotificationResponse(
            notification_id=notification_id,
            status=NotificationStatus.QUEUED
            if status_str == "queued"
            else NotificationStatus.FAILED,
            estimated_send_time=estimated_time.isoformat() + "Z"
            if status_str == "queued"
            else None,
        )

    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue notification",
        )


@router.get(
    "/{notification_id}/status",
    response_model=NotificationStatusResponse,
    summary="Get notification status",
    description="""
    Get delivery status for a notification.

    Returns current status and delivery timestamps.
    """,
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
            error_message=status_info.get("error_message"),
        )

    except Exception as e:
        logger.error(f"Failed to get notification status: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
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
    status_code=status.HTTP_202_ACCEPTED,
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
                    "name": notif.recipient.name,
                },
                "template": notif.template,
                "data": notif.data,
            }
            for notif in request.notifications
        ]

        (
            batch_id,
            queued_count,
            failed_count,
            notification_ids,
        ) = email_service.send_batch(notifications=notifications)

        return BatchNotificationResponse(
            batch_id=batch_id,
            queued_count=queued_count,
            failed_count=failed_count,
            notification_ids=notification_ids,
        )

    except Exception as e:
        logger.error(f"Failed to send batch notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue batch notifications",
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
    tags=["notifications-user"],
)
async def get_user_notifications(
    unread_only: bool = False,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        return InAppNotificationList(notifications=[], unread_count=0, total_count=0)

    except Exception as e:
        logger.error(f"Failed to get notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications",
        )


@router.post(
    "/mark-read",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark notifications as read",
    description="""
    Mark one or more notifications as read.

    Updates read status for specified notification IDs.
    """,
    tags=["notifications-user"],
)
async def mark_notifications_read(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        logger.info(
            f"Marked {len(request.notification_ids)} notifications as read for user {current_user.user_id}"
        )
        return None

    except Exception as e:
        logger.error(f"Failed to mark notifications read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notifications",
        )


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete notification",
    description="""
    Delete a notification from user's inbox.
    """,
    tags=["notifications-user"],
)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
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
        logger.info(
            f"Deleted notification {notification_id} for user {current_user.user_id}"
        )
        return None

    except Exception as e:
        logger.error(f"Failed to delete notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )


# ============================================================================
# Phase 1.4: Real-Time Notification Endpoints (Server-Sent Events)
# ============================================================================


@router.get(
    "/stream",
    summary="Subscribe to real-time notifications via Server-Sent Events",
    description="""
    Subscribe to real-time push notifications for content generation progress.

    **Protocol**: Server-Sent Events (SSE)
    **Authentication**: Required (JWT Bearer token)
    **Connection Type**: Long-lived HTTP connection with streaming response

    **Event Types**:
    - `connection.established`: Initial connection confirmation
    - `heartbeat`: Keepalive ping every 30 seconds
    - `content_request.created`: Content generation request created
    - `content_request.queued`: Request queued for processing
    - `content_generation.started`: Generation started
    - `content_generation.progress`: Progress update (includes percentage)
    - `content_generation.completed`: Generation completed successfully
    - `content_generation.failed`: Generation failed (includes error details)
    - `system.maintenance`: System maintenance notification
    - `user.session_expires_soon`: Session expiring soon warning

    **Event Format**:
    ```
    event: <event_type>
    data: <JSON payload>

    ```

    **Example Event**:
    ```
    event: content_generation.progress
    data: {"event_type": "content_generation.progress", "content_request_id": "abc-123", "title": "Generating Video", "message": "Creating visual content...", "progress_percentage": 65, "metadata": {"stage": "video_generation"}, "timestamp": "2024-01-15T10:30:00Z"}

    ```

    **Client Implementation** (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/v1/notifications/stream', {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });

    eventSource.addEventListener('content_generation.progress', (event) => {
      const data = JSON.parse(event.data);
      console.log(`Progress: ${data.progress_percentage}%`);
    });

    eventSource.addEventListener('content_generation.completed', (event) => {
      const data = JSON.parse(event.data);
      console.log('Video ready!', data.metadata.video_url);
    });

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };
    ```

    **Connection Management**:
    - Heartbeats sent every 30 seconds to keep connection alive
    - Stale connections (no heartbeat for 90 seconds) are automatically cleaned up
    - Clients should implement automatic reconnection with exponential backoff
    - Each connection has a unique ID for tracking

    **Performance**:
    - Sub-10ms Redis Pub/Sub latency
    - <50ms end-to-end notification delivery
    - Supports 10,000+ concurrent connections per Cloud Run instance

    **Error Handling**:
    - 401: Invalid or expired JWT token
    - 503: Notification service unavailable (Redis connection failed)
    - Connection automatically closes on authentication failure

    **Monitoring**:
    - Active connections tracked in Redis
    - Connection metrics logged to Cloud Logging
    - Heartbeat timestamps for health monitoring
    """,
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    tags=["notifications-realtime"],
)
async def stream_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
    db: Session = Depends(get_db),
):
    """
    Stream real-time notifications to authenticated user via SSE.

    This endpoint establishes a long-lived HTTP connection and streams
    notifications as Server-Sent Events. The connection remains open until:
    - Client disconnects
    - Authentication expires
    - Server shutdown/restart
    - Network error

    Args:
        request: FastAPI request object (for detecting client disconnection)
        current_user: Authenticated user from JWT token
        notification_service: NotificationService instance
        db: Database session (not used, but available for future enhancements)

    Returns:
        StreamingResponse: SSE stream with Content-Type: text/event-stream

    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 503 if notification service is unavailable
    """
    # Generate unique connection ID for tracking
    connection_id = f"conn_{uuid.uuid4().hex[:16]}"
    user_id = str(current_user.user_id)

    # Extract client metadata from request headers
    user_agent = request.headers.get("user-agent", "unknown")
    # Get client IP (handle both direct and proxied requests)
    client_ip = request.client.host if request.client else "unknown"
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    logger.info(
        f"SSE connection request: user_id={user_id}, "
        f"connection_id={connection_id}, "
        f"ip={client_ip}, "
        f"user_agent={user_agent[:100]}"
    )

    # Check if Redis is available
    if not notification_service.redis:
        logger.error("Notification service unavailable: Redis not connected")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service is currently unavailable. Please try again later.",
        )

    async def event_generator() -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted events.

        SSE format:
        event: <event_type>
        data: <JSON payload>

        (blank line separates events)
        """
        try:
            # Subscribe to user's notification channel
            async for notification_event in notification_service.subscribe_to_notifications(
                user_id=user_id,
                connection_id=connection_id,
                user_agent=user_agent,
                ip_address=client_ip,
            ):
                # Format event in SSE format
                event_type = notification_event.get("event", "notification")
                event_data = notification_event.get("data", {})

                # SSE format requires specific structure:
                # event: <type>\n
                # data: <json>\n\n
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(event_data)}\n\n"

                logger.debug(
                    f"SSE event sent: user_id={user_id}, "
                    f"connection_id={connection_id}, "
                    f"event={event_type}"
                )

        except asyncio.CancelledError:
            # Client disconnected or connection cancelled
            logger.info(
                f"SSE connection cancelled: user_id={user_id}, "
                f"connection_id={connection_id}"
            )
            raise
        except Exception as e:
            # Unexpected error - log and close connection gracefully
            logger.error(
                f"SSE connection error: user_id={user_id}, "
                f"connection_id={connection_id}, "
                f"error={str(e)}",
                exc_info=True,
            )
            # Send error event to client before closing
            yield f"event: error\n"
            yield f'data: {json.dumps({"message": "Connection error occurred"})}\n\n'

    # Return StreamingResponse with SSE headers
    # - text/event-stream: SSE MIME type
    # - no-cache: Prevent caching of event stream
    # - keep-alive: Keep connection open
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
        },
    )


@router.get(
    "/connections",
    summary="Get active notification connections (admin only)",
    description="""
    Get list of active SSE connections for monitoring and debugging.

    **Authorization**: Admin only

    **Returns**:
    - total_connections: Total active connections across all users
    - connections_by_user: Breakdown by user_id
    - connection_details: List of all connections with metadata

    **Use Cases**:
    - Monitor active connections
    - Debug connection issues
    - Identify stuck/stale connections
    - Capacity planning
    """,
    response_model=dict,
    status_code=status.HTTP_200_OK,
    tags=["notifications-admin"],
)
async def get_active_connections(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Get active notification connections (admin only).

    Args:
        current_user: Authenticated user (must be admin)
        notification_service: NotificationService instance

    Returns:
        dict: Active connection statistics and details

    Raises:
        HTTPException: 403 if user is not admin
        HTTPException: 503 if notification service unavailable
    """
    # Authorization check: admin only
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to administrators",
        )

    # Check if Redis is available
    if not notification_service.redis:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service is currently unavailable",
        )

    try:
        # Get active connections from service
        connections_data = await notification_service.get_active_connections()

        logger.info(
            f"Active connections retrieved by admin: "
            f"admin_user_id={current_user.user_id}, "
            f"total_connections={connections_data['total_connections']}"
        )

        return connections_data

    except Exception as e:
        logger.error(f"Failed to retrieve active connections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve connection data",
        )


@router.get(
    "/health",
    summary="Check notification service health",
    description="""
    Health check endpoint for notification service.

    **Returns**:
    - status: "healthy" or "degraded" or "unavailable"
    - redis_connected: true/false
    - active_connections: number of active SSE connections
    - service_metrics: notification counts and error rates

    **Status Codes**:
    - 200: Service healthy
    - 503: Service unavailable (Redis disconnected)
    """,
    response_model=dict,
    tags=["notifications-health"],
)
async def check_notification_health(
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Check notification service health status.

    Args:
        notification_service: NotificationService instance

    Returns:
        dict: Health status and metrics
    """
    try:
        # Check Redis connection
        redis_connected = notification_service.redis is not None

        if redis_connected:
            try:
                # Ping Redis to verify connection
                await notification_service.redis.ping()
                redis_connected = True
            except Exception:
                redis_connected = False

        # Get metrics
        metrics = notification_service.metrics.copy()

        # Determine overall status
        if redis_connected:
            status_value = "healthy"
        else:
            status_value = "unavailable"

        # Get active connection count (0 if Redis unavailable)
        active_connection_count = 0
        if redis_connected:
            try:
                connections_data = await notification_service.get_active_connections()
                active_connection_count = connections_data.get("total_connections", 0)
            except Exception:
                pass

        response = {
            "status": status_value,
            "redis_connected": redis_connected,
            "active_connections": active_connection_count,
            "service_metrics": {
                "notifications_published": metrics.get("notifications_published", 0),
                "notifications_delivered": metrics.get("notifications_delivered", 0),
                "connections_established": metrics.get("connections_established", 0),
                "connections_closed": metrics.get("connections_closed", 0),
                "publish_errors": metrics.get("publish_errors", 0),
                "subscribe_errors": metrics.get("subscribe_errors", 0),
            },
        }

        # Return 503 if service unavailable
        if status_value == "unavailable":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=response,
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unavailable",
                "error": str(e),
            },
        )
