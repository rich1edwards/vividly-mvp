"""
Unit and Integration Tests for Notification Monitoring Endpoints (Phase 1.4)

Tests the comprehensive monitoring and observability infrastructure for the
real-time notification system.

Test Coverage:
- Health check endpoints (/health, /redis/health)
- Metrics endpoints (/metrics)
- Connection monitoring (/connections)
- Alert monitoring (/alerts)
- Authorization and access control
- Error handling and edge cases
- Performance and latency metrics

Usage:
    pytest backend/tests/test_notification_monitoring.py -v
    pytest backend/tests/test_notification_monitoring.py::test_notification_health_check -v
"""
import pytest
import pytest_asyncio
from fastapi import status
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import fakeredis.aioredis

from app.main import app
from app.services.notification_service import NotificationService
from app.models.user import User, UserRole


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_redis():
    """Create a fake Redis client for testing."""
    # Use fakeredis for testing
    redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return redis_client


@pytest_asyncio.fixture
async def notification_service(mock_redis):
    """Create NotificationService with fake Redis."""
    service = NotificationService(redis_client=mock_redis)
    # Pre-populate some metrics for testing
    service.metrics = {
        "notifications_published": 100,
        "notifications_delivered": 95,
        "publish_errors": 5,
        "subscribe_errors": 2,
        "connections_established": 50,
        "connections_closed": 45,
    }
    return service


@pytest.fixture
def admin_user():
    """Create mock admin user for testing."""
    user = Mock(spec=User)
    user.user_id = "admin-user-123"
    user.email = "admin@vividly.com"
    user.first_name = "Admin"
    user.last_name = "User"
    user.role = UserRole.ADMIN
    return user


@pytest.fixture
def student_user():
    """Create mock student user for testing (non-admin)."""
    user = Mock(spec=User)
    user.user_id = "student-user-456"
    user.email = "student@vividly.com"
    user.first_name = "Student"
    user.last_name = "User"
    user.role = UserRole.STUDENT
    return user


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


# =============================================================================
# Health Check Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
async def test_notification_health_check_healthy(
    client, notification_service, admin_user, mock_redis
):
    """Test /health endpoint returns healthy status when Redis is connected."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ):
        # Setup: Redis is connected and responsive
        await mock_redis.set("test_key", "test_value")

        response = client.get("/api/v1/monitoring/notifications/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "healthy"
        assert data["redis_connected"] is True
        assert data["redis_ping_latency_ms"] is not None
        assert data["redis_ping_latency_ms"] < 100  # Should be fast
        assert data["active_connections"] >= 0
        assert len(data["issues"]) == 0


@pytest.mark.asyncio
async def test_notification_health_check_degraded(
    client, notification_service, mock_redis
):
    """Test /health endpoint returns degraded status when latency is high."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ):
        # Mock high latency
        with patch.object(mock_redis, "ping", new_callable=AsyncMock) as mock_ping:

            async def slow_ping():
                import asyncio

                await asyncio.sleep(0.06)  # 60ms latency
                return True

            mock_ping.side_effect = slow_ping

            response = client.get("/api/v1/monitoring/notifications/health")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "degraded"
            assert "High Redis ping latency" in data["issues"][0]


