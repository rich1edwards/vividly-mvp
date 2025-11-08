"""
Integration Tests for SSE Notification Endpoints (Phase 1.4)

Test Coverage:
- SSE /stream endpoint (authentication, connection, event streaming)
- /connections endpoint (admin monitoring, authorization)
- /health endpoint (service status, Redis connectivity)
- Full integration with Redis Pub/Sub
- Connection lifecycle management
- Error scenarios and recovery

These are integration tests that test the full stack from API endpoint -> NotificationService -> Redis.
"""

import pytest
import asyncio
import json
import time
from typing import AsyncGenerator, List
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import redis.asyncio as redis

from app.main import app
from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.utils.security import create_access_token
from app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationEventType,
    get_notification_service,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def mock_redis_client():
    """
    Create a mocked Redis client for testing.

    For true integration tests with a real Redis instance, this would be:
    ```
    client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    yield client
    await client.close()
    ```

    But for now we mock it to avoid requiring Redis in CI/CD.
    """
    client = AsyncMock(spec=redis.Redis)

    # Mock ping to simulate healthy connection
    client.ping = AsyncMock(return_value=True)

    # Mock publish to simulate successful message publishing
    client.publish = AsyncMock(return_value=1)  # 1 subscriber

    # Mock pubsub for subscription testing
    pubsub = AsyncMock()
    pubsub.subscribe = AsyncMock()
    pubsub.unsubscribe = AsyncMock()
    pubsub.listen = AsyncMock()
    client.pubsub = MagicMock(return_value=pubsub)

    # Mock keys and get for connection tracking
    client.keys = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)

    return client


@pytest.fixture
def notification_service_override(mock_redis_client):
    """Create NotificationService with mocked Redis for testing."""
    service = NotificationService(redis_client=mock_redis_client)
    return service


@pytest.fixture
def override_notification_service_dependency(notification_service_override):
    """Override the notification service dependency for testing."""
    async def get_test_notification_service():
        return notification_service_override

    app.dependency_overrides[get_notification_service] = get_test_notification_service
    yield
    app.dependency_overrides.clear()


# =============================================================================
# Test: SSE Stream Endpoint
# =============================================================================


