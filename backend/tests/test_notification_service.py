"""
Unit Tests for NotificationService (Phase 1.4)

Test Coverage:
- Notification publishing (success, failure, batch)
- Notification subscription (SSE stream, heartbeats, disconnection)
- Connection tracking and management
- Stale connection cleanup
- Metrics and monitoring
- Error handling and recovery
- Redis Pub/Sub integration

Target Coverage: >90%
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import redis.asyncio as redis

from app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationEventType,
    ConnectionInfo,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def redis_client():
    """
    Create Redis client for testing.

    In real integration tests, this would connect to a real Redis instance.
    For unit tests, we'll mock it.
    """
    client = AsyncMock(spec=redis.Redis)
    yield client
    # Cleanup would happen here if using real Redis


@pytest.fixture
def notification_service(redis_client):
    """Create NotificationService instance with mocked Redis."""
    service = NotificationService(redis_client=redis_client)
    return service


@pytest.fixture
def sample_notification():
    """Create sample notification payload."""
    return NotificationPayload(
        event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
        content_request_id="req_12345",
        title="Generating video",
        message="Analyzing your query about Newton's Laws...",
        progress_percentage=25,
        metadata={"stage": "nlu_processing"},
    )


# =============================================================================
# Test: Notification Publishing
# =============================================================================


class TestNotificationPublishing:
    """Test notification publishing to Redis Pub/Sub."""

    @pytest.mark.asyncio
    async def test_publish_notification_success(
        self, notification_service, sample_notification
    ):
        """Test successful notification publishing."""
        # Arrange
        user_id = "user_123"
        notification_service.redis.publish = AsyncMock(return_value=2)  # 2 subscribers

        # Act
        result = await notification_service.publish_notification(
            user_id=user_id, notification=sample_notification
        )

        # Assert
        assert result is True
        assert notification_service.metrics["notifications_published"] == 1
        assert notification_service.metrics["publish_errors"] == 0

        # Verify Redis publish was called with correct args
        notification_service.redis.publish.assert_called_once()
        call_args = notification_service.redis.publish.call_args
        assert call_args[0][0] == "notifications:user:user_123"  # channel name

        # Verify message content
        published_message = json.loads(call_args[0][1])
        assert published_message["event_type"] == "content_generation.progress"
        assert published_message["content_request_id"] == "req_12345"
        assert published_message["progress_percentage"] == 25

    @pytest.mark.asyncio
    async def test_publish_notification_no_subscribers(
        self, notification_service, sample_notification
    ):
        """Test publishing when no subscribers are listening."""
        # Arrange
        user_id = "user_456"
        notification_service.redis.publish = AsyncMock(return_value=0)  # No subscribers

        # Act
        result = await notification_service.publish_notification(
            user_id=user_id, notification=sample_notification
        )

        # Assert
        assert result is True  # Publishing succeeds even if no subscribers
        assert notification_service.metrics["notifications_published"] == 1

    @pytest.mark.asyncio
    async def test_publish_notification_redis_error(
        self, notification_service, sample_notification
    ):
        """Test handling Redis connection error during publish."""
        # Arrange
        user_id = "user_789"
        notification_service.redis.publish = AsyncMock(
            side_effect=redis.ConnectionError("Redis connection lost")
        )

        # Act
        result = await notification_service.publish_notification(
            user_id=user_id, notification=sample_notification
        )

        # Assert
        assert result is False
        assert notification_service.metrics["publish_errors"] == 1

    @pytest.mark.asyncio
    async def test_publish_batch_notifications(
        self, notification_service, sample_notification
    ):
        """Test batch publishing multiple notifications."""
        # Arrange
        user_id = "user_batch"
        notification_service.redis.publish = AsyncMock(return_value=1)

        notifications = [
            NotificationPayload(
                event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
                content_request_id="req_1",
                title="Step 1",
                message="Processing...",
                progress_percentage=10,
            ),
            NotificationPayload(
                event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
                content_request_id="req_1",
                title="Step 2",
                message="Generating...",
                progress_percentage=50,
            ),
            NotificationPayload(
                event_type=NotificationEventType.CONTENT_GENERATION_COMPLETED,
                content_request_id="req_1",
                title="Complete",
                message="Video ready!",
                progress_percentage=100,
            ),
        ]

        # Act
        success_count = await notification_service.publish_batch_notifications(
            user_id=user_id, notifications=notifications
        )

        # Assert
        assert success_count == 3
        assert notification_service.redis.publish.call_count == 3
        assert notification_service.metrics["notifications_published"] == 3

    @pytest.mark.asyncio
    async def test_publish_notification_different_event_types(
        self, notification_service
    ):
        """Test publishing different event types."""
        notification_service.redis.publish = AsyncMock(return_value=1)

        # Test each event type
        event_types = [
            NotificationEventType.CONTENT_REQUEST_CREATED,
            NotificationEventType.CONTENT_REQUEST_QUEUED,
            NotificationEventType.CONTENT_GENERATION_STARTED,
            NotificationEventType.CONTENT_GENERATION_PROGRESS,
            NotificationEventType.CONTENT_GENERATION_COMPLETED,
            NotificationEventType.CONTENT_GENERATION_FAILED,
            NotificationEventType.SYSTEM_MAINTENANCE,
            NotificationEventType.USER_SESSION_EXPIRES_SOON,
        ]

        for event_type in event_types:
            notification = NotificationPayload(
                event_type=event_type,
                title=f"Test {event_type}",
                message="Test message",
            )

            result = await notification_service.publish_notification(
                user_id="user_test", notification=notification
            )

            assert result is True


# =============================================================================
# Test: Notification Subscription (SSE)
# =============================================================================


class TestNotificationSubscription:
    """Test SSE notification subscription and streaming."""

    @pytest.mark.asyncio
    async def test_subscribe_to_notifications_basic(self, notification_service):
        """Test basic subscription flow."""
        # Arrange
        user_id = "user_sub_test"
        connection_id = "conn_123"

        # Mock Redis Pub/Sub
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        # Mock getting messages
        test_message = {
            "type": "message",
            "data": json.dumps({
                "event_type": "content_generation.progress",
                "title": "Generating",
                "message": "Progress update",
                "progress_percentage": 50,
                "timestamp": datetime.utcnow().isoformat(),
            })
        }

        mock_pubsub.get_message = AsyncMock(side_effect=[
            test_message,
            None,  # Timeout
            asyncio.CancelledError(),  # Simulate disconnection
        ])

        notification_service.redis.pubsub = Mock(return_value=mock_pubsub)
        notification_service.redis.sadd = AsyncMock()
        notification_service.redis.hset = AsyncMock()
        notification_service.redis.setex = AsyncMock()
        notification_service.redis.expire = AsyncMock()
        notification_service.redis.srem = AsyncMock()
        notification_service.redis.delete = AsyncMock()

        # Act
        messages_received = []
        try:
            async for message in notification_service.subscribe_to_notifications(
                user_id=user_id,
                connection_id=connection_id,
            ):
                messages_received.append(message)
                if len(messages_received) >= 2:  # Get connection confirmation + 1 message
                    break
        except asyncio.CancelledError:
            pass

        # Assert
        assert len(messages_received) >= 2

        # First message is connection confirmation
        assert messages_received[0]["event"] == "connection.established"
        assert messages_received[0]["data"]["connection_id"] == connection_id

        # Second message is the actual notification
        assert messages_received[1]["event"] == "content_generation.progress"
        assert messages_received[1]["data"]["progress_percentage"] == 50

        # Verify connection tracking was called
        notification_service.redis.sadd.assert_called()
        notification_service.redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_subscribe_heartbeat_mechanism(self, notification_service):
        """Test that heartbeat updates are called during subscription."""
        # Arrange
        user_id = "user_heartbeat"
        connection_id = "conn_hb"
        notification_service.heartbeat_interval = 0.1  # 100ms for faster testing

        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        # Return None (timeout) to trigger heartbeat logic, then cancel
        mock_pubsub.get_message = AsyncMock(side_effect=[
            None,  # Timeout (will trigger heartbeat check)
            asyncio.CancelledError(),  # Stop
        ])

        notification_service.redis.pubsub = Mock(return_value=mock_pubsub)
        notification_service.redis.sadd = AsyncMock()
        notification_service.redis.hset = AsyncMock()
        notification_service.redis.setex = AsyncMock()
        notification_service.redis.expire = AsyncMock()
        notification_service.redis.srem = AsyncMock()
        notification_service.redis.delete = AsyncMock()

        # Act
        messages_received = []

        try:
            async for message in notification_service.subscribe_to_notifications(
                user_id=user_id,
                connection_id=connection_id,
            ):
                messages_received.append(message)
        except asyncio.CancelledError:
            pass

        # Assert: Should have received at least connection confirmation
        assert len(messages_received) >= 1
        assert messages_received[0]["event"] == "connection.established"

        # Verify heartbeat updates were called (initial tracking + potential heartbeat)
        assert notification_service.redis.setex.call_count >= 1  # At minimum, initial heartbeat


# =============================================================================
# Test: Connection Tracking
# =============================================================================


class TestConnectionTracking:
    """Test connection state tracking and management."""

    @pytest.mark.asyncio
    async def test_track_connection(self, notification_service):
        """Test tracking a new connection."""
        # Arrange
        user_id = "user_track"
        connection_id = "conn_track_1"
        user_agent = "Mozilla/5.0 ..."
        ip_address = "192.168.1.1"

        notification_service.redis.sadd = AsyncMock(return_value=1)
        notification_service.redis.hset = AsyncMock()
        notification_service.redis.setex = AsyncMock()
        notification_service.redis.expire = AsyncMock()

        # Act
        result = await notification_service._track_connection(
            user_id=user_id,
            connection_id=connection_id,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        # Assert
        assert result is True

        # Verify connection added to user's set
        notification_service.redis.sadd.assert_called_once_with(
            "notifications:connections:user_track", "conn_track_1"
        )

        # Verify connection metadata stored
        notification_service.redis.hset.assert_called_once()
        call_args = notification_service.redis.hset.call_args
        assert call_args[0][0] == "notifications:connection:conn_track_1"
        assert "user_id" in call_args[1]["mapping"]
        assert call_args[1]["mapping"]["user_agent"] == user_agent

        # Verify heartbeat timestamp set
        notification_service.redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_untrack_connection(self, notification_service):
        """Test removing connection tracking."""
        # Arrange
        user_id = "user_untrack"
        connection_id = "conn_untrack_1"

        # Track connection first
        notification_service.active_connections[user_id] = {connection_id}

        notification_service.redis.srem = AsyncMock()
        notification_service.redis.delete = AsyncMock()

        # Act
        result = await notification_service._untrack_connection(
            user_id=user_id, connection_id=connection_id
        )

        # Assert
        assert result is True
        assert user_id not in notification_service.active_connections

        # Verify Redis cleanup
        notification_service.redis.srem.assert_called_once()
        assert notification_service.redis.delete.call_count == 2  # connection + heartbeat

    @pytest.mark.asyncio
    async def test_get_active_connections(self, notification_service):
        """Test retrieving active connections for a user."""
        # Arrange
        user_id = "user_active"
        notification_service.redis.smembers = AsyncMock(
            return_value={"conn_1", "conn_2"}
        )

        # Mock connection data
        conn_1_data = {
            "user_id": user_id,
            "connection_id": "conn_1",
            "connected_at": datetime.utcnow().isoformat(),
            "last_heartbeat_at": datetime.utcnow().isoformat(),
        }
        conn_2_data = {
            "user_id": user_id,
            "connection_id": "conn_2",
            "connected_at": datetime.utcnow().isoformat(),
            "last_heartbeat_at": datetime.utcnow().isoformat(),
        }

        notification_service.redis.hgetall = AsyncMock(
            side_effect=[conn_1_data, conn_2_data]
        )

        # Act
        connections = await notification_service.get_active_connections(user_id)

        # Assert
        assert len(connections) == 2
        assert all(isinstance(conn, ConnectionInfo) for conn in connections)
        assert {conn.connection_id for conn in connections} == {"conn_1", "conn_2"}

    @pytest.mark.asyncio
    async def test_get_connection_count_specific_user(self, notification_service):
        """Test getting connection count for specific user."""
        # Arrange
        user_id = "user_count"
        notification_service.redis.scard = AsyncMock(return_value=3)

        # Act
        count = await notification_service.get_connection_count(user_id=user_id)

        # Assert
        assert count == 3
        notification_service.redis.scard.assert_called_once_with(
            f"notifications:connections:{user_id}"
        )

    @pytest.mark.asyncio
    async def test_update_heartbeat(self, notification_service):
        """Test updating heartbeat timestamp."""
        # Arrange
        connection_id = "conn_heartbeat"
        notification_service.redis.setex = AsyncMock()

        # Act
        result = await notification_service._update_heartbeat(connection_id)

        # Assert
        assert result is True
        notification_service.redis.setex.assert_called_once()
        call_args = notification_service.redis.setex.call_args
        assert call_args[0][0] == f"notifications:heartbeat:{connection_id}"


# =============================================================================
# Test: Stale Connection Cleanup
# =============================================================================


class TestStaleConnectionCleanup:
    """Test automatic cleanup of stale connections."""

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections(self, notification_service):
        """Test cleaning up stale connections."""
        # Arrange
        stale_heartbeat_keys = [
            "notifications:heartbeat:conn_stale_1",
            "notifications:heartbeat:conn_stale_2",
        ]

        # Mock Redis scan to return stale heartbeat keys
        async def mock_scan_iter(match):
            for key in stale_heartbeat_keys:
                yield key

        notification_service.redis.scan_iter = mock_scan_iter

        # First heartbeat key has expired (returns None)
        # Second heartbeat key still exists
        notification_service.redis.get = AsyncMock(side_effect=[None, "timestamp"])

        # Mock connection metadata
        conn_1_data = {"user_id": "user_1"}
        notification_service.redis.hgetall = AsyncMock(return_value=conn_1_data)

        notification_service.redis.srem = AsyncMock()
        notification_service.redis.delete = AsyncMock()

        # Act
        cleanup_count = await notification_service.cleanup_stale_connections()

        # Assert
        assert cleanup_count == 1  # Only conn_stale_1 was cleaned
        notification_service.redis.srem.assert_called_once()


# =============================================================================
# Test: Metrics and Monitoring
# =============================================================================


class TestMetricsAndMonitoring:
    """Test metrics tracking and reporting."""

    def test_get_metrics(self, notification_service):
        """Test retrieving metrics."""
        # Arrange
        notification_service.metrics = {
            "notifications_published": 100,
            "notifications_delivered": 95,
            "connections_established": 50,
            "connections_closed": 45,
            "publish_errors": 2,
            "subscribe_errors": 1,
        }

        # Act
        metrics = notification_service.get_metrics()

        # Assert
        assert metrics["notifications_published"] == 100
        assert metrics["notifications_delivered"] == 95
        assert metrics["publish_errors"] == 2

    def test_reset_metrics(self, notification_service):
        """Test resetting metrics."""
        # Arrange
        notification_service.metrics["notifications_published"] = 100

        # Act
        notification_service.reset_metrics()

        # Assert
        assert notification_service.metrics["notifications_published"] == 0
        assert notification_service.metrics["notifications_delivered"] == 0


# =============================================================================
# Test: Helper Methods
# =============================================================================


class TestHelperMethods:
    """Test utility helper methods."""

    def test_get_channel_name(self, notification_service):
        """Test Redis channel name generation."""
        # Act
        channel = notification_service._get_channel_name("user_123")

        # Assert
        assert channel == "notifications:user:user_123"

    def test_get_channel_name_consistency(self, notification_service):
        """Test that channel names are consistent."""
        # Act
        channel1 = notification_service._get_channel_name("test_user")
        channel2 = notification_service._get_channel_name("test_user")

        # Assert
        assert channel1 == channel2


# =============================================================================
# Test: NotificationPayload Model
# =============================================================================


class TestNotificationPayload:
    """Test NotificationPayload Pydantic model."""

    def test_notification_payload_creation(self):
        """Test creating notification payload."""
        # Act
        payload = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_STARTED,
            content_request_id="req_test",
            title="Test Title",
            message="Test Message",
            progress_percentage=0,
        )

        # Assert
        assert payload.event_type == NotificationEventType.CONTENT_GENERATION_STARTED
        assert payload.content_request_id == "req_test"
        assert payload.progress_percentage == 0
        assert isinstance(payload.timestamp, str)

    def test_notification_payload_validation_progress_percentage(self):
        """Test progress percentage validation."""
        # Valid range
        payload = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
            title="Test",
            message="Test",
            progress_percentage=50,
        )
        assert payload.progress_percentage == 50

        # Test boundary values
        payload_min = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
            title="Test",
            message="Test",
            progress_percentage=0,
        )
        assert payload_min.progress_percentage == 0

        payload_max = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
            title="Test",
            message="Test",
            progress_percentage=100,
        )
        assert payload_max.progress_percentage == 100

    def test_notification_payload_optional_fields(self):
        """Test notification with optional fields."""
        # Minimal payload
        payload = NotificationPayload(
            event_type=NotificationEventType.SYSTEM_MAINTENANCE,
            title="Maintenance",
            message="System maintenance scheduled",
        )

        assert payload.content_request_id is None
        assert payload.progress_percentage is None
        assert payload.metadata == {}

    def test_notification_payload_metadata(self):
        """Test notification with custom metadata."""
        # Act
        payload = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
            title="Test",
            message="Test",
            metadata={
                "stage": "script_generation",
                "estimated_time_remaining": 120,
                "custom_field": "value",
            },
        )

        # Assert
        assert payload.metadata["stage"] == "script_generation"
        assert payload.metadata["estimated_time_remaining"] == 120

    def test_notification_payload_serialization(self):
        """Test notification serialization to dict."""
        # Arrange
        payload = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_COMPLETED,
            content_request_id="req_done",
            title="Complete",
            message="Your video is ready!",
            progress_percentage=100,
        )

        # Act
        payload_dict = payload.model_dump()

        # Assert
        assert payload_dict["event_type"] == "content_generation.completed"
        assert payload_dict["content_request_id"] == "req_done"
        assert "timestamp" in payload_dict


# =============================================================================
# Test: Error Handling and Edge Cases
# =============================================================================


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_publish_with_redis_timeout(self, notification_service, sample_notification):
        """Test handling Redis timeout during publish."""
        # Arrange
        notification_service.redis.publish = AsyncMock(
            side_effect=redis.TimeoutError("Redis timeout")
        )

        # Act
        result = await notification_service.publish_notification(
            user_id="user_test", notification=sample_notification
        )

        # Assert
        assert result is False
        assert notification_service.metrics["publish_errors"] == 1

    @pytest.mark.asyncio
    async def test_track_connection_redis_failure(self, notification_service):
        """Test graceful handling when connection tracking fails."""
        # Arrange
        notification_service.redis.sadd = AsyncMock(
            side_effect=Exception("Redis error")
        )

        # Act
        result = await notification_service._track_connection(
            user_id="user_fail",
            connection_id="conn_fail",
        )

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_get_active_connections_empty(self, notification_service):
        """Test getting connections when none exist."""
        # Arrange
        notification_service.redis.smembers = AsyncMock(return_value=set())

        # Act
        connections = await notification_service.get_active_connections("user_none")

        # Assert
        assert connections == []

    @pytest.mark.asyncio
    async def test_cleanup_stale_connections_redis_error(self, notification_service):
        """Test stale connection cleanup with Redis errors."""
        # Arrange
        notification_service.redis.scan_iter = AsyncMock(
            side_effect=redis.ConnectionError("Redis down")
        )

        # Act
        cleanup_count = await notification_service.cleanup_stale_connections()

        # Assert
        assert cleanup_count == 0  # Returns 0 on error, doesn't crash


# =============================================================================
# Test: Integration Scenarios
# =============================================================================


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_notification_flow(self, notification_service):
        """
        Test complete flow: publish notification → subscriber receives it.

        This simulates:
        1. Worker publishes progress update
        2. Client subscribed via SSE receives the update
        """
        # This would require a real Redis instance for true integration testing
        # For unit tests, we verify the components work correctly in isolation

        # Setup
        user_id = "user_integration"
        notification = NotificationPayload(
            event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
            content_request_id="req_int",
            title="Generating",
            message="Video generation in progress",
            progress_percentage=75,
        )

        notification_service.redis.publish = AsyncMock(return_value=1)

        # Act: Publish
        publish_result = await notification_service.publish_notification(
            user_id=user_id, notification=notification
        )

        # Assert: Publishing succeeded
        assert publish_result is True
        assert notification_service.metrics["notifications_published"] == 1

    @pytest.mark.asyncio
    async def test_concurrent_publishing(self, notification_service):
        """Test publishing notifications concurrently."""
        # Arrange
        user_id = "user_concurrent"
        notification_service.redis.publish = AsyncMock(return_value=1)

        notifications = [
            NotificationPayload(
                event_type=NotificationEventType.CONTENT_GENERATION_PROGRESS,
                title=f"Progress {i}",
                message=f"Step {i}",
                progress_percentage=i * 10,
            )
            for i in range(10)
        ]

        # Act: Publish concurrently
        tasks = [
            notification_service.publish_notification(user_id, notif)
            for notif in notifications
        ]
        results = await asyncio.gather(*tasks)

        # Assert
        assert all(results)
        assert notification_service.metrics["notifications_published"] == 10