@pytest.mark.asyncio
async def test_notification_health_check_unavailable(client):
    """Test /health endpoint returns 503 when Redis is disconnected."""
    # Create service with no Redis client
    service = NotificationService(redis_client=None)

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=service,
    ):
        response = client.get("/api/v1/monitoring/notifications/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()

        assert data["detail"]["status"] == "unavailable"
        assert "Redis client not initialized" in data["detail"]["issues"]


# =============================================================================
# Metrics Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_notification_metrics(client, notification_service, mock_redis):
    """Test /metrics endpoint returns aggregated metrics."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ):
        response = client.get("/api/v1/monitoring/notifications/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify metric fields
        assert data["notifications_published_total"] == 100
        assert data["notifications_delivered_total"] == 95
        assert data["publish_errors_total"] == 5
        assert data["publish_success_rate"] == pytest.approx(100 / 105, rel=0.01)

        assert data["connections_established_total"] == 50
        assert data["connections_closed_total"] == 45
        assert data["active_connections_current"] >= 0

        assert data["sli_availability"] > 0.9  # Should be high availability

        # Verify timestamp fields
        assert data["collected_at"] is not None
        datetime.fromisoformat(data["collected_at"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_get_notification_metrics_with_zero_operations(client, mock_redis):
    """Test metrics endpoint handles zero operations gracefully."""
    # Create service with zero metrics
    service = NotificationService(redis_client=mock_redis)
    service.metrics = {
        "notifications_published": 0,
        "notifications_delivered": 0,
        "publish_errors": 0,
        "subscribe_errors": 0,
        "connections_established": 0,
        "connections_closed": 0,
    }

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=service,
    ):
        response = client.get("/api/v1/monitoring/notifications/metrics")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should handle division by zero gracefully
        assert data["publish_success_rate"] == 1.0
        assert data["sli_availability"] == 1.0


# =============================================================================
# Connection Monitoring Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_active_connections_as_admin(
    client, notification_service, admin_user, mock_redis
):
    """Test /connections endpoint returns connection stats for admin."""
    # Setup: Create fake connections in Redis
    connection_data = {
        "connection_id": "conn_abc123",
        "user_id": "user_789",
        "connected_at": datetime.utcnow().isoformat() + "Z",
        "last_heartbeat_at": datetime.utcnow().isoformat() + "Z",
        "user_agent": "Mozilla/5.0",
        "ip_address": "192.168.1.1",
    }

    await mock_redis.hset(
        "notifications:connection:conn_abc123", mapping=connection_data
    )

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=admin_user,
    ):
        response = client.get("/api/v1/monitoring/notifications/connections")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total_connections"] >= 0
        assert isinstance(data["connections_by_user"], dict)
        assert isinstance(data["connections"], list)


@pytest.mark.asyncio
async def test_get_active_connections_forbidden_for_student(
    client, notification_service, student_user
):
    """Test /connections endpoint returns 403 for non-admin users."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=student_user,
    ):
        response = client.get("/api/v1/monitoring/notifications/connections")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "administrators" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_active_connections_with_stale_connections(
    client, notification_service, admin_user, mock_redis
):
    """Test /connections endpoint filters stale connections."""
    # Setup: Create stale connection (no heartbeat for > 90 seconds)
    stale_connection_data = {
        "connection_id": "conn_stale",
        "user_id": "user_stale",
        "connected_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat() + "Z",
        "last_heartbeat_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        + "Z",
        "user_agent": "Mozilla/5.0",
        "ip_address": "192.168.1.1",
    }

    await mock_redis.hset(
        "notifications:connection:conn_stale", mapping=stale_connection_data
    )

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=admin_user,
    ):
        # Without include_stale
        response = client.get("/api/v1/monitoring/notifications/connections")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["stale_connections_count"] > 0

        # With include_stale
        response = client.get(
            "/api/v1/monitoring/notifications/connections?include_stale=true"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should include stale connections in results
        stale_conns = [c for c in data["connections"] if c["is_stale"]]
        assert len(stale_conns) > 0


# =============================================================================
# Redis Pub/Sub Health Check Tests
# =============================================================================


@pytest.mark.asyncio
async def test_redis_pubsub_health_check_healthy(
    client, notification_service, mock_redis
):
    """Test /redis/health endpoint returns healthy status."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ):
        response = client.get("/api/v1/monitoring/notifications/redis/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "healthy"
        assert data["redis_connected"] is True
        assert data["ping_latency_ms"] is not None
        assert len(data["issues"]) == 0


@pytest.mark.asyncio
async def test_redis_pubsub_health_check_unavailable(client):
    """Test /redis/health endpoint returns 503 when Redis is down."""
    service = NotificationService(redis_client=None)

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=service,
    ):
        response = client.get("/api/v1/monitoring/notifications/redis/health")

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        data = response.json()

        assert data["detail"]["status"] == "unavailable"


# =============================================================================
# Alert Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_alert_status_no_alerts(
    client, notification_service, admin_user, mock_redis
):
    """Test /alerts endpoint returns no alerts when thresholds are met."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=admin_user,
    ):
        response = client.get("/api/v1/monitoring/notifications/alerts")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["alerts_count"] == 0
        assert len(data["alerts_active"]) == 0
        assert data["alert_config"] is not None


