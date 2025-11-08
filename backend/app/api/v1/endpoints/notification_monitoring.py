"""
Notification System Monitoring Endpoints (Phase 1.4)

Comprehensive monitoring and observability for the real-time notification system.
Provides health checks, metrics, diagnostics, and alerting capabilities.

Features:
- SSE connection pool monitoring
- Redis Pub/Sub health checks
- Notification delivery metrics and SLIs
- Connection diagnostics and debugging
- Automated alerting for degraded service
- Performance metrics and latency tracking
- Stale connection cleanup monitoring

Usage:
    # Check notification system health
    GET /api/v1/monitoring/notifications/health

    # Get detailed metrics
    GET /api/v1/monitoring/notifications/metrics

    # Get active connections for debugging
    GET /api/v1/monitoring/notifications/connections

    # Check Redis Pub/Sub health
    GET /api/v1/monitoring/notifications/redis/health

References:
- SESSION_13_PHASE_1_4_INFRASTRUCTURE.md
- PHASE_1_4_WEBSOCKET_SPECIFICATION.md
"""
import os
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.notification_service import NotificationService, get_notification_service
from app.utils.dependencies import get_current_user, require_super_admin
from app.models.user import User

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


# =============================================================================
# Pydantic Models for API Responses
# =============================================================================


class NotificationHealthStatus(BaseModel):
    """Health status for notification system components."""

    status: str = Field(..., description="Overall status: healthy, degraded, or unavailable")
    redis_connected: bool = Field(..., description="Redis connection status")
    redis_ping_latency_ms: Optional[float] = Field(None, description="Redis ping latency in milliseconds")
    active_connections: int = Field(..., description="Number of active SSE connections")
    service_uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_heartbeat_cleanup: Optional[str] = Field(None, description="Last heartbeat cleanup timestamp")
    issues: List[str] = Field(default_factory=list, description="List of current issues")


class NotificationMetrics(BaseModel):
    """Aggregated metrics for notification system."""

    # Publishing metrics
    notifications_published_total: int = Field(..., description="Total notifications published")
    notifications_delivered_total: int = Field(..., description="Total notifications delivered")
    publish_errors_total: int = Field(..., description="Total publish errors")
    publish_success_rate: float = Field(..., description="Publish success rate (0.0-1.0)")

    # Connection metrics
    connections_established_total: int = Field(..., description="Total connections established")
    connections_closed_total: int = Field(..., description="Total connections closed")
    active_connections_current: int = Field(..., description="Current active connections")
    subscribe_errors_total: int = Field(..., description="Total subscription errors")

    # Performance metrics
    avg_publish_latency_ms: Optional[float] = Field(None, description="Average publish latency in ms")
    avg_delivery_latency_ms: Optional[float] = Field(None, description="Average delivery latency in ms")

    # SLI (Service Level Indicator) metrics
    sli_availability: float = Field(..., description="Availability SLI (0.0-1.0)")
    sli_latency_p95_ms: Optional[float] = Field(None, description="95th percentile latency in ms")

    # Time range
    collected_at: str = Field(..., description="Metrics collection timestamp (ISO 8601)")
    period_start: Optional[str] = Field(None, description="Metrics period start (ISO 8601)")
    period_end: Optional[str] = Field(None, description="Metrics period end (ISO 8601)")


class ConnectionInfo(BaseModel):
    """Information about an active SSE connection."""

    connection_id: str = Field(..., description="Unique connection ID")
    user_id: str = Field(..., description="User ID")
    connected_at: str = Field(..., description="Connection timestamp (ISO 8601)")
    last_heartbeat_at: str = Field(..., description="Last heartbeat timestamp (ISO 8601)")
    duration_seconds: float = Field(..., description="Connection duration in seconds")
    user_agent: Optional[str] = Field(None, description="Client User-Agent header")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    is_stale: bool = Field(False, description="Whether connection is stale (no recent heartbeat)")


