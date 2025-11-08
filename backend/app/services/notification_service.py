"""
Notification Service for Phase 1.4 Real-Time Push Notifications

Provides Server-Sent Events (SSE) based real-time notifications for content
generation progress updates using Redis Pub/Sub for distributed messaging
across Cloud Run instances.

Architecture:
- Redis Pub/Sub for distributed messaging between worker and API instances
- SSE (Server-Sent Events) for server→client push notifications
- Connection state tracking for heartbeat and cleanup
- User-specific notification channels (notifications:user:{user_id})

Performance Targets:
- Message publish latency: <10ms
- Message delivery latency: <50ms (Redis→SSE)
- Concurrent connections: 10,000+ per Cloud Run instance
- Connection memory footprint: <1KB per connection
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, Optional, Set, Any, AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import redis.asyncio as redis
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =============================================================================
# Notification Event Types
# =============================================================================


class NotificationEventType(str, Enum):
    """Types of notification events that can be sent to clients."""

    # Content generation lifecycle events
    CONTENT_REQUEST_CREATED = "content_request.created"
    CONTENT_REQUEST_QUEUED = "content_request.queued"
    CONTENT_GENERATION_STARTED = "content_generation.started"
    CONTENT_GENERATION_PROGRESS = "content_generation.progress"
    CONTENT_GENERATION_COMPLETED = "content_generation.completed"
    CONTENT_GENERATION_FAILED = "content_generation.failed"

    # System events
    SYSTEM_MAINTENANCE = "system.maintenance"
    SYSTEM_UPDATE = "system.update"

    # User events
    USER_SESSION_EXPIRES_SOON = "user.session_expires_soon"


# =============================================================================
# Notification Models (Pydantic Schemas)
# =============================================================================


class NotificationPayload(BaseModel):
    """
    Notification payload sent to clients via SSE.

    SSE Event Format:
        event: content_generation.progress
        data: {"content_request_id": "...", "progress_percentage": 45, ...}
        id: 1234567890
    """

    event_type: NotificationEventType = Field(
        ..., description="Type of notification event"
    )
    content_request_id: Optional[str] = Field(
        None, description="Content request ID (for content-related events)"
    )
    title: str = Field(..., description="Notification title (displayed to user)")
    message: str = Field(..., description="Notification message body")
    progress_percentage: Optional[int] = Field(
        None, ge=0, le=100, description="Progress percentage for generation events"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional event-specific data"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO 8601 timestamp",
    )

    class Config:
        use_enum_values = True


class ConnectionInfo(BaseModel):
    """Information about an active SSE connection."""

    connection_id: str
    user_id: str
    connected_at: str
    last_heartbeat_at: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


# =============================================================================
# Notification Service
# =============================================================================


class NotificationService:
    """
    Manages real-time push notifications via SSE and Redis Pub/Sub.

    Key Features:
    - User-specific notification channels
    - Connection state tracking with heartbeats
    - Automatic cleanup of stale connections
    - Graceful handling of Redis failures
    - Message persistence for missed notifications (future enhancement)

    Redis Keys:
    - notifications:channel:{user_id} - Pub/Sub channel for user notifications
    - notifications:connections:{user_id} - Set of active connection IDs
    - notifications:connection:{connection_id} - Connection metadata hash
    - notifications:heartbeat:{connection_id} - Last heartbeat timestamp

    Example Usage:
        # Initialize service
        service = NotificationService(redis_client)

        # Publish notification (from worker)
        await service.publish_notification(
            user_id="user_123",
            notification=NotificationPayload(
                event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
                content_request_id="req_456",
                title="Generating video",
                message="Analyzing your query...",
                progress_percentage=25
            )
        )

        # Subscribe to notifications (from API endpoint)
        async for message in service.subscribe_to_notifications(user_id="user_123"):
            # Send to client via SSE
            yield f"event: {message['event_type']}\\n"
            yield f"data: {json.dumps(message)}\\n\\n"
    """

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize notification service.

        Args:
            redis_client: Async Redis client (if None, creates from redis_url)
            redis_url: Redis connection URL (default: from environment REDIS_URL)
        """
        if redis_client:
            self.redis = redis_client
        else:
            redis_url = redis_url or os.getenv(
                "REDIS_URL", "redis://localhost:6379/0"
            )
            self.redis = redis.from_url(redis_url, decode_responses=True)

        # Active connections tracking (in-memory for this instance)
        # Note: This is per-instance. Cross-instance tracking uses Redis.
        self.active_connections: Dict[str, Set[str]] = {}  # user_id -> set of conn_ids

        # Performance metrics
        self.metrics = {
            "notifications_published": 0,
            "notifications_delivered": 0,
            "connections_established": 0,
            "connections_closed": 0,
            "publish_errors": 0,
            "subscribe_errors": 0,
        }

        # Configuration
        self.heartbeat_interval = int(os.getenv("SSE_HEARTBEAT_INTERVAL", "30"))
        self.connection_timeout = int(os.getenv("SSE_CONNECTION_TIMEOUT", "300"))
        self.max_backlog_messages = int(os.getenv("SSE_MAX_BACKLOG_MESSAGES", "100"))

    # =========================================================================
    # Core Publishing Methods (Called by Workers)
    # =========================================================================

    async def publish_notification(
        self,
        user_id: str,
        notification: NotificationPayload,
    ) -> bool:
        """
        Publish notification to user's channel via Redis Pub/Sub.

        This method is called by the content worker to send notifications
        to all connected clients for a specific user.

        Args:
            user_id: Target user ID
            notification: Notification payload (Pydantic model)

        Returns:
            True if published successfully, False otherwise

        Example:
            await service.publish_notification(
                user_id="user_123",
                notification=NotificationPayload(
                    event_type=NotificationEventType.CONTENT_GENERATION_STARTED,
                    content_request_id="req_456",
                    title="Video generation started",
                    message="We're creating your video about Newton's Laws...",
                    progress_percentage=0
                )
            )
        """
        try:
            # Build Redis Pub/Sub channel name
            channel = self._get_channel_name(user_id)

            # Serialize notification to JSON
            message_data = notification.model_dump()
            message_json = json.dumps(message_data)

            # Publish to Redis Pub/Sub channel
            start_time = time.time()
            subscribers_count = await self.redis.publish(channel, message_json)
            publish_latency = (time.time() - start_time) * 1000  # ms

            # Metrics
            self.metrics["notifications_published"] += 1

            logger.info(
                f"Published notification to {channel} "
                f"(event={notification.event_type}, "
                f"subscribers={subscribers_count}, "
                f"latency={publish_latency:.2f}ms)"
            )

            # Log warning if no subscribers (user may not be connected)
            if subscribers_count == 0:
                logger.warning(
                    f"No subscribers for {channel} - notification may be missed"
                )

            return True

        except Exception as e:
            self.metrics["publish_errors"] += 1
            logger.error(
                f"Failed to publish notification to user {user_id}: {e}",
                exc_info=True,
            )
            return False

    async def publish_batch_notifications(
        self,
        user_id: str,
        notifications: list[NotificationPayload],
    ) -> int:
        """
        Publish multiple notifications to user's channel (batch operation).

        Useful for sending multiple progress updates or events at once.

        Args:
            user_id: Target user ID
            notifications: List of notification payloads

        Returns:
            Number of successfully published notifications
        """
        success_count = 0

        for notification in notifications:
            if await self.publish_notification(user_id, notification):
                success_count += 1

        return success_count

    # =========================================================================
    # Core Subscription Methods (Called by API Endpoints)
    # =========================================================================

    async def subscribe_to_notifications(
        self,
        user_id: str,
        connection_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Subscribe to user's notification channel and yield messages as they arrive.

        This is an async generator that yields notification dictionaries
        suitable for SSE streaming. It automatically handles:
        - Redis Pub/Sub subscription
        - Connection tracking
        - Heartbeat messages
        - Graceful cleanup on disconnect

        Args:
            user_id: User ID to subscribe for
            connection_id: Unique connection ID (e.g., UUID)
            user_agent: Client User-Agent header (optional)
            ip_address: Client IP address (optional)

        Yields:
            Dict with notification data + metadata

        Example:
            async for message in service.subscribe_to_notifications(
                user_id="user_123",
                connection_id=str(uuid.uuid4())
            ):
                # Send to client via SSE
                yield f"event: {message['event']}\\n"
                yield f"data: {json.dumps(message['data'])}\\n\\n"
        """
        pubsub = None

        try:
            # Track connection
            await self._track_connection(
                user_id=user_id,
                connection_id=connection_id,
                user_agent=user_agent,
                ip_address=ip_address,
            )

            # Create Redis Pub/Sub subscription
            channel = self._get_channel_name(user_id)
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)

            logger.info(
                f"User {user_id} subscribed to {channel} (conn={connection_id})"
            )

            # Metrics
            self.metrics["connections_established"] += 1

            # Send initial connection confirmation
            yield {
                "event": "connection.established",
                "data": {
                    "connection_id": connection_id,
                    "message": "Connected to notification service",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            }

            # Listen for messages with periodic heartbeats
            last_heartbeat = time.time()

            while True:
                try:
                    # Non-blocking message check with timeout
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=1.0,
                    )

                    if message and message["type"] == "message":
                        # Parse notification data
                        notification_data = json.loads(message["data"])

                        # Update metrics
                        self.metrics["notifications_delivered"] += 1

                        # Yield to SSE stream
                        yield {
                            "event": notification_data.get("event_type", "notification"),
                            "data": notification_data,
                        }

                        # Update heartbeat
                        await self._update_heartbeat(connection_id)
                        last_heartbeat = time.time()

                    # Send heartbeat if interval exceeded
                    elif time.time() - last_heartbeat > self.heartbeat_interval:
                        await self._update_heartbeat(connection_id)
                        last_heartbeat = time.time()

                        # Send heartbeat to client (SSE comment to keep connection alive)
                        yield {
                            "event": "heartbeat",
                            "data": {"timestamp": datetime.utcnow().isoformat()},
                        }

                except asyncio.TimeoutError:
                    # No message received, continue loop (heartbeat will be sent if needed)
                    continue

                except asyncio.CancelledError:
                    # Client disconnected gracefully
                    logger.info(
                        f"Client disconnected gracefully (user={user_id}, conn={connection_id})"
                    )
                    break

                except Exception as e:
                    # Unexpected error in message processing
                    logger.error(
                        f"Error processing message for user {user_id}: {e}",
                        exc_info=True,
                    )
                    self.metrics["subscribe_errors"] += 1
                    # Continue listening unless it's a critical error
                    if isinstance(e, (redis.ConnectionError, redis.TimeoutError)):
                        break

        except Exception as e:
            logger.error(
                f"Fatal error in notification subscription for user {user_id}: {e}",
                exc_info=True,
            )
            self.metrics["subscribe_errors"] += 1

        finally:
            # Cleanup: unsubscribe and remove connection tracking
            if pubsub:
                try:
                    await pubsub.unsubscribe()
                    await pubsub.close()
                except Exception as e:
                    logger.error(f"Error closing pubsub connection: {e}")

            await self._untrack_connection(user_id, connection_id)
            self.metrics["connections_closed"] += 1

            logger.info(
                f"User {user_id} unsubscribed from notifications (conn={connection_id})"
            )

    # =========================================================================
    # Connection Tracking & Management
    # =========================================================================

    async def _track_connection(
        self,
        user_id: str,
        connection_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Track active connection in Redis and local memory.

        Redis Keys Created:
        - notifications:connections:{user_id} - Set of active connection IDs
        - notifications:connection:{connection_id} - Connection metadata hash
        - notifications:heartbeat:{connection_id} - Last heartbeat timestamp

        Args:
            user_id: User ID
            connection_id: Unique connection ID
            user_agent: Client User-Agent
            ip_address: Client IP address

        Returns:
            True if successful
        """
        try:
            # Store in local memory
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(connection_id)

            # Store in Redis for cross-instance tracking
            connections_key = f"notifications:connections:{user_id}"
            connection_key = f"notifications:connection:{connection_id}"
            heartbeat_key = f"notifications:heartbeat:{connection_id}"

            # Add connection ID to user's connection set
            await self.redis.sadd(connections_key, connection_id)

            # Store connection metadata
            connection_info = {
                "user_id": user_id,
                "connection_id": connection_id,
                "connected_at": datetime.utcnow().isoformat(),
                "last_heartbeat_at": datetime.utcnow().isoformat(),
                "user_agent": user_agent or "",
                "ip_address": ip_address or "",
            }
            await self.redis.hset(connection_key, mapping=connection_info)

            # Set initial heartbeat timestamp
            await self.redis.setex(
                heartbeat_key,
                timedelta(seconds=self.connection_timeout),
                datetime.utcnow().isoformat(),
            )

            # Set expiration on connection metadata (auto-cleanup)
            await self.redis.expire(connection_key, self.connection_timeout)

            logger.debug(
                f"Tracked connection: user={user_id}, conn={connection_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track connection: {e}", exc_info=True)
            return False

    async def _untrack_connection(self, user_id: str, connection_id: str) -> bool:
        """
        Remove connection tracking from Redis and local memory.

        Args:
            user_id: User ID
            connection_id: Connection ID to remove

        Returns:
            True if successful
        """
        try:
            # Remove from local memory
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(connection_id)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            # Remove from Redis
            connections_key = f"notifications:connections:{user_id}"
            connection_key = f"notifications:connection:{connection_id}"
            heartbeat_key = f"notifications:heartbeat:{connection_id}"

            await self.redis.srem(connections_key, connection_id)
            await self.redis.delete(connection_key)
            await self.redis.delete(heartbeat_key)

            logger.debug(
                f"Untracked connection: user={user_id}, conn={connection_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to untrack connection: {e}", exc_info=True)
            return False

    async def _update_heartbeat(self, connection_id: str) -> bool:
        """
        Update heartbeat timestamp for connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if successful
        """
        try:
            heartbeat_key = f"notifications:heartbeat:{connection_id}"
            await self.redis.setex(
                heartbeat_key,
                timedelta(seconds=self.connection_timeout),
                datetime.utcnow().isoformat(),
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update heartbeat: {e}", exc_info=True)
            return False

    # =========================================================================
    # Admin & Monitoring Methods
    # =========================================================================

    async def get_active_connections(self, user_id: str) -> list[ConnectionInfo]:
        """
        Get list of active connections for a user.

        Args:
            user_id: User ID

        Returns:
            List of ConnectionInfo objects
        """
        try:
            connections_key = f"notifications:connections:{user_id}"
            connection_ids = await self.redis.smembers(connections_key)

            connections = []
            for conn_id in connection_ids:
                connection_key = f"notifications:connection:{conn_id}"
                conn_data = await self.redis.hgetall(connection_key)

                if conn_data:
                    connections.append(ConnectionInfo(**conn_data))

            return connections

        except Exception as e:
            logger.error(f"Failed to get active connections: {e}", exc_info=True)
            return []

    async def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get total number of active connections.

        Args:
            user_id: If provided, count for specific user. Otherwise, total.

        Returns:
            Number of active connections
        """
        try:
            if user_id:
                connections_key = f"notifications:connections:{user_id}"
                return await self.redis.scard(connections_key)
            else:
                # Count all connection keys
                pattern = "notifications:connections:*"
                total = 0
                async for key in self.redis.scan_iter(match=pattern):
                    total += await self.redis.scard(key)
                return total

        except Exception as e:
            logger.error(f"Failed to get connection count: {e}", exc_info=True)
            return 0

    async def cleanup_stale_connections(self) -> int:
        """
        Remove stale connections that haven't sent heartbeat.

        This should be run periodically (e.g., every 5 minutes) as a background task.

        Returns:
            Number of connections cleaned up
        """
        try:
            cleanup_count = 0
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.connection_timeout)

            # Scan all heartbeat keys
            pattern = "notifications:heartbeat:*"
            async for heartbeat_key in self.redis.scan_iter(match=pattern):
                # Check if heartbeat exists (TTL will auto-delete stale ones)
                last_heartbeat = await self.redis.get(heartbeat_key)

                if not last_heartbeat:
                    # Heartbeat expired, clean up connection
                    connection_id = heartbeat_key.split(":")[-1]

                    # Find user_id from connection metadata
                    connection_key = f"notifications:connection:{connection_id}"
                    conn_data = await self.redis.hgetall(connection_key)

                    if conn_data and "user_id" in conn_data:
                        user_id = conn_data["user_id"]
                        await self._untrack_connection(user_id, connection_id)
                        cleanup_count += 1

            if cleanup_count > 0:
                logger.info(f"Cleaned up {cleanup_count} stale connections")

            return cleanup_count

        except Exception as e:
            logger.error(f"Failed to cleanup stale connections: {e}", exc_info=True)
            return 0

    def get_metrics(self) -> Dict[str, int]:
        """
        Get service performance metrics.

        Returns:
            Dict with metric counters
        """
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset all metrics counters (for testing)."""
        self.metrics = {
            "notifications_published": 0,
            "notifications_delivered": 0,
            "connections_established": 0,
            "connections_closed": 0,
            "publish_errors": 0,
            "subscribe_errors": 0,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _get_channel_name(self, user_id: str) -> str:
        """
        Get Redis Pub/Sub channel name for user.

        Args:
            user_id: User ID

        Returns:
            Channel name (e.g., "notifications:user:user_123")
        """
        return f"notifications:user:{user_id}"


# =============================================================================
# Helper Functions for FastAPI Integration
# =============================================================================


async def get_notification_service() -> NotificationService:
    """
    Dependency injection for FastAPI endpoints.

    Usage:
        @router.get("/notifications/stream")
        async def notification_stream(
            service: NotificationService = Depends(get_notification_service),
            current_user: User = Depends(get_current_user)
        ):
            ...
    """
    # In production, this would get Redis client from app state
    # For now, create a new instance (will be optimized in endpoint integration)
    service = NotificationService()
    return service
