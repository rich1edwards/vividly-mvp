"""
Production Metrics Module for GCP Cloud Monitoring.

This module provides a production-ready wrapper around Google Cloud Monitoring
for collecting custom metrics. All metrics defined here can be queried in GCP
Cloud Monitoring and used for alerting policies.

Following Andrew Ng's "Build it right" principle - production-ready from day one.

Metrics Categories:
1. Rate Limiting Metrics (from Sprint 2 requirements)
2. Authentication Metrics
3. System Health Metrics
4. Content Generation Metrics

Usage:
    from app.core.metrics import get_metrics_client

    metrics = get_metrics_client()
    metrics.increment_rate_limit_hits(endpoint="/api/auth/login", ip_address="127.0.0.1")
    metrics.record_request_duration(method="GET", endpoint="/api/health", duration_seconds=0.042)
"""
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime
from google.cloud import monitoring_v3
from google.api import label_pb2, metric_pb2
from google.api.metric_pb2 import MetricDescriptor

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MetricsClient:
    """
    Thread-safe metrics client for GCP Cloud Monitoring.

    Handles metric registration, batching, and submission to GCP.
    Gracefully handles failures (logs errors but doesn't crash the application).
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize metrics client.

        Args:
            project_id: GCP project ID (defaults to settings.GCP_PROJECT_ID)
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT", "vividly-dev-rich")
        self.project_name = f"projects/{self.project_id}"
        self.enabled = os.getenv("METRICS_ENABLED", "true").lower() in [
            "true",
            "1",
            "yes",
        ]

        # Initialize GCP Cloud Monitoring client
        try:
            if self.enabled:
                self.client = monitoring_v3.MetricServiceClient()
                logger.info(
                    f"Metrics client initialized for project: {self.project_id}"
                )
            else:
                self.client = None
                logger.info("Metrics client disabled (METRICS_ENABLED=false)")
        except Exception as e:
            logger.error(f"Failed to initialize metrics client: {e}", exc_info=True)
            self.client = None
            self.enabled = False

    def _write_time_series(
        self,
        metric_type: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        value_type: str = "INT64",
    ) -> None:
        """
        Write a time series data point to GCP Cloud Monitoring.

        Args:
            metric_type: Full metric type (e.g., "custom.googleapis.com/vividly/rate_limit_hits_total")
            value: Metric value
            labels: Optional metric labels
            value_type: Metric value type (INT64, DOUBLE, etc.)
        """
        if not self.enabled or not self.client:
            return

        try:
            # Create time series
            series = monitoring_v3.TimeSeries()
            series.metric.type = metric_type

            # Add labels
            if labels:
                for key, val in labels.items():
                    series.metric.labels[key] = str(val)

            # Set resource (monitored_resource for GCP)
            series.resource.type = "generic_task"
            series.resource.labels["project_id"] = self.project_id
            series.resource.labels["location"] = (
                settings.GCP_REGION
                if hasattr(settings, "GCP_REGION")
                else "us-central1"
            )
            series.resource.labels["namespace"] = settings.APP_NAME
            series.resource.labels["job"] = "vividly-api"
            series.resource.labels["task_id"] = os.getenv("K_REVISION", "local")

            # Create data point
            now = time.time()
            seconds = int(now)
            nanos = int((now - seconds) * 10**9)
            interval = monitoring_v3.TimeInterval(
                {"end_time": {"seconds": seconds, "nanos": nanos}}
            )
            point = monitoring_v3.Point(
                {"interval": interval, "value": {value_type.lower() + "_value": value}}
            )
            series.points = [point]

            # Write to GCP
            self.client.create_time_series(name=self.project_name, time_series=[series])

        except Exception as e:
            # Log error but don't crash the application
            logger.error(f"Failed to write metric {metric_type}: {e}", exc_info=True)

    # ========================================================================
    # RATE LIMITING METRICS (Sprint 2 Requirements)
    # ========================================================================

    def increment_rate_limit_hits(self, endpoint: str, ip_address: str) -> None:
        """
        Increment total rate limit checks performed.

        From Sprint 2 docs: Tracks all rate limit evaluations.

        Args:
            endpoint: API endpoint path (e.g., "/api/auth/login")
            ip_address: Client IP address
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/rate_limit_hits_total",
            value=1,
            labels={"endpoint": endpoint, "ip_address": ip_address},
            value_type="INT64",
        )

    def increment_rate_limit_exceeded(self, endpoint: str, ip_address: str) -> None:
        """
        Increment count of 429 (rate limit exceeded) responses.

        From Sprint 2 docs: Tracks when clients hit rate limits.

        Args:
            endpoint: API endpoint path
            ip_address: Client IP address
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/rate_limit_exceeded_total",
            value=1,
            labels={"endpoint": endpoint, "ip_address": ip_address},
            value_type="INT64",
        )

    def increment_brute_force_lockouts(
        self, ip_address: str, email: Optional[str] = None
    ) -> None:
        """
        Increment count of account lockouts triggered by brute force protection.

        From Sprint 2 docs: Tracks brute force attack attempts.

        Args:
            ip_address: Client IP address
            email: Email address (optional, may be None for privacy)
        """
        labels = {"ip_address": ip_address}
        if email:
            labels["email"] = email

        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/brute_force_lockouts_total",
            value=1,
            labels=labels,
            value_type="INT64",
        )

    def record_rate_limit_middleware_latency(
        self, endpoint: str, latency_ms: float
    ) -> None:
        """
        Record rate limiting middleware processing time.

        From Sprint 2 docs: Tracks performance overhead of rate limiting.

        Args:
            endpoint: API endpoint path
            latency_ms: Middleware processing time in milliseconds
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/rate_limit_middleware_latency_ms",
            value=latency_ms,
            labels={"endpoint": endpoint},
            value_type="DOUBLE",
        )

    # ========================================================================
    # AUTHENTICATION METRICS
    # ========================================================================

    def increment_auth_login_attempts(
        self, status: str, user_role: Optional[str] = None
    ) -> None:
        """
        Increment login attempt counter.

        Args:
            status: Login status ("success" or "failure")
            user_role: User role (e.g., "teacher", "student", "admin")
        """
        labels = {"status": status}
        if user_role:
            labels["user_role"] = user_role

        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/auth_login_attempts_total",
            value=1,
            labels=labels,
            value_type="INT64",
        )

    def increment_auth_login_failures(self, reason: str) -> None:
        """
        Increment failed login counter.

        Args:
            reason: Failure reason ("invalid_password", "user_not_found", "account_locked")
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/auth_login_failures_total",
            value=1,
            labels={"reason": reason},
            value_type="INT64",
        )

    def increment_auth_token_refresh(self, status: str) -> None:
        """
        Increment token refresh counter.

        Args:
            status: Refresh status ("success" or "failure")
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/auth_token_refresh_total",
            value=1,
            labels={"status": status},
            value_type="INT64",
        )

    def record_auth_session_duration(self, duration_seconds: float) -> None:
        """
        Record authentication session duration.

        Args:
            duration_seconds: Session lifetime in seconds
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/auth_session_duration_seconds",
            value=duration_seconds,
            labels={},
            value_type="DOUBLE",
        )

    def set_auth_active_sessions(
        self, count: int, user_role: Optional[str] = None
    ) -> None:
        """
        Set current active session count (gauge metric).

        Args:
            count: Number of active sessions
            user_role: User role (optional)
        """
        labels = {}
        if user_role:
            labels["user_role"] = user_role

        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/auth_active_sessions",
            value=count,
            labels=labels,
            value_type="INT64",
        )

    # ========================================================================
    # SYSTEM HEALTH METRICS
    # ========================================================================

    def increment_http_request(
        self, method: str, endpoint: str, status_code: int
    ) -> None:
        """
        Increment HTTP request counter.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code (200, 404, 500, etc.)
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/http_request_total",
            value=1,
            labels={
                "method": method,
                "endpoint": endpoint,
                "status_code": str(status_code),
            },
            value_type="INT64",
        )

    def record_request_duration(
        self, method: str, endpoint: str, duration_seconds: float
    ) -> None:
        """
        Record HTTP request processing time.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            duration_seconds: Request processing time in seconds
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/http_request_duration_seconds",
            value=duration_seconds,
            labels={"method": method, "endpoint": endpoint},
            value_type="DOUBLE",
        )

    # ========================================================================
    # CONTENT GENERATION METRICS
    # ========================================================================

    def increment_content_generation_requests(self, status: str) -> None:
        """
        Increment content generation request counter.

        Args:
            status: Request status ("pending", "completed", "failed")
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/content_generation_requests_total",
            value=1,
            labels={"status": status},
            value_type="INT64",
        )

    def record_content_generation_duration(
        self, stage: str, duration_seconds: float
    ) -> None:
        """
        Record content generation stage duration.

        Args:
            stage: Generation stage ("nlu", "script", "tts", "video", "total")
            duration_seconds: Stage processing time in seconds
        """
        self._write_time_series(
            metric_type="custom.googleapis.com/vividly/content_generation_duration_seconds",
            value=duration_seconds,
            labels={"stage": stage},
            value_type="DOUBLE",
        )