class ConnectionStats(BaseModel):
    """Statistics about active connections."""

    total_connections: int = Field(..., description="Total active connections")
    connections_by_user: Dict[str, int] = Field(..., description="Connections grouped by user_id")
    oldest_connection_age_seconds: Optional[float] = Field(None, description="Age of oldest connection")
    newest_connection_age_seconds: Optional[float] = Field(None, description="Age of newest connection")
    stale_connections_count: int = Field(0, description="Number of stale connections")
    connections: List[ConnectionInfo] = Field(..., description="List of all active connections")


class RedisPubSubHealth(BaseModel):
    """Health status for Redis Pub/Sub infrastructure."""

    status: str = Field(..., description="Redis Pub/Sub status: healthy, degraded, unavailable")
    redis_connected: bool = Field(..., description="Redis connection status")
    ping_latency_ms: Optional[float] = Field(None, description="Ping latency in milliseconds")
    pub_sub_channels_active: int = Field(0, description="Number of active pub/sub channels")
    subscriptions_active: int = Field(0, description="Number of active subscriptions")
    messages_in_flight: Optional[int] = Field(None, description="Estimated messages in flight")
    redis_info: Optional[Dict[str, Any]] = Field(None, description="Redis server info")
    issues: List[str] = Field(default_factory=list, description="List of current issues")


class AlertConfig(BaseModel):
    """Alert configuration for monitoring thresholds."""

    max_publish_error_rate: float = Field(0.05, description="Max publish error rate (5%)")
    max_subscribe_error_rate: float = Field(0.02, description="Max subscribe error rate (2%)")
    max_connection_count: int = Field(10000, description="Max concurrent connections")
    min_availability_sli: float = Field(0.99, description="Minimum availability SLI (99%)")
    max_latency_p95_ms: float = Field(100.0, description="Max 95th percentile latency (100ms)")
    stale_connection_threshold_seconds: int = Field(90, description="Stale connection threshold")


class AlertStatus(BaseModel):
    """Current alert status for notification system."""

    alerts_active: List[str] = Field(default_factory=list, description="List of active alerts")
    alerts_count: int = Field(0, description="Number of active alerts")
    last_alert_time: Optional[str] = Field(None, description="Last alert timestamp")
    alert_config: AlertConfig = Field(default_factory=AlertConfig, description="Alert thresholds")


# =============================================================================
# Health Check Endpoints
# =============================================================================


@router.get(
    "/health",
    response_model=NotificationHealthStatus,
    summary="Check notification system health",
    description="""
    Comprehensive health check for the notification system.

    **Health Status Values**:
    - `healthy`: All components operational
    - `degraded`: Some components experiencing issues but service available
    - `unavailable`: Critical components down, service unavailable

    **Returns**:
    - Overall health status
    - Redis connectivity
    - Active connection count
    - Service uptime
    - List of current issues

    **Use Cases**:
    - Kubernetes liveness/readiness probes
    - Load balancer health checks
    - Monitoring dashboard integration
    - Alerting system integration
    """,
    status_code=status.HTTP_200_OK,
    tags=["notification-monitoring"],
)
async def check_notification_health(
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationHealthStatus:
    """
    Check notification system health.

    Args:
        notification_service: NotificationService instance

    Returns:
        NotificationHealthStatus: Comprehensive health status

    Raises:
        HTTPException: 503 if service is unavailable
    """
    issues = []
    redis_connected = False
    redis_ping_latency_ms = None
    active_connections = 0

    try:
        # Check Redis connection
        if notification_service.redis is None:
            issues.append("Redis client not initialized")
        else:
            try:
                # Ping Redis and measure latency
                start_time = time.time()
                await notification_service.redis.ping()
                redis_ping_latency_ms = (time.time() - start_time) * 1000
                redis_connected = True

                # Check if latency is acceptable
                if redis_ping_latency_ms > 50:
                    issues.append(f"High Redis ping latency: {redis_ping_latency_ms:.2f}ms")

            except Exception as e:
                issues.append(f"Redis connection failed: {str(e)}")
                redis_connected = False

        # Get active connection count
        if redis_connected:
            try:
                active_connections = await notification_service.get_connection_count()
            except Exception as e:
                issues.append(f"Failed to get connection count: {str(e)}")

        # Determine overall status
        if not redis_connected:
            overall_status = "unavailable"
        elif issues:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        health_status = NotificationHealthStatus(
            status=overall_status,
            redis_connected=redis_connected,
            redis_ping_latency_ms=redis_ping_latency_ms,
            active_connections=active_connections,
            service_uptime_seconds=None,  # Can be tracked with process start time
            last_heartbeat_cleanup=None,  # Can be tracked by background cleanup task
            issues=issues,
        )

        # Return 503 if unavailable
        if overall_status == "unavailable":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_status.model_dump(),
            )

        return health_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unavailable",
                "error": str(e),
                "issues": issues,
            },
        )