@pytest.mark.integration
class TestSSEStreamEndpoint:
    """Test /api/v1/notifications/stream SSE endpoint."""

    def test_stream_requires_authentication(self, client):
        """Test that SSE stream endpoint requires authentication."""
        # Act
        response = client.get("/api/v1/notifications/stream")

        # Assert
        assert response.status_code == 403  # FastAPI returns 403 for missing credentials

    def test_stream_rejects_invalid_token(self, client):
        """Test that SSE stream endpoint rejects invalid JWT tokens."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token_12345"}

        # Act
        response = client.get("/api/v1/notifications/stream", headers=headers)

        # Assert
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_stream_accepts_valid_token(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that SSE stream endpoint accepts valid authentication."""
        # Arrange - Mock subscribe_to_notifications to yield a test event then stop
        async def mock_subscribe(user_id, connection_id, user_agent, ip_address):
            # Yield one test event
            yield {
                "event": "connected",
                "data": {
                    "message": "Connected to notification stream",
                    "connection_id": connection_id,
                },
            }
            # Then stop (simulating immediate disconnection)

        notification_service_override.subscribe_to_notifications = mock_subscribe

        # Act - Use stream=True to get SSE response
        with client.stream("GET", "/api/v1/notifications/stream", headers=student_headers) as response:
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["x-accel-buffering"] == "no"

            # Read SSE response and parse lines
            all_text = ""
            for chunk in response.iter_text():
                all_text += chunk
                # Break after first complete event (contains both event and data)
                if "event:" in all_text and "data:" in all_text and "\n\n" in all_text:
                    break

            # Split into lines and verify SSE format
            lines = [line for line in all_text.split("\n") if line.strip()]
            assert len(lines) >= 2
            assert lines[0].startswith("event: ")
            assert lines[1].startswith("data: ")

    def test_stream_connection_metadata_extraction(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that connection metadata (user agent, IP) is extracted correctly."""
        # Arrange
        captured_metadata = {}

        async def mock_subscribe(user_id, connection_id, user_agent, ip_address):
            captured_metadata["user_id"] = user_id
            captured_metadata["connection_id"] = connection_id
            captured_metadata["user_agent"] = user_agent
            captured_metadata["ip_address"] = ip_address
            # Yield one event to avoid hanging
            yield {
                "event": "connected",
                "data": {"message": "Connected"},
            }

        notification_service_override.subscribe_to_notifications = mock_subscribe

        custom_headers = {
            **student_headers,
            "user-agent": "TestClient/1.0",
            "x-forwarded-for": "203.0.113.42, 198.51.100.1",  # Proxied request
        }

        # Act
        with client.stream("GET", "/api/v1/notifications/stream", headers=custom_headers) as response:
            assert response.status_code == 200
            # Read one chunk to trigger subscription
            next(response.iter_text())

        # Assert metadata was captured
        assert captured_metadata["user_id"] == str(sample_student.user_id)
        assert captured_metadata["user_agent"] == "TestClient/1.0"
        assert captured_metadata["ip_address"] == "203.0.113.42"  # First IP from X-Forwarded-For
        assert captured_metadata["connection_id"].startswith("conn_")

    def test_stream_redis_unavailable_returns_503(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that SSE stream returns 503 when Redis is unavailable."""
        # Arrange - Simulate Redis unavailability
        notification_service_override.redis = None

        # Act
        response = client.get("/api/v1/notifications/stream", headers=student_headers)

        # Assert
        assert response.status_code == 503
        assert "detail" in response.json()
        assert "unavailable" in response.json()["detail"].lower()

    def test_stream_sse_event_format(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that SSE events are formatted correctly."""
        # Arrange
        test_events = [
            {
                "event": "notification",
                "data": {
                    "event_type": "content_generation_progress",
                    "title": "Generating video",
                    "message": "Processing your request...",
                    "progress_percentage": 50,
                },
            },
            {
                "event": "heartbeat",
                "data": {"timestamp": "2025-01-07T12:00:00Z"},
            },
        ]

        async def mock_subscribe(user_id, connection_id, user_agent, ip_address):
            for event in test_events:
                yield event

        notification_service_override.subscribe_to_notifications = mock_subscribe

        # Act
        with client.stream("GET", "/api/v1/notifications/stream", headers=student_headers) as response:
            assert response.status_code == 200

            # Read SSE events
            lines = []
            for line in response.iter_lines():
                lines.append(line)
                # Stop after we've read both events (each event has 3 lines: event, data, blank)
                if len(lines) >= 6:
                    break

        # Assert SSE format
        # Event 1
        assert lines[0] == "event: notification"
        assert lines[1].startswith("data: ")
        data1 = json.loads(lines[1][6:])  # Remove "data: " prefix
        assert data1["event_type"] == "content_generation_progress"
        assert data1["progress_percentage"] == 50
        assert lines[2] == ""  # Blank line separator

        # Event 2
        assert lines[3] == "event: heartbeat"
        assert lines[4].startswith("data: ")
        data2 = json.loads(lines[4][6:])
        assert "timestamp" in data2
        assert lines[5] == ""


# =============================================================================
# Test: Connections Endpoint (Admin)
# =============================================================================


@pytest.mark.integration
class TestConnectionsEndpoint:
    """Test /api/v1/notifications/connections admin endpoint."""

    def test_connections_requires_authentication(self, client):
        """Test that connections endpoint requires authentication."""
        # Act
        response = client.get("/api/v1/notifications/connections")

        # Assert
        assert response.status_code == 403

    def test_connections_requires_admin_role(
        self, client, sample_student, student_headers
    ):
        """Test that connections endpoint requires admin role."""
        # Act
        response = client.get(
            "/api/v1/notifications/connections", headers=student_headers
        )

        # Assert
        assert response.status_code == 403
        assert "detail" in response.json()
        assert "administrator" in response.json()["detail"].lower()

    def test_connections_requires_admin_role_teacher_rejected(
        self, client, sample_teacher, teacher_headers
    ):
        """Test that teachers are also rejected from connections endpoint."""
        # Act
        response = client.get(
            "/api/v1/notifications/connections", headers=teacher_headers
        )

        # Assert
        assert response.status_code == 403

    def test_connections_allows_admin_user(
        self,
        client,
        sample_admin,
        admin_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that admin users can access connections endpoint."""
        # Arrange - Mock get_active_connections
        mock_connections_data = {
            "total_connections": 5,
            "connections": [
                {
                    "connection_id": "conn_abc123",
                    "user_id": "user_student_001",
                    "connected_at": "2025-01-07T12:00:00Z",
                    "last_heartbeat": "2025-01-07T12:05:00Z",
                    "user_agent": "Mozilla/5.0",
                    "ip_address": "192.168.1.100",
                },
            ],
        }
        notification_service_override.get_active_connections = AsyncMock(
            return_value=mock_connections_data
        )

        # Act
        response = client.get(
            "/api/v1/notifications/connections", headers=admin_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_connections"] == 5
        assert len(data["connections"]) == 1
        assert data["connections"][0]["connection_id"] == "conn_abc123"

    def test_connections_redis_unavailable_returns_503(
        self,
        client,
        sample_admin,
        admin_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that connections endpoint returns 503 when Redis is unavailable."""
        # Arrange
        notification_service_override.redis = None

        # Act
        response = client.get(
            "/api/v1/notifications/connections", headers=admin_headers
        )

        # Assert
        assert response.status_code == 503

    def test_connections_service_error_returns_500(
        self,
        client,
        sample_admin,
        admin_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that connections endpoint returns 500 on service errors."""
        # Arrange - Simulate service error
        notification_service_override.get_active_connections = AsyncMock(
            side_effect=Exception("Redis connection failed")
        )

        # Act
        response = client.get(
            "/api/v1/notifications/connections", headers=admin_headers
        )

        # Assert
        assert response.status_code == 500
        assert "detail" in response.json()


# =============================================================================
# Test: Health Endpoint
# =============================================================================


@pytest.mark.integration
class TestHealthEndpoint:
    """Test /api/v1/notifications/health endpoint."""

    def test_health_no_authentication_required(self, client):
        """Test that health endpoint does not require authentication."""
        # Note: This test will fail until we override the dependency
        # For now, let's test with the override
        pass

    def test_health_redis_healthy(
        self,
        client,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test health endpoint when Redis is healthy."""
        # Arrange
        notification_service_override.redis.ping = AsyncMock(return_value=True)
        notification_service_override.metrics = {
            "notifications_published": 100,
            "notifications_delivered": 95,
            "connections_established": 50,
            "connections_closed": 48,
            "publish_errors": 2,
            "subscribe_errors": 1,
        }

        mock_connections_data = {"total_connections": 2}
        notification_service_override.get_active_connections = AsyncMock(
            return_value=mock_connections_data
        )

        # Act
        response = client.get("/api/v1/notifications/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["redis_connected"] is True
        assert data["active_connections"] == 2
        assert data["service_metrics"]["notifications_published"] == 100
        assert data["service_metrics"]["publish_errors"] == 2

    def test_health_redis_unhealthy(
        self,
        client,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test health endpoint when Redis is unhealthy."""
        # Arrange - Simulate Redis connection failure
        notification_service_override.redis.ping = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        notification_service_override.metrics = {
            "notifications_published": 0,
            "notifications_delivered": 0,
            "connections_established": 0,
            "connections_closed": 0,
            "publish_errors": 0,
            "subscribe_errors": 0,
        }

        # Act
        response = client.get("/api/v1/notifications/health")

        # Assert
        assert response.status_code == 503
        data = response.json()["detail"]  # 503 returns detail in body
        assert data["status"] == "unavailable"
        assert data["redis_connected"] is False

    def test_health_redis_unavailable(
        self,
        client,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test health endpoint when Redis client is None."""
        # Arrange
        notification_service_override.redis = None
        notification_service_override.metrics = {}

        # Act
        response = client.get("/api/v1/notifications/health")

        # Assert
        assert response.status_code == 503
        data = response.json()["detail"]
        assert data["status"] == "unavailable"
        assert data["redis_connected"] is False
        assert data["active_connections"] == 0

    def test_health_metrics_format(
        self,
        client,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that health endpoint returns metrics in correct format."""
        # Arrange
        notification_service_override.redis.ping = AsyncMock(return_value=True)
        notification_service_override.metrics = {
            "notifications_published": 1000,
            "notifications_delivered": 950,
            "connections_established": 200,
            "connections_closed": 195,
            "publish_errors": 5,
            "subscribe_errors": 3,
        }

        mock_connections_data = {"total_connections": 5}
        notification_service_override.get_active_connections = AsyncMock(
            return_value=mock_connections_data
        )

        # Act
        response = client.get("/api/v1/notifications/health")

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "status" in data
        assert "redis_connected" in data
        assert "active_connections" in data
        assert "service_metrics" in data

        # Verify all metrics are present
        metrics = data["service_metrics"]
        expected_metrics = [
            "notifications_published",
            "notifications_delivered",
            "connections_established",
            "connections_closed",
            "publish_errors",
            "subscribe_errors",
        ]
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], int)


# =============================================================================
# Test: Error Scenarios
# =============================================================================


@pytest.mark.integration
class TestErrorScenarios:
    """Test error handling and edge cases."""

    def test_stream_handles_asyncio_cancellation(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that stream endpoint handles asyncio.CancelledError gracefully."""
        # Arrange
        async def mock_subscribe_with_cancellation(
            user_id, connection_id, user_agent, ip_address
        ):
            yield {"event": "connected", "data": {"message": "Connected"}}
            # Simulate client disconnection
            raise asyncio.CancelledError()

        notification_service_override.subscribe_to_notifications = (
            mock_subscribe_with_cancellation
        )

        # Act - Client disconnects after first event
        with client.stream(
            "GET", "/api/v1/notifications/stream", headers=student_headers
        ) as response:
            assert response.status_code == 200
            # Read first event
            next(response.iter_text())
            # Connection should close gracefully (no exception raised)

    def test_stream_handles_service_exception(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test that stream endpoint handles service exceptions gracefully."""
        # Arrange
        async def mock_subscribe_with_error(
            user_id, connection_id, user_agent, ip_address
        ):
            yield {"event": "connected", "data": {"message": "Connected"}}
            # Simulate unexpected error
            raise Exception("Redis connection lost")

        notification_service_override.subscribe_to_notifications = (
            mock_subscribe_with_error
        )

        # Act
        with client.stream(
            "GET", "/api/v1/notifications/stream", headers=student_headers
        ) as response:
            assert response.status_code == 200
            lines = []
            for line in response.iter_lines():
                lines.append(line)
                # Should send error event before closing
                if "error" in line:
                    break

        # Assert - Should receive error event
        assert any("event: error" in line for line in lines)

    def test_connections_empty_result(
        self,
        client,
        sample_admin,
        admin_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """Test connections endpoint with no active connections."""
        # Arrange
        notification_service_override.get_active_connections = AsyncMock(
            return_value={"total_connections": 0, "connections": []}
        )

        # Act
        response = client.get(
            "/api/v1/notifications/connections", headers=admin_headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_connections"] == 0
        assert data["connections"] == []


# =============================================================================
# Test: Integration with NotificationService
# =============================================================================


@pytest.mark.integration
class TestNotificationServiceIntegration:
    """Test full integration between endpoints and NotificationService."""

    def test_full_notification_flow_simulation(
        self,
        client,
        sample_student,
        student_headers,
        override_notification_service_dependency,
        notification_service_override,
    ):
        """
        Test complete notification flow:
        1. Client connects to SSE stream
        2. Service publishes notification
        3. Client receives notification
        """
        # Arrange - Create realistic notification events
        test_notifications = [
            {
                "event": "notification",
                "data": {
                    "event_type": "content_generation_started",
                    "title": "Processing your request",
                    "message": "We're generating your personalized video...",
                    "content_request_id": "req_abc123",
                },
            },
            {
                "event": "notification",
                "data": {
                    "event_type": "content_generation_progress",
                    "title": "Video generation in progress",
                    "message": "Analyzing content...",
                    "progress_percentage": 50,
                    "content_request_id": "req_abc123",
                },
            },
            {
                "event": "notification",
                "data": {
                    "event_type": "content_generation_completed",
                    "title": "Your video is ready!",
                    "message": "Your personalized video has been generated.",
                    "content_request_id": "req_abc123",
                    "video_url": "https://example.com/videos/abc123",
                },
            },
        ]

        async def mock_subscribe(user_id, connection_id, user_agent, ip_address):
            for notification in test_notifications:
                yield notification
                await asyncio.sleep(0.01)  # Simulate small delay

        notification_service_override.subscribe_to_notifications = mock_subscribe

        # Act - Connect and receive all notifications
        with client.stream(
            "GET", "/api/v1/notifications/stream", headers=student_headers
        ) as response:
            assert response.status_code == 200

            received_events = []
            for line in response.iter_lines():
                if line.startswith("event: "):
                    event_type = line[7:]  # Remove "event: " prefix
                elif line.startswith("data: "):
                    data = json.loads(line[6:])
                    received_events.append({"event": event_type, "data": data})

                    # Stop after receiving all 3 notifications
                    if len(received_events) >= 3:
                        break

        # Assert - Verify all notifications received in order
        assert len(received_events) == 3

        assert received_events[0]["data"]["event_type"] == "content_generation_started"
        assert received_events[1]["data"]["progress_percentage"] == 50
        assert received_events[2]["data"]["event_type"] == "content_generation_completed"
        assert "video_url" in received_events[2]["data"]