@pytest.mark.asyncio
async def test_get_alert_status_with_high_error_rate(client, admin_user, mock_redis):
    """Test /alerts endpoint detects high error rates."""
    # Create service with high error rate
    service = NotificationService(redis_client=mock_redis)
    service.metrics = {
        "notifications_published": 50,
        "notifications_delivered": 50,
        "publish_errors": 50,  # 50% error rate (threshold is 5%)
        "subscribe_errors": 0,
        "connections_established": 100,
        "connections_closed": 100,
    }

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=admin_user,
    ):
        response = client.get("/api/v1/monitoring/notifications/alerts")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["alerts_count"] > 0
        assert any(
            "publish error rate" in alert.lower() for alert in data["alerts_active"]
        )


@pytest.mark.asyncio
async def test_get_alert_status_forbidden_for_student(
    client, notification_service, student_user
):
    """Test /alerts endpoint returns 403 for non-admin users."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=student_user,
    ):
        response = client.get("/api/v1/monitoring/notifications/alerts")

        assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# Integration Tests with Full Stack
# =============================================================================


@pytest.mark.asyncio
async def test_monitoring_workflow_full_stack(
    client, notification_service, admin_user, mock_redis
):
    """Test complete monitoring workflow: health -> metrics -> connections -> alerts."""
    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ), patch(
        "app.api.v1.endpoints.notification_monitoring.get_current_user",
        return_value=admin_user,
    ):
        # 1. Check overall health
        health_response = client.get("/api/v1/monitoring/notifications/health")
        assert health_response.status_code == status.HTTP_200_OK
        assert health_response.json()["status"] in ["healthy", "degraded"]

        # 2. Get metrics
        metrics_response = client.get("/api/v1/monitoring/notifications/metrics")
        assert metrics_response.status_code == status.HTTP_200_OK
        metrics = metrics_response.json()
        assert metrics["notifications_published_total"] > 0

        # 3. Check active connections
        connections_response = client.get(
            "/api/v1/monitoring/notifications/connections"
        )
        assert connections_response.status_code == status.HTTP_200_OK
        connections = connections_response.json()
        assert "total_connections" in connections

        # 4. Check Redis health
        redis_response = client.get("/api/v1/monitoring/notifications/redis/health")
        assert redis_response.status_code == status.HTTP_200_OK

        # 5. Check alerts
        alerts_response = client.get("/api/v1/monitoring/notifications/alerts")
        assert alerts_response.status_code == status.HTTP_200_OK
        alerts = alerts_response.json()
        assert "alerts_count" in alerts


@pytest.mark.asyncio
async def test_performance_metrics_latency(client, notification_service):
    """Test that metrics endpoints respond within acceptable latency."""
    import time

    with patch(
        "app.api.v1.endpoints.notification_monitoring.get_notification_service",
        return_value=notification_service,
    ):
        # Test health check latency
        start = time.time()
        response = client.get("/api/v1/monitoring/notifications/health")
        health_latency = (time.time() - start) * 1000  # ms

        assert response.status_code == status.HTTP_200_OK
        assert health_latency < 500  # Should respond within 500ms

        # Test metrics latency
        start = time.time()
        response = client.get("/api/v1/monitoring/notifications/metrics")
        metrics_latency = (time.time() - start) * 1000  # ms

        assert response.status_code == status.HTTP_200_OK
        assert metrics_latency < 500  # Should respond within 500ms


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