# =============================================================================
# Metrics Endpoints
# =============================================================================


@router.get(
    "/metrics",
    response_model=NotificationMetrics,
    summary="Get notification system metrics",
    description="""
    Get aggregated metrics for the notification system.

    **Metric Categories**:
    - **Publishing**: Total published, delivered, errors, success rate
    - **Connections**: Established, closed, active, subscription errors
    - **Performance**: Latency metrics (publish, delivery)
    - **SLI**: Service Level Indicators (availability, latency percentiles)

    **Use Cases**:
    - Performance monitoring
    - SLO tracking
    - Capacity planning
    - Alerting and anomaly detection
    - Dashboard visualization
    """,
    status_code=status.HTTP_200_OK,
    tags=["notification-monitoring"],
)
async def get_notification_metrics(
    notification_service: NotificationService = Depends(get_notification_service),
) -> NotificationMetrics:
    """
    Get notification system metrics.

    Args:
        notification_service: NotificationService instance

    Returns:
        NotificationMetrics: Aggregated metrics
    """
    try:
        # Get raw metrics from service
        raw_metrics = notification_service.get_metrics()

        # Calculate derived metrics
        notifications_published = raw_metrics.get("notifications_published", 0)
        notifications_delivered = raw_metrics.get("notifications_delivered", 0)
        publish_errors = raw_metrics.get("publish_errors", 0)
        subscribe_errors = raw_metrics.get("subscribe_errors", 0)
        connections_established = raw_metrics.get("connections_established", 0)
        connections_closed = raw_metrics.get("connections_closed", 0)

        # Calculate success rate (avoid division by zero)
        total_publish_attempts = notifications_published + publish_errors
        publish_success_rate = (
            notifications_published / total_publish_attempts
            if total_publish_attempts > 0
            else 1.0
        )

        # Get active connections
        active_connections = await notification_service.get_connection_count()

        # Calculate availability SLI (based on error rates)
        total_operations = total_publish_attempts + connections_established + subscribe_errors
        total_errors = publish_errors + subscribe_errors
        sli_availability = (
            1.0 - (total_errors / total_operations)
            if total_operations > 0
            else 1.0
        )

        metrics = NotificationMetrics(
            notifications_published_total=notifications_published,
            notifications_delivered_total=notifications_delivered,
            publish_errors_total=publish_errors,
            publish_success_rate=publish_success_rate,
            connections_established_total=connections_established,
            connections_closed_total=connections_closed,
            active_connections_current=active_connections,
            subscribe_errors_total=subscribe_errors,
            avg_publish_latency_ms=None,  # Can be tracked with timing decorators
            avg_delivery_latency_ms=None,  # Can be tracked with timing decorators
            sli_availability=sli_availability,
            sli_latency_p95_ms=None,  # Can be tracked with latency histogram
            collected_at=datetime.utcnow().isoformat() + "Z",
            period_start=None,  # Can be tracked with metrics reset timestamp
            period_end=None,
        )

        return metrics

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}",
        )