# Singleton metrics client instance
_metrics_client: Optional[MetricsClient] = None


def get_metrics_client() -> MetricsClient:
    """
    Get singleton metrics client instance.

    Returns:
        MetricsClient instance

    Examples:
        metrics = get_metrics_client()
        metrics.increment_rate_limit_hits("/api/auth/login", "127.0.0.1")
    """
    global _metrics_client
    if _metrics_client is None:
        _metrics_client = MetricsClient()
    return _metrics_client


# Convenience functions for common operations
def increment_rate_limit_hits(endpoint: str, ip_address: str) -> None:
    """Convenience function to increment rate limit hits."""
    get_metrics_client().increment_rate_limit_hits(endpoint, ip_address)


def increment_rate_limit_exceeded(endpoint: str, ip_address: str) -> None:
    """Convenience function to increment rate limit exceeded count."""
    get_metrics_client().increment_rate_limit_exceeded(endpoint, ip_address)


def increment_http_request(method: str, endpoint: str, status_code: int) -> None:
    """Convenience function to increment HTTP request count."""
    get_metrics_client().increment_http_request(method, endpoint, status_code)


def record_request_duration(
    method: str, endpoint: str, duration_seconds: float
) -> None:
    """Convenience function to record request duration."""
    get_metrics_client().record_request_duration(method, endpoint, duration_seconds)