# =============================================================================
# Connection Monitoring Endpoints
# =============================================================================


@router.get(
    "/connections",
    response_model=ConnectionStats,
    summary="Get active notification connections",
    description="""
    Get detailed information about active SSE connections.

    **Authorization**: Admin or Super Admin

    **Returns**:
    - Total connection count
    - Connections grouped by user
    - Oldest/newest connection ages
    - Stale connection count
    - Full connection details list

    **Use Cases**:
    - Connection debugging
    - User activity monitoring
    - Identify stuck/stale connections
    - Capacity planning
    - Performance optimization
    """,
    status_code=status.HTTP_200_OK,
    tags=["notification-monitoring"],
)
async def get_active_connections(
    include_stale: bool = Query(False, description="Include stale connections in results"),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> ConnectionStats:
    """
    Get active notification connections.

    Args:
        include_stale: Whether to include stale connections
        current_user: Authenticated user (must be admin)
        notification_service: NotificationService instance

    Returns:
        ConnectionStats: Connection statistics and details

    Raises:
        HTTPException: 403 if user is not admin
        HTTPException: 503 if notification service unavailable
    """
    # Authorization check: admin or super_admin only
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
        # Get all connection keys from Redis
        connection_keys = []
        async for key in notification_service.redis.scan_iter(match="notifications:connection:*"):
            connection_keys.append(key)

        # Fetch connection details
        connections = []
        connections_by_user: Dict[str, int] = {}
        oldest_age = None
        newest_age = None
        stale_count = 0
        stale_threshold = 90  # seconds

        for conn_key in connection_keys:
            try:
                conn_data = await notification_service.redis.hgetall(conn_key)

                if not conn_data:
                    continue

                # Parse connection data
                connection_id = conn_data.get("connection_id", "")
                user_id = conn_data.get("user_id", "")
                connected_at_str = conn_data.get("connected_at", "")
                last_heartbeat_str = conn_data.get("last_heartbeat_at", "")
                user_agent = conn_data.get("user_agent", "")
                ip_address = conn_data.get("ip_address", "")

                # Calculate connection duration
                try:
                    connected_at = datetime.fromisoformat(connected_at_str.replace("Z", "+00:00"))
                    duration_seconds = (datetime.utcnow() - connected_at.replace(tzinfo=None)).total_seconds()
                except Exception:
                    duration_seconds = 0.0

                # Check if stale (no recent heartbeat)
                is_stale = False
                try:
                    last_heartbeat = datetime.fromisoformat(last_heartbeat_str.replace("Z", "+00:00"))
                    time_since_heartbeat = (datetime.utcnow() - last_heartbeat.replace(tzinfo=None)).total_seconds()
                    is_stale = time_since_heartbeat > stale_threshold
                except Exception:
                    is_stale = True  # No valid heartbeat = stale

                # Skip stale connections if not requested
                if is_stale and not include_stale:
                    stale_count += 1
                    continue

                if is_stale:
                    stale_count += 1

                # Track oldest/newest
                if oldest_age is None or duration_seconds > oldest_age:
                    oldest_age = duration_seconds
                if newest_age is None or duration_seconds < newest_age:
                    newest_age = duration_seconds

                # Count by user
                connections_by_user[user_id] = connections_by_user.get(user_id, 0) + 1

                # Create connection info
                conn_info = ConnectionInfo(
                    connection_id=connection_id,
                    user_id=user_id,
                    connected_at=connected_at_str,
                    last_heartbeat_at=last_heartbeat_str,
                    duration_seconds=duration_seconds,
                    user_agent=user_agent if user_agent else None,
                    ip_address=ip_address if ip_address else None,
                    is_stale=is_stale,
                )

                connections.append(conn_info)

            except Exception as e:
                logger.warning(f"Failed to parse connection {conn_key}: {e}")
                continue

        stats = ConnectionStats(
            total_connections=len(connections),
            connections_by_user=connections_by_user,
            oldest_connection_age_seconds=oldest_age,
            newest_connection_age_seconds=newest_age,
            stale_connections_count=stale_count,
            connections=connections,
        )

        logger.info(
            f"Active connections retrieved by admin: "
            f"admin_user_id={current_user.user_id}, "
            f"total_connections={stats.total_connections}"
        )

        return stats

    except Exception as e:
        logger.error(f"Failed to retrieve active connections: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve connection data: {str(e)}",
        )


# =============================================================================
# Redis Pub/Sub Monitoring
# =============================================================================


@router.get(
    "/redis/health",
    response_model=RedisPubSubHealth,
    summary="Check Redis Pub/Sub health",
    description="""
    Check health status of Redis Pub/Sub infrastructure.

    **Returns**:
    - Redis connection status
    - Ping latency
    - Active pub/sub channels
    - Active subscriptions
    - Redis server info
    - List of current issues

    **Use Cases**:
    - Infrastructure monitoring
    - Troubleshooting connection issues
    - Performance optimization
    - Capacity planning
    """,
    status_code=status.HTTP_200_OK,
    tags=["notification-monitoring"],
)
async def check_redis_pubsub_health(
    notification_service: NotificationService = Depends(get_notification_service),
) -> RedisPubSubHealth:
    """
    Check Redis Pub/Sub health.

    Args:
        notification_service: NotificationService instance

    Returns:
        RedisPubSubHealth: Redis Pub/Sub health status

    Raises:
        HTTPException: 503 if Redis is unavailable
    """
    issues = []
    redis_connected = False
    ping_latency_ms = None
    pub_sub_channels_active = 0
    redis_info = None

    try:
        # Check Redis connection
        if notification_service.redis is None:
            issues.append("Redis client not initialized")
        else:
            try:
                # Ping Redis and measure latency
                start_time = time.time()
                await notification_service.redis.ping()
                ping_latency_ms = (time.time() - start_time) * 1000
                redis_connected = True

                # Check latency thresholds
                if ping_latency_ms > 100:
                    issues.append(f"High Redis latency: {ping_latency_ms:.2f}ms (threshold: 100ms)")
                elif ping_latency_ms > 50:
                    issues.append(f"Elevated Redis latency: {ping_latency_ms:.2f}ms (threshold: 50ms)")

                # Count active pub/sub channels
                pattern = "notifications:user:*"
                async for key in notification_service.redis.scan_iter(match=pattern):
                    pub_sub_channels_active += 1

                # Get Redis info (basic stats)
                try:
                    info = await notification_service.redis.info()
                    redis_info = {
                        "version": info.get("redis_version", "unknown"),
                        "connected_clients": info.get("connected_clients", 0),
                        "used_memory_human": info.get("used_memory_human", "unknown"),
                        "uptime_seconds": info.get("uptime_in_seconds", 0),
                    }
                except Exception as e:
                    logger.warning(f"Failed to get Redis info: {e}")
                    redis_info = None

            except Exception as e:
                issues.append(f"Redis connection failed: {str(e)}")
                redis_connected = False

        # Determine overall status
        if not redis_connected:
            overall_status = "unavailable"
        elif issues:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        health = RedisPubSubHealth(
            status=overall_status,
            redis_connected=redis_connected,
            ping_latency_ms=ping_latency_ms,
            pub_sub_channels_active=pub_sub_channels_active,
            subscriptions_active=0,  # Not easily available without PubSub instance
            messages_in_flight=None,  # Not easily available
            redis_info=redis_info,
            issues=issues,
        )

        # Return 503 if unavailable
        if overall_status == "unavailable":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health.model_dump(),
            )

        return health

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Redis health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unavailable",
                "error": str(e),
                "issues": issues,
            },
        )


# =============================================================================
# Alerting Endpoints
# =============================================================================


@router.get(
    "/alerts",
    response_model=AlertStatus,
    summary="Get active alerts for notification system",
    description="""
    Get current alert status based on predefined thresholds.

    **Alert Thresholds** (configurable):
    - Max publish error rate: 5%
    - Max subscribe error rate: 2%
    - Max concurrent connections: 10,000
    - Min availability SLI: 99%
    - Max 95th percentile latency: 100ms
    - Stale connection threshold: 90 seconds

    **Returns**:
    - List of active alerts
    - Alert count
    - Last alert timestamp
    - Alert configuration

    **Use Cases**:
    - Automated monitoring
    - PagerDuty/Opsgenie integration
    - Dashboard alerting
    - SRE incident management
    """,
    status_code=status.HTTP_200_OK,
    tags=["notification-monitoring"],
)
async def get_alert_status(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> AlertStatus:
    """
    Get active alerts for notification system.

    Args:
        current_user: Authenticated user (must be admin)
        notification_service: NotificationService instance

    Returns:
        AlertStatus: Current alert status

    Raises:
        HTTPException: 403 if user is not admin
    """
    # Authorization check: admin or super_admin only
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to administrators",
        )

    try:
        # Get alert configuration (can be from environment or database)
        alert_config = AlertConfig()

        # Get current metrics
        raw_metrics = notification_service.get_metrics()

        notifications_published = raw_metrics.get("notifications_published", 0)
        publish_errors = raw_metrics.get("publish_errors", 0)
        subscribe_errors = raw_metrics.get("subscribe_errors", 0)
        connections_established = raw_metrics.get("connections_established", 0)

        # Calculate error rates
        total_publish_attempts = notifications_published + publish_errors
        publish_error_rate = (
            publish_errors / total_publish_attempts
            if total_publish_attempts > 0
            else 0.0
        )

        total_subscribe_attempts = connections_established + subscribe_errors
        subscribe_error_rate = (
            subscribe_errors / total_subscribe_attempts
            if total_subscribe_attempts > 0
            else 0.0
        )

        # Get active connections
        active_connections = await notification_service.get_connection_count()

        # Calculate availability SLI
        total_operations = total_publish_attempts + connections_established
        total_errors = publish_errors + subscribe_errors
        availability_sli = (
            1.0 - (total_errors / total_operations)
            if total_operations > 0
            else 1.0
        )

        # Check thresholds and generate alerts
        alerts_active = []

        if publish_error_rate > alert_config.max_publish_error_rate:
            alerts_active.append(
                f"High publish error rate: {publish_error_rate:.2%} "
                f"(threshold: {alert_config.max_publish_error_rate:.2%})"
            )

        if subscribe_error_rate > alert_config.max_subscribe_error_rate:
            alerts_active.append(
                f"High subscribe error rate: {subscribe_error_rate:.2%} "
                f"(threshold: {alert_config.max_subscribe_error_rate:.2%})"
            )

        if active_connections > alert_config.max_connection_count:
            alerts_active.append(
                f"High connection count: {active_connections} "
                f"(threshold: {alert_config.max_connection_count})"
            )

        if availability_sli < alert_config.min_availability_sli:
            alerts_active.append(
                f"Low availability SLI: {availability_sli:.2%} "
                f"(threshold: {alert_config.min_availability_sli:.2%})"
            )

        # Create alert status
        alert_status = AlertStatus(
            alerts_active=alerts_active,
            alerts_count=len(alerts_active),
            last_alert_time=datetime.utcnow().isoformat() + "Z" if alerts_active else None,
            alert_config=alert_config,
        )

        if alerts_active:
            logger.warning(
                f"Notification system alerts: {len(alerts_active)} active alerts: {alerts_active}"
            )

        return alert_status

    except Exception as e:
        logger.error(f"Failed to get alert status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert status: {str(e)}",
        )
